import { useTranslation } from "@/lib/i18n"

export default function BusinessProcessesPage() {
  const { t } = useTranslation()

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">{t("businessProcesses.title")}</h1>
      <p className="text-muted-foreground">{t("businessProcesses.noData")}</p>
    </div>
  )
}