# Dedicated Bulk Asset View

## Goal
Create a third view mode (`"bulk"`) for assets — a simplified list with checkboxes for multi-select bulk editing. Keep the existing "list" view clean (no checkboxes) and "cards" view unchanged.

## Steps

### 1. Remove checkbox column from list view table
**File**: `frontend/src/pages/AssetsPage.tsx`

Remove lines 200-220 (the `id: "select"` column) from the `columns` definition inside `useReactTable`.

**Before** (around lines 199-220):
```tsx
columns: useMemo(() => [
  {
    id: "select",
    header: ({ table }: any) => (
      <input
        type="checkbox"
        checked={table.getIsAllRowsSelected()}
        onChange={() => handleSelectAll()}
        className="rounded border-input"
      />
    ),
    cell: ({ row }: any) => (
      <input
        type="checkbox"
        checked={selectedAssetIds.has(row.original.id)}
        onChange={() => handleToggleSelect(row.original.id)}
        onClick={(e) => e.stopPropagation()}
        className="rounded border-input"
      />
    ),
    enableSorting: false,
  },
  {
```
**After**:
```tsx
columns: useMemo(() => [
  {
```

### 2. Change viewMode type declaration
**Line 128**: Change `useState<"cards" | "list">("cards")` to `useState<"cards" | "list" | "bulk">("cards")`

### 3. Add a third toggle button for bulk view
Replace the existing view toggle div (around lines 1059-1076) with a 3-button group:

```tsx
<div className="flex items-center border rounded-md">
  <Button
    variant={viewMode === "cards" ? "default" : "ghost"}
    size="sm"
    onClick={() => { setViewMode("cards"); handleClearSelection(); }}
    className="rounded-r-none"
  >
    <LayoutGrid className="h-4 w-4" />
  </Button>
  <Button
    variant={viewMode === "list" ? "default" : "ghost"}
    size="sm"
    onClick={() => { setViewMode("list"); handleClearSelection(); }}
    className="rounded-none border-x"
  >
    <List className="h-4 w-4" />
  </Button>
  <Button
    variant={viewMode === "bulk" ? "default" : "ghost"}
    size="sm"
    onClick={() => setViewMode("bulk")}
    className="rounded-l-none"
  >
    <List className="h-4 w-4" />  {/* or another icon */}
  </Button>
</div>
```

The middle button gets `rounded-none border-x` to separate it from neighbors.

### 4. Create bulk columns definition
After the existing `table` variable (around line 461), add:

```tsx
const bulkColumns = useMemo(() => [
  {
    id: "select",
    header: () => (
      <input
        type="checkbox"
        checked={selectedAssetIds.size === filteredAssets.length && filteredAssets.length > 0}
        onChange={() => handleSelectAll()}
        className="rounded border-input"
      />
    ),
    cell: ({ row }: any) => (
      <input
        type="checkbox"
        checked={selectedAssetIds.has(row.original.id)}
        onChange={() => handleToggleSelect(row.original.id)}
        className="rounded border-input"
      />
    ),
  },
  {
    accessorKey: "name",
    header: t("common.name"),
    cell: ({ row }: any) => <span className="font-medium">{row.getValue("name")}</span>,
  },
  {
    accessorKey: "asset_type",
    header: t("assets.type"),
    cell: ({ row }: any) => (
      <Badge variant="outline" className="bg-purple-50 dark:bg-purple-900 dark:text-purple-200">
        {t(`assets.types.${row.getValue("asset_type")}`) || row.getValue("asset_type")}
      </Badge>
    ),
  },
  {
    accessorKey: "criticality",
    header: t("assets.criticality"),
    cell: ({ row }: any) => {
      const crit = row.getValue("criticality") as string
      return (
        <Badge variant="outline" className={criticalityColors[crit] || criticalityColors.normal}>
          {t(`assets.criticalityLevels.${crit}`) || crit}
        </Badge>
      )
    },
  },
  {
    id: "owner",
    accessorFn: (row: any) => row.owner?.name || "",
    header: t("assets.owner"),
    cell: ({ row }: any) => {
      const owner = row.original.owner as OwnerInfo | null
      return owner?.name || "-"
    },
  },
  {
    accessorKey: "linked_process_count",
    header: t("assets.linkedProcesses"),
    cell: ({ row }: any) => {
      const count = row.getValue("linked_process_count") as number
      const processes = row.original.linked_processes as LinkedProcess[] | undefined
      if (count === 1 && processes?.[0]) {
        return (
          <span className="text-sm max-w-[200px] truncate block" title={processes[0].name}>
            {processes[0].name}
          </span>
        )
      }
      return (
        <Badge variant="outline" className="bg-blue-50 dark:bg-blue-900 dark:text-blue-200">
          {count}
        </Badge>
      )
    },
  },
], [t, selectedAssetIds, filteredAssets])
```

Then create the bulk table:
```tsx
const bulkTable = useReactTable({
  data: filteredAssets,
  columns: bulkColumns,
  getCoreRowModel: getCoreRowModel(),
})
```

### 5. Add bulk view render block
After the list view section (around line 1289), add:

```tsx
{filteredAssets.length > 0 && viewMode === "bulk" && (
  <div className="border rounded-md overflow-hidden">
    <table className="w-full">
      <thead className="bg-muted">
        {bulkTable.getHeaderGroups().map((headerGroup) => (
          <tr key={headerGroup.id}>
            {headerGroup.headers.map((header) => (
              <th key={header.id} className="px-4 py-3 text-left text-sm font-medium">
                {header.isPlaceholder
                  ? null
                  : flexRender(header.column.columnDef.header, header.getContext())}
              </th>
            ))}
          </tr>
        ))}
      </thead>
      <tbody>
        {bulkTable.getRowModel().rows.map((row) => (
          <tr
            key={row.id}
            className={`border-t hover:bg-muted/50 ${selectedAssetIds.has(row.original.id) ? "bg-primary/5" : ""}`}
          >
            {row.getVisibleCells().map((cell) => (
              <td key={cell.id} className="px-4 py-3 text-sm">
                {flexRender(cell.column.columnDef.cell, cell.getContext())}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  </div>
)}
```

Note: no `onClick` on rows — click is not needed for bulk view.

### 6. Update selection toolbar condition
Line 1079: Change `{selectedAssetIds.size > 0 && viewMode === "list" && (` to `{selectedAssetIds.size > 0 && viewMode === "bulk" && (`

### 7. Clear selection when switching to list
Update the list button onClick: `onClick={() => { setViewMode("list"); handleClearSelection(); }}`

## Files to modify
Only `frontend/src/pages/AssetsPage.tsx` — no backend changes, no new translation keys needed.
