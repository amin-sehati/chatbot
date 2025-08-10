export const dynamic = "force-dynamic";

export async function POST(req: Request) {
  const body = await req.json();
  const { messages } = body;

  if (!process.env.OPENAI_API_KEY) {
    return new Response("OpenAI API key not configured", { status: 500 });
  }

  const openAIMessages = messages.map((m: { role: string; content: string }) => ({
    role: m.role,
    content: m.content,
  }));

  const response = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${process.env.OPENAI_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: "gpt-4o-mini",
      messages: openAIMessages,
    }),
  });

  const data = await response.json();
  const content = data.choices?.[0]?.message?.content || "No response";
  
  return new Response(content, { status: 200, headers: { "Content-Type": "text/plain" } });
}
