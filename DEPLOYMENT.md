# Deployment Guide for OTP MCP Server on Render

## Prerequisites
- GitHub account
- Render account (free tier available at https://render.com)
- Zendesk instance URL

## Step 1: Push to Your GitHub Repository

1. Remove the existing remote:
   ```bash
   git remote remove origin
   ```

2. Create a new repository on GitHub (e.g., `your-username/otp-mcp-server`)

3. Add your new repository as the remote:
   ```bash
   git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPO-NAME.git
   git branch -M main
   git push -u origin main
   ```

## Step 2: Deploy on Render

### Option A: Using the Render Dashboard (Recommended)

1. Log in to your Render account at https://dashboard.render.com

2. Click **"New +"** and select **"Blueprint"**

3. Connect your GitHub repository

4. Render will detect the `render.yaml` file and configure the service automatically

5. Click **"Apply"** to deploy

### Option B: Manual Setup

1. Log in to your Render account

2. Click **"New +"** and select **"Web Service"**

3. Connect your GitHub repository

4. Configure the service:
   - **Name**: otp-mcp-server
   - **Environment**: Docker
   - **Plan**: Free (or choose your preferred plan)
   - **Docker Command**: Leave empty (uses Dockerfile's CMD)

5. Add Environment Variables:
   - `OTP_MCP_SERVER_TRANSPORT`: `http-stream`
   - `OTP_MCP_SERVER_HOST`: `0.0.0.0`
   - `OTP_MCP_SERVER_PORT`: `8000`
   - `OTP_MCP_SERVER_LOG_LEVEL`: `INFO`
   - `OTP_MCP_SERVER_DB`: `/app/freakotp.db`

6. Click **"Create Web Service"**

## Step 3: Get Your Service URL

After deployment completes, Render will provide you with a URL like:
```
https://otp-mcp-server.onrender.com
```

## Step 4: Configure Zendesk

To connect this MCP server to your Zendesk instance:

1. In your Zendesk admin panel, navigate to the integration settings

2. Add the MCP server endpoint:
   ```
   https://your-service-name.onrender.com
   ```

3. Configure authentication if required

4. Test the connection

## Step 5: Configure Claude Desktop (Optional)

If you want to use this locally with Claude Desktop, update your config:

```json
{
  "mcpServers": {
    "otp": {
      "command": "uvx",
      "args": ["otp-mcp-server", "--http-stream", "--host", "YOUR-RENDER-URL", "--port", "443"]
    }
  }
}
```

## Available Features

The OTP MCP server provides:
- TOTP (Time-based OTP) generation
- HOTP (HMAC-based OTP) generation
- Token storage and management
- Multiple transport protocols (HTTP Stream, SSE, STDIO)

## Monitoring

- View logs in the Render dashboard
- Monitor health at: `https://your-service-name.onrender.com/health`

## Troubleshooting

### Service won't start
- Check Render logs for errors
- Verify all environment variables are set correctly
- Ensure the Docker build completes successfully

### Database issues
- The database is stored at `/app/freakotp.db` inside the container
- For persistence, consider adding a mounted volume in render.yaml

### Connection issues from Zendesk
- Verify the Render service URL is correct
- Check that the service is running (not sleeping on free tier)
- Ensure firewall/security settings allow connections

## Notes

- **Free Tier Limitation**: Render's free tier services spin down after 15 minutes of inactivity. They automatically restart on the next request, but this adds ~30 seconds of cold start time.
- **Persistence**: The database is ephemeral on the free tier. For production use, consider upgrading to a paid plan with persistent storage.
- **Security**: For production deployments, implement proper authentication and use HTTPS.

## Additional Resources

- [Render Documentation](https://render.com/docs)
- [Original OTP MCP Repository](https://github.com/andreax79/otp-mcp)
- [MCP Protocol Documentation](https://modelcontextprotocol.io)
