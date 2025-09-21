import { useState } from "react";
import { 
  LayoutDashboard, 
  Cog, 
  Flame, 
  Shield,
  Cpu,
  Circle
} from "lucide-react";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarFooter,
  useSidebar,
} from "@/components/ui/sidebar";
import { Badge } from "@/components/ui/badge";

const navigationItems = [
  {
    title: "Dashboard",
    url: "/",
    icon: LayoutDashboard,
  },
  {
    title: "Raw Materials & Grinding",
    url: "/raw-materials",
    icon: Cog,
  },
  {
    title: "Clinkerization Control",
    url: "/clinkerization",
    icon: Flame,
  },
  {
    title: "Quality Control Center",
    url: "/quality-control",
    icon: Shield,
  },
];

export function AppSidebar() {
  const { state } = useSidebar();
  const isCollapsed = state === "collapsed";
  const [currentPath, setCurrentPath] = useState(window.location.pathname);

  const handleNavigation = (url: string) => {
    setCurrentPath(url);
    window.history.pushState({}, "", url);
    window.dispatchEvent(new PopStateEvent('popstate'));
  };

  return (
    <Sidebar className={`transition-all duration-300 ${isCollapsed ? "w-16" : "w-72"} border-r border-sidebar-border bg-sidebar`}>
      <SidebarHeader className="p-6 border-b border-sidebar-border">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-primary">
            <Cpu className="h-6 w-6 text-primary-foreground" />
          </div>
          {!isCollapsed && (
            <div>
              <h1 className="text-xl font-bold text-sidebar-foreground">CementAI</h1>
              <p className="text-xs text-sidebar-foreground/60">Operations Hub</p>
            </div>
          )}
        </div>
      </SidebarHeader>

      <SidebarContent className="py-4">
        <SidebarGroup>
          <SidebarGroupLabel className={`text-sidebar-foreground/60 font-medium ${isCollapsed ? "sr-only" : ""}`}>
            Plant Control
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {navigationItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton
                    onClick={() => handleNavigation(item.url)}
                    className={`w-full justify-start gap-3 px-3 py-3 transition-all hover:bg-sidebar-accent ${
                      currentPath === item.url 
                        ? "bg-sidebar-accent text-sidebar-primary border-l-2 border-sidebar-primary" 
                        : "text-sidebar-foreground"
                    }`}
                    tooltip={isCollapsed ? item.title : undefined}
                  >
                    <item.icon className="h-5 w-5 flex-shrink-0" />
                    {!isCollapsed && (
                      <span className="font-medium">{item.title}</span>
                    )}
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="p-4 border-t border-sidebar-border">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center">
            <Circle className="h-3 w-3 fill-success text-success animate-pulse" />
          </div>
          {!isCollapsed && (
            <div className="flex-1">
              <p className="text-sm font-medium text-sidebar-foreground">All Systems</p>
              <Badge variant="secondary" className="text-xs bg-success/20 text-success">
                Optimal
              </Badge>
            </div>
          )}
        </div>
      </SidebarFooter>
    </Sidebar>
  );
}