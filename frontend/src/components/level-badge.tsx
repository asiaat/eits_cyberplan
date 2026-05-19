import { Badge, BadgeProps } from "@/components/ui/badge"

const levelStyles: Record<string, string> = {
  BASE: "bg-green-100 text-green-800 border-green-200 dark:bg-green-900 dark:text-green-200 dark:border-green-800",
  STANDARD: "bg-yellow-100 text-yellow-800 border-yellow-200 dark:bg-yellow-900 dark:text-yellow-200 dark:border-yellow-800",
  HIGH: "bg-red-100 text-red-800 border-red-200 dark:bg-red-900 dark:text-red-200 dark:border-red-800",
}

interface LevelBadgeProps extends Omit<BadgeProps, "className"> {
  level: string
}

export function LevelBadge({ level, ...props }: LevelBadgeProps) {
  return (
    <Badge
      className={levelStyles[level] || "bg-gray-100 text-gray-800"}
      {...props}
    >
      {level}
    </Badge>
  )
}