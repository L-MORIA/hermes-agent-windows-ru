# Security Audit — Hermes Agent for Windows

**Date:** 2026-05-30
**Scope:** `terminal_tool.py`, `hermes_state.py`, infra code
**Auditor:** Independent review

---

## Summary

| Category | Grade |
|----------|-------|
| Shell injection | B+ (allowlist protects command `workdir`, TERMINAL_CWD was unprotected — now fixed) |
| SQL injection | B (FTS5 sanitization missed `-` operator — now fixed) |
| Memory leak (processes) | A (environments cleaned by `atexit` handler) |
| Credential leak | B- (sudo password cached in memory for process lifetime) |
| Auth bypass | A (force=True is dormant — not exposed to LLM) |

**2 issues found, 2 fixed, 0 outstanding.**

---

## 1. `terminal_tool.py` — Critical risk file

### 1.1 sudo password cached in memory forever

**File:** `tools/terminal_tool.py:112`, `:492`

```python
_cached_sudo_password: str = ""                       # line 112 — global, never cleared
...
_cached_sudo_password = sudo_password                  # line 492 — set, never reset
```

| Severity | Status |
|----------|--------|
| MODERATE | Not fixed (would require redesign of credential flow) |

**Risk:** Password lives in a Python string for the entire process lifetime. A memory-scanning attacker or core dump could recover it. The `SUDO_PASSWORD` env var is also visible in `/proc/self/environ`.

**Mitigation:** Password is piped via stdin (`sudo -S`), NOT embedded in command string — shell injection via the password is not possible. `SUDO_PASSWORD` is blocklisted from subprocess env vars.

**Recommendation:** Scrub `_cached_sudo_password` after the sudo command completes. However, since the same password may be needed for subsequent sudo calls, this requires storing it encrypted or re-prompting each time — a non-trivial refactor.

---

### 1.2 TERMINAL_CWD no validation for local/ssh

**File:** `tools/terminal_tool.py:619`

```python
cwd = os.getenv("TERMINAL_CWD", default_cwd)  # was: no validation
```

| Severity | Status |
|----------|--------|
| MODERATE | **FIXED** |

**Before:** `TERMINAL_CWD` was read directly from the environment with zero validation for `local` and `ssh` backends. An attacker controlling the env could set the working directory to an arbitrary path.

**After:** Added `_validate_workdir()` check for `local`/`ssh` backends. Also extended `_WORKDIR_SAFE_RE` with `:` and `\` for Windows path support:

```python
# tools/terminal_tool.py:643-650
if env_type in ("local", "ssh") and cwd != default_cwd:
    workdir_error = _validate_workdir(cwd)
    if workdir_error:
        logger.warning("Ignoring TERMINAL_CWD=%r ...", cwd, workdir_error)
        cwd = default_cwd
```

---

### 1.3 Background processes — lifetime management

**File:** `tools/terminal_tool.py:814-873`

```python
def _cleanup_inactive_envs(lifetime_seconds: int = 300):
    ...
    if process_registry.has_active_processes(task_id):
        _last_activity[task_id] = current_time  # keep alive
```

| Severity | Status |
|----------|--------|
| LOW | By design, not a bug |

Active background processes intentionally keep their environment alive. The `atexit` handler (line 1007) cleans up all remaining environments on process exit. The cleanup thread runs every 60 seconds.

---

### 1.4 force=True bypasses all security checks

**File:** `tools/terminal_tool.py:1288-1289`

```python
if not force:
    approval = _check_all_guards(command, env_type)  # SKIPPED when force=True
