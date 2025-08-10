export const dynamic = "force-dynamic";

export async function POST(req: Request) {
  // In development, proxy to Python server
  // In production, Vercel routes directly to Python serverless function
  
  try {
    const body = await req.json();
    
    // Proxy to local Python server running on port 8080
    const pythonUrl = "http://localhost:8080/api/chat";
    const res = await fetch(pythonUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    
    if (!res.ok) {
      throw new Error(`Python server responded with status ${res.status}`);
    }
    
    const text = await res.text();
    return new Response(text, { 
      status: 200, 
      headers: { "Content-Type": "text/plain" } 
    });
    
  } catch (error) {
    return new Response(
      `❌ Chat API Error: ${error instanceof Error ? error.message : 'Unknown error'}\n\n` +
      `🛠️ For local development:\n` +
      `1. Run: python run-python-api.py\n` +
      `2. Then run: npm run dev\n\n` +
      `🚀 Or deploy to Vercel for production use.`, 
      { status: 500, headers: { "Content-Type": "text/plain" } }
    );
  }
}