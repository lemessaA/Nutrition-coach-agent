"use client"

import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Store,
  Plus,
  Pencil,
  Trash2,
  Loader2,
  CheckCircle2,
  Clock,
  XCircle,
  PackageCheck,
  AlertCircle,
  X,
  DollarSign,
  Save,
  Upload,
  ImageIcon,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { useUser } from "@/lib/user-context"
import {
  marketplaceAPI,
  type FoodListing,
  type MarketplaceOrder,
  type OrderStatus,
} from "@/services/api"

type ListingDraft = {
  id?: number
  name: string
  description: string
  image_url: string
  price: string
  unit: string
  stock: string
  serving_size: string
  calories: string
  protein: string
  carbs: string
  fat: string
  fiber: string
  sugar: string
  sodium: string
  tags: string
}

const EMPTY_DRAFT: ListingDraft = {
  name: "",
  description: "",
  image_url: "",
  price: "",
  unit: "serving",
  stock: "",
  serving_size: "",
  calories: "",
  protein: "",
  carbs: "",
  fat: "",
  fiber: "",
  sugar: "",
  sodium: "",
  tags: "",
}

function toNum(v: string): number | undefined {
  const n = parseFloat(v)
  return Number.isFinite(n) ? n : undefined
}

function draftToPayload(draft: ListingDraft) {
  return {
    name: draft.name.trim(),
    description: draft.description.trim() || undefined,
    image_url: draft.image_url.trim() || undefined,
    price: toNum(draft.price) ?? 0,
    unit: draft.unit.trim() || "serving",
    stock: Math.max(0, Math.round(toNum(draft.stock) ?? 0)),
    serving_size: draft.serving_size.trim() || undefined,
    calories: toNum(draft.calories),
    protein: toNum(draft.protein),
    carbs: toNum(draft.carbs),
    fat: toNum(draft.fat),
    fiber: toNum(draft.fiber),
    sugar: toNum(draft.sugar),
    sodium: toNum(draft.sodium),
    tags: draft.tags
      .split(",")
      .map((t) => t.trim().toLowerCase())
      .filter(Boolean),
  }
}

function listingToDraft(listing: FoodListing): ListingDraft {
  return {
    id: listing.id,
    name: listing.name,
    description: listing.description ?? "",
    image_url: listing.image_url ?? "",
    price: String(listing.price),
    unit: listing.unit,
    stock: String(listing.stock),
    serving_size: listing.serving_size ?? "",
    calories: listing.calories != null ? String(listing.calories) : "",
    protein: listing.protein != null ? String(listing.protein) : "",
    carbs: listing.carbs != null ? String(listing.carbs) : "",
    fat: listing.fat != null ? String(listing.fat) : "",
    fiber: listing.fiber != null ? String(listing.fiber) : "",
    sugar: listing.sugar != null ? String(listing.sugar) : "",
    sodium: listing.sodium != null ? String(listing.sodium) : "",
    tags: listing.tags.join(", "),
  }
}

