"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Plus, ChevronUp, Square, Paperclip, X } from "lucide-react";
import type { Skill } from "@/lib/types";

interface Props {
  onSend: (text: string, skill?: Skill) => void;
  isStreaming?: boolean;
  onStop?: () => void;
}

const SKILLS: { label: string; value: Skill; desc: string }[] = [
  { label: "✍️ Essay", value: "ship30", desc: "Ship 30-style atomic essay" },
  { label: "📄 Markdown", value: "artifact_markdown", desc: "Structured markdown doc" },
  { label: "🌐 HTML", value: "artifact_html", desc: "Interactive HTML artifact" },
];

export default function ChatInput({ onSend, isStreaming, onStop }: Props) {
  const [text, setText] = useState("");
  const [skill, setSkill] = useState<Skill | undefined>(undefined);
  const [showSkills, setShowSkills] = useState(false);
  const [attachName, setAttachName] = useState<string | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = Math.min(ta.scrollHeight, 180) + "px";
  }, [text]);

  const handleSend = () => {
    const t = text.trim();
    if (!t || isStreaming) return;
    onSend(t, skill);
    setText("");
    setSkill(undefined);
    setAttachName(null);
  };

  const handleKey = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) setAttachName(file.name);
    e.target.value = "";
  };

  return (
    <div className="chat-input-bar">
      <div className="composer-pill" style={{ width: "100%", maxWidth: 740 }}>
        {/* Attachment chip row */}
        {attachName && (
          <div style={{ padding: "8px 14px 0", display: "flex", gap: 6 }}>
            <div className="attach-chip">
              <Paperclip size={11} />
              <span className="attach-chip-name">{attachName}</span>
              <button
                style={{ background: "none", border: "none", cursor: "pointer", color: "var(--text-muted)", display: "flex", alignItems: "center", marginLeft: 2 }}
                onClick={() => setAttachName(null)}
              >
                <X size={11} />
              </button>
            </div>
          </div>
        )}

        {/* Main row */}
        <div className="composer-pill-inner">
          <button
            className="composer-btn"
            title="Attach file"
            onClick={() => fileRef.current?.click()}
          >
            <Paperclip size={16} />
          </button>
          <input ref={fileRef} type="file" style={{ display: "none" }} onChange={handleFile} />

          <textarea
            ref={textareaRef}
            className="composer-textarea"
            placeholder="Message Lenny's AI…"
            value={text}
            rows={1}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKey}
            disabled={isStreaming}
          />

          {isStreaming ? (
            <button className="composer-stop-btn" onClick={onStop} title="Stop generating">
              <Square size={14} />
            </button>
          ) : (
            <button
              className="composer-send-btn"
              onClick={handleSend}
              disabled={!text.trim()}
              title="Send"
            >
              <Send size={15} />
            </button>
          )}
        </div>

        {/* Footer row */}
        <div className="composer-footer" style={{ position: "relative" }}>
          <button
            className={`composer-footer-btn ${skill ? "active" : ""}`}
            onClick={() => setShowSkills((v) => !v)}
          >
            <Plus size={13} />
            {skill ? SKILLS.find((s) => s.value === skill)?.label ?? "Format" : "Format"}
            <ChevronUp
              size={12}
              style={{
                transform: showSkills ? "rotate(180deg)" : "rotate(0deg)",
                transition: "transform 150ms",
              }}
            />
          </button>

          {skill && (
            <button
              className="composer-footer-btn"
              onClick={() => setSkill(undefined)}
            >
              Clear
            </button>
          )}

          {showSkills && (
            <div className="skills-popup">
              {SKILLS.map((s) => (
                <button
                  key={s.value}
                  className="skills-popup-item"
                  onClick={() => {
                    setSkill(s.value);
                    setShowSkills(false);
                  }}
                >
                  <span>{s.label}</span>
                  <span style={{ fontSize: "12px", color: "var(--text-muted)", marginLeft: "auto" }}>{s.desc}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
