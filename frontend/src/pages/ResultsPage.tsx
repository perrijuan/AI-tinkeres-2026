import { useEffect, useRef, useState } from "react"
import { Link, useLocation } from "react-router-dom"
import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Legend,
} from "recharts"
import { MapContainer, TileLayer, Polygon } from "react-leaflet"
import "leaflet/dist/leaflet.css"
import {
  ArrowLeft,
  CloudRain,
  Thermometer,
  Droplets,
  Wind,
  Satellite,
  FileText,
  Clock,
  AlertTriangle,
  CheckCircle2,
  Sprout,
  ChevronDown,
  MessageCircle,
  X,
  Send,
  Loader2,
  Maximize2,
  Minimize2,
  CalendarRange,
  MapPinned,
  ShieldAlert,
  ShieldCheck,
  Activity,
  CircleHelp,
  Sparkles,
  Bot,
} from "lucide-react"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import {
  Tooltip as InfoTooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { cn } from "@/lib/utils"
import { API_ENDPOINTS } from "@/config"
import ReactMarkdown from "react-markdown"

// ── Tipos ────────────────────────────────────────────────────────────────────

interface AnalysisData {
  field_info: {
    field_id: string
    property_name: string
    culture: string
    municipio: string
    uf: string
    area_ha: number
    irrigated: boolean
    sowing_date: string
    crop_stage: string
  }
  summary: {
    risk_score: number
    risk_level: string
    primary_alert: string
    recommended_action: string
    analysis_timestamp: string
    forecast_run_timestamp: string
  }
  metrics: {
    precip_forecast_7d_mm: number
    precip_forecast_14d_mm: number
    temp_mean_7d_c: number
    temp_max_7d_c: number
    humidity_mean_7d_pct: number
    wind_mean_7d_ms: number
  }
  risk_flags: {
    dry_risk_flag: boolean
    heat_risk_flag: boolean
    outside_zarc_flag: boolean
    vegetation_stress_flag: boolean
  }
  data_sources: {
    climate: { provider: string; model: string; coverage: string; signals: string[] }
    satellite: {
      provider: string
      last_image: string
      cloud_cover_pct: number
      signals: string[]
      ndvi_timeseries: { date: string; ndvi: number }[]
    }
    zarc: {
      provider: string
      zarc_class: number
      zarc_label: string
      planting_within_window: boolean
      signals: string[]
    }
    historical: { provider: string; period: string; signals: string[] }
  }
  forecast_timeseries: {
    forecast_time: string
    precip_mm: number
    temp_c: number
    humidity_pct: number
  }[]
  copilot_response: {
    summary: string
    why: string[]
    action: string
  }
  map_layer: {
    geometry: {
      type: string
      coordinates: number[][][]
    }
    fill_color: string
    stroke_color: string
    tooltip_summary: string
  }
  conversation_id?: string
}

interface ChatMessage {
  role: "user" | "assistant"
  content: string
}

const LOADING_MESSAGES = [
  "Analisando o polígono da área e validando o recorte territorial…",
  "Consultando sinais climáticos para os próximos 14 dias…",
  "Processando indicadores de satélite e vigor da vegetação…",
  "Conferindo aderência à janela ZARC para a cultura informada…",
  "Calculando score de risco e organizando alertas principais…",
  "Montando o resumo da Safrinia para facilitar a leitura da área…",
]

const MIN_LOADING_MS = 3000

// ── Helpers ───────────────────────────────────────────────────────────────────

const RISK_CONFIG: Record<string, { label: string; color: string; bg: string; border: string; scoreColor: string }> = {
  baixo:    { label: "Baixo",    color: "text-emerald-700", bg: "bg-emerald-50", border: "border-emerald-200", scoreColor: "#16a34a" },
  moderado: { label: "Moderado", color: "text-amber-700",   bg: "bg-amber-50",   border: "border-amber-200",   scoreColor: "#d97706" },
  alto:     { label: "Alto",     color: "text-red-700",     bg: "bg-red-50",     border: "border-red-200",     scoreColor: "#dc2626" },
  crítico:  { label: "Crítico",  color: "text-red-900",     bg: "bg-red-100",    border: "border-red-300",     scoreColor: "#7f1d1d" },
}

function fmtDate(iso: string) {
  return new Date(iso).toLocaleDateString("pt-BR", { day: "2-digit", month: "short" })
}

function fmtDateTime(iso: string) {
  return new Date(iso).toLocaleString("pt-BR", {
    day: "2-digit", month: "2-digit", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  })
}

function cultureName(id: string) {
  const map: Record<string, string> = {
    soja: "Soja", milho: "Milho", algodao: "Algodão",
    arroz: "Arroz", feijao: "Feijão", trigo: "Trigo",
    cana: "Cana-de-açúcar", girassol: "Girassol",
  }
  return map[id] ?? id
}

function stageName(id: string) {
  const map: Record<string, string> = {
    enchimento_de_graos: "Enchimento de grãos",
    germinacao: "Germinação",
    vegetativo: "Vegetativo",
    florescimento: "Florescimento",
    maturacao: "Maturação",
  }
  return map[id] ?? id
}

function fmtValue(value: number, digits = 0) {
  return value.toLocaleString("pt-BR", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })
}