export default function SellerDashboardPage() {
  const { userId, ready, isSeller, setRole } = useUser()

  const [listings, setListings] = useState<FoodListing[]>([])
  const [orders, setOrders] = useState<MarketplaceOrder[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [editing, setEditing] = useState<ListingDraft | null>(null)
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)

  const [promoting, setPromoting] = useState(false)
  const [promoteError, setPromoteError] = useState<string | null>(null)

  const loadAll = useCallback(async () => {
    if (!userId || !isSeller) return
    setLoading(true)
    setError(null)
    try {
      const [listingsRes, ordersRes] = await Promise.all([
        marketplaceAPI.getSellerListings(userId, true),
        marketplaceAPI.listOrders(userId, "seller"),
      ])
      setListings(listingsRes)
      setOrders(ordersRes)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load dashboard")
    } finally {
      setLoading(false)
    }
  }, [userId, isSeller])

  useEffect(() => {
    void loadAll()
  }, [loadAll])

  const promoteToSeller = async () => {
    if (!userId) return
    setPromoting(true)
    setPromoteError(null)
    try {
      const updated = await marketplaceAPI.updateRole(userId, "seller")
      // ``updated`` has shape ``{role: "seller" | "both" | "buyer", ...}``
      const nextRole =
        (updated && typeof updated === "object" && "role" in updated
          ? ((updated as { role?: unknown }).role as string | undefined)
          : undefined) ?? "seller"
      if (nextRole === "seller" || nextRole === "both") {
        setRole(nextRole)
      } else {
        setRole("seller")
      }
    } catch (err) {
      setPromoteError(
        err instanceof Error ? err.message : "Could not promote account"
      )
    } finally {
      setPromoting(false)
    }
  }

  const beginCreate = () => {
    setEditing({ ...EMPTY_DRAFT })
    setSaveError(null)
  }

  const beginEdit = (listing: FoodListing) => {
    setEditing(listingToDraft(listing))
    setSaveError(null)
  }

  const cancelEdit = () => {
    setEditing(null)
    setSaveError(null)
  }

  const saveListing = async () => {
    if (!editing || !userId) return
    if (!editing.name.trim() || !toNum(editing.price)) {
      setSaveError("Name and a valid price are required.")
      return
    }
    setSaving(true)
    setSaveError(null)
    try {
      const payload = draftToPayload(editing)
      if (editing.id != null) {
        await marketplaceAPI.updateListing(userId, editing.id, payload)
      } else {
        await marketplaceAPI.createListing(userId, payload)
      }
      setEditing(null)
      await loadAll()
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Failed to save listing")
    } finally {
      setSaving(false)
    }
  }

  const deleteListing = async (listing: FoodListing) => {
    if (!userId) return
    if (!window.confirm(`Delete "${listing.name}"?`)) return
    try {
      await marketplaceAPI.deleteListing(userId, listing.id)
      await loadAll()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed")
    }
  }

  const updateOrderStatus = async (orderId: number, status: OrderStatus) => {
    if (!userId) return
    try {
      await marketplaceAPI.updateOrderStatus(userId, orderId, status)
      await loadAll()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Status change failed")
    }
  }

  const activeListings = useMemo(
    () => listings.filter((l) => l.is_active),
    [listings]
  )
  const inactiveListings = useMemo(
    () => listings.filter((l) => !l.is_active),
    [listings]
  )
  const pendingOrders = useMemo(
    () => orders.filter((o) => o.status === "pending"),
    [orders]
  )
  const activeOrders = useMemo(
    () =>
      orders.filter((o) =>
        ["pending", "confirmed"].includes(o.status)
      ),
    [orders]
  )

  // --- not signed in ---
  if (!ready) {
    return (
      <div className="container mx-auto max-w-4xl px-4 py-12 text-center text-muted-foreground">
        Loading...
      </div>
    )
  }

  if (!userId) {
    return (
      <div className="container mx-auto max-w-xl px-4 py-16 text-center">
        <Store className="mx-auto mb-4 h-12 w-12 text-muted-foreground" />
        <h1 className="text-2xl font-bold">Sign in to sell</h1>
        <p className="mt-2 text-muted-foreground">
          Create a profile first, then promote it to a seller account to start
          posting listings.
        </p>
        <Link href="/profile" className="mt-4 inline-block">
          <Button>Go to profile</Button>
        </Link>
      </div>
    )
  }

  if (!isSeller) {
    return (
      <div className="container mx-auto max-w-xl px-4 py-16 text-center">
        <Store className="mx-auto mb-4 h-12 w-12 text-primary" />
        <h1 className="text-2xl font-bold">Become a seller</h1>
        <p className="mt-2 text-muted-foreground">
          Post the foods you grow, cook, or source and earn from buyers looking
          for nutrient-dense options.
        </p>
        {promoteError && (
          <p className="mt-3 flex items-center justify-center gap-1 text-sm text-destructive">
            <AlertCircle className="h-4 w-4" />
            {promoteError}
          </p>
        )}
        <Button onClick={promoteToSeller} disabled={promoting} className="mt-4 gap-2">
          {promoting ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Store className="h-4 w-4" />
          )}
          Promote my account to seller
        </Button>
      </div>
    )
  }

  return (
    <div className="container mx-auto max-w-6xl px-4 py-8">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">Seller Dashboard</h1>
          <p className="text-muted-foreground">
            Manage your food listings and incoming orders.
          </p>
        </div>
        <Button onClick={beginCreate} className="gap-2">
          <Plus className="h-4 w-4" />
          New listing
        </Button>
      </div>

      {error && (
        <Card className="mb-4 border-destructive/60">
          <CardContent className="flex items-center gap-2 py-3 text-sm text-destructive">
            <AlertCircle className="h-4 w-4" />
            {error}
          </CardContent>
        </Card>
      )}

      {/* Stats */}
      <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatCard label="Active listings" value={activeListings.length} />
        <StatCard label="Pending orders" value={pendingOrders.length} />
        <StatCard label="Open orders" value={activeOrders.length} />
        <StatCard
          label="Inventory value"
          value={`$${activeListings
            .reduce((sum, l) => sum + l.price * l.stock, 0)
            .toFixed(0)}`}
        />
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-16 text-muted-foreground">
          <Loader2 className="mr-2 h-5 w-5 animate-spin" />
          Loading dashboard...
        </div>
      ) : (
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Orders column */}
          <section>
            <h2 className="mb-3 text-lg font-semibold">Incoming orders</h2>
            {orders.length === 0 ? (
              <Card>
                <CardContent className="py-8 text-center text-sm text-muted-foreground">
                  No orders yet. Share your listings!
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-3">
                {orders.map((order) => (
                  <SellerOrderCard
                    key={order.id}
                    order={order}
                    onStatusChange={(status) =>
                      updateOrderStatus(order.id, status)
                    }
                  />
                ))}
              </div>
            )}
          </section>

          {/* Listings column */}
          <section>
            <h2 className="mb-3 text-lg font-semibold">Your listings</h2>
            {listings.length === 0 ? (
              <Card>
                <CardContent className="py-8 text-center text-sm text-muted-foreground">
                  No listings yet. Click “New listing” to post your first product.
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-3">
                {[...activeListings, ...inactiveListings].map((listing) => (
                  <Card key={listing.id}>
                    <CardContent className="flex flex-wrap items-start justify-between gap-4 py-4">
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <h3 className="font-semibold">{listing.name}</h3>
                          {!listing.is_active && (
                            <Badge variant="secondary" className="text-[10px]">
                              inactive
                            </Badge>
                          )}
                        </div>
                        <p className="mt-1 text-xs text-muted-foreground">
                          {listing.stock} {listing.unit} in stock •{" "}
                          {listing.serving_size ?? "no serving info"}
                        </p>
                        <div className="mt-1 text-sm">
                          <DollarSign className="mr-0.5 inline h-3.5 w-3.5 text-primary" />
                          <span className="font-medium">
                            {listing.price.toFixed(2)}
                          </span>
                          <span className="text-muted-foreground">
                            {" "}
                            / {listing.unit}
                          </span>
                        </div>
                        {listing.tags.length > 0 && (
                          <div className="mt-2 flex flex-wrap gap-1">
                            {listing.tags.map((t) => (
                              <Badge
                                key={t}
                                variant="secondary"
                                className="text-[10px]"
                              >
                                {t}
                              </Badge>
                            ))}
                          </div>
                        )}
                      </div>
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => beginEdit(listing)}
                          className="gap-1"
                        >
                          <Pencil className="h-3.5 w-3.5" />
                          Edit
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => deleteListing(listing)}
                          className="gap-1 text-destructive hover:text-destructive"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                          Delete
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </section>
        </div>
      )}

      {editing && (
        <ListingEditorModal
          draft={editing}
          onChange={setEditing}
          onClose={cancelEdit}
          onSave={saveListing}
          saving={saving}
          error={saveError}
        />
      )}
    </div>
  )
}

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <Card>
      <CardContent className="py-4">
        <p className="text-xs uppercase tracking-wide text-muted-foreground">
          {label}
        </p>
        <p className="mt-1 text-2xl font-semibold">{value}</p>
      </CardContent>
    </Card>
  )
}

