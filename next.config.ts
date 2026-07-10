import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Cloudflare Pages 등 정적 호스팅용 완전 정적 export (모든 페이지가 SSG라 서버 불필요)
  output: "export",
};

export default nextConfig;
