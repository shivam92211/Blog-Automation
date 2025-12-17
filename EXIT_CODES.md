# Exit Codes Reference

This document describes all exit codes used by the blog automation scripts.

## Quick Reference Table

| Exit Code | Constant Name | Meaning | Common Cause | Solution |
|-----------|---------------|---------|--------------|----------|
| `0` | `EXIT_SUCCESS` | Success | Everything worked! | No action needed |
| `1` | `EXIT_ERROR` | General error | Various errors | Check logs/app.log |
| `2` | `EXIT_USER_INTERRUPT` | User interrupted | User pressed Ctrl+C | Restart when ready |
| `3` | `EXIT_NO_CATEGORIES` | No categories found | Database not initialized | Run `make init-db` |
| `4` | `EXIT_NO_UNIQUE_TOPIC` | No unique topic | All topics were duplicates | Try again later |
| `5` | `EXIT_BLOG_GENERATION_FAILED` | Blog generation failed | Gemini API error | Check API key |
| `6` | `EXIT_PUBLISH_FAILED` | Publishing failed | Hashnode API error | Check token & publication ID |

## Detailed Exit Codes

### Exit Code 0: Success
- **What it means**: Blog was successfully generated and published to Hashnode
- **What to do**: Nothing! Check the output for the blog URL
- **Example output**:
  ```
  ✅ BLOG AUTOMATION COMPLETED SUCCESSFULLY!
  ⏱️  Total time: 245.67 seconds
  ```

### Exit Code 1: General Error
- **What it means**: An unexpected error occurred during execution
- **Common causes**:
  - Database connection issues
  - File system errors
  - Unexpected API responses
  - Configuration errors
- **What to do**:
  1. Check `logs/app.log` for detailed error messages
  2. Verify your `.env` configuration
  3. Ensure MongoDB is running
  4. Check network connectivity

### Exit Code 2: User Interrupted
- **What it means**: User pressed Ctrl+C to stop the script
- **Common causes**:
  - Intentional user cancellation
  - Script taking too long
- **What to do**:
  - This is expected behavior
  - Simply run the script again when ready
  - Check partial data in database if needed

### Exit Code 3: No Categories in Database
- **What it means**: The database has no active categories configured
- **Common causes**:
  - First time running the script
  - Database was cleared
  - All categories were deactivated
- **What to do**:
  ```bash
  # Option 1: Using Makefile
  make init-db

  # Option 2: Direct Python
  python3 init_categories.py

  # Option 3: Force mode (non-interactive)
  python3 init_categories.py --force
  ```
- **Example error message**:
  ```
  ❌ FATAL ERROR: No active categories found in database
  Please run: make init-db (or python3 init_categories.py)
  ```

### Exit Code 4: No Unique Topic Found
- **What it means**: After 5 attempts, all generated topics were too similar to existing ones
- **Common causes**:
  - Many recent blog posts in the same category
  - Category is saturated with content
  - Similarity threshold is too strict (70%)
- **What to do**:
  1. Try running the script again (Gemini may generate different topics)
  2. Wait a few hours/days before trying again
  3. Consider adding new categories
  4. Adjust `SIMILARITY_THRESHOLD` in `config/settings.py` if needed
- **Example error message**:
  ```
  ❌ Could not find unique topic after 5 attempts
  ```

### Exit Code 5: Blog Generation Failed
- **What it means**: Gemini AI failed to generate blog content
- **Common causes**:
  - Invalid or expired `GEMINI_API_KEY`
  - Gemini API rate limit reached
  - Gemini API is overloaded (503 error)
  - Network connectivity issues
- **What to do**:
  1. Verify `GEMINI_API_KEY` in `.env` file
  2. Check API key status at https://ai.google.dev/
  3. Wait a few minutes if API is overloaded
  4. Check network connectivity
  5. Review logs for specific error message
- **Example error messages**:
  ```
  ❌ FAILED: Could not generate blog content
  Failed to generate blog: 503 UNAVAILABLE - The model is overloaded
  ```

### Exit Code 6: Publishing Failed
- **What it means**: Failed to publish blog to Hashnode
- **Common causes**:
  - Invalid `HASHNODE_API_TOKEN`
  - Wrong `HASHNODE_PUBLICATION_ID`
  - Network connectivity issues
  - Hashnode API temporary issues