function statusMeta(status: OrderStatus) {
  switch (status) {
    case "pending":
      return {
        icon: Clock,
        label: "Pending",
        className: "bg-amber-500/15 text-amber-600 dark:text-amber-400",
      }
    case "confirmed":
      return {
        icon: CheckCircle2,
        label: "Confirmed",
        className: "bg-sky-500/15 text-sky-600 dark:text-sky-400",
      }
    case "fulfilled":
      return {
        icon: PackageCheck,
        label: "Fulfilled",
        className: "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400",
      }
    case "cancelled":
      return {
        icon: XCircle,
        label: "Cancelled",
        className: "bg-muted text-muted-foreground",
      }
  }
}

function SellerOrderCard({
  order,
  onStatusChange,
}: {
  order: MarketplaceOrder
  onStatusChange: (status: OrderStatus) => void
}) {
  const meta = statusMeta(order.status)
  const Icon = meta.icon
  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-3">
          <div>
            <CardTitle className="text-base">
              Order #{order.id} • {order.buyer_name ?? "Buyer"}
            </CardTitle>
            <CardDescription>
              {new Date(order.created_at).toLocaleString()}
            </CardDescription>
          </div>
          <span
            className={cn(
              "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium",
              meta.className
            )}
          >
            <Icon className="h-3.5 w-3.5" />
            {meta.label}
          </span>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <ul className="space-y-1 text-sm">
          {order.items.map((item) => (
            <li key={item.id} className="flex justify-between">
              <span>
                {item.quantity}× {item.name_snapshot}
              </span>
              <span className="text-muted-foreground">
                ${(item.unit_price * item.quantity).toFixed(2)}
              </span>
            </li>
          ))}
        </ul>
        <div className="mt-3 flex items-center justify-between border-t border-border pt-3">
          <span className="text-sm font-semibold">Total</span>
          <span className="text-sm font-semibold">
            ${order.total_price.toFixed(2)}
          </span>
        </div>
        {order.notes && (
          <p className="mt-2 rounded-md bg-muted px-3 py-2 text-xs italic text-foreground/80">
            “{order.notes}”
          </p>
        )}
        {(order.status === "pending" || order.status === "confirmed") && (
          <div className="mt-3 flex flex-wrap gap-2">
            {order.status === "pending" && (
              <Button
                size="sm"
                onClick={() => onStatusChange("confirmed")}
                className="gap-1"
              >
                <CheckCircle2 className="h-4 w-4" />
                Confirm
              </Button>
            )}
            {order.status === "confirmed" && (
              <Button
                size="sm"
                onClick={() => onStatusChange("fulfilled")}
                className="gap-1"
              >
                <PackageCheck className="h-4 w-4" />
                Mark fulfilled
              </Button>
            )}
            <Button
              size="sm"
              variant="outline"
              onClick={() => onStatusChange("cancelled")}
              className="gap-1 text-destructive hover:text-destructive"
            >
              <XCircle className="h-4 w-4" />
              Cancel
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function ListingEditorModal({
  draft,
  onChange,
  onClose,
  onSave,
  saving,
  error,
}: {
  draft: ListingDraft
  onChange: (d: ListingDraft) => void
  onClose: () => void
  onSave: () => void
  saving: boolean
  error: string | null
}) {
  const isEdit = draft.id != null
  const set = <K extends keyof ListingDraft>(key: K, value: ListingDraft[K]) =>
    onChange({ ...draft, [key]: value })

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-background/70 p-4 backdrop-blur-sm sm:items-center">
      <Card className="relative w-full max-w-2xl">
        <button
          onClick={onClose}
          className="absolute right-3 top-3 rounded-md p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground"
          aria-label="Close"
        >
          <X className="h-4 w-4" />
        </button>
        <CardHeader>
          <CardTitle>{isEdit ? "Edit listing" : "Create listing"}</CardTitle>
          <CardDescription>
            Nutrition values are per serving/unit and are used to filter
            buyers&rsquo; searches.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <Field label="Name *" value={draft.name} onChange={(v) => set("name", v)} />
            <Field
              label="Price *"
              value={draft.price}
              onChange={(v) => set("price", v.replace(/[^0-9.]/g, ""))}
              placeholder="9.99"
              inputMode="decimal"
            />
            <Field label="Unit" value={draft.unit} onChange={(v) => set("unit", v)} placeholder="serving / kg / bag" />
            <Field
              label="Stock"
              value={draft.stock}
              onChange={(v) => set("stock", v.replace(/[^0-9]/g, ""))}
              inputMode="numeric"
            />
            <Field
              label="Serving size"
              value={draft.serving_size}
              onChange={(v) => set("serving_size", v)}
              placeholder="100 g"
            />
          </div>
          <ImageUploader
            value={draft.image_url}
            onChange={(v) => set("image_url", v)}
          />
          <label className="flex flex-col gap-1 text-xs font-medium text-foreground/80">
            Description
            <textarea
              value={draft.description}
              onChange={(e) => set("description", e.target.value)}
              rows={3}
              className="resize-none rounded-md border border-input bg-background px-2 py-1.5 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </label>
          <Field
            label="Tags (comma separated)"
            value={draft.tags}
            onChange={(v) => set("tags", v)}
            placeholder="vegan, high-protein, organic"
          />
          <div>
            <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Nutrition per {draft.unit || "serving"}
            </p>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <Field label="Calories" value={draft.calories} onChange={(v) => set("calories", v.replace(/[^0-9.]/g, ""))} inputMode="decimal" />
              <Field label="Protein (g)" value={draft.protein} onChange={(v) => set("protein", v.replace(/[^0-9.]/g, ""))} inputMode="decimal" />
              <Field label="Carbs (g)" value={draft.carbs} onChange={(v) => set("carbs", v.replace(/[^0-9.]/g, ""))} inputMode="decimal" />
              <Field label="Fat (g)" value={draft.fat} onChange={(v) => set("fat", v.replace(/[^0-9.]/g, ""))} inputMode="decimal" />
              <Field label="Fiber (g)" value={draft.fiber} onChange={(v) => set("fiber", v.replace(/[^0-9.]/g, ""))} inputMode="decimal" />
              <Field label="Sugar (g)" value={draft.sugar} onChange={(v) => set("sugar", v.replace(/[^0-9.]/g, ""))} inputMode="decimal" />
              <Field label="Sodium (mg)" value={draft.sodium} onChange={(v) => set("sodium", v.replace(/[^0-9.]/g, ""))} inputMode="decimal" />
            </div>
          </div>
          {error && (
            <p className="flex items-center gap-1 text-sm text-destructive">
              <AlertCircle className="h-4 w-4" />
              {error}
            </p>
          )}
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={onClose} disabled={saving}>
              Cancel
            </Button>
            <Button onClick={onSave} disabled={saving} className="gap-2">
              {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
              {isEdit ? "Save changes" : "Create listing"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

function Field({
  label,
  value,
  onChange,
  placeholder,
  inputMode,
}: {
  label: string
  value: string
  onChange: (v: string) => void
  placeholder?: string
  inputMode?: "decimal" | "numeric" | "text"
}) {
  return (
    <label className="flex flex-col gap-1 text-xs font-medium text-foreground/80">
      {label}
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        inputMode={inputMode}
        className="rounded-md border border-input bg-background px-2 py-1.5 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-ring"
      />
    </label>
  )
}

const MAX_IMAGE_BYTES = 5 * 1024 * 1024
const ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp", "image/gif"]

function ImageUploader({
  value,
  onChange,
}: {
  value: string
  onChange: (url: string) => void
}) {
  const inputRef = useRef<HTMLInputElement | null>(null)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [urlMode, setUrlMode] = useState(false)

  const pickFile = () => inputRef.current?.click()

  const handleFile = async (file: File | null) => {
    if (!file) return
    setError(null)
    if (!ALLOWED_IMAGE_TYPES.includes(file.type)) {
      setError("Please pick a JPEG, PNG, WEBP or GIF image.")
      return
    }
    if (file.size > MAX_IMAGE_BYTES) {
      setError(`Image is too large (max ${MAX_IMAGE_BYTES / (1024 * 1024)} MB).`)
      return
    }
    setUploading(true)
    try {
      const result = await marketplaceAPI.uploadImage(file)
      onChange(result.url)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed")
    } finally {
      setUploading(false)
      if (inputRef.current) inputRef.current.value = ""
    }
  }

  const clearImage = () => {
    onChange("")
    setError(null)
  }

  const hasImage = !!value.trim()

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-foreground/80">Product image</span>
        {hasImage && (
          <button
            type="button"
            onClick={clearImage}
            className="text-xs text-muted-foreground hover:text-destructive"
          >
            Remove
          </button>
        )}
      </div>

      <input
        ref={inputRef}
        type="file"
        accept={ALLOWED_IMAGE_TYPES.join(",")}
        className="hidden"
        onChange={(e) => void handleFile(e.target.files?.[0] ?? null)}
      />

      <div className="flex items-stretch gap-3">
        <div
          onClick={pickFile}
          className={cn(
            "flex h-28 w-28 shrink-0 cursor-pointer items-center justify-center overflow-hidden rounded-md border border-dashed",
            hasImage ? "border-border bg-muted" : "border-input bg-muted/40 hover:border-primary/40"
          )}
          title="Click to upload an image"
        >
          {hasImage ? (
            /* eslint-disable-next-line @next/next/no-img-element */
            <img src={value} alt="Listing preview" className="h-full w-full object-cover" />
          ) : (
            <div className="flex flex-col items-center gap-1 text-muted-foreground">
              <ImageIcon className="h-6 w-6" />
              <span className="text-[10px]">No image</span>
            </div>
          )}
        </div>

        <div className="flex flex-1 flex-col justify-between">
          <div className="flex flex-wrap gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={pickFile}
              disabled={uploading}
              className="gap-2"
            >
              {uploading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Upload className="h-4 w-4" />
              )}
              {uploading ? "Uploading..." : hasImage ? "Replace image" : "Upload from computer"}
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => setUrlMode((v) => !v)}
              className="text-muted-foreground"
            >
              {urlMode ? "Hide URL" : "or paste URL"}
            </Button>
          </div>

          {urlMode && (
            <input
              value={value}
              onChange={(e) => onChange(e.target.value)}
              placeholder="https://..."
              className="mt-2 rounded-md border border-input bg-background px-2 py-1.5 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
          )}

          <p className="mt-2 text-[11px] text-muted-foreground">
            JPEG, PNG, WEBP or GIF. Up to 5 MB.
          </p>
        </div>
      </div>

      {error && (
        <p className="flex items-center gap-1 text-xs text-destructive">
          <AlertCircle className="h-3.5 w-3.5" />
          {error}
        </p>
      )}
    </div>
  )
}
