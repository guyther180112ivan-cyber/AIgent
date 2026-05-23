import { NextResponse } from 'next/server';
import { webSearch, weatherSearch, formatWeatherData, formatSearchResults } from '@/lib/websearch';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const query = searchParams.get('q') || 'test';
  const mode = searchParams.get('mode') || 'web';
  const debug = searchParams.get('debug');

  console.log('[websearch-api] Mode:', mode, 'Query:', query);

  if (mode === 'weather') {
    const result = await weatherSearch(query);
    if (result.success && result.data) {
      return NextResponse.json({
        query,
        type: 'weather',
        formatted: formatWeatherData(result.data),
        data: result.data,
      });
    }
    return NextResponse.json({ query, type: 'weather', error: result.error || 'Не найдено' });
  }

  const results = await webSearch(query, 5);
  console.log('[websearch-api] Results count:', results.results.length);

  if (debug === 'true') {
    return NextResponse.json({
      query,
      results,
      message: 'Check server console for logs',
    });
  }

  return NextResponse.json(results);
}