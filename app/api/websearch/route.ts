import { NextResponse } from 'next/server';
import { webSearch } from '@/lib/websearch';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const query = searchParams.get('q') || 'test';
  const debug = searchParams.get('debug');

  console.log('[websearch-api] Starting search for:', query);
  
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