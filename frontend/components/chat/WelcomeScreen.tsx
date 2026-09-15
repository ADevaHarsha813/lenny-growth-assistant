"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Plus, ChevronUp, Square } from "lucide-react";
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

export default function WelcomeScreen({ onSend, isStreaming, onStop }: Props) {
  const [text, setText] = useState("");
  const [skill, setSkill] = useState<Skill | undefined>(undefined);
  const [showSkills, setShowSkills] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

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
  };

  const handleKey = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="welcome-root">
      <div className="welcome-ambient" />

      <div className="welcome-content welcome-content-centered">
        {/* Turtle */}
        <div className="turtle-wrap">
          <div className="turtle-halo" />
          <span className="turtle-icon">🐢</span>
        </div>

        {/* Heading */}
        <h1 className="welcome-heading">Ask Lenny anything about growth.</h1>

        {/* Composer */}
        <div className="composer-pill" style={{ width: "100%" }}>
          <div className="composer-pill-inner">
            <textarea
              ref={textareaRef}
              className="composer-textarea"
              placeholder="Ask Lenny anything about growth…"
              value={text}
              rows={1}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={handleKey}
              disabled={isStreaming}
              autoFocus
            />
            {isStreaming ? (
              <button className="composer-stop-btn" onClick={onStop} title="Stop">
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

          {/* Footer */}
          <div className="composer-footer" style={{ position: "relative" }}>
            <button
              className={`composer-footer-btn ${skill ? "active" : ""}`}
              onClick={() => setShowSkills((v) => !v)}
              title="Output format"
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
                style={{ color: "var(--text-muted)" }}
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
    </div>
  );
}
