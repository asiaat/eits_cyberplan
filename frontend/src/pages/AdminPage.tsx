import { useTranslation } from "@/lib/i18n"

export default function AdminPage() {
  const { t } = useTranslation()

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">{t("admin.title")}</h1>
      <p className="text-muted-foreground">{t("admin.noData")}</p>
    </div>
  )
}