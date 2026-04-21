"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  ShoppingCart,
  Search,
  X,
  Loader2,
  Minus,
  Plus,
  AlertCircle,
  SlidersHorizontal,
  Flame,
  Drumstick,
  Wheat,
  Leaf,
  Receipt,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { useUser } from "@/lib/user-context"
import {
  marketplaceAPI,
  type FoodListing,
  type ListingSearchFilters,
} from "@/services/api"

type CartLine = {
  listingId: number
  name: string
  sellerName?: string | null
  unitPrice: number
  quantity: number
  imageUrl?: string | null
  maxStock: number
}

const CART_KEY = "nutrition-coach.marketplace.cart"

const SORT_OPTIONS: { value: NonNullable<ListingSearchFilters["sort_by"]>; label: string }[] = [
  { value: "newest", label: "Newest" },
  { value: "protein_per_dollar", label: "Best protein per $" },
  { value: "price_asc", label: "Price: low → high" },
  { value: "price_desc", label: "Price: high → low" },
]

const TAG_CHIPS = [
  "vegan",
  "vegetarian",
  "gluten-free",
  "high-protein",
  "high-fiber",
  "low-sugar",
  "organic",
  "keto",
]

function loadCart(): CartLine[] {
  if (typeof window === "undefined") return []
  try {
    const raw = window.localStorage.getItem(CART_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

function saveCart(cart: CartLine[]) {
  if (typeof window === "undefined") return
  try {
    window.localStorage.setItem(CART_KEY, JSON.stringify(cart))
  } catch {
    /* ignore */
  }
}

function formatPrice(value: number) {
  return `$${value.toFixed(2)}`
}

function NutrientPill({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ComponentType<{ className?: string }>
  label: string
  value: number | null | undefined
}) {
  if (value == null) return null
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-muted/70 px-2 py-0.5 text-xs text-foreground/80">
      <Icon className="h-3 w-3" />
      <span className="font-medium">{Math.round(value)}</span>
      <span className="text-muted-foreground">{label}</span>
    </span>
  )
}

export default function MarketplacePage() {
  const router = useRouter()
  const { userId, ready, isBuyer } = useUser()

  // --- search / filter state ---
  const [q, setQ] = useState("")
  const [debouncedQ, setDebouncedQ] = useState("")
  const [tags, setTags] = useState<string[]>([])
  const [minProtein, setMinProtein] = useState<string>("")
  const [maxSugar, setMaxSugar] = useState<string>("")
  const [minFiber, setMinFiber] = useState<string>("")
  const [maxCalories, setMaxCalories] = useState<string>("")
  const [maxPrice, setMaxPrice] = useState<string>("")
  const [sortBy, setSortBy] =
    useState<NonNullable<ListingSearchFilters["sort_by"]>>("newest")
  const [showFilters, setShowFilters] = useState(false)

  // --- data state ---
  const [listings, setListings] = useState<FoodListing[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // --- cart state ---
  const [cart, setCart] = useState<CartLine[]>([])
  const [cartOpen, setCartOpen] = useState(false)
  const [placingOrder, setPlacingOrder] = useState(false)
  const [orderError, setOrderError] = useState<string | null>(null)
  const [orderNotes, setOrderNotes] = useState("")

  useEffect(() => {
    setCart(loadCart())
  }, [])

  useEffect(() => {
    saveCart(cart)
  }, [cart])

  useEffect(() => {
    const t = setTimeout(() => setDebouncedQ(q.trim()), 250)
    return () => clearTimeout(t)
  }, [q])

  const filters = useMemo<ListingSearchFilters>(() => {
    const toNum = (s: string) => {
      const v = parseFloat(s)
      return Number.isFinite(v) ? v : undefined
    }
    return {
      q: debouncedQ || undefined,
      tags: tags.length ? tags : undefined,
      min_protein: toNum(minProtein),
      max_sugar: toNum(maxSugar),
      min_fiber: toNum(minFiber),
      max_calories: toNum(maxCalories),
      max_price: toNum(maxPrice),
      sort_by: sortBy,
      in_stock_only: true,
    }
  }, [
    debouncedQ,
    tags,
    minProtein,
    maxSugar,
    minFiber,
    maxCalories,
    maxPrice,
    sortBy,
  ])

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const results = await marketplaceAPI.searchListings(filters)
      setListings(results)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load listings")
    } finally {
      setLoading(false)
    }
  }, [filters])

  useEffect(() => {
    void load()
  }, [load])

  const toggleTag = (tag: string) => {
    setTags((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]
    )
  }

  const clearFilters = () => {
    setQ("")
    setTags([])
    setMinProtein("")
    setMaxSugar("")
    setMinFiber("")
    setMaxCalories("")
    setMaxPrice("")
    setSortBy("newest")
  }

  const addToCart = (listing: FoodListing) => {
    if (listing.stock <= 0) return
    setCart((prev) => {
      const existing = prev.find((l) => l.listingId === listing.id)
      if (existing) {
        if (existing.quantity >= listing.stock) return prev
        return prev.map((l) =>
          l.listingId === listing.id ? { ...l, quantity: l.quantity + 1 } : l
        )
      }
      return [
        ...prev,
        {
          listingId: listing.id,
          name: listing.name,
          sellerName: listing.seller_name,
          unitPrice: listing.price,
          quantity: 1,
          imageUrl: listing.image_url,
          maxStock: listing.stock,
        },
      ]
    })
    setCartOpen(true)
  }

  const updateQty = (listingId: number, delta: number) => {
    setCart((prev) =>
      prev
        .map((l) =>
          l.listingId === listingId
            ? {
                ...l,
                quantity: Math.max(
                  0,
                  Math.min(l.maxStock, l.quantity + delta)
                ),
              }
            : l
        )
        .filter((l) => l.quantity > 0)
    )
  }

  const removeFromCart = (listingId: number) => {
    setCart((prev) => prev.filter((l) => l.listingId !== listingId))
  }

  const cartTotal = useMemo(
    () => cart.reduce((sum, l) => sum + l.quantity * l.unitPrice, 0),
    [cart]
  )
  const cartCount = useMemo(
    () => cart.reduce((sum, l) => sum + l.quantity, 0),
    [cart]
  )

  const placeOrder = async () => {
    if (!userId) {
      setOrderError("Please sign in to place an order.")
      return
    }
    if (cart.length === 0) return
    setPlacingOrder(true)
    setOrderError(null)
    try {
      const orders = await marketplaceAPI.createOrder(userId, {
        items: cart.map((l) => ({
          listing_id: l.listingId,
          quantity: l.quantity,
        })),
        notes: orderNotes || undefined,
      })
      setCart([])
      setOrderNotes("")
      setCartOpen(false)
      router.push(
        orders.length === 1
          ? `/marketplace/orders?highlight=${orders[0].id}`
          : "/marketplace/orders"
      )
    } catch (err) {
      setOrderError(err instanceof Error ? err.message : "Failed to place order")
    } finally {
      setPlacingOrder(false)
    }
  }

  const showEmptyState = !loading && listings.length === 0

  return (
    <div className="container mx-auto max-w-6xl px-4 py-8">
      {/* Header */}
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">Food Marketplace</h1>
          <p className="text-muted-foreground">
            Shop whole foods from sellers near you. Filter by the nutrients your
            goals actually need.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {ready && userId && (
            <Link href="/marketplace/orders">
              <Button variant="outline" size="sm" className="gap-2">
                <Receipt className="h-4 w-4" />
                My Orders
              </Button>
            </Link>
          )}
          <Button
            onClick={() => setCartOpen(true)}
            size="sm"
            className="relative gap-2"
            disabled={!ready}
          >
            <ShoppingCart className="h-4 w-4" />
            Cart
            {cartCount > 0 && (
              <span className="ml-1 inline-flex h-5 min-w-[1.25rem] items-center justify-center rounded-full bg-background px-1 text-xs font-semibold text-primary">
                {cartCount}
              </span>
            )}
          </Button>
        </div>
      </div>

      {/* Search bar */}
      <div className="mb-4 flex flex-col gap-3 sm:flex-row">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="search"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search oats, chicken, berries..."
            className="w-full rounded-lg border border-input bg-background py-2.5 pl-10 pr-3 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>
        <select
          value={sortBy}
          onChange={(e) =>
            setSortBy(
              e.target.value as NonNullable<ListingSearchFilters["sort_by"]>
            )
          }
          className="rounded-lg border border-input bg-background px-3 py-2.5 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-ring"
        >
          {SORT_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              Sort: {o.label}
            </option>
          ))}
        </select>
        <Button
          variant="outline"
          onClick={() => setShowFilters((v) => !v)}
          className="gap-2"
        >
          <SlidersHorizontal className="h-4 w-4" />
          Filters
          {(tags.length > 0 ||
            minProtein ||
            maxSugar ||
            minFiber ||
            maxCalories ||
            maxPrice) && (
            <span className="ml-1 rounded-full bg-primary/20 px-1.5 text-xs text-primary">
              on
            </span>
          )}
        </Button>
      </div>

      {/* Tag chips */}
      <div className="mb-3 flex flex-wrap gap-2">
        {TAG_CHIPS.map((tag) => {
          const active = tags.includes(tag)
          return (
            <button
              key={tag}
              type="button"
              onClick={() => toggleTag(tag)}
              className={cn(
                "rounded-full border px-3 py-1 text-xs font-medium transition-colors",
                active
                  ? "border-primary bg-primary text-primary-foreground"
                  : "border-border bg-background text-foreground/70 hover:border-primary/40 hover:text-foreground"
              )}
            >
              {tag}
            </button>
          )
        })}
      </div>

      {/* Advanced filters */}
      {showFilters && (
        <Card className="mb-6">
          <CardContent className="grid grid-cols-1 gap-3 pt-6 sm:grid-cols-2 lg:grid-cols-5">
            <FilterInput
              label="Min protein (g)"
              value={minProtein}
              onChange={setMinProtein}
            />
            <FilterInput
              label="Min fiber (g)"
              value={minFiber}
              onChange={setMinFiber}
            />
            <FilterInput
              label="Max sugar (g)"
              value={maxSugar}
              onChange={setMaxSugar}
            />
            <FilterInput
              label="Max calories"
              value={maxCalories}
              onChange={setMaxCalories}
            />
            <FilterInput
              label="Max price ($)"
              value={maxPrice}
              onChange={setMaxPrice}
            />
            <div className="sm:col-span-2 lg:col-span-5 flex justify-end">
              <Button variant="ghost" size="sm" onClick={clearFilters}>
                Clear filters
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Results */}
      {loading && (
        <div className="flex items-center justify-center py-20 text-muted-foreground">
          <Loader2 className="mr-2 h-5 w-5 animate-spin" />
          Loading listings...
        </div>
      )}

      {error && (
        <Card className="mb-6 border-destructive/60">
          <CardContent className="flex items-center gap-2 py-4 text-sm text-destructive">
            <AlertCircle className="h-4 w-4" />
            {error}
          </CardContent>
        </Card>
      )}

      {showEmptyState && (
        <Card>
          <CardContent className="py-16 text-center">
            <p className="text-lg font-semibold">No listings match your filters.</p>
            <p className="mt-1 text-sm text-muted-foreground">
              Try clearing some filters or check back later.
            </p>
            <Button variant="outline" className="mt-4" onClick={clearFilters}>
              Clear filters
            </Button>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {listings.map((listing) => (
          <ListingCard
            key={listing.id}
            listing={listing}
            onAddToCart={() => addToCart(listing)}
            disabled={!isBuyer && !!userId}
          />
        ))}
      </div>

      {/* Cart drawer */}
      <CartDrawer
        open={cartOpen}
        onClose={() => setCartOpen(false)}
        cart={cart}
        onIncrement={(id) => updateQty(id, 1)}
        onDecrement={(id) => updateQty(id, -1)}
        onRemove={removeFromCart}
        onCheckout={placeOrder}
        total={cartTotal}
        notes={orderNotes}
        onNotesChange={setOrderNotes}
        placing={placingOrder}
        error={orderError}
        signedIn={!!userId}
      />
    </div>
  )
}

function FilterInput({
  label,
  value,
  onChange,
}: {
  label: string
  value: string
  onChange: (v: string) => void
}) {
  return (
    <label className="flex flex-col gap-1 text-xs font-medium text-foreground/80">
      {label}
      <input
        inputMode="decimal"
        value={value}
        onChange={(e) => onChange(e.target.value.replace(/[^0-9.]/g, ""))}
        placeholder="—"
        className="rounded-md border border-input bg-background px-2 py-1.5 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-ring"
      />
    </label>
  )
}

function ListingCard({
  listing,
  onAddToCart,
  disabled,
}: {
  listing: FoodListing
  onAddToCart: () => void
  disabled?: boolean
}) {
  const hasImage = !!listing.image_url
  return (
    <Card className="flex h-full flex-col overflow-hidden">
      <div className="relative aspect-[4/3] w-full bg-muted">
        {hasImage ? (
          /* eslint-disable-next-line @next/next/no-img-element */
          <img
            src={listing.image_url!}
            alt={listing.name}
            className="h-full w-full object-cover"
            loading="lazy"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-emerald-100 to-sky-100 dark:from-emerald-900/40 dark:to-sky-900/40">
            <Leaf className="h-10 w-10 text-emerald-600 dark:text-emerald-300" />
          </div>
        )}
        {listing.stock <= 3 && listing.stock > 0 && (
          <Badge className="absolute right-2 top-2 bg-amber-500 text-white hover:bg-amber-500">
            Only {listing.stock} left
          </Badge>
        )}
      </div>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-start justify-between gap-2 text-base">
          <span className="line-clamp-2">{listing.name}</span>
          <span className="shrink-0 text-primary">
            {formatPrice(listing.price)}
          </span>
        </CardTitle>
        <CardDescription className="flex flex-wrap items-center gap-2 text-xs">
          <span>by {listing.seller_name ?? "Seller"}</span>
          <span className="text-muted-foreground/60">•</span>
          <span>
            {listing.stock} / {listing.unit}
          </span>
          {listing.serving_size && (
            <>
              <span className="text-muted-foreground/60">•</span>
              <span>{listing.serving_size}</span>
            </>
          )}
        </CardDescription>
      </CardHeader>
      <CardContent className="flex-1 pb-3">
        {listing.description && (
          <p className="mb-3 line-clamp-2 text-sm text-muted-foreground">
            {listing.description}
          </p>
        )}
        <div className="flex flex-wrap gap-1.5">
          <NutrientPill icon={Flame} label="kcal" value={listing.calories} />
          <NutrientPill icon={Drumstick} label="g P" value={listing.protein} />
          <NutrientPill icon={Wheat} label="g C" value={listing.carbs} />
        </div>
        {listing.tags.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1">
            {listing.tags.slice(0, 4).map((tag) => (
              <Badge key={tag} variant="secondary" className="text-[10px]">
                {tag}
              </Badge>
            ))}
          </div>
        )}
      </CardContent>
      <CardFooter>
        <Button
          onClick={onAddToCart}
          className="w-full gap-2"
          disabled={listing.stock <= 0 || disabled}
        >
          <Plus className="h-4 w-4" />
          {listing.stock <= 0 ? "Out of stock" : "Add to cart"}
        </Button>
      </CardFooter>
    </Card>
  )
}

