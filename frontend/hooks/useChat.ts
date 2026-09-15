"use client";

import { useState, useCallback, useRef } from "react";
import { Message, Artifact, Session, Skill } from "@/lib/types";
import { api } from "@/lib/api";

export function useChat(session: Session | null, onArtifact: (a: Artifact) => void, onTitleUpdate?: (id: string, title: string) => void) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingText, setStreamingText] = useState("");
  const [error, setError] = useState<string | null>(null);
  const isStreamingRef = useRef(false);
  const abortRef = useRef<(() => void) | null>(null);

  const loadMessages = useCallback(async (sessionId: string) => {
    try {
      setError(null);
      const msgs = await api.getMessages(sessionId);
      setMessages(msgs);
    } catch (e) {
      console.error("Failed to load messages", e);
    }
  }, []);

  const sendMessage = useCallback(
    async (content: string, skill?: Skill, overrideSession?: Session) => {
      const activeSession = overrideSession || session;
      if (!activeSession || isStreamingRef.current) return;

      setError(null);
      const isFirstMessage = messages.length === 0;

      const userMsg: Message = {
        id: Date.now().toString(),
        session_id: activeSession.id,
        role: "user",
        content,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMsg]);
      isStreamingRef.current = true;
      setIsStreaming(true);
      setStreamingText("");

      try {
        const response = await api.streamChat(activeSession.id, { message: content, skill });
        if (!response.ok) {
          const errData = await response.json().catch(() => ({}));
          throw new Error(errData.detail || errData.error || `HTTP ${response.status}`);
        }
        if (!response.body) throw new Error("No response body from server");

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let assistantText = "";

        abortRef.current = () => reader.cancel();

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            const raw = line.slice(6).trim();
            if (!raw) continue;
            try {
              const payload = JSON.parse(raw);
              if (payload.type === "text") {
                assistantText += payload.delta;
                setStreamingText(assistantText);
              } else if (payload.type === "artifact") {
                const art: Artifact = {
                  id: Date.now().toString(),
                  session_id: activeSession.id,
                  artifact_type: payload.artifact.type,
                  title: payload.artifact.title,
                  content: payload.artifact.content,
                  created_at: new Date().toISOString(),
                };
                onArtifact(art);
              } else if (payload.type === "error") {
                throw new Error(payload.message || "Agent error");
              }
            } catch (parseErr) {
              // skip malformed lines
            }
          }
        }

        if (assistantText) {
          const assistantMsg: Message = {
            id: (Date.now() + 1).toString(),
            session_id: activeSession.id,
            role: "assistant",
            content: assistantText,
            created_at: new Date().toISOString(),
          };
          setMessages((prev) => [...prev, assistantMsg]);

          // Trigger title refresh after first exchange
          if (isFirstMessage && onTitleUpdate) {
            setTimeout(async () => {
              try {
                const updated = await api.getSession(activeSession.id);
                if (updated.title && updated.title !== "New conversation") {
                  onTitleUpdate(activeSession.id, updated.title);
                }
              } catch {}
            }, 500);
          }
        } else if (!assistantText) {
          setError("No response received. Please try again.");
        }
      } catch (e: any) {
        console.error("Stream error", e);
        setError(e.message || "Something went wrong. Please try again.");
      } finally {
        isStreamingRef.current = false;
        setIsStreaming(false);
        setStreamingText("");
        abortRef.current = null;
      }
    },
    [session, onArtifact, onTitleUpdate, messages.length]
  );

  const stopStreaming = useCallback(() => {
    abortRef.current?.();
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setError(null);
    setStreamingText("");
  }, []);

  return { messages, isStreaming, streamingText, error, sendMessage, loadMessages, stopStreaming, clearMessages };
}
