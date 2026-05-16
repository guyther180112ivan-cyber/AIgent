#!/bin/bash
# Скрипт деплоя AIgent Platform на VPS
# Запуск: bash deploy.sh

VPS_IP="64.188.116.102"
VPS_USER="root"
PROJECT_NAME="aigent"
PROJECT_DIR="/opt/$PROJECT_NAME"

echo "=== Деплой AIgent Platform на $VPS_IP ==="

# 1. Подключение к VPS и установка зависимостей
ssh $VPS_USER@$VPS_IP << 'ENDSSH'
set -e

echo "--- Обновление системы ---"
apt update && apt upgrade -y

echo "--- Установка Node.js 20.x ---"
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs

echo "--- Установка PM2 ---"
npm install -g pm2

echo "--- Создание директории проекта ---"
mkdir -p $PROJECT_DIR

echo "--- Установка зависимостей готово ---"
ENDSSH

if [ $? -ne 0 ]; then
    echo "Ошибка подключения к VPS!"
    exit 1
fi

echo "--- Архивирование проекта ---"
tar czf /tmp/$PROJECT_NAME.tar.gz \
    --exclude='node_modules' \
    --exclude='.next' \
    --exclude='data' \
    --exclude='legacy' \
    --exclude='.git' \
    .

echo "--- Копирование на VPS ---"
scp /tmp/$PROJECT_NAME.tar.gz $VPS_USER@$VPS_IP:/tmp/

echo "--- Распаковка и установка на VPS ---"
ssh $VPS_USER@$VPS_IP << 'ENDSSH'
set -e

cd $PROJECT_DIR
tar xzf /tmp/$PROJECT_NAME.tar.gz

echo "--- Установка npm зависимостей ---"
npm install --production

echo "--- Создание .env.production ---"
cat > .env.production << 'EOF'
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
OPENROUTER_API_KEY=your_openrouter_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
NEXT_PUBLIC_APP_URL=http://64.188.116.102
JWT_SECRET=change-this-to-random-string-in-production-$(openssl rand -hex 32)
TOOLHOUSE_API_KEY=
NODE_ENV=production
EOF

echo "--- Сборка проекта ---"
npm run build

echo "--- Запуск через PM2 ---"
pm2 delete $PROJECT_NAME 2>/dev/null || true
pm2 start npm --name "$PROJECT_NAME" -- start -- -p 3000
pm2 save
pm2 startup

echo "--- Установка Nginx ---"
apt install -y nginx

cat > /etc/nginx/sites-available/$PROJECT_NAME << 'EOF'
server {
    listen 80;
    server_name 64.188.116.102;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
EOF

ln -sf /etc/nginx/sites-available/$PROJECT_NAME /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

echo ""
echo "=== Деплой завершён! ==="
echo "Проект доступен на: http://64.188.116.102"
echo ""
echo "Полезные команды:"
echo "  pm2 status              - статус приложения"
echo "  pm2 logs $PROJECT_NAME  - логи приложения"
echo "  pm2 restart $PROJECT_NAME - перезапуск"
echo "  systemctl status nginx  - статус nginx"

ENDSSH

# Очистка
rm -f /tmp/$PROJECT_NAME.tar.gz

echo "Готово!"
