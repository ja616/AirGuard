"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  LayoutDashboard, 
  Search, 
  PlaySquare, 
  Library, 
  Activity, 
  BarChart3, 
  Settings, 
  Terminal,
  FileCode2
} from "lucide-react";
import { cn } from "@/lib/utils";

const topNavItems = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Investigations", href: "/investigations", icon: Search },
];

const bottomNavItems: any[] = [
  // { name: "Health", href: "/health", icon: Activity },
];

export function SidebarNav() {
  const pathname = usePathname();

  return (
    <div className="flex h-full w-64 flex-col border-r border-zinc-800 bg-zinc-950/50 p-4">
      <div className="mb-8 flex items-center space-x-3 px-2">
        <div className="flex h-8 w-8 items-center justify-center rounded bg-indigo-500/20 text-indigo-400">
          <FileCode2 size={20} />
        </div>
        <span className="text-lg font-semibold tracking-tight">AirGuard</span>
      </div>

      <div className="flex flex-1 flex-col justify-between">
        <nav className="space-y-1">
          {topNavItems.map((item) => {
            const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  "flex items-center space-x-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-zinc-800/50 text-white"
                    : "text-zinc-400 hover:bg-zinc-800/30 hover:text-white"
                )}
              >
                <item.icon size={18} className={cn(isActive ? "text-indigo-400" : "text-zinc-500")} />
                <span>{item.name}</span>
              </Link>
            );
          })}
        </nav>

        <nav className="space-y-1">
          {bottomNavItems.map((item) => {
            const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  "flex items-center space-x-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-zinc-800/50 text-white"
                    : "text-zinc-400 hover:bg-zinc-800/30 hover:text-white"
                )}
              >
                <item.icon size={18} className={cn(isActive ? "text-indigo-400" : "text-zinc-500")} />
                <span>{item.name}</span>
              </Link>
            );
          })}
        </nav>
      </div>
    </div>
  );
}
