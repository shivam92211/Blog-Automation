# API Retry Policy

## Overview

All external API calls in the blog automation system use a **progressive retry strategy** with increasing delays to handle temporary failures gracefully.

## Retry Strategy

### Progressive Delays

When an API call fails, the system retries with the following delays:

| Attempt | Wait Time | Notes |
|---------|-----------|-------|
| **1st attempt** | Immediate | Initial try |
| **2nd attempt** | 1 minute | First retry after 60 seconds |
| **3rd attempt** | 5 minutes | Second retry after 300 seconds |
| **4th attempt** | 10 minutes | Final retry after 600 seconds |

**Total maximum wait time:** ~16 minutes (1 + 5 + 10 minutes)

### Why Progressive Delays?

1. **Temporary Issues**: Short delays catch temporary glitches
2. **Overload Recovery**: Longer delays allow overloaded services to recover
3. **Rate Limiting**: Respects API rate limits and quota resets
4. **User Experience**: Avoids immediate failure on temporary issues

## Services Using This Policy

### 1. Gemini AI Service
- **Used for**: Topic generation, blog content creation
- **Retries**: 3 attempts (1min, 5min, 10min delays)
- **Exceptions**: Authentication errors (no retry)

**Common failures:**
- 503 Service Unavailable (overloaded)
- Network timeouts
- Rate limiting

### 2. Hashnode API Service
- **Used for**: Publishing blog posts
- **Retries**: 3 attempts (1min, 5min, 10min delays)
- **Exceptions**:
  - 401 Authentication errors (no retry)
  - 429 Rate limiting (uses Retry-After header)

**Common failures:**
- 400 Bad Request (GraphQL errors)
- 500 Internal Server Error
- Network timeouts

### 3. NewsData.io Service
- **Used for**: Fetching trending news
- **Retries**: Uses default strategy (if implemented)
- **Note**: News fetching failures are non-critical

## Error Handling

### Errors That Don't Retry

Some errors indicate permanent failures and won't be retried:

1. **Authentication Errors (401)**
   - Invalid API keys
   - Expired tokens
   - **Action**: Check your `.env` file

2. **Invalid Credentials**
   - Wrong publication ID
   - Invalid parameters
   - **Action**: Verify configuration

### Errors That Retry

These errors trigger the progressive retry strategy:

1. **Service Overload (503)**
   - "Model is overloaded"
   - Server temporarily unavailable
   - **Handled**: Automatically retries with delays

2. **Network Issues**
   - Connection timeouts
   - DNS failures
   - **Handled**: Automatically retries

3. **Rate Limiting (429)**
   - API quota exceeded
   - **Handled**: Respects Retry-After header or uses progressive delays

4. **Temporary Server Errors (500, 502, 504)**
   - Internal server errors
   - Bad gateway
   - Gateway timeout
   - **Handled**: Automatically retries

## Example Retry Flow

### Successful Retry Example

```
2025-12-17 23:59:13 - INFO - Publishing post to Hashnode: Blog Title
2025-12-17 23:59:15 - WARNING - API call failed (attempt 1/3): 503 Service Unavailable
2025-12-17 23:59:15 - INFO - ⏳ Waiting 1 minute(s) before retry...
[waits 60 seconds]
2025-12-18 00:00:15 - WARNING - API call failed (attempt 2/3): 503 Service Unavailable
2025-12-18 00:00:15 - INFO - ⏳ Waiting 5 minute(s) before retry...
[waits 300 seconds]
2025-12-18 00:05:15 - INFO - ✓ Successfully published post
```

### Failed After All Retries

```
2025-12-17 23:59:13 - INFO - Publishing post to Hashnode: Blog Title
2025-12-17 23:59:15 - WARNING - API call failed (attempt 1/3): 400 Bad Request
2025-12-17 23:59:15 - INFO - ⏳ Waiting 1 minute(s) before retry...
[waits 60 seconds]
2025-12-18 00:00:15 - WARNING - API call failed (attempt 2/3): 400 Bad Request
2025-12-18 00:00:15 - INFO - ⏳ Waiting 5 minute(s) before retry...
[waits 300 seconds]
2025-12-18 00:05:15 - WARNING - API call failed (attempt 3/3): 400 Bad Request
2025-12-18 00:05:15 - ERROR - All retry attempts exhausted
2025-12-18 00:05:15 - ERROR - ❌ FAILED: Could not publish blog
```

Exit code: 6 (Publishing failed)

## Monitoring Retries

