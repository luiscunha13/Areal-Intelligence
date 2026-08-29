/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    const apiHost = process.env.API_HOST || 'api:8000';
    return [
      {
        source: '/api/:path*',
        destination: `http://${apiHost}/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
