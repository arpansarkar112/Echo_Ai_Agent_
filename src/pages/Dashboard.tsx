import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { DashboardSidebar } from "@/components/dashboard/DashboardSidebar";
import { ChatInterface } from "@/components/chat/ChatInterface";
import { useProfile } from "@/hooks/use-profile";
import { Bot } from "lucide-react";

export default function Dashboard() {
  const { data: profile, isLoading } = useProfile();

  return (
    <SidebarProvider>
      <div className="min-h-screen flex w-full">
        <DashboardSidebar />
        
        <main className="flex-1 overflow-auto">
          <header className="h-16 border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-40">
            <div className="flex items-center justify-between h-full px-6">
              <div className="flex items-center gap-4">
                <SidebarTrigger />
                <div className="flex items-center gap-3">
                  <Bot className="h-5 w-5 text-primary" />
                  <div>
                    <h1 className="text-xl font-semibold">Echo<span className="block text-sm text-muted-foreground">
                        {isLoading ? "Loading..." : `Welcome back, ${profile?.display_name || 'User'}`}
                      </span>
                    </h1>

                  </div>
                </div>
              </div>
            </div>
          </header>
          
          <div className="flex-1 flex flex-col">
            <ChatInterface />
          </div>
        </main>
      </div>
    </SidebarProvider>
  );
}