function CartDrawer({
  open,
  onClose,
  cart,
  onIncrement,
  onDecrement,
  onRemove,
  onCheckout,
  total,
  notes,
  onNotesChange,
  placing,
  error,
  signedIn,
}: {
  open: boolean
  onClose: () => void
  cart: CartLine[]
  onIncrement: (id: number) => void
  onDecrement: (id: number) => void
  onRemove: (id: number) => void
  onCheckout: () => void
  total: number
  notes: string
  onNotesChange: (v: string) => void
  placing: boolean
  error: string | null
  signedIn: boolean
}) {
  return (
    <>
      {open && (
        <div
          className="fixed inset-0 z-40 bg-background/70 backdrop-blur-sm"
          onClick={onClose}
          aria-hidden
        />
      )}
      <aside
        className={cn(
          "fixed right-0 top-0 z-50 flex h-dvh w-full max-w-md flex-col border-l border-border bg-background shadow-2xl transition-transform duration-200",
          open ? "translate-x-0" : "translate-x-full"
        )}
        aria-hidden={!open}
      >
        <div className="flex items-center justify-between border-b border-border px-4 py-3">
          <h2 className="text-lg font-semibold">Your cart</h2>
          <button
            onClick={onClose}
            className="rounded-md p-2 text-muted-foreground hover:bg-muted hover:text-foreground"
            aria-label="Close cart"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-4 py-4">
          {cart.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center text-center text-sm text-muted-foreground">
              <ShoppingCart className="mb-3 h-10 w-10 opacity-50" />
              Your cart is empty.
            </div>
          ) : (
            <ul className="space-y-3">
              {cart.map((line) => (
                <li
                  key={line.listingId}
                  className="flex gap-3 rounded-lg border border-border bg-card p-3"
                >
                  <div className="flex h-14 w-14 shrink-0 items-center justify-center overflow-hidden rounded-md bg-muted">
                    {line.imageUrl ? (
                      /* eslint-disable-next-line @next/next/no-img-element */
                      <img
                        src={line.imageUrl}
                        alt=""
                        className="h-full w-full object-cover"
                      />
                    ) : (
                      <Leaf className="h-6 w-6 text-muted-foreground" />
                    )}
                  </div>
                  <div className="flex flex-1 flex-col">
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <p className="truncate text-sm font-medium">{line.name}</p>
                        <p className="text-xs text-muted-foreground">
                          {line.sellerName ?? "Seller"} •{" "}
                          {formatPrice(line.unitPrice)}
                        </p>
                      </div>
                      <button
                        className="text-muted-foreground hover:text-destructive"
                        onClick={() => onRemove(line.listingId)}
                        aria-label="Remove"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                    <div className="mt-2 flex items-center justify-between">
                      <div className="inline-flex items-center gap-1 rounded-md border border-border">
                        <button
                          onClick={() => onDecrement(line.listingId)}
                          className="px-2 py-1 text-foreground/70 hover:bg-muted"
                        >
                          <Minus className="h-3.5 w-3.5" />
                        </button>
                        <span className="min-w-[1.5rem] text-center text-sm font-medium">
                          {line.quantity}
                        </span>
                        <button
                          onClick={() => onIncrement(line.listingId)}
                          className="px-2 py-1 text-foreground/70 hover:bg-muted disabled:opacity-40"
                          disabled={line.quantity >= line.maxStock}
                        >
                          <Plus className="h-3.5 w-3.5" />
                        </button>
                      </div>
                      <span className="text-sm font-semibold">
                        {formatPrice(line.quantity * line.unitPrice)}
                      </span>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="border-t border-border px-4 py-3">
          {cart.length > 0 && (
            <label className="mb-3 block text-xs font-medium text-foreground/80">
              Order notes (optional)
              <textarea
                value={notes}
                onChange={(e) => onNotesChange(e.target.value)}
                rows={2}
                placeholder="Delivery instructions, preferences, ..."
                className="mt-1 block w-full resize-none rounded-md border border-input bg-background px-2 py-1.5 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </label>
          )}
          <div className="mb-3 flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Total</span>
            <span className="text-lg font-semibold">{formatPrice(total)}</span>
          </div>
          {error && (
            <p className="mb-2 flex items-center gap-1 text-xs text-destructive">
              <AlertCircle className="h-3.5 w-3.5" />
              {error}
            </p>
          )}
          {!signedIn && cart.length > 0 && (
            <p className="mb-2 text-xs text-muted-foreground">
              Sign in from the navbar to complete your order.
            </p>
          )}
          <Button
            className="w-full gap-2"
            onClick={onCheckout}
            disabled={cart.length === 0 || placing || !signedIn}
          >
            {placing ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Placing order...
              </>
            ) : (
              <>Place order</>
            )}
          </Button>
        </div>
      </aside>
    </>
  )
}
