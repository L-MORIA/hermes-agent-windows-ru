# Установка и устранение проблем на Windows

## 📋 Содержание
1. [Быстрый старт](#-быстрый-старт)
2. [Проблема: Gateway: False в веб-интерфейсе](#-проблема-gateway-false-в-веб-интерфейсе)
3. [Проблема: Ошибки кодировки (UnicodeEncodeError, кракозябры)](#-проблема-ошибки-кодировки-unicodeencodeerror-кракозябры)
4. [Проблема: LM Studio возвращает 401 Unauthorized](#-проблема-lm-studio-возвращает-401-unauthorized)
5. [Проблема: Missing credentials / OpenAI client error](#-проблема-missing-credentials--openai-client-error)
6. [Проблема: Модель имеет слишком маленький контекст (8K вместо 64K)](#-проблема-модель-имеет-слишком-маленький-контекст-8k-вместо-64k)
7. [Проблема: UnicodeEncodeError при запуске gateway](#-проблема-unicodeencodeerror-при-запуске-gateway)
8. [Приложение: Полный чек-лист установки](#-полный-чек-лист-установки)

---

## ✅ Быстрый старт

```powershell
# 1. Клонировать репозиторий
git clone https://github.com/L-MORIA/hermes-agent-windows-ru.git
cd hermes-agent-windows-ru

# 2. Создать виртуальное окружение
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Установить зависимости
pip install -r requirements.txt

# 4. Установить переменную окружения (ОБЯЗАТЕЛЬНО!)
[Environment]::SetEnvironmentVariable("PYTHONIOENCODING", "utf-8", "User")

# 5. Создать конфиг (если нет)
mkdir $env:USERPROFILE\.hermes -Force
```

**Файл `~/.hermes/config.yaml`:**
```yaml
model:
  base_url: http://localhost:1234/v1
  default: qwen/qwen3.5-9b
  provider: custom

platforms:
  api_server:
    enabled: true
```

**Файл `~/.hermes/.env`:**
```bash
OPENAI_API_KEY=
GATEWAY_ALLOW_ALL_USERS=true
```

**Запуск:**
```powershell
# Перезагрузить PowerShell (чтобы применилась переменная PYTHONIOENCODING)
# Затем:
cd C:\путь\к\hermes-agent-windows-ru
.\venv\Scripts\Activate.ps1
python -m hermes_cli.main web
```

**Открыть браузер:** `http://localhost:9119`

---

## 🔴 Проблема: Gateway: False в веб-интерфейсе

### Симптом
Веб-интерфейс показывает `Gateway: False`, хотя процессы Python запущены. Или: Web UI открывается, но при отправке сообщения пишет "⚠️ Агент не вернул ответ" / "⚠️ 无法连接到 Gateway API".

### Причина
Код определения gateway (`gateway/status.py`) использует Linux-специфичные пути:

```python
# БЫЛО (только Linux):
def _read_process_cmdline(pid):
    cmdline_path = Path(f"/proc/{pid}/cmdline")  # ❌ Не работает на Windows
    ...

# СТАЛО (Windows + Linux):
def _read_process_cmdline(pid):
    if _IS_WINDOWS:
        # Используем wmic или psutil
        result = subprocess.run(
            ["wmic", "process", "where", f"processid={pid}", 
             "get", "commandline", "/format:value"],
            ...
        )
    else:
        cmdline_path = Path(f"/proc/{pid}/cmdline")  # ✅ Linux
```

Также шаблоны поиска процесса не учитывали обратные слеши Windows:

```python
# БЫЛО:
patterns = ("hermes_cli.main gateway", "hermes gateway")

# СТАЛО:
patterns = (
    "hermes_cli.main gateway",
    "hermes_cli/main.py gateway",
    "hermes_cli\\main.py gateway",  # ✅ Windows
    "main.py gateway run",           # ✅ Windows
    "hermes gateway",
    "gateway/run.py",
)
```

### Решение
Файл `gateway/status.py` уже исправлен в этом репозитории. Просто используйте эту версию.

### Если проблема всё ещё возникает — пошаговый план

#### Шаг 1: Проверить и почистить залипшие файлы
При аварийном завершении остаются stale `.pid` и `.lock` файлы, которые блокируют новый запуск:

```powershell
# Убить ВСЕ процессы Python
taskkill /F /IM python.exe

# Удалить stale PID и lock файлы
Remove-Item "$env:USERPROFILE\.hermes\gateway.pid" -Force -ErrorAction SilentlyContinue
Remove-Item "$env:USERPROFILE\.hermes\gateway.lock" -Force -ErrorAction SilentlyContinue
Remove-Item "$env:USERPROFILE\.hermes\webui.pid" -Force -ErrorAction SilentlyContinue
Remove-Item "$env:USERPROFILE\.hermes\webui.lock" -Force -ErrorAction SilentlyContinue
```

#### Шаг 2: Проверить, что порты свободны
```powershell
# Проверить порт 8642 (gateway API)
try { $s = [System.Net.Sockets.TcpClient]::new(); 
       $s.ConnectAsync("127.0.0.1", 8642).Wait(1000); 
       if ($s.Connected) { Write-Host "8642 занят" } else { Write-Host "8642 свободен" };
       $s.Dispose() } catch { Write-Host "8642 свободен" }

# Проверить порт 9119 (web UI)
try { $s = [System.Net.Sockets.TcpClient]::new(); 
       $s.ConnectAsync("127.0.0.1", 9119).Wait(1000); 
       if ($s.Connected) { Write-Host "9119 занят" } else { Write-Host "9119 свободен" };
       $s.Dispose() } catch { Write-Host "9119 свободен" }
```

Если порт занят, убить процесс:
```powershell
netstat -ano | Select-String "127.0.0.1:8642"  # или :9119
Stop-Process -Id <PID> -Force
```

#### Шаг 3: Установить PYTHONIOENCODING
Открой **НОВОЕ** окно PowerShell и выполни:

```powershell
# Обязательно для новой сессии (кодировка UTF-8)
[Environment]::SetEnvironmentVariable("PYTHONIOENCODING", "utf-8", "User")
# ИЛИ для текущей сессии:
$env:PYTHONIOENCODING = "utf-8"
```

#### Шаг 4: Проверить config.yaml
```yaml
model:
  provider: custom
  base_url: http://localhost:1234/v1   # или твой IP
  default: <имя-модели>
  # api_key: ''   ← ДОЛЖЕН быть пустым или отсутствовать

platforms:
  api_server:
    enabled: true   # ← обязательно!

# Не забудь также:
model:
  api_key: null    # ← null, а не пустая строка
```

#### Шаг 5: Проверить .env
**Файл `~/.hermes/.env`:**
```bash
OPENAI_API_KEY=           # ← пустое значение
GATEWAY_ALLOW_ALL_USERS=true
```

Без `GATEWAY_ALLOW_ALL_USERS=true` gateway отвечает 403 на все запросы.

#### Шаг 6: Запустить Web UI
```powershell
cd C:\путь\к\hermes-agent-windows-ru
$env:PYTHONIOENCODING = "utf-8"
.\venv\Scripts\python -m hermes_cli.main web
```

#### Шаг 7: Проверить в браузере
1. Открой `http://localhost:9119`
2. Жди ~10-15 секунд (gateway стартует в фоне)
3. Статус Gateway должен смениться на "Запущен"
4. Отправь сообщение

### Диагностика проблем
Если не работает, проверь:

```powershell
# 1. Логи
Get-Content "$env:USERPROFILE\.hermes\logs\agent.log" -Tail 20
Get-Content "$env:USERPROFILE\.hermes\logs\errors.log" -Tail 5

# 2. Gateway API
Invoke-WebRequest -Uri "http://127.0.0.1:8642/health" -UseBasicParsing

# 3. Web UI
Invoke-WebRequest -Uri "http://127.0.0.1:9119" -UseBasicParsing

# 4. LM Studio
Invoke-RestMethod -Uri "http://localhost:1234/v1/models" -Method Get
```

### Полный сброс (если всё сломалось)
```powershell
# Атомарный сброс — одной командой:
taskkill /F /IM python.exe 2>$null; Start-Sleep 2; `
Remove-Item "$env:USERPROFILE\.hermes\gateway.pid" -Force -ErrorAction SilentlyContinue; `
Remove-Item "$env:USERPROFILE\.hermes\gateway.lock" -Force -ErrorAction SilentlyContinue; `
Remove-Item "$env:USERPROFILE\.hermes\webui.pid" -Force -ErrorAction SilentlyContinue; `
Remove-Item "$env:USERPROFILE\.hermes\webui.lock" -Force -ErrorAction SilentlyContinue; `
$env:PYTHONIOENCODING="utf-8"; `
python -m hermes_cli.main web
```

---

## 🔴 Проблема: Ошибки кодировки (UnicodeEncodeError, кракозябры)

### Симптом
```
UnicodeEncodeError: 'charmap' codec can't encode character '\u250f' 
in position 24: character maps to <undefined>
```
Или в консоли отображаются иероглифы/знаки вопросов вместо русского текста.

### Причина
Консоль Windows по умолчанию использует кодировку CP1251 (кириллица) или CP437. 
Hermes Agent использует символы псевдографики (╭─ ─╮ ┊ ◆) и эмодзи (🤖, 🎉), 
которые не входят в эти кодировки.

**Подробнее:**
- `sys.stdout.encoding` = `cp1251` (русская Windows)
- CP1251 содержит русские буквы, но НЕ содержит символы: `╭ ─ ╮ │ ┊ ◆ 🎉 🤖`
- При попытке вывести такие символы Python выбрасывает `UnicodeEncodeError`

### Решение

#### Шаг 1: Установить переменную окружения (ОБЯЗАТЕЛЬНО!)
```powershell
[Environment]::SetEnvironmentVariable("PYTHONIOENCODING", "utf-8", "User")
```

**Почему это работает:**
- `PYTHONIOENCODING=utf-8` заставляет Python использовать UTF-8 для `stdout`/`stderr`
- UTF-8 содержит ВСЕ символы Юникода, включая псевдографику и эмодзи

**Важно:** Переменная применяется только для НОВЫХ процессов PowerShell.
```powershell
# Проверить, что переменная установлена:
[Environment]::GetEnvironmentVariable("PYTHONIOENCODING", "User")

# Если да — нужно открыть НОВОЕ окно PowerShell
```

#### Шаг 2: Открыть новое окно PowerShell
```powershell
# Старое окно: PYTHONIOENCODING ещё не активна
# Новое окно: PYTHONIOENCODING уже активна
Start-Process powershell.exe
```

#### Шаг 3: Запустить Hermes в новом окне
```powershell
cd C:\путь\к\hermes-agent-windows-ru
.\venv\Scripts\Activate.ps1
python -m hermes_cli.main web
```

### Альтернативное решение (если не хотите менять глобальную переменную)
```powershell
# Установить переменную ТОЛЬКО для текущей сессии
$env:PYTHONIOENCODING = "utf-8"
python -m hermes_cli.main web
```

### Проверка кодировки
```powershell
# В новом окне PowerShell выполнить:
python -c "import sys; print(f'Encoding: {sys.stdout.encoding}')"
# Должно вывести: Encoding: utf-8
```

---

## 🔴 Проблема: UnicodeDecodeError в subprocess _readerthread

### Симптом
```
Exception in thread Thread-1 (_readerthread):
Traceback (most recent call last):
  File "C:\Python314\Lib\threading.py", line 1082, in _bootstrap_inner
    ...
  File "C:\Python314\Lib\subprocess.py", line 1613, in _readerthread
    buffer.append(fh.read())
UnicodeDecodeError: 'utf-8' codec can't decode byte 0x88 in position 0: invalid start byte
```

### Причина
Gateway запускает дочерние процессы (например, cron, скрипты). 
Если дочерний процесс выводит байты в кодировке CP1251 (русская Windows),
а Python ожидает UTF-8 (из-за `PYTHONIOENCODING=utf-8`), возникает ошибка декодирования.

### Решение
Ошибка **не критическая** — gateway продолжает работать. Но если она мешает:

#### Вариант 1: Игнорировать (рекомендуется)
Ошибка выводится однократно при запуске и не влияет на работу gateway.

#### Вариант 2: Исправить в subprocess.py (временное решение)
Если ошибка повторяется и вызывает остановку, замени в вызовах `subprocess.run`:
```python
# Было:
capture_output=True, text=True

# Стало:
capture_output=True, text=True, encoding="cp1251", errors="replace"
```

**Файл:** `hermes_cli/gateway.py` (строка ~310, функция `stop_profile_gateway`)

```python
# Было:
os.kill(pid, signal.SIGTERM)  # ❌ Не работает на Windows

# Стало (уже исправлено в этом репозитории):
if _IS_WINDOWS:
    subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True, encoding="cp1251", errors="replace")
else:
    os.kill(pid, signal.SIGTERM)
```

#### Вариант 3: Не использовать `PYTHONIOENCODING=utf-8`
Если кодировка UTF-8 не принципиальна, удали переменную:
```powershell
[Environment]::SetEnvironmentVariable("PYTHONIOENCODING", $null, "User")
```
Но тогда может не работать псевдографика (символы ╭ ─ ╮).

---

## 🔴 Проблема: LM Studio возвращает 401 Unauthorized

### Симптом
```
Non-retryable client error: Error code: 401 - 
{'error': {'message': 'Missing Authentication header', 'code': 401}}
```

### Причина
LM Studio (после обновления) отклоняет запросы с заголовком `Authorization: Bearer <любой_ключ>`.
OpenAI Python SDK автоматически добавляет этот заголовок, если передан `api_key`.

**Цепочка:** Конфиг → `runtime_provider.py` → `run_agent.py` → OpenAI SDK → LM Studio

```python
# OpenAI SDK (venv\Lib\site-packages\openai\_client.py):
def _bearer_auth(self) -> dict[str, str]:
    api_key = self.api_key
    if not api_key:      # ← если api_key пустой
        return {}         # ← Authorization НЕ добавляется
    return {"Authorization": f"Bearer {api_key}"}  # ← 401!
```

### Решение

#### Шаг 1: Убрать `api_key` из конфига
**Файл `~/.hermes/config.yaml`:** Убедитесь, что нет `api_key` в секции `model`.
```yaml
model:
  provider: custom        # ← обязательно 'custom', не 'openrouter'
  base_url: http://localhost:1234/v1
  default: qwen/qwen3.5-9b
  # api_key: lm-studio    ← НЕ ДОЛЖНО БЫТЬ!
```

#### Шаг 2: Очистить OPENAI_API_KEY в .env
**Файл `~/.hermes/.env`:** Убедитесь, что `OPENAI_API_KEY` пустой.
```bash
OPENAI_API_KEY=           # ← пустое значение
```

#### Шаг 3: Использовать provider: custom
При `provider: custom` код `runtime_provider.py` устанавливает `api_key = ""`:
```python
# hermes_cli/runtime_provider.py (строка 503-504):
if effective_provider == "custom" and not api_key and not _is_openrouter_url:
    api_key = ""  # ← пустой ключ вместо "no-key-required"
```

#### Шаг 4: Перезапустить Hermes
```powershell
taskkill /F /IM python.exe
python -m hermes_cli.main web
```

### Как это работает (технически)

В `run_agent.py` добавлен класс `_NoAuthOpenAI`:

```python
class _NoAuthOpenAI(OpenAI):
    """OpenAI client для локальных серверов без аутентификации."""
    def _validate_headers(self, headers, custom_headers):
        pass  # ← пропускаем проверку авторизации
```

Условие активации:
```python
is_local = any(h in base_url for h in ("localhost", "127.0.0.1", "0.0.0.0"))
needs_no_auth = self.provider == "custom" and is_local and not api_key
```

### Проверка
```powershell
# Прямой тест LM Studio (без авторизации):
$body = '{"messages":[{"role":"user","content":"привет"}]}' | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:1234/v1/chat/completions" `
    -Method Post -Body $body -ContentType "application/json"
# Должен вернуть ответ от модели
```

---

## 🔴 Проблема: Missing credentials / OpenAI client error

### Симптом
```
Failed to initialize OpenAI client: Missing credentials. 
Please pass an api_key or set the OPENAI_API_KEY environment variable.
```

### Причина
OpenAI SDK версии 2.30.0 требует непустой `api_key`. 
Если передать `api_key=""`, SDK выбрасывает ошибку:

```python
# openai/_client.py строка 187-196:
if _enforce_credentials and not self.api_key and ... :
    raise OpenAIError("Missing credentials...")
```

### Решение
Используется комбинация:
1. `api_key=""` (пустая строка, а не None)
2. `_enforce_credentials=False` (отключает проверку при инициализации)
3. Кастомный класс `_NoAuthOpenAI` с переопределённым `_validate_headers`

Всё это уже реализовано в `run_agent.py` и активируется автоматически при:
- `provider: custom` в конфиге
- `base_url` указывает на localhost (127.0.0.1, localhost, 0.0.0.0)
- `api_key` пустой или отсутствует

---

## 🔴 Проблема: Модель имеет слишком маленький контекст (8K вместо 64K)

### Симптом
```
ValueError: Model <name> has a context window of 8,192 tokens, 
which is below the minimum 64,000 required by Hermes Agent.
```

### Причина
Hermes Agent требует модель с контекстом **не менее 64K токенов**.
Многие локальные модели имеют контекст всего 8K (например, Gemma 4).

### Решение

#### Вариант 1: Использовать модель с большим контекстом
Рекомендуемые модели для LM Studio:
| Модель | Контекст | Размер |
|--------|----------|--------|
| Qwen 3.5 9B | 128K | ~5.5 GB |
| Qwen 3.5 14B | 128K | ~8.5 GB |
| Qwen 3 Code 30B | 128K | ~18 GB |
| Llama 3.1 8B | 128K | ~4.5 GB |
| Mistral 7B v0.3 | 32K ❌ | ~4 GB |
| Qwen 2.5 7B | 32K ❌ | ~4 GB |

**Проверка в LM Studio:**
```
LM Studio → Select model → Ищите модели с надписью "128K" 
или проверяйте описание модели
```

#### Вариант 2: Переопределить context_length в конфиге (не рекомендуется)
```yaml
model:
  base_url: http://localhost:1234/v1
  default: qwen/qwen3.5-9b
  provider: custom
  context_length: 65000  # ← принудительно
```

**Важно:** Это может привести к ошибкам, если модель реально не поддерживает 
такой контекст (потеря качества, сбои генерации).

---

## 🔴 Проблема: UnicodeEncodeError при запуске gateway

### Симптом
```
UnicodeEncodeError: 'charmap' codec can't encode characters
в позиции 24: character maps to <undefined>
```
Ошибка возникает при выводе логов gateway в консоль.

### Причина
Gateway использует символы псевдографики в логах:
```
╭──────────────────────────────────────────╮
│  Gateway running with 1 platform(s)      │
╰──────────────────────────────────────────╯
```
Консоль Windows (CP1251/CP437) не содержит эти символы.

### Полное решение

#### 1. Установить PYTHONIOENCODING (обязательно)
```powershell
[Environment]::SetEnvironmentVariable("PYTHONIOENCODING", "utf-8", "User")
```

#### 2. Открыть НОВЫЙ PowerShell
```powershell
Start-Process powershell.exe
```

#### 3. Проверить кодировку
```powershell
python -c "import sys; print(sys.stdout.encoding)"
# → utf-8
```

#### 4. Запустить
```powershell
cd C:\hermes-agent-windows-ru
.\venv\Scripts\Activate.ps1
python -m hermes_cli.main web
```

### Проверка после запуска
```powershell
# В браузере открыть http://localhost:9119
# Откроется русский интерфейс
# Gateway должен показывать "Запущен" (Running)
# Отправить сообщение — модель должна ответить
```

---

## 📋 Полный чек-лист установки

### Перед установкой
- [ ] Установлен Python 3.10+
- [ ] Установлен Git
- [ ] Установлен Node.js 20+ (для сборки Web UI)
- [ ] Установлен LM Studio (последняя версия)
- [ ] Скачана модель с контекстом 64K+ (например, qwen/qwen3.5-9b)

### Установка
```powershell
# 1. Клонировать
git clone https://github.com/L-MORIA/hermes-agent-windows-ru.git
cd hermes-agent-windows-ru

# 2. Виртуальное окружение
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Зависимости Python
pip install -r requirements.txt

# 4. Переменная окружения (ОБЯЗАТЕЛЬНО — новое окно!)
[Environment]::SetEnvironmentVariable("PYTHONIOENCODING", "utf-8", "User")

# 5. Конфиг (~/.hermes/config.yaml):
#    provider: custom
#    model: qwen/qwen3.5-9b
#    base_url: http://localhost:1234/v1

# 6. .env файл (~/.hermes/.env):
#    OPENAI_API_KEY= (пусто)
#    GATEWAY_ALLOW_ALL_USERS=true

# 7. НОВОЕ окно PowerShell → запуск
python -m hermes_cli.main web
```

### После запуска
- [ ] `http://localhost:9119` открывается
- [ ] Интерфейс на русском
- [ ] Gateway: True (PID: XXXXX)
- [ ] LM Studio отвечает на запросы
- [ ] Чат работает

### Если что-то пошло не так
```powershell
# Посмотреть логи
Get-Content "$env:USERPROFILE\.hermes\logs\agent.log" -Tail 20
Get-Content "$env:USERPROFILE\.hermes\logs\errors.log" -Tail 5

# Перезапустить с нуля
taskkill /F /IM python.exe
python -m hermes_cli.main web
```

---

## 🆘 Поддержка

Если проблемы остаются:
1. Проверьте `agent.log` на ошибки
2. Убедитесь, что LM Studio запущен и модель загружена
3. Проверьте `http://localhost:1234/v1/models` в браузере
4. Создайте Issue в репозитории: 
   https://github.com/L-MORIA/hermes-agent-windows-ru/issues

**Формат Issue:**
```markdown
**Проблема:** (кратко)
**Windows версия:** 
**Python версия:** 
**LM Studio версия:** 
**Модель:** 
**Лог ошибки:** (из agent.log)
**Конфиг:** (config.yaml без чувствительных данных)
```
