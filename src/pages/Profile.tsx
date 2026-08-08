import { useEffect } from "react";
import { Link } from "react-router-dom";
import { useProfile } from "@/hooks/use-profile";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { useToast } from "@/components/ui/use-toast";
import { useAuth } from "@/components/auth/AuthProvider";
import { useMutation } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";

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

const profileSchema = z.object({
  fullName: z.string().min(2, "Full name must be at least 2 characters"),
  displayName: z.string().min(2, "Display name must be at least 2 characters"),
});
type ProfileFormValues = z.infer<typeof profileSchema>;

const Profile = () => {
  const { toast } = useToast();
  const { session } = useAuth();
  const { data: profile, isLoading, isError, invalidateProfileQuery } = useProfile();
  
  const { register, handleSubmit, formState: { errors }, reset } = useForm<ProfileFormValues>({
    resolver: zodResolver(profileSchema),
    defaultValues: { fullName: "", displayName: "" }
  });

  useEffect(() => {
    if (profile) {
      reset({ fullName: profile.full_name || "", displayName: profile.display_name || "" });
    }
  }, [profile, reset]);

  const mutation = useMutation({
    mutationFn: updateProfileRequest,
    onSuccess: () => {
      toast({
        title: "Success",
        description: "Your profile has been updated successfully.",
      });
      invalidateProfileQuery();
    },
    onError: () => {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Could not update your profile.",
      });
    },
  });

  const onSubmit = (data: ProfileFormValues) => {
    if (!session?.access_token) return;
    mutation.mutate({ fullName: data.fullName, displayName: data.displayName, accessToken: session.access_token });
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
    <div className="container mx-auto p-4 max-w-2xl">
      <Card>
        <CardHeader>
          <CardTitle>Profile</CardTitle>
          <CardDescription>Manage your profile settings.</CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit(onSubmit)}>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" value={session?.user?.email || ""} disabled />
            </div>
            <div className="space-y-2">
              <Label htmlFor="fullName">Full Name</Label>
              <Input
                id="fullName"
                placeholder="Your full name"
                disabled={mutation.isPending}
                className={errors.fullName ? 'border-destructive' : ''}
                {...register("fullName")}
              />
              {errors.fullName && <p className="text-sm text-destructive">{errors.fullName.message}</p>}
            </div>
            <div className="space-y-2">
              <Label htmlFor="displayName">Display Name</Label>
              <Input
                id="displayName"
                placeholder="What should Echo call you?"
                disabled={mutation.isPending}
                className={errors.displayName ? 'border-destructive' : ''}
                {...register("displayName")}
              />
              {errors.displayName && <p className="text-sm text-destructive">{errors.displayName.message}</p>}
            </div>
          </CardContent>
          <CardFooter className="flex gap-2">
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending ? "Saving..." : "Save Changes"}
            </Button>
            <Button variant="outline" asChild type="button">
              <Link to="/dashboard">Return</Link>
            </Button>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
};

export default Profile;
