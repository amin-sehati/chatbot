export const dynamic = "force-dynamic";

export async function POST(req: Request) {
  const body = await req.json();
  type UIPart = { type: "text"; text: string } | { type: string };
  type UIMessage = { role: string; parts?: UIPart[]; content?: string };
  const uiMessages: UIMessage[] = Array.isArray((body as { messages?: unknown })?.messages) ? (body as { messages: UIMessage[] }).messages : [];
  const pyMessages = uiMessages.map((m) => ({
    role: m.role,
    content: Array.isArray(m.parts)
      ? m.parts
          .filter((p): p is Extract<UIPart, { type: "text" }> => p?.type === "text")
          .map((p) => p.text || "")
          .join("")
      : m.content ?? "",
  }));

  const isVercel = !!process.env.VERCEL_URL;
  
  if (isVercel) {
    // On Vercel, call OpenAI directly
    if (!process.env.OPENAI_API_KEY) {
      return new Response("OpenAI API key not configured", { status: 500 });
    }

    const response = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${process.env.OPENAI_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: "gpt-4o-mini",
        messages: pyMessages,
      }),
    });

    const data = await response.json();
    const content = data.choices?.[0]?.message?.content || "No response";
    
    return new Response(content, { status: 200, headers: { "Content-Type": "text/plain" } });
  } else {
    // Local development - call Python FastAPI
    const res = await fetch("http://127.0.0.1:8000/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages: pyMessages }),
    });
    const text = await res.text();
    return new Response(text, { status: res.status, headers: { "Content-Type": "text/plain" } });
  }
}


