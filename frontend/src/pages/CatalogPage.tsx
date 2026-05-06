import { useTranslation } from "@/lib/i18n"

export default function CatalogPage() {
  const { t } = useTranslation()

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">{t("catalog.title")}</h1>
      <p className="text-muted-foreground">{t("catalog.noData")}</p>
    </div>
  )
}