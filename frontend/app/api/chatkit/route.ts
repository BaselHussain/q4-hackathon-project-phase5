import { NextRequest } from 'next/server';

/**
 * Proxy endpoint for ChatKit requests
 * Forwards all requests to the backend ChatKit endpoint
 * This bypasses domain key requirements for local development
 */
export async function POST(request: NextRequest) {
  const backendUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8002';

  try {
    // Get the request body
    const body = await request.text();

    // Forward all headers from the original request
    const headers = new Headers();
    request.headers.forEach((value, key) => {
      // Skip host header to avoid conflicts
      if (key.toLowerCase() !== 'host') {
        headers.set(key, value);
      }
    });

    // Forward the request to the backend
    const response = await fetch(`${backendUrl}/chatkit`, {
      method: 'POST',
      headers,
      body,
    });

    // Return the response with the same status and headers
    const responseHeaders = new Headers();
    response.headers.forEach((value, key) => {
      responseHeaders.set(key, value);
    });

    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: responseHeaders,
    });
  } catch (error: any) {
    console.error('ChatKit proxy error:', error);
    return new Response(
      JSON.stringify({ error: 'Failed to proxy request to backend' }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    );
  }
}

export async function OPTIONS(_request: NextRequest) {
  return new Response(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    },
  });
}
