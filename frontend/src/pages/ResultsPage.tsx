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
  Leaf,
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
} from "lucide-react"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import { cn } from "@/lib/utils"
import { API_ENDPOINTS } from "@/config"

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

// ── Página ────────────────────────────────────────────────────────────────────

// ── Chat Panel ────────────────────────────────────────────────────────────────

function ChatPanel({
  conversationId,
  onClose,
}: {
  conversationId: string
  onClose: () => void
}) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content: "Olá! Sou o copiloto SafraViva. Pode me perguntar qualquer coisa sobre a análise da sua área.",
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
            <p className="text-sm font-semibold">Copiloto SafraViva</p>
            <p className="text-[10px] text-muted-foreground">Tire dúvidas sobre sua análise</p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-1 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
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
              {m.content}
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
  const [data, setData] = useState<AnalysisData | null>(
    (location.state as { analysis?: AnalysisData } | null)?.analysis ?? null
  )
  const [loading, setLoading] = useState(!data)
  const [chatOpen, setChatOpen] = useState(false)

  useEffect(() => {
    if (data) return
    fetch(API_ENDPOINTS.mockAnalysis, { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" })
      .then((r) => r.json())
      .then((d) => { setData(d); setLoading(false) })
      .catch(() => setLoading(false))
  }, [data])

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
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-2">
          <Leaf className="w-8 h-8 text-primary animate-pulse mx-auto" />
          <p className="text-sm text-muted-foreground">Carregando análise…</p>
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
  const { metrics, risk_flags, forecast_timeseries, copilot_response, field_info, summary } = data
  
  // Valores padrão para data_sources se não existir
  const dataSources = (data as any).data_sources || {
    climate: { provider: "GFS", model: "MVP", coverage: "MT", signals: [] },
    satellite: { provider: "Sentinel", last_image: new Date().toISOString(), cloud_cover_pct: 0, signals: [], ndvi_timeseries: [] },
    zarc: { provider: "CONAB", zarc_class: 1, zarc_label: "Favorável", planting_within_window: true, signals: [] },
    historical: { provider: "ERA5", period: "1989-2023", signals: [] },
  }

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
    <div className="h-screen flex flex-col bg-background overflow-hidden">
      {/* Header */}
      <header className="border-b bg-background/95 backdrop-blur-sm z-50 shrink-0">
        <div className="container mx-auto max-w-full px-4 h-14 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <div className="w-7 h-7 bg-primary rounded-lg flex items-center justify-center shrink-0">
              <Leaf className="w-3.5 h-3.5 text-primary-foreground" />
            </div>
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
                {field_info.crop_stage && (
                  <>
                    <span className="text-muted-foreground">Estágio</span>
                    <span className="font-medium">{stageName(field_info.crop_stage)}</span>
                  </>
                )}
              </div>
            </div>

            {/* Flags */}
            <div className="flex flex-wrap gap-1.5">
              <FlagBadge active={risk_flags.dry_risk_flag} label="Seca" />
              <FlagBadge active={risk_flags.heat_risk_flag} label="Calor excessivo" />
              <FlagBadge active={risk_flags.outside_zarc_flag} label="Fora do ZARC" />
              <FlagBadge active={risk_flags.vegetation_stress_flag} label="Estresse vegetativo" />
            </div>

            {/* Métricas */}
            <div className="grid grid-cols-2 gap-2.5">
              <MetricCard icon={CloudRain} label="Chuva 7 dias" value={metrics.precip_forecast_7d_mm} unit="mm"
                sub={`14d: ${metrics.precip_forecast_14d_mm} mm`} highlight={risk_flags.dry_risk_flag} />
              <MetricCard icon={Thermometer} label="Temp. máxima 7d" value={metrics.temp_max_7d_c} unit="°C"
                sub={`Média: ${metrics.temp_mean_7d_c} °C`} highlight={risk_flags.heat_risk_flag} />
              <MetricCard icon={Droplets} label="Umidade 7d" value={metrics.humidity_mean_7d_pct} unit="%" />
              {(metrics as any).wind_mean_7d_ms !== undefined && (
                <MetricCard icon={Wind} label="Vento 7d" value={(metrics as any).wind_mean_7d_ms} unit="m/s" />
              )}
            </div>

            {/* Gráfico previsão */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-semibold">Previsão — 14 dias</CardTitle>
                <p className="text-xs text-muted-foreground">Chuva (barras) · Temperatura (linha)</p>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={190}>
                  <ComposedChart data={forecastChart} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                    <XAxis dataKey="dia" tick={{ fontSize: 9 }} />
                    <YAxis yAxisId="left" tick={{ fontSize: 9 }} />
                    <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 9 }} domain={[20, 40]} />
                    <Tooltip contentStyle={{ fontSize: 11, borderRadius: 8, border: "1px solid #e2e8f0" }} />
                    <Legend wrapperStyle={{ fontSize: 10 }} />
                    <Bar yAxisId="left" dataKey="Chuva (mm)" fill="#93c5fd" radius={[3, 3, 0, 0]} />
                    <Line yAxisId="right" dataKey="Temp (°C)" stroke="#f97316" dot={false} strokeWidth={2} />
                  </ComposedChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Gráfico NDVI */}
            {ndviChart.length > 0 && (
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-semibold">NDVI — Vegetação</CardTitle>
                  <p className="text-xs text-muted-foreground">
                    {dataSources.satellite.provider} · Nuvens: {dataSources.satellite.cloud_cover_pct}%
                  </p>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={160}>
                    <LineChart data={ndviChart} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                      <XAxis dataKey="data" tick={{ fontSize: 9 }} />
                      <YAxis tick={{ fontSize: 9 }} domain={[0.3, 0.9]} />
                      <Tooltip contentStyle={{ fontSize: 11, borderRadius: 8, border: "1px solid #e2e8f0" }} />
                      <Line dataKey="NDVI" stroke="#16a34a" strokeWidth={2.5}
                        dot={{ fill: "#16a34a", r: 4 }} activeDot={{ r: 6 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            )}

            {/* Copiloto */}
            <Card className="border-primary/20 bg-primary/5">
              <CardHeader className="pb-3">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 rounded-lg bg-primary/15">
                    <Sprout className="w-4 h-4 text-primary" />
                  </div>
                  <div>
                    <CardTitle className="text-sm font-semibold">Copiloto SafraViva</CardTitle>
                    <p className="text-xs text-muted-foreground">Diagnóstico em linguagem natural</p>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <p className="text-sm text-foreground leading-relaxed">{copilot_response.summary}</p>
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
                <div className="flex gap-2">
                  <CheckCircle2 className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                  <p className="text-sm font-medium text-foreground">{copilot_response.action}</p>
                </div>
              </CardContent>
            </Card>

            {/* Fontes de dados */}
            <div>
              <p className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wide mb-2">Fontes de dados</p>
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
                  Pergunte ao copiloto
                </button>
              )}

              {/* Chat panel */}
              {chatOpen && (
                <div className="absolute bottom-4 right-4 z-1000 w-[380px] h-[520px] bg-background border rounded-2xl shadow-2xl flex flex-col overflow-hidden">
                  <ChatPanel
                    conversationId={data.conversation_id}
                    onClose={() => setChatOpen(false)}
                  />
                </div>
              )}
            </>
          )}
        </div>

      </div>
    </div>
  )
}
