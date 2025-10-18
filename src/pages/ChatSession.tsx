import { useEffect, useState, useRef, type ChangeEvent, type KeyboardEvent } from "react";
import { Link, useParams } from "react-router-dom";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/components/auth/AuthProvider";
import ReactMarkdown from "react-markdown";
import { Bot, Download, Send, Upload } from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import {
  allowDataUrl,
  markdownComponents,
  markdownPlugins,
} from "@/components/chat/markdown";
const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";

interface Message {
  id: number | string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
}

interface SessionDataset {
  dataset_id: string;
  filename: string;
  rows: number;
  columns: number;
  created_at: string;
}

interface CSVUploadResponse {
  dataset_id: string;
  filename: string;
  rows: number;
  columns: number;
  summary: string;
  preview_table: string;
}

export default function ChatSession() {
  const { id: sessionId } = useParams<{ id: string }>();
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [inputValue, setInputValue] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [datasets, setDatasets] = useState<SessionDataset[]>([]);
  const [activeDatasetId, setActiveDatasetId] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const { session, user } = useAuth();
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const activeDataset = activeDatasetId
    ? datasets.find((dataset) => dataset.dataset_id === activeDatasetId) ?? null
    : null;

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

  useEffect(() => {
    const fetchDatasets = async () => {
      if (!sessionId || !session) return;
      try {
        const res = await fetch(`${apiUrl}/agent/csv/session/${sessionId}`, {
          headers: {
            Authorization: `Bearer ${session.access_token}`,
          },
        });
        if (!res.ok) throw new Error("Failed to load CSV datasets for this session");
        const data: SessionDataset[] = await res.json();
        setDatasets(data);
        setActiveDatasetId((current) => current ?? (data[0]?.dataset_id ?? null));
      } catch (error) {
        console.error(error);
      }
    };

    fetchDatasets();
  }, [sessionId, session]);

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !sessionId || !session) return;

    setIsUploading(true);
    try {
      const formData = new FormData();
      formData.append("session_id", sessionId);
      formData.append("file", file);

      const res = await fetch(`${apiUrl}/agent/csv/upload`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${session.access_token}`,
        },
        body: formData,
      });

      if (!res.ok) {
        let reason = "Failed to upload the CSV file.";
        try {
          const errorBody = await res.json();
          reason = errorBody?.detail ?? reason;
        } catch {
          reason = `${reason} (${res.status})`;
        }
        throw new Error(reason);
      }

      const data: CSVUploadResponse = await res.json();
      const timestamp = new Date().toISOString();

      setMessages((prev) => [
        ...prev,
        {
          id: `csv-upload-${Date.now()}`,
          role: "assistant",
          content: `${data.summary}\n\n${data.preview_table}`,
          created_at: timestamp,
        },
      ]);

      setDatasets((prev) => {
        const next = prev.filter((item) => item.dataset_id !== data.dataset_id);
        next.push({
          dataset_id: data.dataset_id,
          filename: data.filename,
          rows: data.rows,
          columns: data.columns,
          created_at: timestamp,
        });
        return next;
      });

      setActiveDatasetId(data.dataset_id);
    } catch (error) {
      console.error(error);
      const message =
        error instanceof Error ? error.message : "Failed to process the CSV file.";

      setMessages((prev) => [
        ...prev,
        {
          id: `csv-error-${Date.now()}`,
          role: "assistant",
          content: `⚠️ ${message}`,
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setIsUploading(false);
      if (event.target) {
        event.target.value = "";
      }
    }
  };

  const handleDownloadClick = async () => {
    if (!activeDatasetId || !session) return;
    setIsDownloading(true);
    try {
      const response = await fetch(`${apiUrl}/agent/csv/export/${activeDatasetId}`, {
        headers: {
          Authorization: `Bearer ${session.access_token}`,
        },
      });

      if (!response.ok) {
        throw new Error("Failed to download the dataset.");
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = activeDataset?.filename ?? "dataset.csv";
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Error downloading CSV:", error);
    } finally {
      setIsDownloading(false);
    }
  };

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
        body: JSON.stringify({ 
          message: currentInputValue, 
          session_id: sessionId,
          dataset_id: activeDatasetId,
        }),
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

  const handleKeyPress = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex h-[calc(100vh-4rem)] flex-col overflow-hidden">
      <ScrollArea className="flex-1" ref={scrollAreaRef}>
        <div className="border-b border-border bg-card/60 backdrop-blur supports-[backdrop-filter]:bg-card/50">
          <div className="container mx-auto flex items-center justify-between px-4 py-3">
            <h1 className="text-2xl font-bold">Chat Session</h1>
            <Link to="/dashboard/chats">
              <Button>Back to Past Chats</Button>
            </Link>
          </div>
        </div>

        <div className="mx-auto max-w-3xl space-y-4 p-4 pb-20">
          {loading && <p className="text-center">Loading chat history...</p>}
          {messages.map((m) => {
            const imageRegex = /!\[(.*?)\]\((data:image\/[^)]+)\)/;
            const imageMatch = m.content.match(imageRegex);
            
            // The text part of the message is anything that is NOT the image markdown
            const textContent = m.content.replace(imageRegex, "").trim();

            return (
              <div
                key={m.id}
                className={`flex gap-3 ${m.role === "user" ? "justify-end" : "justify-start"}`}
              >
                {m.role === "assistant" && (
                  <Avatar className="h-8 w-8 mt-1">
                    <AvatarFallback className="bg-primary text-primary-foreground">
                      <Bot className="h-4 w-4" />
                    </AvatarFallback>
                  </Avatar>
                )}

                <Card
                  className={`max-w-[80%] p-4 ${
                    m.role === "user" ? "bg-primary text-primary-foreground" : "bg-card"
                  }`}
                >
                  <div className="prose prose-sm dark:prose-invert max-w-none">
                    {/* Render the text part of the message if it exists */}
                    {textContent && (
                      <ReactMarkdown
                        urlTransform={allowDataUrl}
                        remarkPlugins={markdownPlugins}
                        components={markdownComponents}
                      >
                        {textContent}
                      </ReactMarkdown>
                    )}
                    {/* Render the image if it was found */}
                    {imageMatch && (
                      <img
                        src={imageMatch[2]} // The data URL
                        alt={imageMatch[1] || "Generated visualization"} // The alt text
                        className="mt-3 max-h-96 w-auto rounded border border-border shadow-sm"
                      />
                    )}
                  </div>
                  <div className="text-xs opacity-70 mt-2">
                    {new Date(m.created_at).toLocaleString()}
                  </div>
                </Card>

                {m.role === "user" && (
                  <Avatar className="h-8 w-8 mt-1">
                    <AvatarFallback className="bg-secondary">
                      {user?.email?.charAt(0).toUpperCase() || "U"}
                    </AvatarFallback>
                  </Avatar>
                )}
              </div>
            );
          })}
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
        <div className="max-w-3xl mx-auto flex flex-col gap-4">
          <div className="flex flex-wrap items-center gap-3">
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,text/csv"
              className="hidden"
              onChange={handleFileChange}
            />
            <Label className="text-sm font-medium">CSV Agent</Label>
            {activeDataset ? (
              <Badge variant="secondary" className="text-xs font-normal">
                Active: {activeDataset.filename} ({activeDataset.rows} rows)
              </Badge>
            ) : (
              <span className="text-sm text-muted-foreground">
                No dataset selected.
              </span>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={handleUploadClick}
              disabled={isUploading || isSending}
              className="flex items-center gap-2"
            >
              <Upload className="h-4 w-4" />
              {isUploading ? "Uploading..." : "Upload CSV"}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleDownloadClick}
              disabled={!activeDatasetId || isDownloading || isSending}
              className="flex items-center gap-2"
            >
              <Download className="h-4 w-4" />
              {isDownloading ? "Preparing..." : "Download CSV"}
            </Button>
            {datasets.length > 0 && (
              <Select
                value={activeDatasetId ?? "none"}
                onValueChange={(value) =>
                  setActiveDatasetId(value === "none" ? null : value)
                }
              >
                <SelectTrigger className="w-[220px]">
                  <SelectValue placeholder="Choose dataset" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">No dataset</SelectItem>
                  {datasets.map((dataset) => (
                    <SelectItem
                      key={dataset.dataset_id}
                      value={dataset.dataset_id}
                    >
                      {dataset.filename} ({dataset.rows} rows)
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          </div>

          <div className="flex gap-2">
            <Input
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={
                activeDatasetId
                  ? "Ask about this dataset..."
                  : "Continue this conversation..."
              }
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
    </div>
  );
}
