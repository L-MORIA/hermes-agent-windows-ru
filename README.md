# hermes-agent-windows-ru

> **Russian-localized Windows fork of [Hermes Agent](https://github.com/NousResearch/hermes-agent) by [Nous Research](https://nousresearch.com)**
>
> Русскоязычная документация: [RUSSIAN_TRANSLATION.md](RUSSIAN_TRANSLATION.md)

This repository is a Windows-native adaptation of [hermes-agent-windows](https://github.com/pengchengxia75-arch/hermes-agent-windows), which is itself a Windows port of [Hermes Agent](https://github.com/NousResearch/hermes-agent). It runs natively on Windows without WSL2, adds a Russian-language Web UI, and ships several community-driven improvements on top of the donor fork.

## What this fork adds

On top of the upstream Windows adaptation, this fork includes:

- **Full Russian localization** — every Web UI string is translated; the language switcher cycles English → Russian → Chinese
- **Model selector dropdown** — switch between providers (Ollama Cloud, LM Studio, OpenRouter, Anthropic, local) and models without editing config files
- **Backend validation of model/provider pairs** — the web server rejects invalid combinations before they hit the runtime (for example, mixing an LM Studio model with an Ollama Cloud provider)
- **One-click `.bat` launchers** — `hermes-webui.bat` and `kill-hermes.bat` for Windows users who prefer double-click to typing commands
- **Russian troubleshooting and commit guides** — see [WINDOWS_TROUBLESHOOTING.md](WINDOWS_TROUBLESHOOTING.md) and [GIT_COMMIT_GUIDE.md](GIT_COMMIT_GUIDE.md)
- **Changelog** — see [CHANGELOG.md](CHANGELOG.md) for the full history of this fork's changes
- **Daily auto-sync with the Windows-donor fork** — a GitHub Actions workflow pulls new commits from `pengchengxia75-arch/hermes-agent-windows` and opens a PR for manual review

## Differences from the donor

| Feature | Upstream (NousResearch) | Donor (pengchengxia75-arch) | This fork |
|---|---|---|---|
| Runs on Windows without WSL2 | no | yes | yes |
| One-line PowerShell installer | no | yes | yes |
| Web UI (chat, settings, status, sessions, etc.) | yes | yes | yes |
| Chinese UI (`zh`) | no | yes | yes |
| **Russian UI (`ru`)** | no | no | **yes** |
| **Model selector dropdown** | no | no | **yes** |
| **Backend (provider, model) validation** | no | no | **yes** |
| **`.bat` launchers** | no | no | **yes** |
| **Russian docs** (`RUSSIAN_TRANSLATION.md`, `WINDOWS_TROUBLESHOOTING.md`, `GIT_COMMIT_GUIDE.md`) | no | no | **yes** |
| **Daily auto-sync with donor** | no | no | **yes** |
| Native PowerShell one-line install | no | yes | yes |

## Installation

Requires Windows 10 or 11. Tested on Windows 11.

Open PowerShell and run:

```powershell
$u = "https://raw.githubusercontent.com/pengchengxia75-arch/hermes-agent-windows/main/scripts/install.ps1"
$p = "$env:TEMP\hermes-install.ps1"
Invoke-WebRequest -Uri $u -OutFile $p
powershell -ExecutionPolicy Bypass -File $p
```

After installation, install the Web UI dependencies (once):

```powershell
uv pip install fastapi uvicorn --python "$env:LOCALAPPDATA\hermes\hermes-agent\venv\Scripts\python.exe"
```

## Quick start

```powershell
hermes setup      # initial configuration (first run only)
hermes            # start the command-line chat

# Web UI
hermes gateway    # in one window: start the gateway
hermes web        # in another PowerShell window: start the Web UI
                  # browser opens automatically at http://127.0.0.1:9119
```

To start both at once, use the bundled launcher:

```powershell
.\hermes-webui.bat
```

To use a different port:

```powershell
hermes web --port 8080
```

## Web UI pages

| Page | Function |
|---|---|
| **Chat** | Real-time chat with the agent, streaming output |
| **Status** | Gateway status, platform connections |
| **Sessions** | Conversation history with full-text search |
| **Analytics** | Token usage and cost estimates |
| **Logs** | Live logs with level filter |
| **Cron** | Manage and trigger scheduled tasks |
| **Skills** | Enable/disable installed skills |
| **Config** | Visual editor for all configuration |
| **Secrets** | Manage API keys and environment variables |

## Upgrading

```powershell
hermes update
```

## Credits and Acknowledgments

This project is a fork of [hermes-agent-windows](https://github.com/pengchengxia75-arch/hermes-agent-windows), which is itself a fork of [hermes-agent](https://github.com/NousResearch/hermes-agent) by [Nous Research](https://nousresearch.com).

**Built with the help of:**

- **AI coding agent:** [OpenCode](https://opencode.ai) — the CLI assistant that wrote the bulk of this code
- **LLM provider:** **Z**
- **Models used:** MiniMax M3 Free and DeepSeek V4 Flash Free

### A note from the maintainer

This project is maintained by a developer who is relatively new to web coding. Feedback, bug reports, and pull requests are very welcome.

## Disclaimer

This project is provided **as is**. **Future maintenance, updates, and support are not guaranteed.** Use this software at your own risk. The maintainer(s) are not responsible for any issues, data loss, or damages arising from the use of this code.

All trademarks belong to their respective owners. This project is an unofficial community fork and is not affiliated with Nous Research, Microsoft, or any model provider.

## License

Inherited from the upstream project: MIT. See [LICENSE](LICENSE).
