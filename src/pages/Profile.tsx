import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useProfile } from "@/hooks/use-profile";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { useToast } from "@/components/ui/use-toast";
import { useAuth } from "@/components/auth/AuthProvider";
import { useMutation } from "@tanstack/react-query";

const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function updateProfileRequest({ fullName, displayName, accessToken }: { fullName: string; displayName: string; accessToken: string }) {
  const response = await fetch(`${apiUrl}/profile`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify({ full_name: fullName, display_name: displayName }),
  });
  if (!response.ok) {
    throw new Error("Failed to update profile");
  }
  return response.json();
}

const Profile = () => {
  const { toast } = useToast();
  const { session } = useAuth();
  const { data: profile, isLoading, isError, invalidateProfileQuery } = useProfile();
  
  const [fullName, setFullName] = useState("");
  const [displayName, setDisplayName] = useState("");

  useEffect(() => {
    if (profile) {
      setFullName(profile.full_name || "");
      setDisplayName(profile.display_name || "");
    }
  }, [profile]);

  const mutation = useMutation({
    mutationFn: updateProfileRequest,
    onSuccess: () => {
      toast({
        title: "Success",
        description: "Your profile has been updated successfully.",
      });
      invalidateProfileQuery(); // Refetch the profile data to show the latest info
    },
    onError: () => {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Could not update your profile.",
      });
    },
  });

  const handleUpdateProfile = (e: React.FormEvent) => {
    e.preventDefault();
    if (!session?.access_token) return;
    
    mutation.mutate({ fullName, displayName, accessToken: session.access_token });
  };

  useEffect(() => {
    if (isError) {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Could not load your profile data.",
      });
    }
  }, [isError, toast]);

  if (isLoading) {
    return (
      <div className="container mx-auto p-4">
        <p>Loading profile...</p>
      </div>
    );
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
                disabled={mutation.isPending}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="displayName">Display Name</Label>
              <Input
                id="displayName"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder="What should Echo call you?"
                disabled={mutation.isPending}
              />
            </div>
          </CardContent>
          <CardFooter className="flex gap-2">
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending ? "Saving..." : "Save Changes"}
            </Button>
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
