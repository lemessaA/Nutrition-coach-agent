"use client"

import { Suspense, useCallback, useEffect, useMemo, useState } from "react"
import Link from "next/link"
import { useSearchParams } from "next/navigation"
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
  Receipt,
  Clock,
  CheckCircle2,
  XCircle,
  PackageCheck,
  Loader2,
  AlertCircle,
  ShoppingBasket,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { useUser } from "@/lib/user-context"
import {
  marketplaceAPI,
  type MarketplaceOrder,
  type OrderStatus,
} from "@/services/api"

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

function BuyerOrdersContent() {
  const { userId, ready } = useUser()
  const searchParams = useSearchParams()
  const highlightId = Number(searchParams.get("highlight")) || null

  const [orders, setOrders] = useState<MarketplaceOrder[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState<OrderStatus | "all">("all")
  const [cancellingId, setCancellingId] = useState<number | null>(null)

  const load = useCallback(async () => {
    if (!userId) return
    setLoading(true)
    setError(null)
    try {
      const list = await marketplaceAPI.listOrders(userId, "buyer")
      setOrders(list)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load orders")
    } finally {
      setLoading(false)
    }
  }, [userId])

  useEffect(() => {
    void load()
  }, [load])

  const filtered = useMemo(() => {
    return statusFilter === "all"
      ? orders
      : orders.filter((o) => o.status === statusFilter)
  }, [orders, statusFilter])

  const cancelOrder = async (orderId: number) => {
    if (!userId) return
    if (!window.confirm("Cancel this order?")) return
    setCancellingId(orderId)
    try {
      await marketplaceAPI.updateOrderStatus(userId, orderId, "cancelled")
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not cancel order")
    } finally {
      setCancellingId(null)
    }
  }

  if (!ready) {
    return (
      <div className="container mx-auto max-w-3xl px-4 py-12 text-center text-muted-foreground">
        Loading...
      </div>
    )
  }

  if (!userId) {
    return (
      <div className="container mx-auto max-w-md px-4 py-16 text-center">
        <Receipt className="mx-auto mb-4 h-12 w-12 text-muted-foreground" />
        <h1 className="text-2xl font-bold">Sign in to see your orders</h1>
        <p className="mt-2 text-muted-foreground">
          Your order history lives with your profile.
        </p>
        <Link href="/profile" className="mt-4 inline-block">
          <Button>Go to profile</Button>
        </Link>
      </div>
    )
  }

  const filters: { value: OrderStatus | "all"; label: string }[] = [
    { value: "all", label: "All" },
    { value: "pending", label: "Pending" },
    { value: "confirmed", label: "Confirmed" },
    { value: "fulfilled", label: "Fulfilled" },
    { value: "cancelled", label: "Cancelled" },
  ]

  return (
    <div className="container mx-auto max-w-3xl px-4 py-8">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">My orders</h1>
          <p className="text-muted-foreground">
            Track what you&rsquo;ve ordered from sellers on the marketplace.
          </p>
        </div>
        <Link href="/marketplace">
          <Button variant="outline" className="gap-2">
            <ShoppingBasket className="h-4 w-4" />
            Keep shopping
          </Button>
        </Link>
      </div>

      <div className="mb-4 flex flex-wrap gap-2">
        {filters.map((f) => (
          <button
            key={f.value}
            onClick={() => setStatusFilter(f.value)}
            className={cn(
              "rounded-full border px-3 py-1 text-xs font-medium transition-colors",
              statusFilter === f.value
                ? "border-primary bg-primary text-primary-foreground"
                : "border-border bg-background text-foreground/70 hover:border-primary/40"
            )}
          >
            {f.label}
          </button>
        ))}
      </div>

      {error && (
        <Card className="mb-4 border-destructive/60">
          <CardContent className="flex items-center gap-2 py-3 text-sm text-destructive">
            <AlertCircle className="h-4 w-4" />
            {error}
          </CardContent>
        </Card>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-16 text-muted-foreground">
          <Loader2 className="mr-2 h-5 w-5 animate-spin" />
          Loading orders...
        </div>
      ) : filtered.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Receipt className="mx-auto mb-3 h-10 w-10 text-muted-foreground" />
            <p className="font-medium">No orders yet.</p>
            <p className="mt-1 text-sm text-muted-foreground">
              Browse the marketplace to place your first order.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {filtered.map((order) => {
            const meta = statusMeta(order.status)
            const Icon = meta.icon
            const highlighted = highlightId === order.id
            return (
              <Card
                key={order.id}
                className={cn(
                  "transition-all",
                  highlighted && "ring-2 ring-primary"
                )}
              >
                <CardHeader className="pb-3">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <CardTitle className="text-base">
                        Order #{order.id} • {order.seller_name ?? "Seller"}
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
                    {order.items.map((item) => {
                      const n = item.listing_nutrition
                      return (
                        <li
                          key={item.id}
                          className="flex flex-wrap items-baseline justify-between gap-2"
                        >
                          <span>
                            {item.quantity}× {item.name_snapshot}
                          </span>
                          <span className="flex items-center gap-2">
                            {n?.protein != null && (
                              <Badge
                                variant="secondary"
                                className="text-[10px]"
                              >
                                {Math.round(n.protein)}g protein
                              </Badge>
                            )}
                            <span className="text-muted-foreground">
                              ${(item.unit_price * item.quantity).toFixed(2)}
                            </span>
                          </span>
                        </li>
                      )
                    })}
                  </ul>
                  <div className="mt-3 flex items-center justify-between border-t border-border pt-3 text-sm">
                    <span className="font-semibold">Total</span>
                    <span className="font-semibold">
                      ${order.total_price.toFixed(2)}
                    </span>
                  </div>
                  {order.notes && (
                    <p className="mt-2 rounded-md bg-muted px-3 py-2 text-xs italic text-foreground/80">
                      “{order.notes}”
                    </p>
                  )}
                  {order.status === "pending" && (
                    <div className="mt-3 flex justify-end">
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={cancellingId === order.id}
                        onClick={() => cancelOrder(order.id)}
                        className="gap-1 text-destructive hover:text-destructive"
                      >
                        {cancellingId === order.id ? (
                          <Loader2 className="h-3.5 w-3.5 animate-spin" />
                        ) : (
                          <XCircle className="h-3.5 w-3.5" />
                        )}
                        Cancel order
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}

export default function BuyerOrdersPage() {
  return (
    <Suspense
      fallback={
        <div className="container mx-auto max-w-3xl px-4 py-12 text-center text-muted-foreground">
          <Loader2 className="mx-auto h-5 w-5 animate-spin" />
        </div>
      }
    >
      <BuyerOrdersContent />
    </Suspense>
  )
}
