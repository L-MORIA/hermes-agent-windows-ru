# Changelog - Russian Translation & Windows LM Studio Support

## [0.9.0-ru.1] - 2026-05-30

### Added

#### 🌐 Russian Translation
- **Complete Russian localization** of Web UI
  - Added `web/src/i18n/ru.ts` with full translation
  - Translated all chat interface elements
  - Translated settings, errors, notifications
  - Added Russian to language switcher (EN → RU → ZH)
  
- **Updated components:**
  - `web/src/i18n/types.ts` - Added `'ru'` locale type and `chat` section
  - `web/src/i18n/context.tsx` - Registered Russian locale
  - `web/src/components/LanguageSwitcher.tsx` - Added RU to cycle
  - `web/src/pages/ChatPage.tsx` - Replaced hardcoded Chinese strings with `t.chat.*` keys

#### 🤖 Local LLM Support (No Authentication)
- **Custom OpenAI client for local servers** (`run_agent.py`)
  - Created `_NoAuthOpenAI` class that extends `OpenAI`
  - Overrides `_validate_headers()` to skip auth validation
  - Auto-detects localhost endpoints (localhost, 127.0.0.1, 0.0.0.0)
  - Passes `_enforce_credentials=False` to OpenAI SDK
  - Uses empty `api_key=""` to prevent Authorization header

- **Benefits:**
  - Works with LM Studio, Ollama, vLLM, llama.cpp
  - No API key required for local servers
  - No Bearer token sent in requests
  - Seamless integration with existing code

### Fixed

#### 🐛 Windows Gateway Detection
- **Fixed `_read_process_cmdline()` in `gateway/status.py`**
  - **Problem:** Used `/proc/{pid}/cmdline` (Linux-only), always returned `None` on Windows
  - **Solution:** Added Windows support using `wmic` or `psutil`
  - Falls back to `wmic process where "processid=<pid>" get commandline`
  - Maintains Linux compatibility

- **Fixed `_looks_like_gateway_process()` in `gateway/status.py`**
  - Added Windows path patterns: `hermes_cli\main.py gateway`
  - Added generic pattern: `main.py gateway run`
  - Now matches both forward and backslashes

- **Fixed `_record_looks_like_gateway()` in `gateway/status.py`**
  - Added same Windows path patterns
  - Properly validates PID file metadata on Windows

- **Impact:** Gateway status now correctly shows "True" on Windows

#### 🔑 Authentication for Local LLM Servers
- **Fixed `_resolve_openrouter_runtime()` in `hermes_cli/runtime_provider.py`**
  - Changed `api_key = "no-key-required"` to `api_key = ""`
  - Empty string prevents OpenAI SDK from sending Authorization header
  - LM Studio no longer rejects requests with 401

- **Fixed `AIAgent.__init__()` in `run_agent.py`**
  - Changed condition from `if api_key and base_url:` to `if base_url and api_key is not None:`
  - Now accepts `api_key=""` (empty string) as valid
  - Distinguishes between `None` (not provided) and `""` (explicitly empty)

### Changed

#### ⚙️ Configuration
- **Recommended config for LM Studio:**
  ```yaml
  model:
    provider: custom  # Changed from 'openrouter'
    base_url: http://localhost:1234/v1
    default: qwen/qwen3.5-9b
    # No api_key needed
  ```

- **Environment variables:**
  - `OPENAI_API_KEY=` (empty) in `~/.hermes/.env`
  - `PYTHONIOENCODING=utf-8` (required for Windows)
  - `GATEWAY_ALLOW_ALL_USERS=true` (for unauthenticated health checks)

### Technical Details

#### Modified Files
```
gateway/status.py                          (+30 lines)
  - _read_process_cmdline(): Added Windows support
  - _looks_like_gateway_process(): Added Windows patterns
  - _record_looks_like_gateway(): Added Windows patterns

run_agent.py                               (+28 lines)
  - _create_openai_client(): Added _NoAuthOpenAI class
  - __init__(): Changed api_key condition

hermes_cli/runtime_provider.py             (+1 line)
  - _resolve_openrouter_runtime(): api_key = "" instead of "no-key-required"

web/src/i18n/ru.ts                         (+450 lines, NEW FILE)
  - Complete Russian translation

web/src/i18n/types.ts                      (+2 lines)
  - Added 'ru' locale and chat section

web/src/i18n/context.tsx                   (+15 lines)
  - Registered Russian locale

web/src/components/LanguageSwitcher.tsx    (+1 line)
  - Added RU to language cycle

web/src/pages/ChatPage.tsx                 (~50 changes)
  - Replaced hardcoded Chinese strings with t.chat.*
```

### Testing

#### Tested Configurations
- **OS:** Windows 11 (build 26100)
- **Python:** 3.11.15
- **LM Studio:** Latest version (May 2026)
- **Models:** 
  - qwen/qwen3.5-9b (128K context) ✅
  - google/gemma-4-e4b (8K context) ❌ (too small)

#### Test Results
- ✅ Gateway detection works on Windows
- ✅ Web UI shows "Gateway: True"
- ✅ Russian translation displays correctly
- ✅ Language switcher cycles EN → RU → ZH
- ✅ Chat requests work without authentication
- ✅ LM Studio responds successfully
- ✅ No Authorization header sent to localhost
- ✅ Context length properly detected (65,621 tokens)

### Known Issues

#### Limitations
- **Model requirements:** 64K+ context window required
  - Hermes Agent enforces minimum 64K context
  - Use Qwen 3.5, Llama 3.1+, or similar large-context models
  - Small models (8K context) will fail with error

- **First request latency:** 
  - Initial request may take 1-3 minutes
  - Model loading and warmup time
  - Subsequent requests are faster

- **Windows-specific:**
  - Requires `PYTHONIOENCODING=utf-8` environment variable
  - PowerShell console may show encoding issues without it

### Migration Guide

#### From Original Hermes Agent

1. **Update config.yaml:**
   ```yaml
   # Before
   model:
     provider: openrouter
     api_key: your-key
   
   # After (for LM Studio)
   model:
     provider: custom
     base_url: http://localhost:1234/v1
     default: qwen/qwen3.5-9b
   ```

2. **Update .env:**
   ```bash
   # Set to empty
   OPENAI_API_KEY=
   ```

3. **Set environment variable:**
   ```powershell
   [Environment]::SetEnvironmentVariable("PYTHONIOENCODING", "utf-8", "User")
   ```

4. **Rebuild Web UI:**
   ```bash
   cd web
   npm run build
   xcopy /E /I /Y dist ..\hermes_cli\web_dist
   ```

### Credits

- **Original Project:** Nous Research - Hermes Agent
- **Windows Fork:** [Your Name]
- **Russian Translation:** [Your Name]
- **Testing:** Windows 11 + LM Studio + Qwen 3.5 9B

### Links

- **Upstream:** https://github.com/NousResearch/hermes-agent
- **This Fork:** https://github.com/YOUR_USERNAME/hermes-agent-windows
- **Issues:** https://github.com/YOUR_USERNAME/hermes-agent-windows/issues

---

## Previous Versions

See [upstream CHANGELOG](https://github.com/NousResearch/hermes-agent/blob/main/CHANGELOG.md) for version history before this fork.
