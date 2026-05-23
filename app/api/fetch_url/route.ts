import { NextResponse } from 'next/server';

function extractText(html: string): string {
  const withoutScripts = html.replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '');
  const withoutStyles = withoutScripts.replace(/<style[^>]*>[\s\S]*?<\/style>/gi, '');
  const withoutTags = withoutStyles.replace(/<[^>]+>/g, ' ');
  const decoded = withoutTags
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#x27;/g, "'")
    .replace(/&#39;/g, "'");
  return decoded.replace(/\s+/g, ' ').trim();
}

function extractUrl(text: string): string | null {
  const urlRegex = /https?:\/\/[^\s<>"']+/i;
  const match = text.match(urlRegex);
  return match ? match[0].replace(/[.,;:!?)]+$/, '') : null;
}

async function fetchPage(url: string): Promise<{ content: string; title: string }> {
  const response = await fetch(url, {
    headers: {
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
      'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    },
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }

  const html = await response.text();
  const titleMatch = html.match(/<title[^>]*>([^<]+)<\/title>/i);
  const title = titleMatch ? titleMatch[1].trim() : url;
  const content = extractText(html);

  return { title, content };
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const url = searchParams.get('url');
  const raw = searchParams.get('raw');

  const targetUrl = url || (raw ? extractUrl(raw) : null);

  if (!targetUrl) {
    return NextResponse.json(
      { error: 'Параметр url обязателен' },
      { status: 400 }
    );
  }

  try {
    new URL(targetUrl);
  } catch {
    return NextResponse.json(
      { error: 'Некорректный URL' },
      { status: 400 }
    );
  }

  try {
    const result = await fetchPage(targetUrl);
    const truncated = result.content.length > 15000
      ? result.content.substring(0, 15000) + '\n\n[Содержимое обрезано — превышен лимит 15000 символов]'
      : result.content;

    return NextResponse.json({
      url: targetUrl,
      title: result.title,
      content: truncated,
    });
  } catch (error: any) {
    console.error('[FetchURL] Ошибка:', error);
    return NextResponse.json(
      { error: `Не удалось загрузить страницу: ${error.message}` },
      { status: 502 }
    );
  }
}