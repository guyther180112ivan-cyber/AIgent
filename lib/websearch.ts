export interface WebSearchResult {
  title: string;
  url: string;
  snippet: string;
}

export interface WebSearchResponse {
  results: WebSearchResult[];
  query: string;
}

export interface WeatherData {
  city: string;
  current: string;
  forecast: { date: string; avgTemp: string; maxTemp: string; minTemp: string; desc: string }[];
  source: 'wttrin';
}

function extractBingUrl(bingUrl: string): string {
  try {
    const unescaped = bingUrl.replace(/&amp;/g, '&');
    const url = new URL(unescaped);
    const uParam = url.searchParams.get('u');
    if (uParam) {
      const b64 = uParam.replace(/^[a-z0-9]{0,2}/i, '');
      const decoded = Buffer.from(b64, 'base64').toString('utf8');
      if (decoded.startsWith('http://') || decoded.startsWith('https://')) return decoded;
    }
    return bingUrl;
  } catch {
    return bingUrl;
  }
}

export async function webSearch(query: string, limit: number = 5): Promise<WebSearchResponse> {
  if (!query || query.trim().length === 0) {
    return { results: [], query };
  }

  try {
    const encodedQuery = encodeURIComponent(query);

    const response = await fetch(
      `https://www.bing.com/search?q=${encodedQuery}&count=${limit}&setlang=ru&cc=RU&mkt=ru-RU`,
      {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
          'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
          'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        },
      }
    );

    if (!response.ok) {
      throw new Error(`Bing error: ${response.status}`);
    }

    const html = await response.text();
    const results: WebSearchResult[] = [];

    const liRegex = /<li class="b_algo"[^>]*>([\s\S]*?)<\/li>/gi;
    let match;

    while ((match = liRegex.exec(html)) !== null && results.length < limit) {
      const item = match[1];

      const aMatch = item.match(/<a[^>]*href="([^"]+)"[^>]*>([\s\S]*?)<\/a>/i);
      const pMatch = item.match(/<p[^>]*>([\s\S]*?)<\/p>/i);

      if (aMatch) {
        const rawUrl = aMatch[1];
        const title = aMatch[2].replace(/<[^>]+>/g, '').trim();
        const snippet = pMatch ? pMatch[1].replace(/<[^>]+>/g, '').trim() : '';

        if (title && rawUrl && !rawUrl.startsWith('#')) {
          results.push({
            url: extractBingUrl(rawUrl),
            title,
            snippet,
          });
        }
      }
    }

    return { results, query };
  } catch (error) {
    console.error('[WebSearch] Ошибка Bing поиска:', error);
    return { results: [], query };
  }
}

const WEATHER_CITIES: Record<string, string> = {
  'москве': 'Москва',
  'москва': 'Москва',
  'moscow': 'Moscow',
  'спб': 'Санкт-Петербург',
  'питер': 'Санкт-Петербург',
  'санкт-петербург': 'Санкт-Петербург',
  'saint petersburg': 'Saint Petersburg',
  'new york': 'New York',
  'нью йорк': 'New York',
  'нью-йорк': 'New York',
  'london': 'London',
  'лондон': 'London',
  'париж': 'Paris',
  'paris': 'Paris',
  'берлин': 'Berlin',
  'berlin': 'Berlin',
  'пекин': 'Beijing',
  'beijing': 'Beijing',
  'tokyo': 'Tokyo',
  'токио': 'Tokyo',
};

function extractCity(query: string): string | null {
  const lower = query.toLowerCase();
  for (const [key, city] of Object.entries(WEATHER_CITIES)) {
    if (lower.includes(key)) return city;
  }
  const match = lower.match(/в\s+([а-яёa-z\-]+)/i);
  if (match) return match[1];
  return null;
}

export async function weatherSearch(query: string): Promise<{ success: boolean; data?: WeatherData; error?: string }> {
  const city = extractCity(query);
  if (!city) return { success: false, error: 'Город не найден' };

  try {
    const encoded = encodeURIComponent(city);
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 5000);
    const response = await fetch(`https://wttr.in/${encoded}?format=j1&lang=ru`, { signal: controller.signal });
    clearTimeout(timeout);
    if (!response.ok) throw new Error(`wttr.in error: ${response.status}`);

    const data = await response.json();
    const current = data.current_condition?.[0];
    const forecast = (data.weather || []).map((w: any) => ({
      date: w.date,
      avgTemp: `${w.avgtempC}°C`,
      maxTemp: `${w.maxtempC}°C`,
      minTemp: `${w.mintempC}°C`,
      desc: w.hourly?.[0]?.weatherDesc?.[0]?.value || '',
    }));

    return {
      success: true,
      data: {
        city: data.nearest_area?.[0]?.areaName?.[0]?.value || city,
        current: current ? `${current.temp_C}°C, ${current.weatherDesc?.[0]?.value || ''}, ветер ${current.windspeedKmph} км/ч, влажность ${current.humidity}%` : 'Нет данных',
        forecast,
        source: 'wttrin',
      },
    };
  } catch (error) {
    console.error('[WeatherSearch] Ошибка:', error);
    return { success: false, error: String(error) };
  }
}

export function formatWeatherData(data: WeatherData): string {
  const lines = [`Погода в ${data.city}:`];
  lines.push(`Сейчас: ${data.current}`);
  lines.push('');
  lines.push('Прогноз:');
  for (const day of data.forecast) {
    lines.push(`  ${day.date}: ${day.avgTemp} (${day.minTemp}–${day.maxTemp}), ${day.desc}`);
  }
  return lines.join('\n');
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