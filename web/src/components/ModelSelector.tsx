import { useEffect, useRef, useState } from "react";
import { ChevronDown, Loader2, Check, AlertCircle, Search, X } from "lucide-react";
import { api } from "@/lib/api";
import type { ProviderInfo, AvailableModel, ModelInfoResponse } from "@/lib/api";
import { cn } from "@/lib/utils";

interface ModelSelectorProps {
  currentModel: string;
  /** Bump to refetch model info (e.g. after a save) */
  refreshKey?: number;
  /**
   * Notified when user picks a new model.
   * @param newModel    the model id (e.g. "qwen3.6-35b-a3b-claude-4.7-opus-reasoning-distilled@q5_k_m")
   * @param newProvider the provider slug (e.g. "ollama-cloud", "custom", "openrouter")
   */
  onChange: (newModel: string, newProvider: string) => void;
  /** Disable the selector (e.g. while streaming) */
  disabled?: boolean;
}

type Status =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "ready" }
  | { kind: "error"; message: string };

/**
 * Two-level dropdown for picking model & provider.
 *
 * Tier 1 (current implementation): purely informational read-only view
 * that shows the user what's currently active + lists available models
 * from each provider.  Tier 2 will add POST /api/model/switch for live
 * mid-session switching.
 */
export function ModelSelector({
  currentModel,
  refreshKey = 0,
  onChange,
  disabled = false,
}: ModelSelectorProps) {
  const [status, setStatus] = useState<Status>({ kind: "idle" });
  const [providers, setProviders] = useState<ProviderInfo[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<string | null>(null);
  const [models, setModels] = useState<AvailableModel[]>([]);
  const [modelsLoading, setModelsLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [modelInfo, setModelInfo] = useState<ModelInfoResponse | null>(null);
  const [infoLoading, setInfoLoading] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const lastInfoKey = useRef("");

  // ── Initial load: providers + current model info ──
  useEffect(() => {
    let cancelled = false;
    setStatus({ kind: "loading" });
    Promise.all([api.getProviders().catch(() => null), api.getModelInfo().catch(() => null)])
      .then(([provResp, info]) => {
        if (cancelled) return;
        if (provResp) {
          setProviders(provResp.providers);
          // Auto-select the configured provider
          if (info?.provider) {
            setSelectedProvider(info.provider);
          }
        }
        if (info) setModelInfo(info);
        setStatus({ kind: "ready" });
      })
      .catch((e) => {
        if (cancelled) return;
        setStatus({ kind: "error", message: String(e) });
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // ── Refresh model info when model changes externally or refreshKey bumps ──
  useEffect(() => {
    if (!currentModel) return;
    const fetchKey = `${currentModel}:${refreshKey}`;
    if (fetchKey === lastInfoKey.current) return;
    lastInfoKey.current = fetchKey;
    setInfoLoading(true);
    api
      .getModelInfo()
      .then((info) => {
        setModelInfo(info);
        if (info?.provider) setSelectedProvider((p) => p ?? info.provider);
      })
      .catch(() => {})
      .finally(() => setInfoLoading(false));
  }, [currentModel, refreshKey]);

  // ── Fetch models when provider changes ──
  useEffect(() => {
    if (!selectedProvider) {
      setModels([]);
      return;
    }
    let cancelled = false;
    setModelsLoading(true);
    api
      .getAvailableModels(selectedProvider)
      .then((resp) => {
        if (cancelled) return;
        setModels(resp.models);
      })
      .catch(() => {
        if (cancelled) return;
        setModels([]);
      })
      .finally(() => {
        if (cancelled) return;
        setModelsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [selectedProvider]);

  // ── Close on outside click ──
  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  const filteredProviders = providers.filter((p) => {
    if (!search.trim()) return true;
    const q = search.toLowerCase();
    return p.id.toLowerCase().includes(q) || p.display_name.toLowerCase().includes(q);
  });

  const filteredModels = models.filter((m) => {
    if (!search.trim()) return true;
    const q = search.toLowerCase();
    return m.id.toLowerCase().includes(q) || m.display_name.toLowerCase().includes(q);
  });

  const displayLabel = currentModel || (modelInfo?.model ?? "");
  const providerLabel = modelInfo?.provider ?? "";

  return (
    <div ref={containerRef} className="relative shrink-0">
      <button
        type="button"
        onClick={() => !disabled && setOpen((o) => !o)}
        disabled={disabled || status.kind === "loading"}
        className={cn(
          "flex items-center gap-1.5 h-7 px-2.5 border border-border bg-background/40",
          "text-xs font-mono text-foreground transition-colors",
          "hover:border-foreground/25 hover:bg-background/60",
          "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-foreground/30",
          "disabled:cursor-not-allowed disabled:opacity-50",
        )}
        title={`${currentModel}${providerLabel ? ` (${providerLabel})` : ""}`}
      >
        {status.kind === "loading" || infoLoading ? (
          <Loader2 className="h-3 w-3 animate-spin text-muted-foreground" />
        ) : status.kind === "error" ? (
          <AlertCircle className="h-3 w-3 text-destructive" />
        ) : (
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 shrink-0" />
        )}
        <span className="truncate max-w-[180px]">{displayLabel || "No model"}</span>
        <ChevronDown
          className={cn(
            "h-3 w-3 text-muted-foreground transition-transform shrink-0",
            open && "rotate-180",
          )}
        />
      </button>

      {open && (
        <div
          className={cn(
            "absolute right-0 top-full mt-1 z-50 w-[480px]",
            "border border-border bg-popover text-popover-foreground shadow-xl",
            "animate-[fade-in_100ms_ease-out]",
          )}
        >
          {/* Search box */}
          <div className="flex items-center gap-2 border-b border-border px-3 py-2">
            <Search className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
            <input
              autoFocus
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search models or providers…"
              className="flex-1 bg-transparent text-xs font-mono outline-none placeholder:text-muted-foreground/50"
            />
            {search && (
              <button
                type="button"
                onClick={() => setSearch("")}
                className="text-muted-foreground hover:text-foreground"
                title="Clear"
              >
                <X className="h-3 w-3" />
              </button>
            )}
          </div>

          {/* Two-pane layout: providers | models */}
          <div className="flex max-h-[400px]">
            {/* Provider pane */}
            <div className="w-[180px] border-r border-border overflow-y-auto shrink-0">
              <div className="px-2.5 py-1.5 font-display text-[0.6rem] tracking-widest uppercase text-muted-foreground/60">
                Providers
              </div>
              {filteredProviders.length === 0 ? (
                <div className="px-2.5 py-2 text-[10px] text-muted-foreground/50">No matches</div>
              ) : (
                filteredProviders.map((p) => (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => setSelectedProvider(p.id)}
                    className={cn(
                      "w-full text-left px-2.5 py-1.5 text-xs font-mono transition-colors",
                      "flex items-center gap-1.5",
                      selectedProvider === p.id
                        ? "bg-foreground/10 text-foreground"
                        : "text-muted-foreground hover:bg-foreground/5",
                    )}
                  >
                    <span
                      className={cn(
                        "h-1.5 w-1.5 rounded-full shrink-0",
                        p.has_credentials ? "bg-emerald-500" : "bg-muted-foreground/30",
                      )}
                    />
                    <span className="truncate flex-1">{p.display_name}</span>
                    {selectedProvider === p.id && <Check className="h-3 w-3 shrink-0" />}
                  </button>
                ))
              )}
            </div>

            {/* Models pane */}
            <div className="flex-1 overflow-y-auto">
              <div className="px-2.5 py-1.5 font-display text-[0.6rem] tracking-widest uppercase text-muted-foreground/60 flex items-center justify-between">
                <span>Models</span>
                {modelsLoading && <Loader2 className="h-2.5 w-2.5 animate-spin" />}
              </div>
              {filteredModels.length === 0 ? (
                <div className="px-2.5 py-2 text-[10px] text-muted-foreground/50">
                  {modelsLoading
                    ? "Loading…"
                    : models.length === 0
                      ? "No models available"
                      : "No matches"}
                </div>
              ) : (
                filteredModels.map((m) => {
                  const isCurrent = m.id === currentModel;
                  const willSwitchProvider =
                    selectedProvider !== null && modelInfo?.provider !== selectedProvider;
                  return (
                    <button
                      key={m.id}
                      type="button"
                      onClick={() => {
                        if (!isCurrent && selectedProvider) {
                          onChange(m.id, selectedProvider);
                          setOpen(false);
                        }
                      }}
                      disabled={isCurrent}
                      className={cn(
                        "w-full text-left px-2.5 py-1.5 text-xs font-mono transition-colors",
                        "flex items-center gap-1.5",
                        isCurrent
                          ? "bg-foreground/10 text-foreground cursor-default"
                          : willSwitchProvider
                            ? "text-amber-600 dark:text-amber-400 hover:bg-amber-500/10 cursor-pointer"
                            : "text-muted-foreground hover:bg-foreground/5 cursor-pointer",
                      )}
                      title={
                        isCurrent
                          ? "Currently active"
                          : willSwitchProvider
                            ? `Switch to ${m.id} via ${selectedProvider} (changes provider)`
                            : `Switch to ${m.id} (same provider)`
                      }
                    >
                      <span
                        className={cn(
                          "h-1.5 w-1.5 rounded-full shrink-0",
                          m.loaded ? "bg-emerald-500" : "bg-muted-foreground/30",
                        )}
                      />
                      <span className="truncate flex-1">{m.display_name}</span>
                      {isCurrent && <Check className="h-3 w-3 shrink-0" />}
                    </button>
                  );
                })
              )}
            </div>
          </div>

          {/* Footer: model info */}
          {modelInfo && (
            <div className="border-t border-border px-3 py-1.5 text-[10px] text-muted-foreground/60 font-mono">
              <span>
                ctx {modelInfo.effective_context_length.toLocaleString()} tokens
                {modelInfo.capabilities?.model_family && ` · ${modelInfo.capabilities.model_family}`}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
