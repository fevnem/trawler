const ENDPOINT = "https://trawler.espectator.net/api/mcp";

const TOOLS = [
  { name: "probe", body: "Read a link: title, site, duration, every format with a signed URL, and the subtitle tracks." },
  { name: "list_sites", body: "Search the extractor index by name or domain. Omit the query for the full list." },
  { name: "match", body: "Report which extractor claims a URL, without touching the source." },
  { name: "download_link", body: "Mint a signed URL for one format id, optionally trimmed to a range." },
  { name: "audio_link", body: "Mint a signed URL for the audio stream, converted to mp3, m4a, opus, wav or flac." },
  { name: "gif_link", body: "Mint a signed URL for a GIF cut from a range, up to thirty seconds." },
  { name: "subtitle_link", body: "Mint a signed URL for one caption track." },
];

const CONFIG = `{
  "mcpServers": {
    "trawler": {
      "type": "http",
      "url": "${ENDPOINT}",
      "headers": { "Authorization": "Bearer <token>" }
    }
  }
}`;

export default function McpPage() {
  return (
    <div className="pb-24">
      <h1 className="display mt-12 max-w-[16ch] text-[clamp(2rem,4vw,3.2rem)]">
        The same reader, for agents.
      </h1>
      <p className="mt-4 max-w-[58ch] text-sm leading-relaxed text-muted">
        Trawler speaks the Model Context Protocol over Streamable HTTP. An agent calls a tool, gets a
        signed URL back, and fetches the file itself. No bytes travel through the protocol, and
        nothing is stored on the server.
      </p>

      <div className="mt-10 border-t border-rule">
        <div className="flex flex-col gap-1 border-b border-rule py-4 sm:flex-row sm:items-baseline sm:gap-8">
          <p className="w-40 shrink-0 text-sm">Endpoint</p>
          <p className="num break-all text-xs text-muted">{ENDPOINT}</p>
        </div>
        <div className="flex flex-col gap-1 border-b border-rule py-4 sm:flex-row sm:items-baseline sm:gap-8">
          <p className="w-40 shrink-0 text-sm">Transport</p>
          <p className="text-xs text-muted">Streamable HTTP, JSON-RPC 2.0, stateless</p>
        </div>
        <div className="flex flex-col gap-1 border-b border-rule py-4 sm:flex-row sm:items-baseline sm:gap-8">
          <p className="w-40 shrink-0 text-sm">Auth</p>
          <p className="num text-xs text-muted">Authorization: Bearer &lt;token&gt;</p>
        </div>
        <div className="flex flex-col gap-1 border-b border-rule py-4 sm:flex-row sm:items-baseline sm:gap-8">
          <p className="w-40 shrink-0 text-sm">Links expire</p>
          <p className="text-xs text-muted">Every signed URL is short lived. Mint a fresh one per job.</p>
        </div>
      </div>

      <h2 className="mt-14 text-sm">Tools</h2>
      <div className="mt-3 border-t border-rule">
        {TOOLS.map((tool) => (
          <div
            key={tool.name}
            className="flex flex-col gap-1 border-b border-rule py-3 sm:flex-row sm:items-baseline sm:gap-8"
          >
            <p className="num w-40 shrink-0 text-xs text-ink">{tool.name}</p>
            <p className="text-xs leading-relaxed text-muted">{tool.body}</p>
          </div>
        ))}
      </div>

      <h2 className="mt-14 text-sm">Connect a client</h2>
      <p className="mt-2 max-w-[58ch] text-xs leading-relaxed text-muted">
        Drop this into the client&apos;s MCP configuration, or register the endpoint with its own
        command.
      </p>
      <pre className="num mt-4 overflow-x-auto border border-rule bg-card p-4 text-[11px] leading-relaxed text-muted">
        {CONFIG}
      </pre>
      <pre className="num mt-3 overflow-x-auto border border-rule bg-card p-4 text-[11px] leading-relaxed text-muted">
        {`claude mcp add --transport http trawler ${ENDPOINT} \\
  --header "Authorization: Bearer $TRAWLER_MCP_TOKEN"`}
      </pre>

      <p className="mt-8 max-w-[58ch] text-xs leading-relaxed text-muted">
        Some sources refuse datacenter addresses. When a probe fails with a sign-in or bot message,
        the source is blocking the host, not the tool.
      </p>
    </div>
  );
}
