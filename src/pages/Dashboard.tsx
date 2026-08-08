import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { DashboardSidebar } from "@/components/dashboard/DashboardSidebar";
import { ChatInterface } from "@/components/chat/ChatInterface";
import { useProfile } from "@/hooks/use-profile";
import { Bot, UserCircle, LogOut, Settings } from "lucide-react";
import { ModeToggle } from "@/components/ui/mode-toggle";
import DashboardOverview from "./DashboardOverview";
import PastChats from "./PastChats";
import ChatSession from "./ChatSession";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/components/auth/AuthProvider";

interface DashboardProps {
  component?: "overview" | "chat" | "past-chats" | "chat-session";
}

export default function Dashboard({ component = "overview" }: DashboardProps) {
  const { data: profile, isLoading } = useProfile();
  const { signOut } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await signOut();
    navigate("/");
  };

  const renderComponent = () => {
    switch (component) {
      case "chat":
        return <ChatInterface />;
      case "past-chats":
        return <PastChats />;
      case "chat-session":
        return <ChatSession />;
      case "overview":
      default:
        return <DashboardOverview />;
    }
  };

  return (
    <SidebarProvider>
      <div className="flex h-screen w-full overflow-hidden bg-background">
        <DashboardSidebar />
        
        <main className="flex-1 flex flex-col overflow-hidden">
          <header className="h-16 border-b border-border bg-card/60 backdrop-blur supports-[backdrop-filter]:bg-card/50 sticky top-0 z-40">
            <div className="flex items-center justify-between h-full px-6">
              <div className="flex items-center gap-4">
                <SidebarTrigger />
                <div className="flex items-center gap-3">
                  <Bot className="h-5 w-5 text-primary" />
                  <div>
                    <h1 className="text-xl font-semibold"> Echo 
                      <span className="block text-sm text-muted-foreground">
                        {isLoading ? "Loading..." : `Welcome back, ${profile?.display_name || 'User'}`}
                      </span>
                    </h1>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <ModeToggle />
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="icon" className="rounded-full">
                      <UserCircle className="h-6 w-6" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuLabel>My Account</DropdownMenuLabel>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem asChild>
                      <Link to="/dashboard/profile" className="cursor-pointer w-full flex items-center">
                        <UserCircle className="mr-2 h-4 w-4" /> Profile
                      </Link>
                    </DropdownMenuItem>
                    <DropdownMenuItem asChild>
                      <Link to="/dashboard/settings" className="cursor-pointer w-full flex items-center">
                        <Settings className="mr-2 h-4 w-4" /> Settings
                      </Link>
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={handleLogout} className="cursor-pointer text-destructive focus:text-destructive">
                      <LogOut className="mr-2 h-4 w-4" /> Log out
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </div>
          </header>
          
          <div className="flex-1 overflow-hidden">
            {renderComponent()}
          </div>
        </main>
      </div>
    </SidebarProvider>
  );
}
