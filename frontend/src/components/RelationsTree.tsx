import { useState } from "react"
import { ChevronRight, ChevronDown, Unlink, Loader2, Minus } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface TreeNode {
  assetId: string
  assetName: string
  assetType: string
  children: TreeNode[]
  relationType?: string
  relationTypeName?: string
  direction: "upstream" | "downstream"
  relationId?: string
}

interface RelationsTreeProps {
  nodes: TreeNode[]
  onDeleteRelation: (relationId: string, assetId: string) => void
  loading?: boolean
  direction?: "depends_on" | "required_by" | "all"
}

const assetTypeColors: Record<string, string> = {
  APP: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
  SYS: "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200",
  NET: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
  INF: "bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200",
  DATA: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
  SVC: "bg-pink-100 text-pink-800 dark:bg-pink-900 dark:text-pink-200",
  default: "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200",
}

function getAssetTypeColor(type: string): string {
  return assetTypeColors[type] || assetTypeColors.default
}

function TreeNodeComponent({
  node,
  onDeleteRelation,
  depth = 0,
  isLast = true,
}: {
  node: TreeNode
  onDeleteRelation: (relationId: string, assetId: string) => void
  depth?: number
  isLast?: boolean
}) {
  const [expanded, setExpanded] = useState(depth < 2)
  const hasChildren = node.children.length > 0

  return (
    <div className="select-none">
      <div
        className={cn(
          "flex items-center gap-1 py-1.5 px-2 rounded-md hover:bg-accent/50 transition-colors group",
        )}
      >
        {/* Tree branch lines */}
        <div className="flex items-center w-6 shrink-0">
          {depth > 0 && (
            <>
              {/* Vertical line from parent */}
              <div
                className="w-4 h-4 border-l-2 border-border/40"
                style={{ borderLeft: isLast ? "none" : undefined }}
              />
              {/* Horizontal connector */}
              <div className="h-[2px] w-4 bg-border/40" />
            </>
          )}
        </div>

        {/* Expand/collapse button */}
        {hasChildren ? (
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex-shrink-0 p-0.5 hover:bg-accent rounded"
          >
            {expanded ? (
              <ChevronDown className="h-4 w-4 text-muted-foreground" />
            ) : (
              <ChevronRight className="h-4 w-4 text-muted-foreground" />
            )}
          </button>
        ) : (
          <div className="w-5 flex items-center justify-center">
            <Minus className="h-2 w-2 text-muted-foreground/30" />
          </div>
        )}

        {/* Asset info */}
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <span className={cn(
            "w-2 h-2 rounded-full shrink-0",
            node.direction === "upstream" ? "bg-blue-500" : "bg-purple-500"
          )} />
          <span className="text-sm font-medium truncate">{node.assetName}</span>
          <Badge variant="outline" className={cn("text-xs shrink-0", getAssetTypeColor(node.assetType))}>
            {node.assetType}
          </Badge>
          {node.relationType && (
            <Badge variant="secondary" className="text-xs shrink-0 font-normal opacity-70">
              {node.relationTypeName || node.relationType}
            </Badge>
          )}
        </div>

        {/* Delete button */}
        {node.relationId && (
          <Button
            variant="ghost"
            size="sm"
            className="h-6 w-6 p-0 text-destructive opacity-0 group-hover:opacity-100 hover:opacity-100 shrink-0"
            onClick={(e) => {
              e.stopPropagation()
              onDeleteRelation(node.relationId!, node.assetId)
            }}
          >
            <Unlink className="h-3 w-3" />
          </Button>
        )}
      </div>

      {/* Children */}
      {expanded && hasChildren && (
        <div className="relative">
          {/* Continuation line for non-last children */}
          {node.children.map((child, index) => (
            <TreeNodeComponent
              key={`${child.assetId}-${index}`}
              node={child}
              onDeleteRelation={onDeleteRelation}
              depth={depth + 1}
              isLast={index === node.children.length - 1}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export function RelationsTree({ nodes, onDeleteRelation, loading }: RelationsTreeProps) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12 text-muted-foreground">
        <Loader2 className="h-6 w-6 animate-spin mr-2" />
        <span>Building relation tree...</span>
      </div>
    )
  }

  if (nodes.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        No relations to display
      </div>
    )
  }

  return (
    <div className="space-y-0.5 font-mono text-sm">
      {nodes.map((node, index) => (
        <TreeNodeComponent
          key={`${node.assetId}-${index}`}
          node={node}
          onDeleteRelation={onDeleteRelation}
          depth={0}
          isLast={index === nodes.length - 1}
        />
      ))}
    </div>
  )
}

export type { TreeNode }