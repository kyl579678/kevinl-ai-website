#!/bin/bash
# Start Defect iDoctor server with authentication

cd "$(dirname "$0")"

# Load environment variables from .env if it exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
    echo "✅ Loaded configuration from .env"
fi

# Set password (change this!)
export ADMIN_PASSWORD="${ADMIN_PASSWORD:-kevin2026}"

# Optional: Set Anthropic API key to enable AI analysis
# Will be loaded from .env if available

echo "Starting server with:"
echo "  - Admin password: ${ADMIN_PASSWORD:0:3}***"
echo "  - AI enabled: ${ANTHROPIC_API_KEY:+YES (API key configured)}"
[ -z "$ANTHROPIC_API_KEY" ] && echo "  ⚠️  AI disabled: Set ANTHROPIC_API_KEY in .env to enable"

# Kill existing server
pkill -f "uvicorn backend.main" 2>/dev/null

# Start server
nohup python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &

sleep 2

if pgrep -f "uvicorn backend.main" > /dev/null; then
    echo "✅ Server started (PID: $(pgrep -f 'uvicorn backend.main'))"
    echo "📍 URL: http://localhost:8000"
    echo "📍 Frontend: http://localhost:8000/frontend/defect-idoctor.html"
else
    echo "❌ Server failed to start. Check server.log"
    exit 1
fi