- **What to do**:
  1. Verify `HASHNODE_API_TOKEN` in `.env` file
  2. Verify `HASHNODE_PUBLICATION_ID` is correct
  3. Test token at https://hashnode.com/settings/developer
  4. Check network connectivity
  5. Try again in a few minutes
- **Example error message**:
  ```
  ❌ FAILED: Could not publish blog
  Failed to publish: Invalid response from Hashnode
  ```

## Using Exit Codes in Automation

### Bash Scripts

```bash
#!/bin/bash

# Run the script
python3 run_blog_automation.py
EXIT_CODE=$?

# Check the exit code
if [ $EXIT_CODE -eq 0 ]; then
    echo "Success!"
    # Send success notification, update dashboard, etc.
elif [ $EXIT_CODE -eq 3 ]; then
    echo "No categories, initializing..."
    python3 init_categories.py --force
    # Retry the script
    python3 run_blog_automation.py
elif [ $EXIT_CODE -eq 4 ]; then
    echo "No unique topics, will retry tomorrow"
    # Schedule retry for tomorrow
else
    echo "Error occurred: $EXIT_CODE"
    # Send error notification
fi
```

### Cron Jobs

```bash
# Run every day at 9 AM, log exit codes
0 9 * * * cd /path/to/Blog-Automation && make run >> /var/log/blog-automation.log 2>&1; echo "Exit code: $?" >> /var/log/blog-automation.log
```

### Python Wrapper

```python
import subprocess
import sys

def run_blog_automation():
    """Run blog automation and handle exit codes"""
    result = subprocess.run(
        ["python3", "run_blog_automation.py"],
        capture_output=True,
        text=True
    )

    exit_code = result.returncode

    if exit_code == 0:
        print("✅ Success!")
        # Send success notification
    elif exit_code == 3:
        print("⚠️  No categories, initializing...")
        subprocess.run(["python3", "init_categories.py", "--force"])
        # Retry
        return run_blog_automation()
    elif exit_code == 4:
        print("⚠️  No unique topic, will retry later")
        # Schedule retry
    else:
        print(f"❌ Error: {exit_code}")
        # Send error notification

    return exit_code

if __name__ == "__main__":
    sys.exit(run_blog_automation())
```

## Makefile Integration

The Makefile automatically handles exit codes and provides helpful messages:

```bash
make run
```

Output examples:
```
✅ Script completed successfully (exit code: 0)
❌ No categories found. Run 'make init-db' first (exit code: 3)
❌ Could not find unique topic (exit code: 4)
❌ Blog generation failed (exit code: 5)
❌ Blog publishing failed (exit code: 6)
```

## Testing Exit Codes

### Test Script Success (Exit 0)
```bash
# Run with proper setup
make run
echo $?  # Should output: 0
```

### Test No Categories (Exit 3)
```bash
# Clear categories and run
python3 -c "from app.models.database import get_sync_db; get_sync_db().categories.delete_many({})"
make run
echo $?  # Should output: 3
```

### Test User Interrupt (Exit 2)
```bash
# Run and press Ctrl+C
make run
# Press Ctrl+C
echo $?  # Should output: 2
```

## init_categories.py Exit Codes

The initialization script also uses exit codes:

| Code | Meaning |
|------|---------|
| `0` | Categories initialized successfully |
| `1` | Error during initialization |
| `2` | User cancelled initialization |

## Logging Exit Codes

All exit codes are automatically logged to `logs/app.log` for auditing and debugging.

Example log entries:
```
2025-12-17 23:36:15,552 - INFO - 🚀 BLOG AUTOMATION SCRIPT STARTED
2025-12-17 23:36:18,929 - ERROR - ❌ FATAL ERROR: No active categories found in database
# Script exits with code 3
```

## Best Practices

1. **Always check exit codes** in automation scripts
2. **Log exit codes** for historical tracking
3. **Handle specific codes** differently based on your workflow
4. **Use Makefile** for built-in exit code handling
5. **Monitor logs** along with exit codes for full context

## Related Files

- `run_blog_automation.py` - Main script with exit code definitions
- `init_categories.py` - Database initialization with exit codes
- `Makefile` - Automated commands with exit code handling
- `run_with_error_handling.sh` - Example error handling script
- `logs/app.log` - Detailed execution logs

## Questions?

If you encounter an unexpected exit code:
1. Check `logs/app.log` for detailed error messages
2. Review the troubleshooting section in README.md
3. Verify your `.env` configuration
4. Ensure all services (MongoDB, APIs) are accessible
