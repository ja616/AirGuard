"use client";

import { Bell, Command, UserCircle } from "lucide-react";
import { StartInvestigationModal } from "@/components/investigations/StartInvestigationModal";

export function Topbar() {
  return (
    <div className="flex h-14 items-center justify-between border-b border-zinc-800 bg-zinc-950/50 px-6">
      <div className="flex items-center space-x-2 text-sm text-zinc-400">
        <div className="flex items-center space-x-1 rounded bg-zinc-900 px-2 py-1 border border-zinc-800">
          <Command size={14} className="mr-1" />
          <span>K</span>
          <span className="ml-2 text-xs text-zinc-500">to search investigations</span>
        </div>
      </div>
      
      <div className="flex items-center space-x-4">
        <StartInvestigationModal />
        <div className="relative">
          <Bell size={18} className="text-zinc-400 hover:text-white cursor-pointer transition-colors" />
          <span className="absolute -top-1 -right-1 flex h-3 w-3 items-center justify-center rounded-full bg-indigo-500 text-[9px] font-bold text-white">
            2
          </span>
        </div>
        <div className="h-4 w-px bg-zinc-800" />
        <div className="flex items-center space-x-2 cursor-pointer group">
          <div className="h-6 w-6 overflow-hidden rounded-full bg-zinc-800">
            <UserCircle className="h-full w-full text-zinc-400 group-hover:text-white transition-colors" />
          </div>
          <span className="text-sm font-medium text-zinc-300 group-hover:text-white transition-colors">admin</span>
        </div>
      </div>
    </div>
  );
}
