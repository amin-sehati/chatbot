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

  const res = await fetch("http://127.0.0.1:8000/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages: pyMessages }),
  });
  // Expect plain text from the Python API now
  const text = await res.text();
  return new Response(text, { status: res.status, headers: { "Content-Type": "text/plain" } });
}


