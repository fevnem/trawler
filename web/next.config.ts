import type { NextConfig } from "next";

const origin = process.env.API_ORIGIN ?? "http://127.0.0.1:8010";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  output: "standalone",
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${origin}/api/:path*` }];
  },
};

export default nextConfig;
