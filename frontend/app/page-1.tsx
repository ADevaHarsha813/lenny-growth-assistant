"use client";

import { useState, useEffect } from "react";
import { PanelLeft } from "lucide-react";
import SessionSidebar from "@/components/layout/SessionSidebar";
import ChatPanel from "@/components/chat/ChatPanel";
import ArtifactPane from "@/components/artifact/ArtifactPane";
import { useSession } from "@/hooks/useSession";
import { Artifact } from "@/lib/types";
import { api } from "@/lib/api";

export default function Home() {
  const {
    sessions,
    currentSession,
    loadSessions,
    createSession,
    selectSession,
    setCurrentSession,
    renameSession,
    updateSessionTitle,
  } = useSession();

  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [artifact, setArtifact] = useState<Artifact | null>(null);

  useEffect(() => {
    loadSessions();
    try {
      const stored = localStorage.getItem("sidebarOpen");
      if (stored !== null) setSidebarOpen(JSON.parse(stored));
    } catch {}
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const toggleSidebar = () => {
    setSidebarOpen((v) => {
      const next = !v;
      try { localStorage.setItem("sidebarOpen", JSON.stringify(next)); } catch {}
      return next;
    });
  };

  const handleNewChat = () => {
    setCurrentSession(null);
    setArtifact(null);
    if (typeof window !== "undefined" && window.innerWidth < 768) {
      setSidebarOpen(false);
    }
  };

  const handleSelectSession = (s: NonNullable<typeof currentSession>) => {
    selectSession(s);
    setArtifact(null);
    if (typeof window !== "undefined" && window.innerWidth < 768) {
      setSidebarOpen(false);
    }
  };

  const handleDeleteSession = async (id: string) => {
    try {
      await api.deleteSession(id);
      if (currentSession?.id === id) setCurrentSession(null);
      await loadSessions();
    } catch (err) {
      console.error("Delete session failed", err);
    }
  };

  return (
    <div className="app-shell">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-20 md:hidden"
          onClick={toggleSidebar}
        />
      )}

      <SessionSidebar
        open={sidebarOpen}
        sessions={sessions}
        currentSession={currentSession}
        onNewSession={handleNewChat}
        onSelectSession={handleSelectSession}
        onToggle={toggleSidebar}
        onRename={renameSession}
        onDelete={handleDeleteSession}
      />

      <div className="main-area">
        {/* Floating sidebar open button — only when sidebar is collapsed */}
        {!sidebarOpen && (
          <button
            onClick={toggleSidebar}
            className="sidebar-open-fab"
            aria-label="Open sidebar"
          >
            <PanelLeft size={18} />
          </button>
        )}

        <div className="body-area">
          <div style={{ flex: 1, display: "flex", flexDirection: "column", minHeight: 0 }}>
            <ChatPanel
              session={currentSession}
              onArtifact={setArtifact}
              createSession={createSession}
              onTitleUpdate={updateSessionTitle}
            />
          </div>

          {artifact && (
            <div className="artifact-pane">
              <ArtifactPane artifact={artifact} onClose={() => setArtifact(null)} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
