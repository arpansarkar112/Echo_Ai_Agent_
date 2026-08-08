import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { supabase } from "@/integrations/supabase/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";
import { Loader2, Mail, Lock, UserCircle } from "lucide-react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";

const authSchema = z.object({
  email: z.string().email("Invalid email address"),
  password: z.string().min(6, "Password must be at least 6 characters"),
  displayName: z.string().optional(),
});

type AuthFormValues = z.infer<typeof authSchema>;

interface AuthFormProps {
  mode: "login" | "signup";
  onToggle: () => void;
}

export function AuthForm({ mode, onToggle }: AuthFormProps) {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { toast } = useToast();

  const { register, handleSubmit, formState: { errors }, setValue } = useForm<AuthFormValues>({
    resolver: zodResolver(authSchema),
    defaultValues: {
      email: "",
      password: "",
      displayName: "",
    }
  });

  const handleAuth = async (data: AuthFormValues) => {
    setLoading(true);
    try {
      if (mode === "signup") {
        if (!data.displayName || data.displayName.length < 2) {
          throw new Error("Display Name must be at least 2 characters.");
        }
        const redirectUrl = `${window.location.origin}/`;
        const { error } = await supabase.auth.signUp({
          email: data.email,
          password: data.password,
          options: {
            emailRedirectTo: redirectUrl,
            data: { display_name: data.displayName }
          }
        });
        if (error) throw error;
        toast({ title: "Account created successfully!", description: "Please check your email to verify your account." });
      } else {
        const { error } = await supabase.auth.signInWithPassword({
          email: data.email,
          password: data.password,
        });
        if (error) throw error;
        toast({ title: "Welcome back!", description: "You have been logged in successfully." });
        navigate("/dashboard");
      }
    } catch (error: any) {
      toast({ title: "Error", description: error.message || "An unexpected error occurred.", variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = () => {
    setValue("email", "demo@example.com");
    setValue("password", "demo123456");
    if (mode === "signup") onToggle();
  };

  const handleGoogleLogin = async () => {
    try {
      const { error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
      });
      if (error) throw error;
    } catch (error: any) {
      toast({ title: "OAuth Error", description: error.message, variant: "destructive" });
    }
  };

  return (
    <Card className="w-full max-w-md shadow-card glass-effect border-border">
      <CardHeader className="space-y-1 text-center">
        <CardTitle className="text-2xl font-bold bg-gradient-hero bg-clip-text text-transparent">
          {mode === "login" ? "Welcome back to Echo" : "Join Echo"}
        </CardTitle>
        <CardDescription>
          {mode === "login" ? "Sign in to continue chatting with your AI agent" : "Create your account to start using your AI agent"}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(handleAuth)} className="space-y-4">
          {mode === "signup" && (
            <div className="space-y-2">
              <Label htmlFor="displayName">Display Name</Label>
              <div className="relative">
                <UserCircle className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  id="displayName"
                  placeholder="John Doe"
                  className={`pl-10 ${errors.displayName ? 'border-destructive' : ''}`}
                  {...register("displayName")}
                />
              </div>
              {errors.displayName && <p className="text-sm text-destructive">{errors.displayName.message}</p>}
            </div>
          )}
          
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <div className="relative">
              <Mail className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                id="email"
                type="email"
                placeholder="john@example.com"
                className={`pl-10 ${errors.email ? 'border-destructive' : ''}`}
                {...register("email")}
              />
            </div>
            {errors.email && <p className="text-sm text-destructive">{errors.email.message}</p>}
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <div className="relative">
              <Lock className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                id="password"
                type="password"
                placeholder="********"
                className={`pl-10 ${errors.password ? 'border-destructive' : ''}`}
                {...register("password")}
              />
            </div>
            {errors.password && <p className="text-sm text-destructive">{errors.password.message}</p>}
          </div>
          
          <Button type="submit" className="w-full gradient-primary hover:shadow-glow transition-smooth" disabled={loading}>
            {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {mode === "login" ? "Sign In" : "Create Account"}
          </Button>
        </form>
        
        <div className="mt-4 flex flex-col gap-3">
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t border-border" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-background px-2 text-muted-foreground">Or continue with</span>
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-3">
            <Button variant="outline" onClick={handleGoogleLogin} className="w-full">
              Google
            </Button>
            <Button variant="outline" onClick={handleDemoLogin} className="w-full">
              Demo Login
            </Button>
          </div>
        </div>

        <div className="mt-4 text-center">
          <Button variant="link" onClick={onToggle} className="text-sm">
            {mode === "login" ? "Don't have an account? Sign up" : "Already have an account? Sign in"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
