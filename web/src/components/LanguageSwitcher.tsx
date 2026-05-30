import { useI18n } from "@/i18n/context";

const LOCALES = ["en", "ru", "zh"] as const;

const NEXT_FLAG: Record<string, string> = { en: "🇷🇺", ru: "🇨🇳", zh: "🇬🇧" };
const NEXT_LABEL: Record<string, string> = { en: "RU", ru: "中文", zh: "EN" };

/**
 * Compact language toggle — cycles through English, Russian, Chinese.
 * Persists choice to localStorage.
 */
export function LanguageSwitcher() {
  const { locale, setLocale, t } = useI18n();

  const cycle = () => {
    const idx = LOCALES.indexOf(locale as (typeof LOCALES)[number]);
    setLocale(LOCALES[(idx + 1) % LOCALES.length]);
  };

  return (
    <button
      type="button"
      onClick={cycle}
      className="group relative inline-flex items-center gap-1.5 px-2 py-1 text-xs text-muted-foreground hover:text-foreground transition-colors cursor-pointer focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
      title={t.language.switchTo}
      aria-label={t.language.switchTo}
    >
      <span className="text-base leading-none">{NEXT_FLAG[locale]}</span>
      <span className="hidden sm:inline font-display tracking-wide uppercase text-[0.65rem]">
        {NEXT_LABEL[locale]}
      </span>
    </button>
  );
}