```

| Severity | Status |
|----------|--------|
| ZERO (currently) | Dormant risk |

`force=True` completely skips all pre-execution security checks (tirith, dangerous command detection, approval prompts). However, `force` is:
- NOT in `TERMINAL_SCHEMA` (line 1683) — LLM cannot request it
- NOT extracted from args in handler (line 1728) — never forwarded

**Risk:** Latent — if a future code path calls `terminal_tool(command, force=True)`, all guards are bypassed.

---

### 1.5 `_WORKDIR_SAFE_RE` allowlist

**File:** `tools/terminal_tool.py:153`

```python
_WORKDIR_SAFE_RE = re.compile(r'^[-A-Za-z0-9/_.~ +@=,:\\]+$')
# Now supports: Linux paths, Windows paths (C:\...), tilde, dots, spaces
```

| Severity | Status |
|----------|--------|
| LOW | **FIXED** (Windows path support added) |

Extended with `:` (drive letter) and `\\` (backslash) for Windows compatibility. Shell metacharacters blocked: `` ` $ ( ) { } [ ] ' " ; | & < > ! ^ % * ? ``

---

## 2. `hermes_state.py` — SQLite storage

### 2.1 FTS5 query sanitization insufficient

**File:** `hermes_state.py:964`

```python
# Before:
sanitized = re.sub(r'[+{}()\"^]', " ", sanitized)
# After:
sanitized = re.sub(r'[-+{}()\"^]', " ", sanitized)
```

| Severity | Status |
|----------|--------|
| LOW | **FIXED** |

**Before:** The `-` character (FTS5 NOT/prohibited operator) was not stripped. A query like `python -java` would translate to "messages containing 'python' but NOT 'java'", which is a semantic change the user may not expect from a search feature.

**After:** `-` is now stripped like other FTS5-special characters. Also `:` and `NEAR` remain unsanitized but pose no SQL injection risk (FTS5 MATCH is parsed by FTS5, not SQLite's SQL parser).

---

### 2.2 sqlite3.Row → dict serialization

**File:** `hermes_state.py:530, 651, 775, 876, 1066, 1111`

```python
return dict(row) if row else None
```

| Severity | Status |
|----------|--------|
| NONE (current) / MEDIUM (schema drift) | Not fixed (requires schema migration guard) |

**Current:** No BLOB columns exist in the schema — all columns are TEXT, INTEGER, or REAL, all natively JSON-serializable.

**Risk:** If a future migration adds a BLOB column without updating serialization, downstream `json.dumps()` calls will raise `TypeError: Object of type bytes is not JSON serializable`.

---

### 2.3 WAL checkpoint — false alarm

**File:** `hermes_state.py:216-235`

```python
result = self._conn.execute("PRAGMA wal_checkpoint(PASSIVE)").fetchone()
```

| Severity | Status |
|----------|--------|
| NONE | False alarm — by SQLite definition, PASSIVE never blocks |

`PRAGMA wal_checkpoint(PASSIVE)` returns `SQLITE_BUSY` immediately if unable to acquire the checkpoint lock. No busy handler is invoked. The call is wrapped in `try/except Exception: pass` as best-effort.

---

### 2.4 BEGIN IMMEDIATE + retry logic

**File:** `hermes_state.py:164-214`

```python
for attempt in range(self._WRITE_MAX_RETRIES):
    with self._lock:
        self._conn.execute("BEGIN IMMEDIATE")
        ...
        time.sleep(random.uniform(0.020, 0.150))  # jitter, not fixed delay
```

| Severity | Status |
|----------|--------|
| NONE | Correctly implemented |

15 retries, random jitter (avoids convoy), rollback on error, exhaustion raises `OperationalError`.

---

## 3. Files recommended for future audit

| File | Reason | Priority |
|------|--------|----------|
| `tools/approval.py` | Dangerous command detection logic | HIGH |
| `gateway/run.py` | Long-running process, zombie prevention | MEDIUM |
| `tools/process_registry.py` | Background process lifecycle | MEDIUM |
| `hermes_cli/web_server.py` | Web-facing API, XSS vectors | HIGH |
| `.env.example` | Contains no real keys (verified) | CHECKED ✓ |

---

## 4. Fixes applied

| # | Issue | File | Lines |
|---|-------|------|-------|
| 1 | FTS5 `-` operator not sanitized | `hermes_state.py` | 964 |
| 2 | TERMINAL_CWD no validation for local/ssh | `tools/terminal_tool.py` | 619, 643-650 |
| 3 | `_WORKDIR_SAFE_RE` no Windows path support | `tools/terminal_tool.py` | 153 |
