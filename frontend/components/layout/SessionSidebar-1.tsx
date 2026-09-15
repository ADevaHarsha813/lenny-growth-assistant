"use client";

import { useState, useEffect } from "react";
import {
  Plus, Search, Pin,
  Pencil, Trash2, Check, X, ChevronLeft,
} from "lucide-react";
import { Session } from "@/lib/types";

interface Props {
  open: boolean;
  sessions: Session[];
  currentSession: Session | null;
  onNewSession: () => void;
  onSelectSession: (s: Session) => void;
  onToggle: () => void;
  onRename: (id: string, title: string) => void;
  onDelete: (id: string) => void;
}

function timeLabel(iso: string): string {
  const d = new Date(iso);
  const now = new Date();
  const diff = Math.floor((now.getTime() - d.getTime()) / 86400000);
  if (diff === 0) return "Today";
  if (diff === 1) return "Yesterday";
  if (diff < 7) return `${diff} days ago`;
  return d.toLocaleDateString();
}

function groupSessions(sessions: Session[]) {
  const groups: Record<string, Session[]> = {};
  for (const s of sessions) {
    const label = timeLabel(s.created_at ?? new Date().toISOString());
    if (!groups[label]) groups[label] = [];
    groups[label].push(s);
  }
  return groups;
}

export default function SessionSidebar({
  open, sessions, currentSession,
  onNewSession, onSelectSession, onToggle, onRename, onDelete,
}: Props) {
  const [search, setSearch] = useState("");
  const [renameId, setRenameId] = useState<string | null>(null);
  const [renameVal, setRenameVal] = useState("");
  const [pinned, setPinned] = useState<Set<string>>(new Set());

  useEffect(() => {
    try {
      const stored = localStorage.getItem("pinnedSessions");
      if (stored) setPinned(new Set<string>(JSON.parse(stored)));
    } catch {}
  }, []);

  const savePinned = (next: Set<string>) => {
    setPinned(next);
    try { localStorage.setItem("pinnedSessions", JSON.stringify(Array.from(next))); } catch {}
  };

  const togglePin = (id: string) => {
    const next = new Set(pinned);
    next.has(id) ? next.delete(id) : next.add(id);
    savePinned(next);
  };

  const startRename = (s: Session) => {
    setRenameId(s.id);
    setRenameVal(s.title ?? "");
  };

  const commitRename = (id: string) => {
    if (renameVal.trim()) onRename(id, renameVal.trim());
    setRenameId(null);
  };

  const filtered = sessions.filter((s) =>
    !search || (s.title ?? "").toLowerCase().includes(search.toLowerCase())
  );
  const pinnedSessions = filtered.filter((s) => pinned.has(s.id));
  const unpinnedSessions = filtered.filter((s) => !pinned.has(s.id));
  const groups = groupSessions(unpinnedSessions);

  return (
    <aside className={`sidebar-panel ${open ? "open" : "closed"}`}>
      {/* Header */}
      <div className="sidebar-header">
        <span className="sidebar-logo-icon">🐢</span>
        <span className="sidebar-logo-name">Lenny&apos;s AI</span>
        <button className="sidebar-collapse-btn" onClick={onToggle} aria-label="Collapse sidebar">
          <ChevronLeft size={16} />
        </button>
      </div>

      {/* New chat */}
      <button className="sidebar-new-chat" onClick={onNewSession}>
        <Plus size={15} />
        New chat
      </button>

      {/* Search */}
      <div className="sidebar-search-wrap">
        <Search size={13} className="sidebar-search-icon" />
        <input
          className="sidebar-search-input"
          placeholder="Search chats"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {/* Session list */}
      <div className="sidebar-sessions">
        {/* Pinned */}
        {pinnedSessions.length > 0 && (
          <>
            <div className="sidebar-time-group">Pinned</div>
            {pinnedSessions.map((s) => (
              <SessionItem
                key={s.id}
                session={s}
                active={currentSession?.id === s.id}
                isPinned
                renameId={renameId}
                renameVal={renameVal}
                onSelect={() => onSelectSession(s)}
                onPin={() => togglePin(s.id)}
                onRenameStart={() => startRename(s)}
                onRenameChange={setRenameVal}
                onRenameCommit={() => commitRename(s.id)}
                onRenameCancel={() => setRenameId(null)}
                onDelete={() => onDelete(s.id)}
              />
            ))}
          </>
        )}

        {/* Grouped by time */}
        {Object.entries(groups).map(([label, items]) => (
          <div key={label}>
            <div className="sidebar-time-group">{label}</div>
            {items.map((s) => (
              <SessionItem
                key={s.id}
                session={s}
                active={currentSession?.id === s.id}
                isPinned={false}
                renameId={renameId}
                renameVal={renameVal}
                onSelect={() => onSelectSession(s)}
                onPin={() => togglePin(s.id)}
                onRenameStart={() => startRename(s)}
                onRenameChange={setRenameVal}
                onRenameCommit={() => commitRename(s.id)}
                onRenameCancel={() => setRenameId(null)}
                onDelete={() => onDelete(s.id)}
              />
            ))}
          </div>
        ))}

        {filtered.length === 0 && (
          <p style={{ padding: "16px", fontSize: "13px", color: "var(--text-muted)", textAlign: "center" }}>
            {search ? "No results" : "No chats yet"}
          </p>
        )}
      </div>
    </aside>
  );
}

/* ---- SessionItem ---- */
interface ItemProps {
  session: Session;
  active: boolean;
  isPinned: boolean;
  renameId: string | null;
  renameVal: string;
  onSelect: () => void;
  onPin: () => void;
  onRenameStart: () => void;
  onRenameChange: (v: string) => void;
  onRenameCommit: () => void;
  onRenameCancel: () => void;
  onDelete: () => void;
}

function SessionItem({
  session, active, isPinned, renameId, renameVal,
  onSelect, onPin, onRenameStart, onRenameChange, onRenameCommit, onRenameCancel, onDelete,
}: ItemProps) {
  const isRenaming = renameId === session.id;

  return (
    <div
      className={`sidebar-session-item ${active ? "active" : ""}`}
      onClick={!isRenaming ? onSelect : undefined}
      style={{ cursor: isRenaming ? "default" : "pointer" }}
    >
      {isPinned && <Pin size={10} className="sidebar-session-pin" />}

      {isRenaming ? (
        <>
          <input
            className="sidebar-rename-input"
            value={renameVal}
            onChange={(e) => onRenameChange(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") onRenameCommit();
              if (e.key === "Escape") onRenameCancel();
            }}
            autoFocus
            onClick={(e) => e.stopPropagation()}
          />
          <button className="sidebar-session-action-btn" onClick={(e) => { e.stopPropagation(); onRenameCommit(); }}>
            <Check size={12} />
          </button>
          <button className="sidebar-session-action-btn" onClick={(e) => { e.stopPropagation(); onRenameCancel(); }}>
            <X size={12} />
          </button>
        </>
      ) : (
        <>
          <span className="sidebar-session-title">{session.title ?? "New conversation"}</span>
          <div className="sidebar-session-actions" onClick={(e) => e.stopPropagation()}>
            <button className="sidebar-session-action-btn" title="Pin" onClick={onPin}>
              <Pin size={11} />
            </button>
            <button className="sidebar-session-action-btn" title="Rename" onClick={onRenameStart}>
              <Pencil size={11} />
            </button>
            <button className="sidebar-session-action-btn danger" title="Delete" onClick={onDelete}>
              <Trash2 size={11} />
            </button>
          </div>
        </>
      )}
    </div>
  );
}
