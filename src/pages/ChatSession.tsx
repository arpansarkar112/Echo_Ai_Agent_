import { useEffect, useState, useRef } from "react";
import { Link, useParams } from "react-router-dom";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/components/auth/AuthProvider";
import ReactMarkdown from "react-markdown";
import { Bot, Send } from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";

const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";

interface Message {
  id: number | string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
}

export default function ChatSession() {
  const { id: sessionId } = useParams<{ id: string }>();
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [inputValue, setInputValue] = useState("");
  const [isSending, setIsSending] = useState(false);
  const { session, user } = useAuth();
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTo({
        top: scrollAreaRef.current.scrollHeight,
        behavior: "smooth",
      });
    }
  };

  useEffect(() => {
    const fetchMessages = async () => {
      if (!sessionId || !session) return;
      setLoading(true);
      try {
        const res = await fetch(`${apiUrl}/sessions/${sessionId}`, {
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
  }, [sessionId, session]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || !sessionId) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue,
      created_at: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    const currentInputValue = inputValue;
    setInputValue("");
    setIsSending(true);

    try {
      const response = await fetch(`${apiUrl}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: session ? `Bearer ${session.access_token}` : "",
        },
        body: JSON.stringify({ message: currentInputValue, session_id: sessionId }),
      });

      if (!response.ok) {
        throw new Error('Failed to get response from the server.');
      }

      const data = await response.json();

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.response || "Sorry, I couldn't get a response.",
        created_at: new Date().toISOString()
      };
      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error("Error sending message:", error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: "Sorry, something went wrong. Please try again.",
        created_at: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsSending(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)]">
      <div className="p-4 border-b">
        <div className="container mx-auto flex justify-between items-center">
          <h1 className="text-2xl font-bold">Chat Session</h1>
          <Link to="/dashboard/chats">
            <Button>Back to Past Chats</Button>
          </Link>
        </div>
      </div>
      
      <ScrollArea className="flex-1 p-4" ref={scrollAreaRef}>
        <div className="space-y-4 max-w-3xl mx-auto">
          {loading && <p className="text-center">Loading chat history...</p>}
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
          
          {isSending && (
            <div className="flex gap-3 justify-start">
              <Avatar className="h-8 w-8 mt-1">
                <AvatarFallback className="bg-primary text-primary-foreground">
                  <Bot className="h-4 w-4" />
                </AvatarFallback>
              </Avatar>
              <Card className="p-4 bg-card">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-primary rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                  <div className="w-2 h-2 bg-primary rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                  <div className="w-2 h-2 bg-primary rounded-full animate-bounce"></div>
                </div>
              </Card>
            </div>
          )}
        </div>
      </ScrollArea>
      
      <div className="border-t bg-card/50 p-4">
        <div className="max-w-3xl mx-auto flex gap-2">
          <Input
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Continue this conversation..."
            className="flex-1"
            disabled={isSending}
          />
          <Button 
            onClick={handleSendMessage} 
            disabled={!inputValue.trim() || isSending}
            className="gradient-primary hover:shadow-glow"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
