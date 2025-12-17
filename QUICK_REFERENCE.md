# Quick Reference Card

## 🚀 Quick Start

```bash
make run
```

That's it! The system will:
- ✅ Auto-install dependencies if needed
- ✅ Auto-initialize database if needed
- ✅ Retry API calls (1min, 5min, 10min)
- ✅ Complete successfully or exit with clear error

---

## 📋 Common Commands

```bash
make help          # Show all commands
make run           # Run with auto-recovery
make run-safe      # Run (never fails)
make check-db      # Check database status
make logs          # View logs
make clean         # Clean environment
```

---

## ⏱️ Expected Times

| Scenario | Time |
|----------|------|
| Normal run | 3-5 min |
| With 1 retry | 4-6 min |
| With 2 retries | 9-11 min |
| With all retries | 14-16 min |

---

## 🔢 Exit Codes

| Code | Meaning | Action |
|------|---------|--------|
| 0 | Success | ✅ Done! |
| 3 | No categories | Auto-fixed by `make run` |
| 5 | Gemini failed | Check API key |
| 6 | Publishing failed | Check Hashnode token |

---

## 🔄 Retry Timeline

```
00:00 - First attempt fails
00:01 - Retry #1 (after 1 min)
00:06 - Retry #2 (after 5 min)
00:16 - Retry #3 (after 10 min)
```

---

## 📝 Cron Job Example

```bash
# Daily at 9 AM
0 9 * * * cd /path && make run-safe >> /var/log/blog.log 2>&1
```

---

## 🐛 Troubleshooting

### Script taking long?
Retries in progress. Check: `make logs`

### Exit code 3?
Auto-recovered. No action needed.

### Exit code 5?
Check: `echo $GEMINI_API_KEY` in `.env`

### Exit code 6?
Check: `echo $HASHNODE_API_TOKEN` in `.env`

---

## 📚 Documentation

- `README.md` - Main docs
- `API_RETRY_POLICY.md` - Retry details
- `AUTO_RECOVERY.md` - Recovery features
- `EXIT_CODES.md` - Exit code reference
- `UPDATES_SUMMARY.md` - Recent changes

---

**Quick Tip:** Use `make run` for everything. It just works! 🎉
