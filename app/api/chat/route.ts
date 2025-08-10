export const dynamic = "force-dynamic";

export async function POST(req: Request) {
  const body = await req.json();
  const uiMessages = Array.isArray(body?.messages) ? body.messages : [];
  const pyMessages = uiMessages.map((m: any) => ({
    role: m?.role,
    content: Array.isArray(m?.parts)
      ? m.parts.filter((p: any) => p?.type === "text").map((p: any) => p?.text || "").join("")
      : (m?.content ?? ""),
  }));

  const isVercel = !!process.env.VERCEL_URL;
  const target = isVercel
    ? `https://${process.env.VERCEL_URL}/api/py_chat`
    : "http://127.0.0.1:8000/";

  const res = await fetch(target, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages: pyMessages }),
  });
  const text = await res.text();
  return new Response(text, { status: res.status, headers: { "Content-Type": "text/plain" } });
}


