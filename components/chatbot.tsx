import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { MessageCircle } from "lucide-react";

export default function Chatbot({ paperId }: { paperId?: string }) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<{ role: "user" | "bot"; text: string }[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!input.trim()) return;
    setMessages((prev) => [...prev, { role: "user", text: input }]);
    setLoading(true);
    try {
      // Send request directly to backend FastAPI server where the RAG pipeline runs
      const res = await fetch("http://127.0.0.1:8000/api/chat_pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: input, paper_id: paperId }),
      });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(`HTTP ${res.status}: ${text}`);
      }
      const data = await res.json();
      setMessages((prev) => [...prev, { role: "bot", text: data.answer ?? "(no answer returned)" }]);
    } catch (err: any) {
      console.error('chatbot request failed', err);
      setMessages((prev) => [...prev, { role: "bot", text: `Error: Could not get answer. ${err?.message ?? ''}` }]);
    }
    setInput("");
    setLoading(false);
  };

  return (
    <>
      <Button
        className="fixed bottom-8 right-8 z-50 rounded-full p-4 bg-purple-600 hover:bg-purple-700 shadow-lg"
        onClick={() => setOpen(true)}
      >
        <MessageCircle className="h-6 w-6 text-white" />
      </Button>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-w-md w-full">
          <DialogHeader>
            <DialogTitle>Ask about this paper</DialogTitle>
          </DialogHeader>
          <div className="flex flex-col gap-4 h-96 overflow-y-auto border rounded p-2 bg-gray-50">
            {messages.map((msg, i) => (
              <div key={i} className={`text-sm p-2 rounded ${msg.role === "user" ? "bg-purple-100 text-right" : "bg-white text-left"}`}>
                {msg.text}
              </div>
            ))}
          </div>
          <div className="flex gap-2 mt-2">
            <input
              type="text"
              className="flex-1 border rounded p-2"
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Ask anything about the paper..."
              disabled={loading}
              onKeyDown={e => { if (e.key === "Enter") handleSend(); }}
            />
            <Button onClick={handleSend} disabled={loading || !input.trim()} className="bg-purple-600 text-white">
              Send
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
