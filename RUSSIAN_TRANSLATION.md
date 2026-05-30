# Russian Translation & LM Studio Support for Hermes Agent

This fork adds full Russian language support to the Hermes Agent Web UI and fixes critical bugs for running on Windows with local LLM servers like LM Studio and Ollama.

## Features

### 🌐 Russian Translation
- Complete Russian localization of the Web UI
- All chat interface elements translated
- Language switcher: English → Russian → Chinese
- Native Russian error messages and notifications

### 🔧 Windows Compatibility Fixes
- Fixed gateway process detection on Windows
- Added support for Windows-style paths in process monitoring
- Resolved `_read_process_cmdline()` Linux-only implementation

### 🤖 Local LLM Support (LM Studio, Ollama)
- No authentication required for localhost endpoints
- Custom OpenAI client that bypasses auth validation
- Works with any OpenAI-compatible local server
- Tested with LM Studio and qwen/qwen3.5-9b model

## Installation

### Prerequisites
- Windows 11 (tested) or Windows 10
- Python 3.11+
- LM Studio or Ollama (for local LLM)
- Node.js 20+ (for building Web UI)

### Setup

1. Clone this repository:
```bash
git clone https://github.com/YOUR_USERNAME/hermes-agent-windows.git
cd hermes-agent-windows
```

2. Install Python dependencies:
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

3. Build the Web UI:
```bash
cd web
npm install
npm run build
```

4. Copy built files to the CLI:
```bash
xcopy /E /I /Y dist ..\hermes_cli\web_dist
cd ..
```

5. Configure for LM Studio:

Edit `~/.hermes/config.yaml`:
```yaml
model:
  base_url: http://localhost:1234/v1
  default: qwen/qwen3.5-9b
  provider: custom

platforms:
  api_server:
    enabled: true
```

Edit `~/.hermes/.env`:
```bash
OPENAI_API_KEY=
GATEWAY_ALLOW_ALL_USERS=true
```

6. Set environment variables (PowerShell):
```powershell
[Environment]::SetEnvironmentVariable("PYTHONIOENCODING", "utf-8", "User")
```

7. Start LM Studio and load your model (e.g., qwen/qwen3.5-9b)

8. Run Hermes Web UI:
```bash
python -m hermes_cli.main web
```

9. Open browser: `http://localhost:9119`

## Configuration

### LM Studio Setup
1. Download and install [LM Studio](https://lmstudio.ai/)
2. Download a model with 64K+ context (e.g., Qwen 3.5 9B)
3. Start the local server on port 1234
4. Ensure no API key is configured in LM Studio settings

### Supported Models
Any OpenAI-compatible model with 64K+ context window:
- Qwen 3.5 (9B, 14B, 32B)
- Llama 3.1/3.2
- Mistral models
- DeepSeek models

## Technical Details

### Changes Made

#### 1. Russian Translation (`web/src/i18n/ru.ts`)
- Complete translation of all UI strings
- Chat interface, settings, errors, notifications
- Consistent terminology across the interface

#### 2. Gateway Detection Fix (`gateway/status.py`)
**Problem:** `_read_process_cmdline()` used `/proc/{pid}/cmdline` (Linux-only)

**Solution:**
- Added Windows support using `wmic` or `psutil`
- Updated `_looks_like_gateway_process()` patterns for Windows paths
- Added `hermes_cli\main.py gateway` pattern matching

#### 3. Local LLM Authentication (`run_agent.py`)
**Problem:** OpenAI SDK requires non-empty `api_key`, but LM Studio rejects all Bearer tokens

**Solution:**
- Created `_NoAuthOpenAI` subclass that overrides `_validate_headers()`
- Detects localhost endpoints automatically
- Passes `_enforce_credentials=False` to bypass SDK validation
- Empty `api_key=""` prevents Authorization header from being sent

#### 4. Runtime Provider Fix (`hermes_cli/runtime_provider.py`)
**Problem:** `api_key = "no-key-required"` was sent to LM Studio, causing 401 errors

**Solution:**
- Changed to `api_key = ""` for custom providers without credentials
- Updated `run_agent.py` condition: `if base_url and api_key is not None:`

### File Changes Summary

```
Modified files:
- gateway/status.py                    (Windows process detection)
- run_agent.py                         (No-auth OpenAI client)
- hermes_cli/runtime_provider.py       (Empty API key for local servers)
- web/src/i18n/ru.ts                   (Russian translation - NEW)
- web/src/i18n/types.ts                (Added 'ru' locale and chat section)
- web/src/i18n/context.tsx             (Registered Russian locale)
- web/src/components/LanguageSwitcher.tsx (EN → RU → ZH cycle)
- web/src/pages/ChatPage.tsx           (Replaced hardcoded Chinese strings)
```

## Troubleshooting

### Gateway shows "False" in Web UI
- Restart all Python processes: `taskkill /F /IM python.exe`
- Ensure `PYTHONIOENCODING=utf-8` is set
- Check `~/.hermes/logs/agent.log` for errors

### "Missing credentials" error
- Verify `OPENAI_API_KEY=` is empty in `~/.hermes/.env`
- Ensure `provider: custom` in config.yaml
- Check that `base_url` points to localhost

### LM Studio returns 401
- Remove any `api_key` from config.yaml model section
- Restart Hermes after config changes
- Verify LM Studio has no API key configured

### Model context too small error
- Use models with 64K+ context window
- Qwen 3.5, Llama 3.1+, Mistral 7B+ recommended
- Check model card for context length

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Test on Windows with LM Studio
4. Submit a pull request

## License

Same as original Hermes Agent project.

## Credits

- Original Hermes Agent: [Nous Research](https://github.com/NousResearch/hermes-agent)
- Windows fork maintainer: [Your Name]
- Russian translation: [Your Name]

## Support

For issues specific to this fork:
- Open an issue on GitHub
- Include `agent.log` and `config.yaml` (redact sensitive info)
- Specify Windows version and LM Studio version

For general Hermes Agent issues:
- See [upstream repository](https://github.com/NousResearch/hermes-agent)
