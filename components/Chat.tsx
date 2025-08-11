"use client";
import { useChat } from "@ai-sdk/react";
import { TextStreamChatTransport } from "ai";
import type { UIMessage, UIMessagePart } from "ai";
import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Send, User, Bot } from "@/components/ui/icons";
import { cn } from "@/lib/utils";

export default function Chat() {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  
  // In development, use local server (FastAPI prefers /chat, BaseHTTPRequestHandler needs /api/chat)
  // In production, use Vercel's routed endpoint
  const apiEndpoint = process.env.NODE_ENV === 'development' 
    ? "http://localhost:8080/chat"  // FastAPI endpoint
    : "/api/chat";
    
  const { messages, sendMessage, status } = useChat({
    transport: new TextStreamChatTransport({ api: apiEndpoint }),
  });
  
  const [input, setInput] = useState("");

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && status === "ready") {
      sendMessage({ text: input });
      setInput("");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const isLoading = status === "streaming";

  return (
    <div className="flex flex-col h-[calc(100vh-2rem)] max-w-4xl mx-auto bg-background border border-border rounded-lg shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border bg-muted/30">
        <div className="flex items-center gap-2">
          <Bot size={24} className="text-primary" />
          <h1 className="text-lg font-semibold">AI Assistant</h1>
        </div>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <div className={cn(
            "w-2 h-2 rounded-full",
            status === "ready" ? "bg-green-500" : 
            status === "streaming" ? "bg-yellow-500" : "bg-red-500"
          )} />
          {status === "ready" ? "Ready" : 
           status === "streaming" ? "Thinking..." : "Disconnected"}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center space-y-4">
            <Bot size={48} className="text-muted-foreground" />
            <div className="space-y-2">
              <h3 className="text-lg font-medium">Welcome to AI Assistant</h3>
              <p className="text-muted-foreground max-w-md">
                Start a conversation by typing a message below. I can help you with questions, analysis, and various tasks.
              </p>
            </div>
          </div>
        ) : (
          messages.map((message: UIMessage<unknown>) => (
            <div key={message.id} className={cn(
              "flex gap-3 max-w-full",
              message.role === "user" ? "justify-end" : "justify-start"
            )}>
              {message.role === "assistant" && (
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                  <Bot size={16} className="text-primary" />
                </div>
              )}
              
              <div className={cn(
                "rounded-lg px-4 py-3 max-w-[70%] break-words",
                message.role === "user" 
                  ? "bg-primary text-primary-foreground ml-12" 
                  : "bg-muted"
              )}>
                {message.parts.map((part: UIMessagePart<Record<string, unknown>, Record<string, { input: unknown; output: unknown }>>, idx: number) => (
                  part.type === "text" ? (
                    <div key={idx} className="whitespace-pre-wrap">
                      {part.text}
                    </div>
                  ) : null
                ))}
              </div>

              {message.role === "user" && (
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center">
                  <User size={16} />
                </div>
              )}
            </div>
          ))
        )}
        
        {isLoading && (
          <div className="flex gap-3 justify-start">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
              <Bot size={16} className="text-primary" />
            </div>
            <div className="bg-muted rounded-lg px-4 py-3 flex items-center gap-2">
              <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
              <span className="text-muted-foreground">AI is thinking...</span>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-border p-4">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <div className="flex-1 relative">
            <Textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type your message here... (Press Enter to send, Shift+Enter for new line)"
              className="min-h-[50px] max-h-[150px] resize-none pr-12"
              disabled={status !== "ready"}
            />
            <Button
              type="submit"
              disabled={!input.trim() || status !== "ready"}
              className="absolute bottom-2 right-2 h-8 w-8 p-0"
            >
              <Send size={16} />
            </Button>
          </div>
        </form>
        <div className="text-xs text-muted-foreground mt-2 text-center">
          AI can make mistakes. Please verify important information.
        </div>
      </div>
    </div>
  );
}


