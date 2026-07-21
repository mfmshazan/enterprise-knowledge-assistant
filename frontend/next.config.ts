import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // `standalone` produces a minimal, self-contained server bundle that the
  // Docker runtime stage copies — no node_modules in the final image.
  output: "standalone",
};

export default nextConfig;
