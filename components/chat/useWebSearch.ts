import { useState, useCallback } from 'react';

export interface WebSearchResult {
  title: string;
  url: string;
  snippet: string;
}

export interface WebSearchResponse {
  results: WebSearchResult[];
  query: string;
}

function extractActualUrl(duckduckgoUrl: string): string {
  try {
    const url = new URL(duckduckgoUrl.startsWith('//') ? 'https:' + duckduckgoUrl : duckduckgoUrl);
    const uddg = url.searchParams.get('uddg');
    return uddg ? decodeURIComponent(uddg) : duckduckgoUrl;
  } catch {
    return duckduckgoUrl;
  }
}

async function parseSearchResults(html: string, limit: number): Promise<WebSearchResult[]> {
  const results: WebSearchResult[] = [];
  
  const titleUrlRegex = /<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>([^<]+)<\/a>/g;
  let match;
  
  while ((match = titleUrlRegex.exec(html)) !== null && results.length < limit) {
    const href = match[1];
    const title = match[2].trim();
    
    if (href && title) {
      results.push({
        url: extractActualUrl(href),
        title,
        snippet: '',
      });
    }
  }
  
  const snippetRegex = /<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>[\s\S]*?<a[^>]*class="result__snippet"[^>]*>([^<]+)<\/a>/g;
  
  while ((match = snippetRegex.exec(html)) !== null && results.length < limit) {
    const href = match[1];
    const title = match[2].trim();
    const snippetMatch = match[0].match(/class="result__snippet"[^>]*>([^<]+)<\/a>/);
    const snippet = snippetMatch ? snippetMatch[1].trim() : '';
    
    const existingIndex = results.findIndex(r => r.title === title);
    
    if (existingIndex >= 0) {
      results[existingIndex].snippet = snippet;
    } else if (href && title) {
      results.push({
        url: extractActualUrl(href),
        title,
        snippet,
      });
    }
  }

  return results;
}

export async function webSearch(query: string, limit: number = 5): Promise<WebSearchResponse> {
  if (!query || query.trim().length === 0) {
    return { results: [], query };
  }

  try {
    const encodedQuery = encodeURIComponent(query);
    
    const response = await fetch(
      `https://html.duckduckgo.com/html/?q=${encodedQuery}`,
      {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        },
      }
    );

    if (!response.ok) {
      throw new Error(`DuckDuckGo error: ${response.status}`);
    }

    const html = await response.text();
    const results = await parseSearchResults(html, limit);

    return { results, query };
  } catch (error) {
    console.error('[WebSearch] Ошибка:', error);
    return { results: [], query };
  }
}

export function formatSearchResults(response: WebSearchResponse): string {
  if (response.results.length === 0) {
    return `По запросу "${response.query}" ничего не найдено.`;
  }

  const formatted = response.results.map((r, i) => {
    const snippet = r.snippet ? `\n   Кратко: ${r.snippet}` : '';
    return `${i + 1}. **${r.title}**\n   Ссылка: ${r.url}${snippet}`;
  }).join('\n\n');

  return `Результаты поиска по запросу "${response.query}":\n\n${formatted}\n\nИспользуй эту актуальную информацию для ответа на вопрос пользователя.`;
}

export function useWebSearch() {
  const [searching, setSearching] = useState(false);

  const search = useCallback(async (query: string): Promise<WebSearchResponse> => {
    setSearching(true);
    try {
      return await webSearch(query);
    } finally {
      setSearching(false);
    }
  }, []);

  return { search, searching };
}