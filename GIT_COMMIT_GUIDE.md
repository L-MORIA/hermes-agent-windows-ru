# Git Commit Guide - Russian Translation & Windows Support

## Summary of Changes

This commit adds Russian translation to Hermes Agent Web UI and fixes critical Windows compatibility issues for local LLM servers (LM Studio, Ollama).

## Files Changed

### Core Fixes (3 files)
```
gateway/status.py                    - Windows process detection fix
run_agent.py                         - No-auth OpenAI client for local servers
hermes_cli/runtime_provider.py       - Empty API key for localhost
```

### Web UI - Russian Translation (6 files)
```
web/src/i18n/ru.ts                   - NEW: Complete Russian translation
web/src/i18n/types.ts                - Added 'ru' locale and chat section
web/src/i18n/context.tsx             - Registered Russian locale
web/src/i18n/en.ts                   - Added chat section structure
web/src/i18n/zh.ts                   - Added chat section structure
web/src/components/LanguageSwitcher.tsx - Added RU to cycle
web/src/pages/ChatPage.tsx           - Replaced hardcoded strings with t.chat.*
```

### Built Web UI (3 files)
```
hermes_cli/web_dist/index.html       - Updated with new build
hermes_cli/web_dist/assets/index-*.css - Updated styles
hermes_cli/web_dist/assets/index-*.js  - Updated with Russian locale
```

### Documentation (2 files)
```
RUSSIAN_TRANSLATION.md               - NEW: Full documentation
CHANGELOG.md                         - NEW: Detailed changelog
```

## Git Commands

### 1. Stage All Changes
```bash
cd C:\Openecode\new\hermes-agent

# Stage modified files
git add gateway/status.py
git add hermes_cli/runtime_provider.py
git add run_agent.py
git add web/src/i18n/ru.ts
git add web/src/i18n/types.ts
git add web/src/i18n/context.tsx
git add web/src/i18n/en.ts
git add web/src/i18n/zh.ts
git add web/src/components/LanguageSwitcher.tsx
git add web/src/pages/ChatPage.tsx

# Stage built web UI
git add hermes_cli/web_dist/

# Stage documentation
git add RUSSIAN_TRANSLATION.md
git add CHANGELOG.md
```

### 2. Commit with Detailed Message
```bash
git commit -m "feat: Add Russian translation and Windows LM Studio support

🌐 Russian Translation:
- Complete Russian localization of Web UI
- Added ru.ts with full translation
- Language switcher: EN → RU → ZH
- Replaced hardcoded Chinese strings with i18n keys

🔧 Windows Compatibility:
- Fixed gateway process detection on Windows
- Added Windows path support in status.py
- Process cmdline now works with wmic/psutil

🤖 Local LLM Support (No Auth):
- Custom OpenAI client for localhost endpoints
- Bypasses auth validation for LM Studio/Ollama
- Empty api_key prevents Authorization header
- Auto-detects localhost/127.0.0.1

🐛 Bug Fixes:
- Fixed _read_process_cmdline() Linux-only implementation
- Fixed _looks_like_gateway_process() Windows paths
- Fixed runtime_provider api_key for custom providers
- Fixed AIAgent api_key='' handling

✅ Tested:
- Windows 11 + LM Studio + qwen/qwen3.5-9b
- Gateway detection works correctly
- Chat requests succeed without auth
- Russian UI displays properly

Closes #XXX (if applicable)
"
```

### 3. Alternative: Shorter Commit Message
```bash
git commit -m "feat: Russian translation + Windows LM Studio support

- Add complete Russian localization
- Fix Windows gateway detection
- Support local LLM without authentication
- Tested with LM Studio on Windows 11
"
```

## Before Pushing

### 1. Review Changes
```bash
git status
git diff --staged
```

### 2. Check Commit
```bash
git log --oneline -1
git show HEAD
```

### 3. Create Branch (Recommended)
```bash
git checkout -b feature/russian-translation-windows-support
```

### 4. Push to Remote
```bash
# If new branch
git push -u origin feature/russian-translation-windows-support

# If main branch (not recommended without PR)
git push origin main
```

## Creating Pull Request

### PR Title
```
feat: Russian translation and Windows LM Studio support
```

### PR Description Template
```markdown
## Summary
Adds complete Russian translation to Hermes Agent Web UI and fixes critical Windows compatibility issues for local LLM servers.

## Changes
- ✅ Complete Russian localization (450+ strings)
- ✅ Windows gateway process detection fix
- ✅ Local LLM support without authentication
- ✅ Tested with LM Studio + Qwen 3.5 9B

## Testing
- [x] Windows 11 compatibility
- [x] Gateway detection works
- [x] Russian UI displays correctly
- [x] LM Studio integration works
- [x] No authentication errors

## Screenshots
(Add screenshots of Russian UI)

## Documentation
- Added RUSSIAN_TRANSLATION.md with full setup guide
- Added CHANGELOG.md with detailed changes
- Updated inline code comments

## Breaking Changes
None. Fully backward compatible.

## Related Issues
Closes #XXX (if applicable)
```

## Post-Commit Checklist

- [ ] Commit message is clear and descriptive
- [ ] All modified files are staged
- [ ] Documentation files included
- [ ] No sensitive data in commit (API keys, passwords)
- [ ] Tested locally before pushing
- [ ] Branch name follows convention
- [ ] Ready to create PR

## Notes

### Important Files Modified
1. **gateway/status.py** - Critical for Windows gateway detection
2. **run_agent.py** - Core authentication bypass for local servers
3. **web/src/i18n/ru.ts** - Complete Russian translation

### Files to Review Carefully
- Ensure no debug code left in run_agent.py
- Check that all Russian strings are properly translated
- Verify web_dist build is complete and working

### Testing Before Push
```bash
# Test gateway detection
python -m hermes_cli.main web

# Check Web UI
# Open http://localhost:9119
# Switch to Russian language
# Send test message

# Verify no errors in logs
type C:\Openecode\new\.hermes\logs\agent.log
```

## Rollback (If Needed)

```bash
# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes)
git reset --hard HEAD~1

# Restore specific file
git restore gateway/status.py
```

---

**Ready to commit!** Follow the steps above to create a clean, well-documented commit.
