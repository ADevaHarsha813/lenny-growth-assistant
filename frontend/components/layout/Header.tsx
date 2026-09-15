"use client";

import { Menu, Cpu } from "lucide-react";
import ThemeToggle from "./ThemeToggle";
import { Session } from "@/lib/types";

interface Props {
  sidebarOpen: boolean;
  onToggleSidebar: () => void;
  session: Session | null;
}

export default function Header({ sidebarOpen, onToggleSidebar, session }: Props) {
  return (
    <header className="flex items-center gap-3 px-4 py-3 border-b border-border bg-background/80 backdrop-blur-sm sticky top-0 z-10">
      <button
        onClick={onToggleSidebar}
        className="p-1.5 rounded-md hover:bg-muted transition-colors text-muted-foreground hover:text-foreground"
        aria-label="Toggle sidebar"
      >
        <Menu size={18} />
      </button>

      <div className="flex items-center gap-2 flex-1 min-w-0">
        <div className="w-7 h-7 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
          <span className="text-sm">🐢</span>
        </div>
        <span className="font-semibold text-sm truncate">
          {session?.title || "Lenny Growth Assistant"}
        </span>
      </div>

      <div className="flex items-center gap-2">
        {session && (
          <div className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-muted text-xs text-muted-foreground">
            <Cpu size={12} />
            <span>{session.llm_provider || "ollama"}</span>
          </div>
        )}
        <ThemeToggle />
      </div>
    </header>
  );
}
