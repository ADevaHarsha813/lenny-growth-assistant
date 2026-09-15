"use client";

import { useState } from "react";
import { X, Copy, Check, ExternalLink } from "lucide-react";
import { Artifact } from "@/lib/types";
import MarkdownViewer from "./MarkdownViewer";
import SandboxedFrame from "./SandboxedFrame";
import ReactMarkdown from "react-markdown";

interface Props {
  artifact: Artifact;
  onClose: () => void;
}

type Tab = "preview" | "source";

export default function ArtifactPane({ artifact, onClose }: Props) {
  const [tab, setTab] = useState<Tab>("preview");
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(artifact.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const typeLabel =
    artifact.artifact_type === "ship30"
      ? "✍️ Essay"
      : artifact.artifact_type === "html"
      ? "🌐 HTML"
      : "📄 Markdown";

  return (
    <div className="flex flex-col h-full bg-background">
      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-border">
        <span className="text-xs font-medium text-muted-foreground">{typeLabel}</span>
        <h2 className="flex-1 text-sm font-medium truncate">{artifact.title}</h2>
        <div className="flex items-center gap-1">
          {/* Tab switcher */}
          {(artifact.artifact_type === "html" || artifact.artifact_type === "markdown" || artifact.artifact_type === "ship30") && (
            <div className="flex rounded-lg bg-muted p-0.5 mr-1">
              {(["preview", "source"] as Tab[]).map((t) => (
                <button
                  key={t}
                  onClick={() => setTab(t)}
                  className={`px-2.5 py-1 text-xs rounded-md font-medium transition-colors ${
                    tab === t ? "bg-background shadow-sm text-foreground" : "text-muted-foreground"
                  }`}
                >
                  {t === "preview" ? "Preview" : "Source"}
                </button>
              ))}
            </div>
          )}
          <button
            onClick={handleCopy}
            className="p-1.5 rounded-md hover:bg-muted transition-colors text-muted-foreground hover:text-foreground"
            title="Copy"
          >
            {copied ? <Check size={15} className="text-green-500" /> : <Copy size={15} />}
          </button>
          <button
            onClick={onClose}
            className="p-1.5 rounded-md hover:bg-muted transition-colors text-muted-foreground hover:text-foreground"
          >
            <X size={15} />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {tab === "source" ? (
          <div className="h-full overflow-auto p-4">
            <pre className="text-xs font-mono text-foreground/80 whitespace-pre-wrap break-words leading-relaxed">
              {artifact.content}
            </pre>
          </div>
        ) : artifact.artifact_type === "html" ? (
          <SandboxedFrame html={artifact.content} />
        ) : (
          <MarkdownViewer content={artifact.content} />
        )}
      </div>
    </div>
  );
}
