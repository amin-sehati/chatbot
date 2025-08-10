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

  const baseUrl = req.url ? new URL(req.url).origin : 'http://localhost:3001';
  const res = await fetch(`${baseUrl}/pychat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages: pyMessages }),
  });
  // Expect plain text from the Python API now
  const text = await res.text();
  return new Response(text, { status: res.status, headers: { "Content-Type": "text/plain" } });
}


