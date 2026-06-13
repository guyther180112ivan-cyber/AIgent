'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useRouter } from 'next/navigation';
import {
  Bot,
  Zap,
  Wrench,
  Brain,
  Calendar,
  Bell,
  LogOut,
  ChevronRight,
  X,
  Download,
  BellRing,
} from 'lucide-react';
import { usePwaInstall, usePushSubscription } from '@/components/PwaRegister';

const NAV_ITEMS = [
  { href: '/agents', label: 'Агенты', icon: Bot },
  { href: '/skills', label: 'Навыки', icon: Zap },
  { href: '/tools', label: 'Инструменты', icon: Wrench },
  { href: '/memory', label: 'Память', icon: Brain },
  { href: '/scheduler', label: 'Расписание', icon: Calendar },
  { href: '/reminders', label: 'Напоминания', icon: Bell },
];

interface SidebarProps {
  user: {
    id: string;
    email: string;
    user_metadata?: Record<string, string>;
  };
  isOpen: boolean;
  onClose: () => void;
}

export default function Sidebar({ user, isOpen, onClose }: SidebarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { canInstall, install } = usePwaInstall();
  const { supported: pushSupported, enabled: pushEnabled, subscribe } = usePushSubscription();

  const handleLogout = async () => {
    await fetch('/api/auth/logout', { method: 'POST' });
    router.push('/login');
    router.refresh();
  };

  const handleNavClick = () => {
    onClose();
  };

  const displayName = user.user_metadata?.username || user.email;

  return (
    <>
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/60 z-40 md:hidden"
          onClick={onClose}
        />
      )}
      <aside
        className={`
          fixed inset-y-0 left-0 z-50 w-64 bg-gray-900 border-r border-gray-800 flex flex-col
          transition-transform duration-300 ease-in-out
          md:static md:translate-x-0
          ${isOpen ? 'translate-x-0' : '-translate-x-full'}
        `}
      >
        <div className="flex items-center justify-between p-4 border-b border-gray-800 md:p-6">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-indigo-500/30 flex-shrink-0">
              <Bot className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="font-bold text-white text-sm">AIgent</h2>
              <p className="text-xs text-gray-500">Platform v3</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="md:hidden text-gray-400 hover:text-white p-1"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <nav className="flex-1 p-3 space-y-1 md:p-4">
          {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
            const isActive = pathname.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                onClick={handleNavClick}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all group ${
                  isActive
                    ? 'bg-indigo-600/20 text-indigo-400 border border-indigo-500/20'
                    : 'text-gray-400 hover:text-white hover:bg-gray-800'
                }`}
              >
                <Icon className={`w-4 h-4 flex-shrink-0 ${isActive ? 'text-indigo-400' : ''}`} />
                <span className="flex-1">{label}</span>
                {isActive && (
                  <ChevronRight className="w-3 h-3 text-indigo-400" />
                )}
              </Link>
            );
          })}
        </nav>

        {(canInstall || (pushSupported && !pushEnabled)) && (
          <div className="px-3 space-y-1 md:px-4">
            {canInstall && (
              <button
                onClick={install}
                className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all text-gray-400 hover:text-white hover:bg-gray-800"
              >
                <Download className="w-4 h-4 flex-shrink-0" />
                <span>Установить приложение</span>
              </button>
            )}
            {pushSupported && !pushEnabled && (
              <button
                onClick={subscribe}
                className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all text-gray-400 hover:text-white hover:bg-gray-800"
              >
                <BellRing className="w-4 h-4 flex-shrink-0" />
                <span>Включить уведомления</span>
              </button>
            )}
          </div>
        )}

        <div className="p-3 border-t border-gray-800 md:p-4">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-8 h-8 bg-gray-700 rounded-full flex items-center justify-center text-xs font-bold text-gray-300 uppercase flex-shrink-0">
              {displayName?.[0] || 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-white truncate">{displayName}</p>
              <p className="text-xs text-gray-500">Пользователь</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-400 hover:text-red-400 hover:bg-red-900/20 rounded-xl transition"
          >
            <LogOut className="w-4 h-4" />
            Выйти
          </button>
        </div>
      </aside>
    </>
  );
}
