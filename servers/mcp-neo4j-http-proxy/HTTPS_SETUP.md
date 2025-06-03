# HTTPS Setup Guide for memory.aynshteyn.dev

This guide will help you set up HTTPS for your Neo4j MCP HTTP Proxy server on `memory.aynshteyn.dev`.

## Prerequisites

✅ Domain DNS record configured (pointing to your server IP)  
✅ SSL certificates available (`domain.cert.pem`, `private.key.pem`)  
✅ Server running on 95.163.223.236  
✅ FastMCP server with SSL support added  

## Quick Setup

### 1. Copy SSL Certificates

Copy your SSL certificates to the server:

```bash
# Create SSL directory
mkdir -p /home/user/ssl

# Copy certificates (replace paths as needed)
cp /path/to/your/domain.cert.pem /home/user/ssl/domain.cert.pem
cp /path/to/your/private.key.pem /home/user/ssl/private.key.pem

# Set proper permissions
chmod 600 /home/user/ssl/private.key.pem
chmod 644 /home/user/ssl/domain.cert.pem
```

### 2. Configure Environment

Edit the production configuration:

```bash
cd servers/mcp-neo4j-http-proxy
cp production.config .env
# Edit .env with your Neo4j credentials
```

Update these values in `.env`:
```bash
NEO4J_URL=your_neo4j_url
NEO4J_USERNAME=your_username
NEO4J_PASSWORD=your_password
SSL_CERTFILE=/home/user/ssl/domain.cert.pem
SSL_KEYFILE=/home/user/ssl/private.key.pem
```

### 3. Start HTTPS Server

```bash
# Make script executable (if not already done)
chmod +x run_https.sh

# Start the server
sudo ./run_https.sh
```

Note: `sudo` is required because port 443 (HTTPS) is a privileged port.

## Manual Configuration

If you prefer manual configuration, you can start the server directly:

```bash
sudo python -m mcp_neo4j_http_proxy \
    --ssl \
    --ssl-certfile /home/user/ssl/domain.cert.pem \
    --ssl-keyfile /home/user/ssl/private.key.pem \
    --port 443 \
    --host 0.0.0.0 \
    --db-url your_neo4j_url \
    --username your_neo4j_username \
    --password your_neo4j_password
```

## Environment Variables

You can also configure via environment variables:

```bash
export SSL_ENABLED=true
export SSL_CERTFILE=/home/user/ssl/domain.cert.pem
export SSL_KEYFILE=/home/user/ssl/private.key.pem
export HTTP_PORT=443
export NEO4J_URL=your_neo4j_url
export NEO4J_USERNAME=your_username
export NEO4J_PASSWORD=your_password

python -m mcp_neo4j_http_proxy --ssl
```

## Testing HTTPS

Once started, test your HTTPS server:

```bash
# Health check
curl https://memory.aynshteyn.dev/health

# Expected response:
# {"status":"healthy","service":"mcp-neo4j-memory-http"}
```

## MCP Client Connection

Your HTTPS MCP server will be available at:

**URL**: `https://memory.aynshteyn.dev/sse`

## Production Deployment

### Using systemd (recommended)

Create a systemd service file:

```bash
sudo tee /etc/systemd/system/mcp-neo4j-https.service > /dev/null <<EOF
[Unit]
Description=Neo4j MCP HTTPS Server
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/mcp-neo4j-https/servers/mcp-neo4j-http-proxy
Environment=SSL_ENABLED=true
Environment=SSL_CERTFILE=/home/user/ssl/domain.cert.pem
Environment=SSL_KEYFILE=/home/user/ssl/private.key.pem
Environment=HTTP_PORT=443
ExecStart=/usr/bin/python -m mcp_neo4j_http_proxy --ssl
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
sudo systemctl enable mcp-neo4j-https
sudo systemctl start mcp-neo4j-https

# Check status
sudo systemctl status mcp-neo4j-https
```

### Using PM2

```bash
# Install PM2 if not already installed
npm install -g pm2

# Create ecosystem file
cat > ecosystem.config.js <<EOF
module.exports = {
  apps: [{
    name: 'mcp-neo4j-https',
    script: 'python',
    args: '-m mcp_neo4j_http_proxy --ssl',
    cwd: '/path/to/mcp-neo4j-https/servers/mcp-neo4j-http-proxy',
    env: {
      SSL_ENABLED: 'true',
      SSL_CERTFILE: '/home/user/ssl/domain.cert.pem',
      SSL_KEYFILE: '/home/user/ssl/private.key.pem',
      HTTP_PORT: '443'
    },
    restart_delay: 3000,
    max_restarts: 5
  }]
};
EOF

# Start with PM2
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

## Troubleshooting

### Common Issues

1. **Permission Denied (Port 443)**
   ```bash
   # Run with sudo or use a higher port (e.g., 8443) and configure reverse proxy
   sudo python -m mcp_neo4j_http_proxy --ssl --port 443
   ```

2. **Certificate Not Found**
   ```bash
   # Check certificate paths
   ls -la /home/user/ssl/
   # Ensure correct paths in configuration
   ```

3. **SSL Certificate Errors**
   ```bash
   # Verify certificate validity
   openssl x509 -in /home/user/ssl/domain.cert.pem -text -noout
   ```

4. **Neo4j Connection Issues**
   ```bash
   # Test Neo4j connection
   python -c "from neo4j import GraphDatabase; driver = GraphDatabase.driver('your_url', auth=('user', 'pass')); driver.verify_connectivity(); print('Connected!')"
   ```

### Logs

Check server logs for debugging:

```bash
# If using systemd
sudo journalctl -u mcp-neo4j-https -f

# If using PM2
pm2 logs mcp-neo4j-https

# If running manually
python -m mcp_neo4j_http_proxy --ssl --log-level debug
```

## Security Notes

- Keep your private key secure (`chmod 600`)
- Consider using a reverse proxy (nginx/caddy) for additional security
- Regularly update SSL certificates before expiration
- Monitor server access logs
- Use strong Neo4j credentials

## Next Steps

After HTTPS is working:
1. Set up automatic SSL certificate renewal (if using Let's Encrypt)
2. Configure monitoring and alerting
3. Set up backup procedures
4. Consider rate limiting and authentication
5. Document your MCP tools and usage

## Support

If you encounter issues:
1. Check the logs for error messages
2. Verify SSL certificate validity
3. Test Neo4j connectivity separately
4. Ensure firewall allows port 443
5. Check DNS resolution for memory.aynshteyn.dev 