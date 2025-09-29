import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/components/auth/AuthProvider";
import ReactMarkdown from "react-markdown";
import { Bot } from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";

const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";

interface Message {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
}

export default function ChatSession() {
  const { id } = useParams<{ id: string }>();
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const { session, user } = useAuth();

  useEffect(() => {
    const fetchMessages = async () => {
      if (!id || !session) return;
      setLoading(true);
      try {
        const res = await fetch(`${apiUrl}/sessions/${id}`, {
          headers: {
            Authorization: `Bearer ${session.access_token}`,
          },
        });
        if (!res.ok) throw new Error("Failed to load messages");
        const data = await res.json();
        setMessages(data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };

    fetchMessages();
  }, [id, session]);

  return (
    <div className="container mx-auto p-4">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">Chat Session</h1>
        <Link to="/dashboard/chats">
          <Button>Back to Past Chats</Button>
        </Link>
      </div>
      {loading && <p>Loading...</p>}
      <div className="space-y-4 max-w-3xl mx-auto">
        {messages.map((m) => (
          <div
            key={m.id}
            className={`flex gap-3 ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {m.role === 'assistant' && (
              <Avatar className="h-8 w-8 mt-1">
                <AvatarFallback className="bg-primary text-primary-foreground">
                  <Bot className="h-4 w-4" />
                </AvatarFallback>
              </Avatar>
            )}
            
            <Card className={`max-w-[80%] p-4 ${
              m.role === 'user' 
                ? 'bg-primary text-primary-foreground' 
                : 'bg-card'
            }`}>
              <div className="prose prose-sm dark:prose-invert max-w-none prose-force-white">
                <ReactMarkdown>{m.content}</ReactMarkdown>
              </div>
              <div className="text-xs opacity-70 mt-2">
                {new Date(m.created_at).toLocaleString()}
              </div>
            </Card>
            
            {m.role === 'user' && (
              <Avatar className="h-8 w-8 mt-1">
                <AvatarFallback className="bg-secondary">
                  {user?.email?.charAt(0).toUpperCase() || 'U'}
                </AvatarFallback>
              </Avatar>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
