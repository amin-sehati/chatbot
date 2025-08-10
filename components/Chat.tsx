"use client";
import { useChat } from "@ai-sdk/react";
import { TextStreamChatTransport } from "ai";
import type { UIMessage, UIMessagePart } from "ai";
import { useState } from "react";

export default function Chat() {
  const api = process.env.NODE_ENV === "development" ? "/api/dev-chat" : "/api/chat";
  const { messages, sendMessage, status } = useChat({
    transport: new TextStreamChatTransport({ api }),
  });
  const [input, setInput] = useState("");

  return (
    <div className="mx-auto max-w-2xl w-full h-[80vh] flex flex-col gap-4 p-4">
      <div className="flex-1 overflow-y-auto space-y-3">
        {messages.map((message: UIMessage<unknown>) => (
          <div key={message.id} className={message.role === "user" ? "text-right" : "text-left"}>
            <div className="inline-block rounded-lg px-3 py-2 bg-gray-100 dark:bg-gray-800">
              {message.parts.map((part: UIMessagePart<Record<string, unknown>, Record<string, { input: unknown; output: unknown }>>, idx: number) => (
                part.type === "text" ? <span key={idx}>{part.text}</span> : null
              ))}
            </div>
          </div>
        ))}
      </div>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (input.trim()) {
            sendMessage({ text: input });
            setInput("");
          }
        }}
        className="flex gap-2"
      >
        <input
          className="flex-1 rounded-md border px-3 py-2"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Say something..."
          disabled={status !== "ready"}
        />
        <button className="rounded-md bg-black text-white px-4 py-2 disabled:opacity-50" type="submit" disabled={status !== "ready"}>
          Submit
        </button>
      </form>
    </div>
  );
}


