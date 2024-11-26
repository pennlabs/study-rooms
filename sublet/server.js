const express = require('express');
const next = require('next');
const { createProxyMiddleware } = require('http-proxy-middleware');

const port = parseInt(process.env.PORT, 10) || 3000;
const dev = process.env.NODE_ENV !== 'production';
const app = next({ dev });
const handle = app.getRequestHandler();

app.prepare().then(() => {
  const server = express();

  // Proxy configuration for '/api' endpoint
  const devProxy = {
    target: 'http://127.0.0.1:8000', // Target backend server
    changeOrigin: true,
    //pathRewrite: { '^/api': '' }, // Rewrite the '/api' prefix from the request path if needed
    logLevel: 'debug'
  };

  // Use the proxy middleware for requests to '/api'

  server.use('/api', (req, res, next) => {
    console.log(`Received request for ${req.url}`);
    next();
  });

  server.use('/api', createProxyMiddleware(devProxy));

  // Default catch-all handler to allow Next.js to handle all other routes
  server.all('*', (req, res) => handle(req, res));

  server.listen(port, (err) => {
    if (err) throw err;
    console.log(`> Ready on http://localhost:${port}`);
  });
});