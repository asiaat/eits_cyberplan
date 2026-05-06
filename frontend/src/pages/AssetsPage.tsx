import { useTranslation } from "@/lib/i18n"

export default function AssetsPage() {
  const { t } = useTranslation()

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">{t("assets.title")}</h1>
      <p className="text-muted-foreground">{t("assets.noData")}</p>
    </div>
  )
}