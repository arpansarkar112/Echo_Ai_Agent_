import { NavLink, useLocation } from "react-router-dom";
import { 
  MessageSquare, 
  User, 
  History,
  LogOut,
  Bot,
  Info,
  LayoutDashboard,
  Users,
  Settings,
  BarChart
} from "lucide-react";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/components/auth/AuthProvider";
import { useProfile } from "@/hooks/use-profile";

const userNavigation = [
  { name: "Overview", href: "/dashboard", icon: LayoutDashboard },
  { name: "New Chat", href: "/dashboard/chat", icon: MessageSquare },
  { name: "Past Chats", href: "/dashboard/chats", icon: History },
  { name: "Profile", href: "/dashboard/profile", icon: User },
  { name: "Credit", href: "/dashboard/credit", icon: Info },
  { name: "Settings", href: "/dashboard/settings", icon: Settings },
];

const adminNavigation = [
  { name: "Overview", href: "/dashboard", icon: LayoutDashboard },
  { name: "Manage Users", href: "/dashboard/users", icon: Users },
  { name: "Analytics", href: "/dashboard/analytics", icon: BarChart },
  { name: "Settings", href: "/dashboard/settings", icon: Settings },
];

export function DashboardSidebar() {
  const { state } = useSidebar();
  const location = useLocation();
  const { signOut } = useAuth();
  const { data: profile } = useProfile();
  
  const collapsed = state === "collapsed";
  const navigation = profile?.role === "admin" ? adminNavigation : userNavigation;

  return (
    <Sidebar className={collapsed ? "w-16" : "w-64"} collapsible="icon">
      <SidebarContent className="bg-sidebar border-sidebar-border">
        <div className="p-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 gradient-primary rounded-lg flex items-center justify-center">
              <Bot className="h-4 w-4 text-white" />
            </div>
            {!collapsed && (
              <h2 className="text-lg font-bold bg-gradient-primary bg-clip-text text-transparent">
                Echo
              </h2>
            )}
          </div>
        </div>
        
        <SidebarGroup>
          <SidebarGroupLabel>{profile?.role === 'admin' ? 'Admin Menu' : 'Main Menu'}</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {navigation.map((item) => (
                <SidebarMenuItem key={item.name}>
                  <SidebarMenuButton asChild>
                    <NavLink
                      to={item.href}
                      end={item.href === "/dashboard"}
                      className={({ isActive }) =>
                        `flex items-center gap-3 px-3 py-2 rounded-lg transition-smooth ${
                          isActive
                            ? "bg-sidebar-accent text-sidebar-accent-foreground font-medium"
                            : "hover:bg-sidebar-accent/50 text-sidebar-foreground"
                        }`
                      }
                    >
                      <item.icon className="h-4 w-4" />
                      {!collapsed && <span>{item.name}</span>}
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
        
        <div className="mt-auto p-4 space-y-4 border-t border-sidebar-border">
          <Button
            variant="ghost"
            onClick={signOut}
            className="w-full justify-start text-sidebar-foreground hover:bg-sidebar-accent"
          >
            <LogOut className="h-4 w-4" />
            {!collapsed && <span className="ml-2">Sign Out</span>}
          </Button>
        </div>
      </SidebarContent>
    </Sidebar>
  );
}