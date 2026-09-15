"use client";

import ReactMarkdown from "react-markdown";

interface Props {
  text: string;
}

export default function StreamingMessage({ text }: Props) {
  return (
    <div className="flex gap-3 animate-fade-in">
      <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center flex-shrink-0">
        <span className="text-sm">🐢</span>
      </div>
      <div className="max-w-[85%] rounded-2xl rounded-tl-sm bg-muted px-4 py-3 text-sm leading-relaxed">
        {text ? (
          <div className="prose prose-sm dark:prose-invert max-w-none prose-p:leading-relaxed">
            <ReactMarkdown>{text}</ReactMarkdown>
          </div>
        ) : (
          <div className="flex gap-1 items-center h-5">
            <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground/60 animate-pulse-dot" style={{ animationDelay: "0ms" }} />
            <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground/60 animate-pulse-dot" style={{ animationDelay: "150ms" }} />
            <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground/60 animate-pulse-dot" style={{ animationDelay: "300ms" }} />
          </div>
        )}
      </div>
    </div>
  );
}
