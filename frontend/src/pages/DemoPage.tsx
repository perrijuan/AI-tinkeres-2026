import { useState, useCallback, useEffect } from "react"
import { Link, useNavigate } from "react-router-dom"
import {
  MapContainer,
  TileLayer,
  Polygon,
  Polyline,
  CircleMarker,
  useMapEvents,
} from "react-leaflet"
import type { LatLng } from "leaflet"
import "leaflet/dist/leaflet.css"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import AnalysisLoadingScreen from "@/components/AnalysisLoadingScreen"
import BrandLogo from "@/components/BrandLogo"
import { cn } from "@/lib/utils"
import { API_ENDPOINTS } from "@/config"
import {
  ArrowLeft,
  ArrowRight,
  Undo2,
  Trash2,
  CheckCircle2,
  User,
  Sprout,
  MapPin,
  Loader2,
} from "lucide-react"

// ── Helpers ───────────────────────────────────────────────────────────────────

function calcAreaHa(pts: LatLng[]): number {
  if (pts.length < 3) return 0
  const R = 6371000
  let area = 0
  const n = pts.length
  for (let i = 0; i < n; i++) {
    const j = (i + 1) % n
    const lat1 = (pts[i].lat * Math.PI) / 180
    const lat2 = (pts[j].lat * Math.PI) / 180
    const dLng = ((pts[j].lng - pts[i].lng) * Math.PI) / 180
    area += dLng * (2 + Math.sin(lat1) + Math.sin(lat2))
  }
  return Math.abs((area * R * R) / 2) / 10000
}


function MapClickHandler({ onClick }: { onClick: (ll: LatLng) => void }) {
  useMapEvents({ click: (e) => onClick(e.latlng) })
  return null
}

// ── Tipos ────────────────────────────────────────────────────────────────────

interface Cultura {
  id: string
  label: string
  emoji: string
}

// ── Steps config ─────────────────────────────────────────────────────────────

const STEPS = [
  { id: 1, label: "Seus dados",  icon: User },
  { id: 2, label: "Cultura",     icon: Sprout },
  { id: 3, label: "Área",        icon: MapPin },
]

// ── Componente ────────────────────────────────────────────────────────────────

