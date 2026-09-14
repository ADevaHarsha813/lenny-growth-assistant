export default function ChatPage() {
  return (
    <main className="flex h-screen bg-background text-foreground">
      {/* Phase 4 — full chat UI goes here */}
      <div className="flex flex-1 items-center justify-center">
        <div className="text-center space-y-3">
          <div className="text-4xl">🌱</div>
          <h1 className="text-2xl font-semibold">Lenny Growth Assistant</h1>
          <p className="text-muted-foreground text-sm max-w-xs">
            Backend is starting up. Full UI coming in Phase 4.
          </p>
          <a
            href="http://localhost:8000/health"
            target="_blank"
            className="inline-block mt-2 text-xs text-primary underline underline-offset-4"
          >
            Check API health →
          </a>
        </div>
      </div>
    </main>
  );
}