function clamp(value: number, min: number, max: number) {
  return Math.max(min, Math.min(max, value))
}

function riskTone(active: boolean) {
  return active
    ? "bg-red-50 text-red-700 border-red-200"
    : "bg-emerald-50 text-emerald-700 border-emerald-200"
}

function normalizeMetric(value: number, max: number) {
  return clamp((value / max) * 100, 6, 100)
}

function forecastLabel(precip: number, temp: number) {
  if (precip < 3 && temp >= 33) return "Mais crítico"
  if (precip < 5) return "Seco"
  if (temp >= 32) return "Calor"
  return "Estável"
}

function HelpTooltip({ text }: { text: string }) {
  return (
    <InfoTooltip>
      <TooltipTrigger asChild>
        <button
          type="button"
          className="inline-flex h-5 w-5 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          aria-label="Explicar este bloco"
        >
          <CircleHelp className="h-3.5 w-3.5" />
        </button>
      </TooltipTrigger>
      <TooltipContent side="top" sideOffset={8} className="max-w-64">
        <p className="text-xs leading-relaxed">{text}</p>
      </TooltipContent>
    </InfoTooltip>
  )
}

// ── Sub-componentes ───────────────────────────────────────────────────────────

function MetricCard({
  icon: Icon,
  label,
  value,
  unit,
  sub,
  highlight,
}: {
  icon: React.ElementType
  label: string
  value: number
  unit: string
  sub?: string
  highlight?: boolean
}) {
  return (
    <Card className={cn("relative overflow-hidden", highlight && "border-red-200")}>
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-xs text-muted-foreground mb-1">{label}</p>
            <p className={cn("text-2xl font-bold", highlight ? "text-red-600" : "text-foreground")}>
              {value}
              <span className="text-sm font-normal text-muted-foreground ml-1">{unit}</span>
            </p>
            {sub && <p className="text-xs text-muted-foreground mt-0.5">{sub}</p>}
          </div>
          <div className={cn("p-2 rounded-lg", highlight ? "bg-red-50" : "bg-muted/50")}>
            <Icon className={cn("w-4 h-4", highlight ? "text-red-500" : "text-muted-foreground")} />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function FlagBadge({ active, label }: { active: boolean; label: string }) {
  return (
    <Badge
      variant={active ? "destructive" : "outline"}
      className={cn(
        "gap-1.5 text-xs",
        !active && "text-muted-foreground"
      )}
    >
      {active
        ? <AlertTriangle className="w-3 h-3" />
        : <CheckCircle2 className="w-3 h-3" />}
      {label}
    </Badge>
  )
}

function SourceCard({
  icon: Icon,
  title,
  subtitle,
  signals,
  defaultOpen = false,
}: {
  icon: React.ElementType
  title: string
  subtitle: string
  signals: string[]
  defaultOpen?: boolean
}) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <Card>
        <CollapsibleTrigger asChild>
          <CardHeader className="cursor-pointer hover:bg-muted/30 transition-colors rounded-t-xl pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-lg bg-primary/10">
                  <Icon className="w-4 h-4 text-primary" />
                </div>
                <div>
                  <CardTitle className="text-sm font-semibold">{title}</CardTitle>
                  <p className="text-xs text-muted-foreground mt-0.5">{subtitle}</p>
                </div>
              </div>
              <ChevronDown className={cn("w-4 h-4 text-muted-foreground transition-transform", open && "rotate-180")} />
            </div>
          </CardHeader>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <CardContent className="pt-0 pb-4">
            <Separator className="mb-3" />
            <ul className="space-y-2">
              {signals.map((s, i) => (
                <li key={i} className="flex gap-2 text-sm text-muted-foreground">
                  <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-primary/60 shrink-0" />
                  {s}
                </li>
              ))}
            </ul>
          </CardContent>
        </CollapsibleContent>
      </Card>
    </Collapsible>
  )
}

function SignalMeter({
  label,
  value,
  unit,
  progress,
  tone = "neutral",
  hint,
}: {
  label: string
  value: string
  unit?: string
  progress: number
  tone?: "neutral" | "alert" | "good"
  hint?: string
}) {
  const toneClass =
    tone === "alert"
      ? "bg-red-500"
      : tone === "good"
        ? "bg-emerald-500"
        : "bg-primary"

  return (
    <div className="space-y-2 rounded-xl border bg-card/70 p-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[11px] uppercase tracking-wide text-muted-foreground">{label}</p>
          <p className="text-lg font-semibold">
            {value}
            {unit && <span className="ml-1 text-sm font-normal text-muted-foreground">{unit}</span>}
          </p>
        </div>
        {hint && (
          <span className="max-w-26 text-right text-[11px] leading-tight text-muted-foreground">{hint}</span>
        )}
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-muted">
        <div className={cn("h-full rounded-full transition-all", toneClass)} style={{ width: `${progress}%` }} />
      </div>
    </div>
  )
}