export default function DemoPage() {
  const navigate = useNavigate()

  const [step, setStep] = useState(1)
  const [nome, setNome] = useState("")
  const [empresa, setEmpresa] = useState("")
  const [email, setEmail] = useState("")
  const [cultura, setCultura] = useState("")
  const [culturas, setCulturas] = useState<Cultura[]>([])
  const [points, setPoints] = useState<LatLng[]>([])
  const [loading, setLoading] = useState(false)
  const [sowingDate, setSowingDate] = useState(
    new Date().toISOString().split("T")[0]
  )

  useEffect(() => {
    fetch(API_ENDPOINTS.culturas)
      .then((r) => r.json())
      .then(setCulturas)
      .catch(() => {})
  }, [])

  // Trava scroll da página
  useEffect(() => {
    document.documentElement.style.overflow = "hidden"
    document.body.style.overflow = "hidden"
    return () => {
      document.documentElement.style.overflow = ""
      document.body.style.overflow = ""
    }
  }, [])

  const addPoint = useCallback((latlng: LatLng) => {
    setPoints((prev) => [...prev, latlng])
  }, [])

  const undo = () => setPoints((prev) => prev.slice(0, -1))
  const clear = () => setPoints([])

  const canStep1 = !!nome.trim() && !!email.trim()
  const canStep2 = !!cultura
  const canConfirm = points.length >= 3

  const areaHa = calcAreaHa(points)

  const handleConfirm = async () => {
    if (!canConfirm) return
    setLoading(true)

    // Novo payload conforme contrato API
    const geometryCoords = [
      ...points.map((p) => [p.lng, p.lat]),
      [points[0].lng, points[0].lat],
    ]
    
    const payload = {
      field_id: `${nome.replace(/\s+/g, "_").toLowerCase()}_${Date.now()}`,
      property_name: empresa || nome,
      culture: cultura,
      sowing_date: sowingDate,
      crop_stage: null,
      irrigated: false,
      analysis_timestamp: new Date().toISOString(),
      geometry: {
        type: "Polygon",
        coordinates: [geometryCoords],
      },
    }

    try {
      const res = await fetch(API_ENDPOINTS.analysis, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })
      
      if (!res.ok) {
        const error = await res.json()
        throw new Error(error.detail || "Erro ao analisar")
      }
      
      const analysis = await res.json()
      navigate("/resultado", { state: { analysis } })
    } catch (err) {
      console.error("Erro na análise:", err)
      navigate("/resultado", { state: { analysis: null, error: String(err) } })
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <AnalysisLoadingScreen
        title="Estamos montando a análise da sua área"
        subtitle="Os dados do talhão já foram enviados. Agora o sistema está cruzando sinais climáticos, satelitais e agronômicos para preparar o dashboard."
      />
    )
  }

  return (
    <div className="flex h-dvh flex-col bg-background lg:h-screen lg:overflow-hidden">

      {/* ── Header ── */}
      <header className="shrink-0 border-b bg-background/95 backdrop-blur-sm z-50">
        <div className="mx-auto flex min-h-14 w-full max-w-7xl items-center justify-between gap-3 px-3 sm:px-4 lg:px-6">
          <Link to="/" className="flex min-w-0 items-center gap-2">
            <BrandLogo className="h-8 w-8 rounded-[0.95rem]" imageClassName="rounded-[0.7rem]" />
            <span className="font-bold text-sm">SafraViva</span>
          </Link>

          {/* Stepper */}
          <div className="flex min-w-0 items-center gap-1 overflow-x-auto px-1 py-1 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
            {STEPS.map((s, i) => {
              const Icon = s.icon
              const done = step > s.id
              const active = step === s.id
              return (
                <div key={s.id} className="flex shrink-0 items-center gap-1.5">
                  <div className="flex items-center gap-1.5">
                    <div className={cn(
                      "w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-colors",
                      done   && "bg-primary text-primary-foreground",
                      active && "bg-primary text-primary-foreground ring-4 ring-primary/20",
                      !done && !active && "bg-muted text-muted-foreground",
                    )}>
                      {done ? <CheckCircle2 className="w-3.5 h-3.5" /> : <Icon className="w-3.5 h-3.5" />}
                    </div>
                    <span className={cn(
                      "text-xs font-medium hidden sm:block",
                      active ? "text-foreground" : "text-muted-foreground"
                    )}>
                      {s.label}
                    </span>
                  </div>
                  {i < STEPS.length - 1 && (
                    <div className={cn("h-px w-5 sm:w-8", done ? "bg-primary" : "bg-border")} />
                  )}
                </div>
              )
            })}
          </div>

          <Button variant="ghost" size="sm" className="shrink-0" asChild>
            <Link to="/" className="gap-1.5 text-muted-foreground">
              <ArrowLeft className="w-3.5 h-3.5" />
              <span className="hidden sm:block">Voltar</span>
            </Link>
          </Button>
        </div>
      </header>

      {/* ── Conteúdo por step ── */}

      {/* Step 1: Dados pessoais */}
      {step === 1 && (
        <div className="flex flex-1 items-center justify-center p-4 sm:p-6">
          <div className="w-full max-w-md space-y-6">
            <div className="text-center">
              <div className="w-12 h-12 bg-primary/10 rounded-2xl flex items-center justify-center mx-auto mb-3">
                <User className="w-6 h-6 text-primary" />
              </div>
              <h1 className="text-2xl font-bold">Seus dados</h1>
              <p className="text-muted-foreground text-sm mt-1">
                Precisamos de algumas informações para gerar sua análise.
              </p>
            </div>

            <div className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="nome">Nome completo *</Label>
                <Input
                  id="nome"
                  placeholder="João Silva"
                  value={nome}
                  onChange={(e) => setNome(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && canStep1 && setStep(2)}
                  autoFocus
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="empresa">Empresa <span className="text-muted-foreground">(opcional)</span></Label>
                <Input
                  id="empresa"
                  placeholder="Cooperativa / Seguradora"
                  value={empresa}
                  onChange={(e) => setEmpresa(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && canStep1 && setStep(2)}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="email">E-mail *</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="joao@empresa.com.br"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && canStep1 && setStep(2)}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="sowingDate">Data de plantio</Label>
                <Input
                  id="sowingDate"
                  type="date"
                  value={sowingDate}
                  onChange={(e) => setSowingDate(e.target.value)}
                />
              </div>
            </div>

            <Button
              className="w-full gap-2"
              disabled={!canStep1}
              onClick={() => setStep(2)}
            >
              Próximo
              <ArrowRight className="w-4 h-4" />
            </Button>
          </div>
        </div>
      )}

      {/* Step 2: Cultura */}
      {step === 2 && (
        <div className="flex flex-1 flex-col items-center justify-center gap-5 overflow-y-auto p-4 sm:gap-6 sm:p-6">
          <div className="text-center">
            <div className="w-12 h-12 bg-primary/10 rounded-2xl flex items-center justify-center mx-auto mb-3">
              <Sprout className="w-6 h-6 text-primary" />
            </div>
            <h1 className="text-2xl font-bold">Qual a cultura?</h1>
            <p className="text-muted-foreground text-sm mt-1">
              Selecione o que está sendo cultivado na área.
            </p>
          </div>

          <div className="grid w-full max-w-2xl grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-5">
            {culturas.map((c) => (
              <button
                key={c.id}
                type="button"
                onClick={() => setCultura(c.id)}
                className={cn(
                  "flex flex-col items-center gap-2 rounded-xl border-2 p-4 transition-all cursor-pointer hover:border-primary/50",
                  cultura === c.id
                    ? "border-primary bg-primary/8 shadow-sm"
                    : "border-border bg-card hover:bg-accent/50"
                )}
              >
                <span className="text-3xl leading-none">{c.emoji}</span>
                <span className={cn(
                  "text-xs font-medium text-center leading-tight",
                  cultura === c.id ? "text-primary" : "text-foreground"
                )}>
                  {c.label}
                </span>
              </button>
            ))}
          </div>

          <div className="flex w-full max-w-2xl flex-col gap-3 sm:flex-row">
            <Button variant="outline" className="gap-2 sm:w-auto" onClick={() => setStep(1)}>
              <ArrowLeft className="w-4 h-4" />
              Voltar
            </Button>
            <Button
              className="flex-1 gap-2"
              disabled={!canStep2}
              onClick={() => setStep(3)}
            >
              Próximo
              <ArrowRight className="w-4 h-4" />
            </Button>
          </div>
        </div>
      )}

      {/* Step 3: Mapa */}
      {step === 3 && (
        <div className="flex-1 relative overflow-hidden">

          {/* Mapa full */}
          <MapContainer
            center={[-12.7, -56.9]}
            zoom={6}
            style={{ height: "100%", width: "100%" }}
            zoomControl={false}
          >
            <TileLayer
              attribution='&copy; <a href="https://carto.com/">CARTO</a>'
              url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
            />
            <MapClickHandler onClick={addPoint} />

            {points.length >= 2 && (
              <Polyline
                positions={points}
                pathOptions={{ color: "#16a34a", weight: 2, dashArray: "6 4", opacity: 0.8 }}
              />
            )}
            {points.length >= 3 && (
              <Polygon
                positions={points}
                pathOptions={{ color: "#16a34a", weight: 2, fillColor: "#16a34a", fillOpacity: 0.15 }}
              />
            )}
            {points.map((pt, i) => (
              <CircleMarker
                key={i}
                center={pt}
                radius={i === 0 ? 8 : 5}
                pathOptions={{ fillColor: "#16a34a", color: "#fff", weight: 2, fillOpacity: 1 }}
              />
            ))}
          </MapContainer>

          {/* Painel flutuante: topo esquerdo — controles */}
          <div className="absolute left-3 right-3 top-3 z-1000 flex flex-wrap gap-2 sm:left-4 sm:right-auto sm:top-4">
            <button
              onClick={() => setStep(2)}
              className="flex min-h-10 items-center gap-1.5 rounded-lg border bg-background/95 px-3 py-2 text-sm font-medium shadow backdrop-blur-sm transition-colors hover:bg-accent"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              Voltar
            </button>
            <button
              onClick={undo}
              disabled={points.length === 0}
              className="flex min-h-10 items-center gap-1.5 rounded-lg border bg-background/95 px-3 py-2 text-sm font-medium shadow backdrop-blur-sm transition-colors hover:bg-accent disabled:pointer-events-none disabled:opacity-40"
            >
              <Undo2 className="w-3.5 h-3.5" />
              Desfazer
            </button>
            <button
              onClick={clear}
              disabled={points.length === 0}
              className="flex min-h-10 items-center gap-1.5 rounded-lg border bg-background/95 px-3 py-2 text-sm font-medium text-destructive shadow backdrop-blur-sm transition-colors hover:bg-destructive/10 disabled:pointer-events-none disabled:opacity-40"
            >
              <Trash2 className="w-3.5 h-3.5" />
              Limpar
            </button>
          </div>

          {/* Instrução flutuante: topo centro */}
          <div className="absolute left-3 right-3 top-20 z-1000 sm:left-1/2 sm:right-auto sm:top-4 sm:-translate-x-1/2">
            <div className="rounded-2xl border bg-background/95 px-4 py-2 text-center text-xs text-muted-foreground shadow backdrop-blur-sm sm:rounded-full sm:py-1.5">
              Clique no mapa para marcar os vértices da área
            </div>
          </div>

          {/* Painel flutuante: rodapé — resumo + confirmar */}
          <div className="absolute bottom-4 left-1/2 z-1000 w-full max-w-sm -translate-x-1/2 px-3 sm:bottom-6 sm:px-4">
            <div className="bg-background/95 backdrop-blur-sm border rounded-2xl shadow-lg p-4 space-y-3">
              {points.length >= 3 ? (
                <>
                  <div className="flex items-center justify-between text-sm">
                    <div>
                      <p className="text-xs text-muted-foreground">Área estimada</p>
                      <p className="font-bold text-primary text-lg">
                        {areaHa >= 10000
                          ? `${(areaHa / 100).toFixed(1)} km²`
                          : `${areaHa.toFixed(1)} ha`}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-muted-foreground">Vértices</p>
                      <p className="font-semibold">{points.length} pontos</p>
                    </div>
                  </div>
                  <Button
                    className="w-full gap-2"
                    onClick={handleConfirm}
                    disabled={loading}
                  >
                    {loading
                      ? <><Loader2 className="w-4 h-4 animate-spin" /> Analisando…</>
                      : <><CheckCircle2 className="w-4 h-4" /> Ver análise de risco</>}
                  </Button>
                </>
              ) : (
                <div className="text-center py-1">
                  <p className="text-sm text-muted-foreground">
                    {points.length === 0
                      ? "Clique no mapa para começar a delimitar a área."
                      : `Adicione mais ${3 - points.length} ponto${3 - points.length > 1 ? "s" : ""} para fechar o polígono.`}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

    </div>
  )
}
