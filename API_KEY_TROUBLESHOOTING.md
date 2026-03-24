# API Key Troubleshooting

## Current Issue

API key is configured and authenticates successfully, but returns `404 not_found_error` for all Claude models.

**Error**: `Error code: 404 - model: claude-3-5-sonnet-20241022`

## Tested Models (All Failed)

- claude-3-5-sonnet-20241022
- claude-3-5-sonnet-20240620
- claude-3-sonnet-20240229
- claude-3-opus-20240229

## Possible Causes

### 1. Organization Has No Model Access

The API key belongs to an organization that hasn't been granted access to Claude models.

**Solution**: 
- Log in to https://console.anthropic.com
- Check "Organization Settings" → "API Access"
- Ensure Claude models are enabled for your organization

### 2. API Key Scope Limitation

The key may have restricted scopes that don't include model inference.

**Solution**:
- Go to https://console.anthropic.com/settings/keys
- Check the key's permissions/scopes
- Generate a new key with full permissions if needed

### 3. Billing/Subscription Issue

Account may not have active billing or sufficient credits.

**Solution**:
- Check https://console.anthropic.com/settings/billing
- Ensure billing is active and credits are available
- Add payment method if needed

### 4. Wrong API Endpoint

The key might be for a different API version or endpoint.

**Solution**:
- Verify you're using the correct Anthropic API endpoint
- Check if your organization uses a custom/private endpoint

## Quick Test

Run this command to test your key directly:

```bash
curl https://api.anthropic.com/v1/messages \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 10,
    "messages": [{"role": "user", "content": "test"}]
  }'
```

## Current Workaround

The system is configured to gracefully handle this:
- Authentication works (users can log in)
- All other features work normally
- AI analysis shows helpful error message
- Once key is fixed, no code changes needed

## Next Steps

1. Check Anthropic Console for organization settings
2. Verify model access is enabled
3. If issue persists, contact Anthropic support
4. Restart server after fixing: `./start_server.sh`
