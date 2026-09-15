"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useChat } from "@/hooks/useChat";
import { Session, Artifact, Skill } from "@/lib/types";
import WelcomeScreen from "./WelcomeScreen";
import ChatInput from "./ChatInput";
import MessageBubble from "./MessageBubble";
import { ChevronDown } from "lucide-react";

interface Props {
  session: Session | null;
  onArtifact: (a: Artifact) => void;
  createSession: (title?: string) => Promise<Session | null>;
  onTitleUpdate?: (id: string, title: string) => void;
}

function makeTitle(text: string): string {
  return text.trim().split(/\s+/).slice(0, 6).join(" ");
}

export default function ChatPanel({ session, onArtifact, createSession, onTitleUpdate }: Props) {
  const { messages, isStreaming, streamingText, error, sendMessage, loadMessages, stopStreaming, clearMessages } =
    useChat(session, onArtifact, onTitleUpdate);

  const bottomRef = useRef<HTMLDivElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const [showScrollBtn, setShowScrollBtn] = useState(false);

  // Load messages when session changes
  useEffect(() => {
    if (session?.id) {
      loadMessages(session.id);
    } else {
      clearMessages();
    }
  }, [session?.id]);

  // Scroll to bottom on new content
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, streamingText]);

  // Show scroll-to-bottom button when scrolled up
  const handleScroll = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return;
    const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 80;
    setShowScrollBtn(!atBottom);
  }, []);

  const scrollToBottom = () => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const handleSend = async (text: string, skill?: Skill, overrideSession?: Session) => {
    let activeSession = overrideSession || session;
    if (!activeSession) {
      const title = makeTitle(text);
      const newSession = await createSession(title);
      if (!newSession) return;
      activeSession = newSession;
    }
    await sendMessage(text, skill, activeSession);
  };

  const handleWelcomeSend = async (text: string, skill?: Skill) => {
    const title = makeTitle(text);
    const newSession = session ?? (await createSession(title));
    if (!newSession) return;
    await sendMessage(text, skill, newSession);
  };

  const hasMessages = messages.length > 0 || !!streamingText;

  if (!hasMessages && !isStreaming) {
    return (
      <WelcomeScreen
        onSend={handleWelcomeSend}
        isStreaming={isStreaming}
        onStop={stopStreaming}
      />
    );
  }

  return (
    <div className="chat-root">
      {/* Messages */}
      <div
        className="messages-list"
        ref={scrollRef}
        onScroll={handleScroll}
      >
        {messages.map((msg, i) => (
          <MessageBubble
            key={msg.id}
            message={msg}
            onRegenerate={
              msg.role === "assistant" && i === messages.length - 1 && !isStreaming
                ? () => {
                    const prev = messages[i - 1];
                    if (prev?.role === "user") handleSend(prev.content);
                  }
                : undefined
            }
          />
        ))}

        {/* Streaming assistant message */}
        {isStreaming && streamingText && (
          <div className="msg-row">
            <div className="msg-avatar msg-avatar-bot">🐢</div>
            <div className="msg-bubble-wrap">
              <div className="msg-bubble msg-bubble-bot">
                <div className="chat-prose">{streamingText}</div>
              </div>
            </div>
          </div>
        )}

        {/* Typing dots when no text yet */}
        {isStreaming && !streamingText && (
          <div className="msg-row">
            <div className="msg-avatar msg-avatar-bot">🐢</div>
            <div className="msg-bubble-wrap">
              <div className="msg-bubble msg-bubble-bot">
                <div className="typing-indicator">
                  <div className="typing-dot" />
                  <div className="typing-dot" />
                  <div className="typing-dot" />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="error-banner" style={{ margin: "8px 24px" }}>
            <span>⚠</span>
            <span>{error}</span>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Scroll to bottom */}
      {showScrollBtn && (
        <button className="scroll-bottom-btn" onClick={scrollToBottom}>
          <ChevronDown size={16} />
        </button>
      )}

      {/* Input */}
      <ChatInput
        onSend={(text, skill) => handleSend(text, skill)}
        isStreaming={isStreaming}
        onStop={stopStreaming}
      />
    </div>
  );
}
