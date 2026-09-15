"use client";

import { useState, useCallback } from "react";
import { Session } from "@/lib/types";
import { api } from "@/lib/api";

export function useSession() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSession, setCurrentSession] = useState<Session | null>(null);

  const loadSessions = useCallback(async () => {
    try {
      const data = await api.getSessions();
      setSessions(data);
      if (data.length > 0 && !currentSession) {
        setCurrentSession(data[0]);
      }
    } catch (e) {
      console.error("Failed to load sessions", e);
    }
  }, [currentSession]);

  const createSession = useCallback(async (title?: string): Promise<Session | null> => {
    try {
      const session = await api.createSession({ title: title || "New conversation" });
      setSessions((prev) => [session, ...prev]);
      setCurrentSession(session);
      return session;
    } catch (e) {
      console.error("Failed to create session", e);
      return null;
    }
  }, []);

  const selectSession = useCallback((session: Session) => {
    setCurrentSession(session);
  }, []);

  const renameSession = useCallback(async (id: string, title: string) => {
    try {
      await api.renameSession(id, title);
      setSessions((prev) => prev.map((s) => (s.id === id ? { ...s, title } : s)));
      setCurrentSession((prev) => (prev?.id === id ? { ...prev, title } : prev));
    } catch (e) {
      console.error("Failed to rename session", e);
    }
  }, []);

  const updateSessionTitle = useCallback((id: string, title: string) => {
    setSessions((prev) => prev.map((s) => (s.id === id ? { ...s, title } : s)));
    setCurrentSession((prev) => (prev?.id === id ? { ...prev, title } : prev));
  }, []);

  return {
    sessions,
    currentSession,
    loadSessions,
    createSession,
    selectSession,
    setCurrentSession,
    renameSession,
    updateSessionTitle,
  };
}
