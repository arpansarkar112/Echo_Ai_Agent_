import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@/components/auth/AuthProvider";

async function fetchProfile(accessToken: string) {
  const response = await fetch("http://localhost:8001/profile", {
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
    },
  });
  if (!response.ok) {
    throw new Error("Failed to fetch profile");
  }
  return response.json();
}

export function useProfile() {
  const { session } = useAuth();
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: ["profile", session?.user?.id],
    queryFn: () => {
      if (!session?.access_token) {
        throw new Error("No access token available");
      }
      return fetchProfile(session.access_token);
    },
    enabled: !!session?.user, // Only run the query if the user is logged in
  });

  const invalidateProfileQuery = () => {
    queryClient.invalidateQueries({ queryKey: ["profile", session?.user?.id] });
  };

  return { ...query, invalidateProfileQuery };
}
