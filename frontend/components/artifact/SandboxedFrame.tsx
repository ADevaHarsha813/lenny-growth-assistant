"use client";

interface Props {
  html: string;
}

export default function SandboxedFrame({ html }: Props) {
  return (
    <iframe
      srcDoc={html}
      sandbox="allow-scripts"
      className="w-full h-full border-0"
      title="HTML Artifact Preview"
    />
  );
}
