"use client";

import { useState } from "react";
import { Copy, Check, ThumbsUp, ThumbsDown, RefreshCw, Share2 } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Message } from "@/lib/types";

interface Props {
  message: Message;
  onRegenerate?: () => void;
}

export default function MessageBubble({ message, onRegenerate }: Props) {
  const [copied, setCopied]           = useState(false);
  const [shared, setShared]           = useState(false);
  const [thumbed, setThumbed]         = useState<"up" | "down" | null>(null);
  const [showFeedback, setShowFeedback] = useState(false);
  const [feedbackText, setFeedbackText] = useState("");
  const [feedbackSent, setFeedbackSent] = useState(false);

  const isUser = message.role === "user";

  /* ── Copy message text ── */
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {}
  };

  /* ── Share: copy message text to clipboard with confirmation ── */
  const handleShare = async () => {
    try {
      const text = `${message.content}\n\n— Oogway AI`;
      await navigator.clipboard.writeText(text);
      setShared(true);
      setTimeout(() => setShared(false), 2500);
    } catch {}
  };

  /* ── Thumbs up ── */
  const handleThumbUp = () => {
    if (thumbed === "up") {
      setThumbed(null);
      setShowFeedback(false);
    } else {
      setThumbed("up");
      setShowFeedback(false);
      setFeedbackSent(false);
    }
  };

  /* ── Thumbs down: show feedback box ── */
  const handleThumbDown = () => {
    if (thumbed === "down") {
      setThumbed(null);
      setShowFeedback(false);
    } else {
      setThumbed("down");
      setShowFeedback(true);
      setFeedbackSent(false);
    }
  };

  /* ── Submit feedback ── */
  const handleFeedbackSubmit = () => {
    // In production: POST to /api/feedback with message.id + feedbackText
    setFeedbackSent(true);
    setShowFeedback(false);
    setFeedbackText("");
  };

  const timeStr = (() => {
    try {
      return new Date(message.created_at).toLocaleTimeString(undefined, {
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return "";
    }
  })();

  return (
    <div className={`msg-row ${isUser ? "msg-row-user" : ""}`}>
      {!isUser && (
        <div className="msg-avatar msg-avatar-bot" aria-hidden="true">🐢</div>
      )}

      <div className={`msg-bubble-wrap ${isUser ? "msg-bubble-wrap-user" : ""}`}>
        <div className={`msg-bubble ${isUser ? "msg-bubble-user" : "msg-bubble-bot"}`}>
          {isUser ? (
            <p style={{ whiteSpace: "pre-wrap", wordBreak: "break-word", margin: 0 }}>
              {message.content}
            </p>
          ) : (
            <div className="chat-prose">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.content}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {timeStr && (
          <span className="msg-time" aria-label={`Sent at ${timeStr}`}>{timeStr}</span>
        )}

        {/* Sources */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="source-chips">
            {message.sources.slice(0, 3).map((src, i) => (
              <span key={i} className="source-chip" title={src.source_file}>
                <span style={{ width: 5, height: 5, borderRadius: "50%", background: "var(--green)", flexShrink: 0, display: "inline-block" }} />
                {src.episode_title?.slice(0, 32) ?? src.source_file}
              </span>
            ))}
          </div>
        )}

        {/* ── Action buttons (bot only) ── */}
        {!isUser && (
          <>
            <div className="msg-actions">
              {/* Copy */}
              <button
                onClick={handleCopy}
                className={`msg-action-btn ${copied ? "share-active" : ""}`}
                title={copied ? "Copied!" : "Copy response"}
              >
                {copied ? <Check size={13} /> : <Copy size={13} />}
              </button>

              {/* Regenerate */}
              {onRegenerate && (
                <button
                  onClick={onRegenerate}
                  className="msg-action-btn"
                  title="Regenerate response"
                >
                  <RefreshCw size={13} />
                </button>
              )}

              {/* Thumbs up */}
              <button
                onClick={handleThumbUp}
                className={`msg-action-btn ${thumbed === "up" ? "thumb-up-active" : ""}`}
                title={thumbed === "up" ? "Marked helpful" : "Helpful"}
              >
                <ThumbsUp size={13} />
              </button>

              {/* Thumbs down */}
              <button
                onClick={handleThumbDown}
                className={`msg-action-btn ${thumbed === "down" ? "thumb-down-active" : ""}`}
                title={thumbed === "down" ? "Feedback noted" : "Not helpful"}
              >
                <ThumbsDown size={13} />
              </button>

              {/* Share */}
              <button
                onClick={handleShare}
                className={`msg-action-btn ${shared ? "share-active" : ""}`}
                title={shared ? "Copied to clipboard!" : "Copy to share"}
              >
                {shared ? <Check size={13} /> : <Share2 size={13} />}
              </button>

              {/* Toast confirmations */}
              {thumbed === "up" && !showFeedback && !feedbackSent && (
                <span className="msg-toast success">👍 Helpful!</span>
              )}
              {feedbackSent && (
                <span className="msg-toast success">✓ Thanks for the feedback</span>
              )}
              {shared && (
                <span className="msg-toast success">Copied!</span>
              )}
            </div>

            {/* Thumbs-down feedback box */}
            {showFeedback && thumbed === "down" && (
              <div className="msg-feedback-wrap">
                <textarea
                  className="msg-feedback-textarea"
                  placeholder="What was wrong with this response? (optional)"
                  value={feedbackText}
                  onChange={(e) => setFeedbackText(e.target.value)}
                  rows={2}
                  autoFocus
                />
                <div style={{ display: "flex", gap: 6 }}>
                  <button
                    className="msg-feedback-submit"
                    onClick={handleFeedbackSubmit}
                  >
                    Send feedback
                  </button>
                  <button
                    className="msg-feedback-submit"
                    onClick={() => { setShowFeedback(false); setThumbed(null); }}
                    style={{ background: "none", border: "none", color: "var(--text-muted)" }}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
