# YouTube Scraper Configuration

## Setup Instructions

1. **Copy the template config:**
   ```bash
   cp scraper_config.json.template scraper_config.json
   ```

2. **Add your API keys to `scraper_config.json`:**
   - `youtube.api_key` - Your YouTube Data API v3 key
   - `supabase.auth_token` - Your Supabase service role key
   - `annealing.claude_api_key` - Your Anthropic Claude API key

3. **IMPORTANT:** Never commit `scraper_config.json` to git!
   - It's already in `.gitignore`
   - Only commit `scraper_config.json.template`

## Environment Variables (Alternative)

You can also use environment variables instead of config file:

```bash
export YOUTUBE_API_KEY="your-key"
export SUPABASE_AUTH_TOKEN="your-token"
export CLAUDE_API_KEY="your-claude-key"
```

The scripts will check environment variables first, then fall back to config file.

## Security Checklist

- [ ] `scraper_config.json` is in `.gitignore`
- [ ] Real API keys are only in `scraper_config.json` (not the template)
- [ ] Never share `scraper_config.json` publicly
- [ ] Use environment variables in production/CI environments
