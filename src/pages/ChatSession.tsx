import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Card, CardContent } from "@/components/ui/card";
import { useAuth } from "@/components/auth/AuthProvider";

interface Message {
  id: number;
  role: string;
  content: string;
  created_at: string;
}

export default function ChatSession() {
  const { id } = useParams<{ id: string }>();
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const { session } = useAuth();

  useEffect(() => {
    const fetchMessages = async () => {
      if (!id || !session) return;
      setLoading(true);
      try {
        const res = await fetch(`http://localhost:8001/sessions/${id}`, {
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
      <h1 className="text-2xl font-bold mb-4">Chat Session</h1>
      {loading && <p>Loading...</p>}
      <div className="space-y-3">
        {messages.map((m) => (
          <Card key={m.id} className={m.role === 'user' ? 'bg-primary text-primary-foreground p-4' : 'p-4'}>
            <CardContent>
              <p>{m.content}</p>
              <div className="text-xs opacity-70 mt-2">{new Date(m.created_at).toLocaleString()}</div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
