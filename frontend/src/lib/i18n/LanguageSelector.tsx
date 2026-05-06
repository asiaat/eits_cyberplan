import { useTranslation, Language } from "./index";

const languages: { code: Language; label: string }[] = [
  { code: "en", label: "EN" },
  { code: "ee", label: "EE" },
];

export default function LanguageSelector() {
  const { language, setLanguage } = useTranslation();

  return (
    <div className="flex gap-1">
      {languages.map((lang) => (
        <button
          key={lang.code}
          onClick={() => setLanguage(lang.code)}
          className={`px-2 py-1 text-xs rounded transition-colors ${
            language === lang.code
              ? "bg-primary text-primary-foreground"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          {lang.label}
        </button>
      ))}
    </div>
  );
}