function SummaryPanel({
  title,
  description,
  icon: Icon,
  tone = "neutral",
}: {
  title: string
  description: string
  icon: React.ElementType
  tone?: "neutral" | "alert" | "good"
}) {
  const toneClass =
    tone === "alert"
      ? "bg-red-50 border-red-200"
      : tone === "good"
        ? "bg-emerald-50 border-emerald-200"
        : "bg-card border-border"

  const iconTone =
    tone === "alert"
      ? "text-red-600 bg-red-100"
      : tone === "good"
        ? "text-emerald-600 bg-emerald-100"
        : "text-primary bg-primary/10"

  return (
    <div className={cn("rounded-xl border p-3", toneClass)}>
      <div className="mb-2 flex items-center gap-2">
        <div className={cn("rounded-lg p-2", iconTone)}>
          <Icon className="h-4 w-4" />
        </div>
        <p className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">{title}</p>
      </div>
      <p className="text-sm leading-relaxed text-foreground">{description}</p>
    </div>
  )
}

function ForecastTable({
  points,
}: {
  points: AnalysisData["forecast_timeseries"]
}) {
  const rows = points.slice(0, 5)

  return (
    <div className="overflow-hidden rounded-xl border">
      <table className="w-full text-left text-sm">
        <thead className="bg-muted/50 text-[11px] uppercase tracking-wide text-muted-foreground">
          <tr>
            <th className="px-3 py-2 font-medium">Dia</th>
            <th className="px-3 py-2 font-medium">Chuva</th>
            <th className="px-3 py-2 font-medium">Temp.</th>
            <th className="px-3 py-2 font-medium">Umidade</th>
            <th className="px-3 py-2 font-medium">Leitura</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const label = forecastLabel(row.precip_mm, row.temp_c)
            const labelClass =
              label === "Mais crítico"
                ? "bg-red-50 text-red-700"
                : label === "Seco" || label === "Calor"
                  ? "bg-amber-50 text-amber-700"
                  : "bg-emerald-50 text-emerald-700"

            return (
              <tr key={row.forecast_time} className="border-t first:border-t-0">
                <td className="px-3 py-2 font-medium">{fmtDate(row.forecast_time)}</td>
                <td className="px-3 py-2">{fmtValue(row.precip_mm, 1)} mm</td>
                <td className="px-3 py-2">{fmtValue(row.temp_c, 1)} °C</td>
                <td className="px-3 py-2">{fmtValue(row.humidity_pct, 0)}%</td>
                <td className="px-3 py-2">
                  <span className={cn("rounded-full px-2 py-1 text-[11px] font-medium", labelClass)}>
                    {label}
                  </span>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

// ── Página ────────────────────────────────────────────────────────────────────

// ── Chat Panel ────────────────────────────────────────────────────────────────

function ChatPanel({
  conversationId,
  onClose,
  isFullscreen,
  onToggleFullscreen,
}: {
  conversationId: string
  onClose: () => void
  isFullscreen: boolean
  onToggleFullscreen: () => void
}) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content: "Olá! Sou a Safrinia, sua assistente agroclimática. Pode me perguntar qualquer coisa sobre a análise da sua área.",
    },
  ])
  const [input, setInput] = useState("")
  const [sending, setSending] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  async function handleSend() {
    const text = input.trim()
    if (!text || sending) return
    setInput("")
    setMessages((prev) => [...prev, { role: "user", content: text }])
    setSending(true)
    try {
      const res = await fetch(API_ENDPOINTS.chat, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ conversation_id: conversationId, message: text }),
      })
      const json = await res.json()
      if (!res.ok) throw new Error(json.detail ?? "Erro")
      setMessages((prev) => [...prev, { role: "assistant", content: json.response }])
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Erro ao contatar o copiloto."
      setMessages((prev) => [...prev, { role: "assistant", content: `Desculpe, ocorreu um erro: ${msg}` }])
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b shrink-0">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-primary/15">
            <Sprout className="w-4 h-4 text-primary" />
          </div>
          <div>
            <p className="text-sm font-semibold">Safrinia</p>
            <p className="text-[10px] text-muted-foreground">Tire dúvidas sobre sua análise</p>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={onToggleFullscreen}
            className="p-1 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors"
            title={isFullscreen ? "Minimizar" : "Tela cheia"}
          >
            {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
          </button>
          <button
            onClick={onClose}
            className="p-1 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors"
            title="Fechar"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3 min-h-0">
        {messages.map((m, i) => (
          <div key={i} className={cn("flex", m.role === "user" ? "justify-end" : "justify-start")}>
            <div
              className={cn(
                "max-w-[85%] rounded-xl px-3 py-2 text-sm leading-relaxed",
                m.role === "user"
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-foreground"
              )}
            >
              {m.role === "assistant" ? (
                <ReactMarkdown
                  components={{
                    p: ({ children }) => <p className="mb-1 last:mb-0">{children}</p>,
                    strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                    em: ({ children }) => <em className="italic">{children}</em>,
                    ul: ({ children }) => <ul className="list-disc pl-4 space-y-0.5 my-1">{children}</ul>,
                    ol: ({ children }) => <ol className="list-decimal pl-4 space-y-0.5 my-1">{children}</ol>,
                    li: ({ children }) => <li>{children}</li>,
                    code: ({ children }) => <code className="bg-background/50 rounded px-1 text-xs font-mono">{children}</code>,
                  }}
                >
                  {m.content}
                </ReactMarkdown>
              ) : (
                m.content
              )}
            </div>
          </div>
        ))}
        {sending && (
          <div className="flex justify-start">
            <div className="bg-muted rounded-xl px-3 py-2">
              <Loader2 className="w-4 h-4 animate-spin text-muted-foreground" />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="p-3 border-t shrink-0">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
            placeholder="Escreva sua pergunta…"
            disabled={sending}
            className="flex-1 rounded-lg border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50 disabled:opacity-50"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || sending}
            className="p-2 rounded-lg bg-primary text-primary-foreground disabled:opacity-40 hover:bg-primary/90 transition-colors"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  )
}

