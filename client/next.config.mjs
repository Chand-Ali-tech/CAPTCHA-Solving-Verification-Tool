/** @type {import('next').NextConfig} */

// The FastAPI backend base URL. Override with BACKEND_URL in the environment
// (e.g. in production). Defaults to the local dev server on port 8000.
const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8000";

const nextConfig = {
  // Proxy every /api/* request from the browser to the FastAPI backend.
  // This avoids CORS entirely: the browser only ever talks to the Next.js
  // origin, and Next forwards API calls server-side to FastAPI.
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${BACKEND_URL}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
