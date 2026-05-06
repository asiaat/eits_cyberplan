import { useTranslation } from "@/lib/i18n"

export default function ImplementationPlanPage() {
  const { t } = useTranslation()

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">{t("implementationPlan.title")}</h1>
      <p className="text-muted-foreground">{t("implementationPlan.noData")}</p>
    </div>
  )
}