### Log Messages

Watch for these log indicators:

```bash
# Retry in progress
⏳ Waiting 1 minute(s) before retry...
⏳ Waiting 5 minute(s) before retry...
⏳ Waiting 10 minute(s) before retry...

# All retries exhausted
All retry attempts exhausted
```

### Checking Logs

```bash
# View real-time logs
make logs

# Search for retry patterns
grep "Waiting.*minute" logs/app.log

# Count retry attempts
grep "API call failed" logs/app.log | wc -l
```

## Configuration

The retry policy is configured in [config/settings.py](config/settings.py):

```python
# API Configuration
API_MAX_RETRIES = 3  # Number of retry attempts
API_TIMEOUT = 60     # Request timeout in seconds
```

**Note:** Retry delays (1min, 5min, 10min) are hardcoded in the service implementations.

## Best Practices

### For Users

1. **Be Patient**: The script may run for 15+ minutes if retries are needed
2. **Don't Interrupt**: Let retries complete naturally
3. **Check Logs**: Monitor `logs/app.log` for retry status
4. **Verify APIs**: Ensure API keys are valid before running

### For Cron Jobs

```bash
# Allow enough time for retries (30 minutes recommended)
0 9 * * * cd /path && timeout 30m make run-safe >> /var/log/blog.log 2>&1
```

### For Automation

```bash
# Handle long-running retries
make run
EXIT_CODE=$?

if [ $EXIT_CODE -eq 5 ]; then
    echo "Gemini API failed after all retries"
    # Send notification
elif [ $EXIT_CODE -eq 6 ]; then
    echo "Hashnode publishing failed after all retries"
    # Send notification
fi
```

## Common Scenarios

### Scenario 1: Gemini API Overloaded (503)

**Timeline:**
- 00:00 - First attempt fails
- 00:01 - Retry after 1 minute (fails)
- 00:06 - Retry after 5 minutes (fails)
- 00:16 - Retry after 10 minutes (succeeds!)

**Total time:** ~16 minutes

### Scenario 2: Invalid Hashnode Token (401)

**Timeline:**
- 00:00 - First attempt fails with 401
- 00:00 - Immediately exits (no retry)

**Total time:** Instant failure

**Action:** Fix your `HASHNODE_API_TOKEN` in `.env`

### Scenario 3: Network Glitch

**Timeline:**
- 00:00 - First attempt times out
- 00:01 - Retry after 1 minute (succeeds!)

**Total time:** ~1 minute

## Troubleshooting

### "All retry attempts exhausted"

**What it means:** API failed 3 times despite retries

**Common causes:**
1. Invalid API credentials → Check `.env`
2. Wrong publication ID → Verify `HASHNODE_PUBLICATION_ID`
3. Malformed data → Check blog content/tags
4. Service outage → Check API status pages

**Actions:**
```bash
# Check credentials
cat .env | grep -E "(GEMINI|HASHNODE)"

# Verify Hashnode setup
python3 -c "from app.services.hashnode_service import HashnodeService; \
    hs = HashnodeService(); \
    print(hs.get_publication_info())"

# Review error logs
make logs
```

### "Script taking too long"

**What it means:** Retries are in progress

**Expected duration:**
- No retries: 3-5 minutes
- With 1 retry: 4-6 minutes
- With 2 retries: 9-11 minutes
- With 3 retries: 14-16 minutes

**Actions:**
- Wait patiently
- Check `logs/app.log` for retry status
- Don't interrupt (Ctrl+C)

### Rate Limiting (429)

**What it means:** API quota exceeded

**Handling:**
- Respects `Retry-After` header if provided
- Falls back to progressive delays
- Eventually gives up after 3 attempts

**Actions:**
- Wait for quota reset (usually hourly/daily)
- Upgrade API plan if needed
- Reduce automation frequency

## API Status Pages

Check these if experiencing persistent failures:

- **Gemini AI**: https://ai.google.dev/
- **Hashnode**: https://hashnode.com/ (check @HashnodeHQ on Twitter)
- **NewsData.io**: https://newsdata.io/

## Summary

- ✅ **Progressive delays**: 1min → 5min → 10min
- ✅ **Smart retry**: Only retries temporary failures
- ✅ **Clear logging**: See exactly what's happening
- ✅ **User-friendly**: Automatic recovery from transient issues
- ✅ **Respects limits**: Handles rate limiting gracefully

The retry policy ensures your blog automation is **resilient** and **reliable** without manual intervention.
