import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

import { useAuth } from "@/components/auth/AuthProvider";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { useToast } from "@/components/ui/use-toast";

interface Session {
  session_id: string;
  title: string | null;
  created_at: string;
}

export default function PastChats() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(false);
  const { session } = useAuth();
  const { toast } = useToast();

  const fetchSessions = async () => {
    if (!session) return;
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8001/sessions", {
        headers: {
          Authorization: `Bearer ${session.access_token}`,
        },
      });
      if (!res.ok) throw new Error("Failed to load sessions");
      const data = await res.json();
      setSessions(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSessions();
  }, [session]);

  const handleDelete = async (sessionId: string) => {
    if (!session) return;
    try {
      const res = await fetch(`http://localhost:8001/sessions/${sessionId}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${session.access_token}`,
        },
      });

      if (!res.ok) {
        throw new Error('Failed to delete session');
      }

      toast({
        title: "Success",
        description: "Chat session deleted successfully.",
      });
      setSessions(sessions.filter((s) => s.session_id !== sessionId));
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Could not delete the chat session.",
      });
    }
  };

  return (
    <div className="container mx-auto p-4">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">Past Chats</h1>
        <Link to="/dashboard">
          <Button>Return</Button>
        </Link>
      </div>
      {loading && <p>Loading...</p>}
      <div className="grid gap-3">
        {sessions.map((s) => (
          <Card key={s.session_id} className="p-4">
            <CardContent>
              <div className="flex justify-between items-center">
                <div>
                  <h3 className="font-medium">{s.title || "Untitled session"}</h3>
                  <p className="text-sm text-muted-foreground">{new Date(s.created_at).toLocaleString()}</p>
                </div>
                <div className="flex gap-2">
                  <Link to={`/dashboard/chats/${s.session_id}`}>
                    <Button>Open</Button>
                  </Link>
                  <AlertDialog>
                    <AlertDialogTrigger asChild>
                      <Button variant="destructive">Delete</Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent>
                      <AlertDialogHeader>
                        <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
                        <AlertDialogDescription>
                          This action cannot be undone. This will permanently delete this chat session and all of its messages.
                        </AlertDialogDescription>
                      </AlertDialogHeader>
                      <AlertDialogFooter>
                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                        <AlertDialogAction onClick={() => handleDelete(s.session_id)}>
                          Continue
                        </AlertDialogAction>
                      </AlertDialogFooter>
                    </AlertDialogContent>
                  </AlertDialog>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
