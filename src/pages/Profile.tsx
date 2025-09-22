import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "@/components/auth/AuthProvider";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { useToast } from "@/components/ui/use-toast";

const Profile = () => {
  const { session } = useAuth();
  const { toast } = useToast();
  const [fullName, setFullName] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchProfile = async () => {
      if (!session) return;
      setLoading(true);
      try {
        const response = await fetch("http://localhost:8001/profile", {
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${session.access_token}`,
          },
        });
        if (!response.ok) throw new Error("Failed to fetch profile");
        const data = await response.json();
        setFullName(data.full_name || "");
        setDisplayName(data.display_name || "");
      } catch (error) {
        toast({
          variant: "destructive",
          title: "Error",
          description: "Could not load your profile data.",
        });
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, [session, toast]);

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!session) return;
    try {
      const response = await fetch("http://localhost:8001/profile", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({ full_name: fullName, display_name: displayName }),
      });
      if (!response.ok) throw new Error("Failed to update profile");
      toast({
        title: "Success",
        description: "Your profile has been updated successfully.",
      });
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Could not update your profile.",
      });
    }
  };

  if (loading) {
    return <div>Loading profile...</div>;
  }

  return (
    <div className="container mx-auto p-4">
      <Card>
        <CardHeader>
          <CardTitle>Profile</CardTitle>
          <CardDescription>Manage your profile settings.</CardDescription>
        </CardHeader>
        <form onSubmit={handleUpdateProfile}>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" value={session?.user?.email || ""} disabled />
            </div>
            <div className="space-y-2">
              <Label htmlFor="fullName">Full Name</Label>
              <Input
                id="fullName"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Your full name"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="displayName">Display Name</Label>
              <Input
                id="displayName"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder="What should Echo call you?"
              />
            </div>
          </CardContent>
          <CardFooter className="flex gap-2">
            <Button type="submit">Save Changes</Button>
            <Button variant="outline" asChild>
              <Link to="/dashboard">Return</Link>
            </Button>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
};

export default Profile;
