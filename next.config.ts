import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/python-chat',
        destination: 'http://localhost:8000/api/python-chat',
      },
    ]
  },
};

export default nextConfig;