export default function ResultsPage() {
  const location = useLocation()
  const initialAnalysis =
    (location.state as { analysis?: AnalysisData } | null)?.analysis ?? null
  const [data, setData] = useState<AnalysisData | null>(null)
  const [loading, setLoading] = useState(true)
  const [chatOpen, setChatOpen] = useState(false)
  const [chatFullscreen, setChatFullscreen] = useState(false)
  const [loadingStep, setLoadingStep] = useState(0)
  const [typedLoadingText, setTypedLoadingText] = useState("")

  useEffect(() => {
    const interval = window.setInterval(() => {
      setLoadingStep((prev) => (prev + 1) % LOADING_MESSAGES.length)
    }, 1200)

    return () => window.clearInterval(interval)
  }, [])

  useEffect(() => {
    const target = LOADING_MESSAGES[loadingStep]
    let index = 0
    setTypedLoadingText("")

    const typing = window.setInterval(() => {
      index += 1
      setTypedLoadingText(target.slice(0, index))
      if (index >= target.length) {
        window.clearInterval(typing)
      }
    }, 28)

    return () => window.clearInterval(typing)
  }, [loadingStep])

  useEffect(() => {
    let cancelled = false

    async function loadDashboard() {
      setLoading(true)
      const startedAt = Date.now()

      try {
        let resolved = initialAnalysis
        if (!resolved) {
          const response = await fetch(API_ENDPOINTS.mockAnalysis, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: "{}",
          })
          resolved = await response.json()
        }

        const elapsed = Date.now() - startedAt
        const remaining = Math.max(0, MIN_LOADING_MS - elapsed)
        if (remaining > 0) {
          await new Promise((resolve) => window.setTimeout(resolve, remaining))
        }

        if (!cancelled) {
          setData(resolved)
        }
      } catch {
        if (!cancelled) {
          setData(null)
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    loadDashboard()

    return () => {
      cancelled = true
    }
  }, [initialAnalysis])

  useEffect(() => {
    document.documentElement.style.overflow = "hidden"
    document.body.style.overflow = "hidden"
    return () => {
      document.documentElement.style.overflow = ""
      document.body.style.overflow = ""
    }
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen overflow-hidden bg-[radial-gradient(circle_at_top,_rgba(22,163,74,0.10),_transparent_35%),linear-gradient(180deg,#fbfdfb_0%,#f4f8f4_100%)]">
        <div className="mx-auto flex min-h-screen max-w-4xl items-center justify-center px-6">
          <div className="flex w-full flex-col items-center text-center">
            <div className="relative mb-8 flex items-center justify-center">
              <div className="absolute h-28 w-28 rounded-full bg-primary/10 blur-2xl" />
              <div className="relative flex h-24 w-24 items-center justify-center rounded-full border border-primary/15 bg-white shadow-lg">
                <div className="absolute h-20 w-20 animate-spin rounded-full border-2 border-primary/15 border-t-primary" />
                <div className="absolute -right-2 -top-2 rounded-2xl bg-primary p-2 text-primary-foreground shadow-md animate-[bounce_1.8s_ease-in-out_infinite]">
                  <Bot className="h-4 w-4" />
                </div>
                <img
                  src="/logo.jpeg"
                  alt="Logo SafraViva"
                  className="h-10 w-10 rounded-2xl object-cover animate-pulse"
                />
              </div>
            </div>

            <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-primary/15 bg-white/80 px-4 py-2 text-xs font-medium text-primary shadow-sm">
              <Sparkles className="h-3.5 w-3.5" />
              Safrinia preparando sua leitura da área
            </div>

            <h1 className="max-w-2xl text-3xl font-black tracking-tight text-foreground sm:text-4xl">
              Gerando seu dashboard agroclimático
            </h1>

            <p className="mt-3 max-w-2xl text-sm leading-relaxed text-muted-foreground sm:text-base">
              Estamos cruzando clima, satélite, território e contexto agronômico para montar uma leitura mais clara da sua área.
            </p>

            <div className="mt-8 min-h-16 max-w-2xl rounded-2xl border bg-white/85 px-5 py-4 text-sm text-foreground shadow-sm backdrop-blur sm:text-base">
              <span>{typedLoadingText}</span>
              <span className="ml-1 inline-block h-5 w-[2px] animate-pulse bg-primary align-middle" />
            </div>

            <div className="mt-6 h-1.5 w-full max-w-md overflow-hidden rounded-full bg-primary/10">
              <div
                className="h-full rounded-full bg-primary transition-all duration-500"
                style={{ width: `${((loadingStep + 1) / LOADING_MESSAGES.length) * 100}%` }}
              />
            </div>

            <p className="mt-4 text-xs text-muted-foreground">
              Isso leva só alguns segundos.
            </p>
          </div>
        </div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-sm text-muted-foreground">Erro ao carregar dados. Backend online?</p>
      </div>
    )
  }

  const risk = RISK_CONFIG[data.summary.risk_level] ?? RISK_CONFIG.moderado
  const { metrics, risk_flags, forecast_timeseries, copilot_response, field_info, summary, data_sources: dataSources } = data

  const criticalFlags = [
    risk_flags.dry_risk_flag && "seca no curto prazo",
    risk_flags.heat_risk_flag && "temperatura acima do ideal",
    risk_flags.outside_zarc_flag && "fora da janela ZARC",
    risk_flags.vegetation_stress_flag && "estresse vegetativo",
  ].filter(Boolean) as string[]

  const situationSummary =
    criticalFlags.length > 0
      ? `Os principais pontos de atenção agora são ${criticalFlags.join(", ")}.`
      : "Os sinais atuais estão dentro da faixa esperada para a área analisada."

  const sourceStatus =
    dataSources.climate.provider.toLowerCase().includes("synthetic") ||
    dataSources.satellite.provider.toLowerCase().includes("synthetic")
      ? "Análise com parte dos sinais em fallback."
      : "Análise baseada em fontes conectadas."

  const forecastChart = forecast_timeseries.map((d) => ({
    dia: fmtDate(d.forecast_time),
    "Chuva (mm)": d.precip_mm,
    "Temp (°C)": d.temp_c,
  }))

  const ndviChart = dataSources.satellite.ndvi_timeseries?.length > 0 
    ? dataSources.satellite.ndvi_timeseries.map((d: any) => ({
        data: fmtDate(d.date),
        NDVI: d.ndvi,
      }))
    : []

  const mapCenter: [number, number] = [
    data.map_layer.geometry.coordinates[0].reduce((s: number, c: number[]) => s + c[1], 0) /
      data.map_layer.geometry.coordinates[0].length,
    data.map_layer.geometry.coordinates[0].reduce((s: number, c: number[]) => s + c[0], 0) /
      data.map_layer.geometry.coordinates[0].length,
  ]

  const mapPositions: [number, number][] = data.map_layer.geometry.coordinates[0].map(
    (c: number[]) => [c[1], c[0]]
  )

  return (
    <TooltipProvider>
      <div className="h-screen flex flex-col bg-background overflow-hidden">
      {/* Header */}
      <header className="border-b bg-background/95 backdrop-blur-sm z-50 shrink-0">
        <div className="container mx-auto max-w-full px-4 h-14 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <img
              src="/logo.jpeg"
              alt="Logo SafraViva"
              className="h-7 w-7 shrink-0 rounded-lg object-cover"
            />
            <span className="font-bold text-sm">SafraViva</span>
          </Link>
          <Link to="/solicitar-demo" className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors">
            <ArrowLeft className="w-3.5 h-3.5" />
            Nova análise
          </Link>
        </div>
      </header>

      {/* Layout: painel esquerdo com scroll + mapa fixo à direita */}
      <div className="flex-1 flex overflow-hidden min-h-0">

        {/* ── Painel esquerdo: scroll ── */}
        <div className="w-full lg:w-130 xl:w-145 shrink-0 overflow-y-auto border-r min-h-0">
          <div className="p-5 space-y-5">

            {/* Hero: Score + Info */}
            <div className={cn("rounded-xl border p-4", risk.bg, risk.border)}>
              <div className="flex items-center gap-4">
                {/* Score circular */}
                <div className="relative flex items-center justify-center shrink-0">
                  <svg width="80" height="80" viewBox="0 0 80 80">
                    <circle cx="40" cy="40" r="32" fill="none" stroke="#e2e8f0" strokeWidth="7" />
                    <circle
                      cx="40" cy="40" r="32"
                      fill="none"
                      stroke={risk.scoreColor}
                      strokeWidth="7"
                      strokeLinecap="round"
                      strokeDasharray={`${(summary.risk_score / 100) * 201} 201`}
                      strokeDashoffset="50"
                      transform="rotate(-90 40 40)"
                    />
                  </svg>
                  <div className="absolute text-center">
                    <p className={cn("text-xl font-black leading-none", risk.color)}>{summary.risk_score}</p>
                    <p className="text-[9px] text-muted-foreground">/ 100</p>
                  </div>
                </div>
                <div className="flex-1 min-w-0">
                  <Badge className={cn("mb-1 text-xs", risk.color, risk.bg, risk.border)}>
                    Risco {risk.label}
                  </Badge>
                  <p className={cn("font-semibold text-sm leading-snug", risk.color)}>{summary.primary_alert}</p>
                  <p className="text-xs text-muted-foreground mt-0.5">{summary.recommended_action}</p>
                </div>
              </div>

              <Separator className="my-3" />

              <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
                <span className="text-muted-foreground">Propriedade</span>
                <span className="font-medium truncate">{field_info.property_name}</span>
                <span className="text-muted-foreground">Cultura</span>
                <span className="font-medium">{cultureName(field_info.culture)} · {field_info.area_ha} ha</span>
                <span className="text-muted-foreground">Município</span>
                <span className="font-medium">{field_info.municipio}, {field_info.uf}</span>
                <span className="text-muted-foreground">Plantio</span>
                <span className="font-medium">{fmtDate(field_info.sowing_date)}</span>
                <span className="text-muted-foreground">Estágio</span>
                <span className="font-medium">{stageName(field_info.crop_stage)}</span>
              </div>
            </div>

            <div className="grid gap-3 md:grid-cols-3">
              <SummaryPanel
                title="Situação agora"
                description={situationSummary}
                icon={risk_flags.dry_risk_flag || risk_flags.heat_risk_flag ? ShieldAlert : ShieldCheck}
                tone={risk_flags.dry_risk_flag || risk_flags.heat_risk_flag ? "alert" : "good"}
              />
              <SummaryPanel
                title="Prioridade de ação"
                description={summary.recommended_action}
                icon={Activity}
                tone="neutral"
              />
              <SummaryPanel
                title="Confiabilidade da leitura"
                description={sourceStatus}
                icon={Satellite}
                tone="neutral"
              />
            </div>

            {/* Flags */}
            <div className="flex flex-wrap gap-1.5">
              <FlagBadge active={risk_flags.dry_risk_flag} label="Seca" />
              <FlagBadge active={risk_flags.heat_risk_flag} label="Calor excessivo" />
              <FlagBadge active={risk_flags.outside_zarc_flag} label="Fora do ZARC" />
              <FlagBadge active={risk_flags.vegetation_stress_flag} label="Estresse vegetativo" />
            </div>

            <Card>
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between gap-2">
                  <CardTitle className="text-sm font-semibold">Leitura rápida da área</CardTitle>
                  <HelpTooltip text="Resumo visual dos sinais principais da análise. Serve para bater o olho no comportamento de chuva, temperatura, umidade e vento sem precisar interpretar cada fonte técnica separadamente." />
                </div>
                <p className="text-xs text-muted-foreground">Valores organizados para leitura operacional</p>
              </CardHeader>
              <CardContent className="grid gap-3 md:grid-cols-2">
                <SignalMeter
                  label="Chuva prevista"
                  value={fmtValue(metrics.precip_forecast_7d_mm, 1)}
                  unit="mm em 7 dias"
                  progress={normalizeMetric(metrics.precip_forecast_7d_mm, 60)}
                  tone={risk_flags.dry_risk_flag ? "alert" : "good"}
                  hint={`14 dias: ${fmtValue(metrics.precip_forecast_14d_mm, 1)} mm`}
                />
                <SignalMeter
                  label="Temperatura máxima"
                  value={fmtValue(metrics.temp_max_7d_c, 1)}
                  unit="°C"
                  progress={normalizeMetric(metrics.temp_max_7d_c, 40)}
                  tone={risk_flags.heat_risk_flag ? "alert" : "neutral"}
                  hint={`Média: ${fmtValue(metrics.temp_mean_7d_c, 1)} °C`}
                />
                <SignalMeter
                  label="Umidade média"
                  value={fmtValue(metrics.humidity_mean_7d_pct, 0)}
                  unit="%"
                  progress={normalizeMetric(metrics.humidity_mean_7d_pct, 100)}
                  tone={metrics.humidity_mean_7d_pct >= 58 ? "good" : "alert"}
                />
                <SignalMeter
                  label="Vento médio"
                  value={fmtValue(metrics.wind_mean_7d_ms, 1)}
                  unit="m/s"
                  progress={normalizeMetric(metrics.wind_mean_7d_ms, 10)}
                  tone={metrics.wind_mean_7d_ms > 4.8 ? "alert" : "neutral"}
                />
              </CardContent>
            </Card>

            {/* Métricas */}
            <div className="grid grid-cols-2 gap-2.5">
              <MetricCard icon={CloudRain} label="Chuva 7 dias" value={metrics.precip_forecast_7d_mm} unit="mm"
                sub={`14d: ${metrics.precip_forecast_14d_mm} mm`} highlight={risk_flags.dry_risk_flag} />
              <MetricCard icon={Thermometer} label="Temp. máxima 7d" value={metrics.temp_max_7d_c} unit="°C"
                sub={`Média: ${metrics.temp_mean_7d_c} °C`} highlight={risk_flags.heat_risk_flag} />
              <MetricCard icon={Droplets} label="Umidade 7d" value={metrics.humidity_mean_7d_pct} unit="%" />
              <MetricCard icon={Wind} label="Vento 7d" value={metrics.wind_mean_7d_ms} unit="m/s" />
            </div>

            {/* Gráfico previsão */}
            <Card>
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between gap-2">
                  <CardTitle className="text-sm font-semibold">Previsão — 14 dias</CardTitle>
                  <HelpTooltip text="O gráfico combina chuva e temperatura dos próximos 14 dias. Barras maiores indicam mais precipitação; a linha mostra a temperatura esperada. Use para entender tendência, não só um valor isolado." />
                </div>
                <p className="text-xs text-muted-foreground">Chuva (barras) · Temperatura (linha) · foco no curto prazo</p>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={190}>
                  <ComposedChart data={forecastChart} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                    <XAxis dataKey="dia" tick={{ fontSize: 9 }} />
                    <YAxis yAxisId="left" tick={{ fontSize: 9 }} width={32} />
                    <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 9 }} domain={[20, 40]} width={32} />
                    <Tooltip contentStyle={{ fontSize: 11, borderRadius: 8, border: "1px solid #e2e8f0" }} />
                    <Legend wrapperStyle={{ fontSize: 10 }} />
                    <Bar yAxisId="left" dataKey="Chuva (mm)" fill="#93c5fd" isAnimationActive={false} />
                    <Line yAxisId="right" dataKey="Temp (°C)" stroke="#f97316" dot={false} strokeWidth={2} isAnimationActive={false} />
                  </ComposedChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <CalendarRange className="h-4 w-4 text-primary" />
                    <CardTitle className="text-sm font-semibold">Próximos 5 dias</CardTitle>
                  </div>
                  <HelpTooltip text="Tabela curta para leitura rápida do curto prazo. A coluna de leitura resume o dia como mais crítico, seco, calor ou estável para facilitar a decisão." />
                </div>
                <p className="text-xs text-muted-foreground">Tabela curta para leitura rápida de decisão</p>
              </CardHeader>
              <CardContent>
                <ForecastTable points={forecast_timeseries} />
              </CardContent>
            </Card>

            {/* Gráfico NDVI */}
            {ndviChart.length > 0 && (
              <Card>
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between gap-2">
                    <CardTitle className="text-sm font-semibold">NDVI — Vegetação</CardTitle>
                    <HelpTooltip text="NDVI é um indicador de vigor da vegetação. Em geral, curvas mais altas e estáveis sugerem melhor resposta vegetativa; quedas podem sinalizar estresse e devem ser lidas junto com clima e estágio da cultura." />
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {dataSources.satellite.provider} · Nuvens: {dataSources.satellite.cloud_cover_pct}%
                  </p>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={160}>
                    <LineChart data={ndviChart} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                      <XAxis dataKey="data" tick={{ fontSize: 9 }} />
                      <YAxis tick={{ fontSize: 9 }} domain={[0.3, 0.9]} width={36} />
                      <Tooltip contentStyle={{ fontSize: 11, borderRadius: 8, border: "1px solid #e2e8f0" }} />
                      <Line dataKey="NDVI" stroke="#16a34a" strokeWidth={2.5}
                        dot={{ fill: "#16a34a", r: 4 }} activeDot={{ r: 6 }} isAnimationActive={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            )}

            {/* Copiloto */}
            <Card className="border-primary/20 bg-primary/5">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <div className="p-1.5 rounded-lg bg-primary/15">
                      <Sprout className="w-4 h-4 text-primary" />
                    </div>
                    <div>
                      <CardTitle className="text-sm font-semibold">Safrinia</CardTitle>
                      <p className="text-xs text-muted-foreground">Diagnóstico em linguagem natural</p>
                    </div>
                  </div>
                  <HelpTooltip text="Este card traduz a análise técnica em linguagem direta. O conteúdo vem das regras do backend com base no score, nas flags e nas métricas calculadas para a área." />
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="rounded-xl border border-primary/15 bg-background/80 p-3">
                  <p className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">Resumo direto</p>
                  <p className="mt-1 text-sm text-foreground leading-relaxed">{copilot_response.summary}</p>
                </div>
                <div>
                  <p className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wide mb-2">Por que esse risco?</p>
                  <ul className="space-y-1.5">
                    {copilot_response.why.map((w, i) => (
                      <li key={i} className="flex gap-2 text-xs text-muted-foreground">
                        <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-primary shrink-0" />
                        {w}
                      </li>
                    ))}
                  </ul>
                </div>
                <Separator />
                <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-3">
                  <div className="mb-1 flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
                    <p className="text-[11px] font-semibold uppercase tracking-wide text-emerald-700">Ação sugerida</p>
                  </div>
                  <p className="text-sm font-medium text-foreground">{copilot_response.action}</p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <MapPinned className="h-4 w-4 text-primary" />
                    <CardTitle className="text-sm font-semibold">Quadro da área</CardTitle>
                  </div>
                  <HelpTooltip text="Resumo cadastral e agronômico da análise. Mostra o recorte territorial, a data de plantio, o estágio inferido e a aderência ao ZARC para contextualizar o risco." />
                </div>
                <p className="text-xs text-muted-foreground">Resumo objetivo do que foi analisado</p>
              </CardHeader>
              <CardContent>
                <div className="overflow-hidden rounded-xl border">
                  <table className="w-full text-left text-sm">
                    <tbody>
                      <tr className="border-b">
                        <td className="bg-muted/40 px-3 py-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">Área</td>
                        <td className="px-3 py-2 font-medium">{fmtValue(field_info.area_ha, 2)} ha</td>
                      </tr>
                      <tr className="border-b">
                        <td className="bg-muted/40 px-3 py-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">Local</td>
                        <td className="px-3 py-2 font-medium">{field_info.municipio}, {field_info.uf}</td>
                      </tr>
                      <tr className="border-b">
                        <td className="bg-muted/40 px-3 py-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">Plantio</td>
                        <td className="px-3 py-2 font-medium">{fmtDate(field_info.sowing_date)}</td>
                      </tr>
                      <tr className="border-b">
                        <td className="bg-muted/40 px-3 py-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">Estágio</td>
                        <td className="px-3 py-2 font-medium">{stageName(field_info.crop_stage)}</td>
                      </tr>
                      <tr>
                        <td className="bg-muted/40 px-3 py-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">ZARC</td>
                        <td className="px-3 py-2">
                          <span className={cn("rounded-full border px-2 py-1 text-xs font-medium", riskTone(!dataSources.zarc.planting_within_window))}>
                            {dataSources.zarc.planting_within_window ? "Dentro da janela" : "Fora da janela"}
                          </span>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>

            {/* Fontes de dados */}
            <div>
              <div className="mb-2 flex items-center justify-between gap-2">
                <p className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wide">Fontes de dados</p>
                <HelpTooltip text="Mostra de onde vieram os sinais usados na análise e quais observações foram consideradas em clima, satélite, ZARC e histórico. Serve para dar transparência ao resultado." />
              </div>
              <div className="space-y-2">
                <SourceCard icon={CloudRain} title="Clima"
                  subtitle={`${dataSources.climate.provider} · ${dataSources.climate.model}`}
                  signals={dataSources.climate.signals || ["Precipitação", "Temperatura", "Umidade"]} defaultOpen />
                <SourceCard icon={Satellite} title="Satélite"
                  subtitle={`${dataSources.satellite.provider} · ${fmtDate(dataSources.satellite.last_image)}`}
                  signals={dataSources.satellite.signals || ["NDVI", "EVI", "Cobertura de nuvens"]} defaultOpen />
                <SourceCard
                  icon={FileText}
                  title={`ZARC — Classe ${dataSources.zarc.zarc_class} (${dataSources.zarc.zarc_label})`}
                  subtitle={dataSources.zarc.provider}
                  signals={dataSources.zarc.signals || ["Zoneamento", "Risco de plantio"]}
                />
                <SourceCard icon={Clock} title="Histórico"
                  subtitle={`${dataSources.historical.provider} · ${dataSources.historical.period}`}
                  signals={dataSources.historical.signals || ["Precipitação histórica", "Temperatura média", "Padrões climáticos"]} />
              </div>
            </div>

            <p className="text-[10px] text-muted-foreground text-center pb-2">
              Atualizado em {fmtDateTime(summary.analysis_timestamp)}
            </p>
          </div>
        </div>

        {/* ── Mapa fixo à direita ── */}
        <div className="flex-1 relative hidden lg:block">
          <MapContainer
            center={mapCenter}
            zoom={12}
            style={{ height: "100%", width: "100%" }}
            zoomControl={true}
          >
            <TileLayer
              attribution='&copy; <a href="https://carto.com/">CARTO</a>'
              url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
            />
            <Polygon
              positions={mapPositions}
              pathOptions={{
                color: data.map_layer.stroke_color,
                weight: 2.5,
                fillColor: data.map_layer.fill_color,
                fillOpacity: 0.35,
              }}
            />
          </MapContainer>

          {/* Tooltip overlay */}
          <div className="absolute bottom-4 left-4 z-1000 bg-background/95 backdrop-blur-sm border rounded-lg px-3 py-2 text-xs shadow-md">
            {data.map_layer.tooltip_summary}
          </div>

          {/* Chat panel (slide-in over the map) */}
          {data.conversation_id && (
            <>
              {/* Floating button */}
              {!chatOpen && (
                <button
                  onClick={() => setChatOpen(true)}
                  className="absolute bottom-4 right-4 z-1000 flex items-center gap-2 bg-primary text-primary-foreground rounded-full px-4 py-3 shadow-lg hover:bg-primary/90 transition-all text-sm font-medium"
                >
                  <MessageCircle className="w-4 h-4" />
                  Fale com a Safrinia
                </button>
              )}

              {/* Chat panel */}
              {chatOpen && (
                <div className={cn(
                  "bg-background border shadow-2xl flex flex-col overflow-hidden transition-all duration-300",
                  chatFullscreen
                    ? "fixed inset-0 z-9999 rounded-none"
                    : "absolute bottom-4 right-4 z-1000 w-95 h-130 rounded-2xl"
                )}>
                  <ChatPanel
                    conversationId={data.conversation_id}
                    onClose={() => { setChatOpen(false); setChatFullscreen(false) }}
                    isFullscreen={chatFullscreen}
                    onToggleFullscreen={() => setChatFullscreen((f) => !f)}
                  />
                </div>
              )}
            </>
          )}
        </div>

      </div>
      </div>
    </TooltipProvider>
  )
}
