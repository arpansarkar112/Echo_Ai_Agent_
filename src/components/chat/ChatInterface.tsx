import {
  useState,
  useRef,
  useEffect,
  type ChangeEvent,
  type KeyboardEvent,
} from "react";
import ReactMarkdown from "react-markdown";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Send, Bot, Upload, Download } from "lucide-react";
import { useAuth } from "@/components/auth/AuthProvider";
import { useToast } from "@/components/ui/use-toast";

import {
  allowDataUrl,
  markdownComponents,
  markdownPlugins,
} from "@/components/chat/markdown";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
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

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content:
        "Hello! I'm Echo. I can help you with various tasks and projects. What would you like to work on today?",
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [datasets, setDatasets] = useState<SessionDataset[]>([]);
  const [activeDatasetId, setActiveDatasetId] = useState<string | null>(null);

  const { user, session } = useAuth();
  const { toast } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";

  const activeDataset = activeDatasetId
    ? datasets.find((dataset) => dataset.dataset_id === activeDatasetId) ?? null
    : null;

  useEffect(() => {
    if (!sessionId || !session) return;

    const fetchDatasets = async () => {
      try {
        const res = await fetch(`${apiUrl}/agent/csv/session/${sessionId}`, {
          headers: {
            Authorization: `Bearer ${session.access_token}`,
          },
        });
        if (!res.ok) {
          throw new Error("Failed to load CSV datasets.");
        }
        const data: SessionDataset[] = await res.json();
        setDatasets(data);
        setActiveDatasetId(
          (current) => current ?? (data[0]?.dataset_id ?? null)
        );
      } catch (error) {
        console.error(error);
      }
    };

    fetchDatasets();
  }, [sessionId, session, apiUrl]);

  const handleUploadClick = () => {
    if (!sessionId) {
      toast({
        title: "Start a chat first",
        description:
          "Send a message to create a session before uploading CSV files.",
        variant: "destructive",
      });
      return;
    }
    fileInputRef.current?.click();
  };

  const handleFileChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !session || !sessionId) {
      if (event.target) event.target.value = "";
      return;
    }

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
      const timestamp = new Date();

      setDatasets((prev) => {
        const next = prev.filter((item) => item.dataset_id !== data.dataset_id);
        next.push({
          dataset_id: data.dataset_id,
          filename: data.filename,
          rows: data.rows,
          columns: data.columns,
          created_at: timestamp.toISOString(),
        });
        return next;
      });
      setActiveDatasetId(data.dataset_id);

      setMessages((prev) => [
        ...prev,
        {
          id: `csv-upload-${Date.now()}`,
          role: "assistant",
          content: `${data.summary}\n\n${data.preview_table}`,
          timestamp,
        },
      ]);
    } catch (error) {
      console.error(error);
      const message =
        error instanceof Error
          ? error.message
          : "Failed to process the CSV file.";
      toast({
        title: "Upload failed",
        description: message,
        variant: "destructive",
      });
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
      const response = await fetch(
        `${apiUrl}/agent/csv/export/${activeDatasetId}`,
        {
          headers: {
            Authorization: `Bearer ${session.access_token}`,
          },
        }
      );

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
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error(error);
      toast({
        title: "Download failed",
        description:
          error instanceof Error
            ? error.message
            : "Unable to download the CSV file right now.",
        variant: "destructive",
      });
    } finally {
      setIsDownloading(false);
    }
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: inputValue,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    const currentInputValue = inputValue;
    setInputValue("");
    setIsLoading(true);

    try {
      const response = await fetch(`${apiUrl}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: session ? `Bearer ${session.access_token}` : "",
        },
        body: JSON.stringify({
          message: currentInputValue,
          session_id: sessionId,
          dataset_id: activeDatasetId,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to get response from the server.");
      }

      const data = await response.json();

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: data.response || "Sorry, I couldn't get a response.",
        timestamp: new Date(),
      };
      if (data.session_id) setSessionId(data.session_id);
      setMessages((prev) => [...prev, aiMessage]);
    } catch (error) {
      console.error("Error sending message:", error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "Sorry, something went wrong. Please try again.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <ScrollArea className="flex-1">
        <div className="mx-auto max-w-3xl space-y-4 p-4 pb-20">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-3 ${
                message.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              {message.role === "assistant" && (
                <Avatar className="h-8 w-8 mt-1">
                  <AvatarFallback className="bg-primary text-primary-foreground">
                    <Bot className="h-4 w-4" />
                  </AvatarFallback>
                </Avatar>
              )}

              <Card
                className={`max-w-[80%] p-4 ${
                  message.role === "user"
                    ? "bg-primary text-primary-foreground"
                    : "bg-card"
                }`}
              >
                <div className="prose prose-sm dark:prose-invert max-w-none prose-force-white">
                  <ReactMarkdown
                    urlTransform={allowDataUrl}
                    remarkPlugins={markdownPlugins}
                    components={markdownComponents}
                  >
                    {message.content}
                  </ReactMarkdown>
                </div>
                <div className="text-xs opacity-70 mt-2">
                  {message.timestamp.toLocaleTimeString()}
                </div>
              </Card>

              {message.role === "user" && (
                <Avatar className="h-8 w-8 mt-1">
                  <AvatarFallback className="bg-secondary">
                    {user?.email?.charAt(0).toUpperCase() || "U"}
                  </AvatarFallback>
                </Avatar>
              )}
            </div>
          ))}

          {isLoading && (
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
                {sessionId
                  ? "No dataset selected."
                  : "Send a message to create a chat session first."}
              </span>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={handleUploadClick}
              disabled={isUploading || isLoading || !session}
              className="flex items-center gap-2"
            >
              <Upload className="h-4 w-4" />
              {isUploading ? "Uploading..." : "Upload CSV"}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleDownloadClick}
              disabled={
                !activeDatasetId || isDownloading || isLoading || !session
              }
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
              onChange={(event) => setInputValue(event.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={
                activeDatasetId
                  ? "Ask about this dataset..."
                  : "Ask me anything or describe what you'd like to create..."
              }
              className="flex-1"
              disabled={isLoading}
            />
            <Button
              onClick={handleSendMessage}
              disabled={!inputValue.trim() || isLoading}
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
