import { NextResponse } from 'next/server';
import { writeFile, mkdir } from 'fs/promises';
import path from 'path';
import crypto from 'crypto';
import mammoth from 'mammoth';

const MAX_SIZE = 10 * 1024 * 1024;

const TEXT_EXTS = new Set([
  '.txt', '.md', '.csv', '.json', '.xml', '.yaml', '.yml',
  '.js', '.ts', '.jsx', '.tsx', '.py', '.rb', '.java',
  '.c', '.cpp', '.h', '.hpp', '.html', '.css', '.scss',
  '.sql', '.sh', '.bash', '.env', '.cfg', '.ini', '.toml',
]);

function isTextFile(name: string, mime: string): boolean {
  const ext = name.toLowerCase().split('.').pop();
  return TEXT_EXTS.has(`.${ext}`) || mime.startsWith('text/');
}

async function extractDocxText(buffer: Buffer): Promise<string> {
  const result = await mammoth.extractRawText({ buffer });
  return result.value;
}

export async function POST(request: Request) {
  try {
    const formData = await request.formData();
    const file = formData.get('file') as File | null;
    if (!file) {
      return NextResponse.json({ error: 'Файл не найден' }, { status: 400 });
    }

    if (file.size > MAX_SIZE) {
      return NextResponse.json({ error: 'Файл слишком большой (макс. 10MB)' }, { status: 400 });
    }

    const ext = path.extname(file.name).toLowerCase();
    const id = crypto.randomUUID();
    const safeName = `${id}${ext}`;

    const uploadDir = path.join(process.cwd(), 'public', 'uploads');
    await mkdir(uploadDir, { recursive: true });

    const buffer = Buffer.from(await file.arrayBuffer());
    await writeFile(path.join(uploadDir, safeName), buffer);

    let content: string | undefined;
    if (isTextFile(file.name, file.type)) {
      content = buffer.toString('utf-8');
    } else if (ext === '.docx') {
      try {
        content = await extractDocxText(buffer);
      } catch (docxErr) {
        console.error('[Upload] docx parse error:', docxErr);
        content = `[Ошибка чтения .docx файла: файл повреждён или имеет неподдерживаемый формат]`;
      }
    }

    return NextResponse.json({
      id,
      name: file.name,
      size: file.size,
      type: file.type,
      url: `/uploads/${safeName}`,
      content,
    });
  } catch (error) {
    console.error('[Upload] Ошибка:', error);
    return NextResponse.json({ error: 'Ошибка загрузки файла' }, { status: 500 });
  }
}