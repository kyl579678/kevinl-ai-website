# Security Configuration

## Authentication

AI analysis endpoints are protected by password authentication to prevent unauthorized API usage.

### Setup

1. **Set Admin Password** (Required)

```bash
export ADMIN_PASSWORD="your-secure-password-here"
```

Default password is `demo123` - **CHANGE THIS IN PRODUCTION!**

2. **Enable AI Analysis** (Optional)

To enable Claude-powered AI analysis:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

3. **Start Server**

```bash
./start_server.sh
```

Or manually:

```bash
python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

## Frontend Usage

1. Navigate to Data Gallery
2. Select a wafer
3. Click "🤖 AI Analysis" button
4. Enter password when prompted
5. Token is stored in localStorage for 24 hours

## API Endpoints

### Login
```bash
POST /api/auth/login
Content-Type: application/json

{"password": "your-password"}

# Response:
{
  "success": true,
  "token": "...",
  "expires_in": 86400
}
```

### Protected Endpoints

All `/api/agent/*` endpoints require authentication:

```bash
GET /api/agent/analyze/{wafer_id}
Header: Authorization: Bearer <token>
```

## Security Features

- ✅ Password-based authentication
- ✅ Session tokens (24-hour expiry)
- ✅ Automatic token storage (localStorage)
- ✅ Graceful degradation (AI disabled without API key)
- ✅ 401 Unauthorized for invalid/expired tokens

## Production Recommendations

1. **Use strong password** (16+ characters, mixed case, symbols)
2. **Set environment variables** in systemd service or .env file
3. **Use HTTPS** (already handled by Cloudflare Tunnel)
4. **Rotate passwords** regularly
5. **Monitor API usage** via server logs
6. **Rate limiting** (not implemented - add if needed)

## Password Reset

To change password, simply restart server with new ADMIN_PASSWORD:

```bash
export ADMIN_PASSWORD="new-password"
./start_server.sh
```

Existing tokens will remain valid until expiry.

## Disabling Authentication

To disable authentication (NOT RECOMMENDED):

Remove or comment out auth imports in `backend/main.py`.
