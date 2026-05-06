import { useTranslation } from "@/lib/i18n"

export default function AuditViewPage() {
  const { t } = useTranslation()

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">{t("auditView.title")}</h1>
      <p className="text-muted-foreground">{t("auditView.noData")}</p>
    </div>
  )
}