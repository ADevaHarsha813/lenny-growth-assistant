"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface Props {
  content: string;
}

export default function MarkdownViewer({ content }: Props) {
  return (
    <div className="h-full overflow-auto px-6 py-5">
      <div className="prose prose-sm dark:prose-invert max-w-none
        prose-headings:font-semibold prose-headings:tracking-tight
        prose-p:leading-relaxed prose-p:text-foreground/90
        prose-strong:text-foreground prose-strong:font-semibold
        prose-code:bg-muted prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-xs
        prose-pre:bg-muted prose-pre:border prose-pre:border-border
        prose-blockquote:border-l-primary prose-blockquote:text-muted-foreground
        prose-li:leading-relaxed prose-hr:border-border">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
      </div>
    </div>
  );
}
