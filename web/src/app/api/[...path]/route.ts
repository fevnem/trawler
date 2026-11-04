import type { NextRequest } from "next/server";

const ORIGIN = process.env.API_ORIGIN ?? "http://127.0.0.1:8010";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

async function proxy(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  const url = new URL(request.url);
  const target = `${ORIGIN}/api/${path.join("/")}${url.search}`;

  const headers = new Headers(request.headers);
  headers.delete("host");
  headers.delete("connection");
  headers.delete("accept-encoding");

  const hasBody = !["GET", "HEAD"].includes(request.method);

  let upstream: Response;
  try {
    upstream = await fetch(target, {
      method: request.method,
      headers,
      body: hasBody ? request.body : undefined,
      redirect: "manual",
      // Required by undici when streaming a request body.
      ...(hasBody ? { duplex: "half" } : {}),
    } as RequestInit);
  } catch {
    return Response.json({ detail: "The reader is not reachable." }, { status: 502 });
  }

  const out = new Headers(upstream.headers);
  out.delete("content-encoding");
  out.delete("transfer-encoding");

  return new Response(upstream.body, {
    status: upstream.status,
    statusText: upstream.statusText,
    headers: out,
  });
}

export const GET = proxy;
export const HEAD = proxy;
export const POST = proxy;
export const OPTIONS = proxy;
