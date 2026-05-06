import { useTranslation } from "@/lib/i18n"

export default function EvidencesPage() {
  const { t } = useTranslation()

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">{t("evidences.title")}</h1>
      <p className="text-muted-foreground">{t("evidences.noData")}</p>
    </div>
  )
}