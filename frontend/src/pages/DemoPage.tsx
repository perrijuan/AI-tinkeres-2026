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
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { Alert, AlertDescription } from "@/components/ui/alert"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { cn } from "@/lib/utils"
import {
  Leaf,
  ArrowLeft,
  Undo2,
  Trash2,
  CheckCircle2,
  MapPin,
  Info,
} from "lucide-react"

// ── Helpers geográficos ──────────────────────────────────────────────────────

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

function calcCentroid(pts: LatLng[]) {
  return {
    lat: pts.reduce((s, p) => s + p.lat, 0) / pts.length,
    lng: pts.reduce((s, p) => s + p.lng, 0) / pts.length,
  }
}

// ── Componente interno: captura cliques no mapa ──────────────────────────────

function MapClickHandler({ onClick }: { onClick: (ll: LatLng) => void }) {
  useMapEvents({ click: (e) => onClick(e.latlng) })
  return null
}

// ── Tipos ────────────────────────────────────────────────────────────────────

interface Cultura {
  id: string
  label: string
}

interface FormData {
  nome: string
  empresa: string
  email: string
  cultura: string
}

// ── Página ───────────────────────────────────────────────────────────────────

export default function DemoPage() {
  const navigate = useNavigate()
  const [form, setForm] = useState<FormData>({
    nome: "",
    empresa: "",
    email: "",
    cultura: "",
  })
  const [culturas, setCulturas] = useState<Cultura[]>([])
  const [points, setPoints] = useState<LatLng[]>([])
  const [confirmed, setConfirmed] = useState(false)

  useEffect(() => {
    fetch("http://localhost:8000/culturas")
      .then((r) => r.json())
      .then(setCulturas)
      .catch(() => {})
  }, [])

  useEffect(() => {
    document.documentElement.style.overflow = "hidden"
    document.body.style.overflow = "hidden"
    return () => {
      document.documentElement.style.overflow = ""
      document.body.style.overflow = ""
    }
  }, [])

  const addPoint = useCallback(
    (latlng: LatLng) => {
      if (confirmed) return
      setPoints((prev) => [...prev, latlng])
    },
    [confirmed]
  )

  const undo = () => setPoints((prev) => prev.slice(0, -1))

  const reset = () => {
    setPoints([])
    setConfirmed(false)
  }

  const handleConfirm = async () => {
    if (points.length < 3) return

    const areaHa = calcAreaHa(points)
    const centroide = calcCentroid(points)

    const payload = {
      nome: form.nome,
      empresa: form.empresa,
      email: form.email,
      cultura: form.cultura,
      poligono: {
        coordenadas: points.map((p) => [p.lat, p.lng]),
        geoJSON: {
          type: "Feature",
          geometry: {
            type: "Polygon",
            coordinates: [
              [
                ...points.map((p) => [p.lng, p.lat]),
                [points[0].lng, points[0].lat],
              ],
            ],
          },
          properties: {
            areaHa: parseFloat(areaHa.toFixed(2)),
            centroide,
          },
        },
        centroide,
        areaHa: parseFloat(areaHa.toFixed(2)),
        bbox: {
          norte: Math.max(...points.map((p) => p.lat)),
          sul: Math.min(...points.map((p) => p.lat)),
          leste: Math.max(...points.map((p) => p.lng)),
          oeste: Math.min(...points.map((p) => p.lng)),
        },
        totalPontos: points.length,
      },
      timestamp: new Date().toISOString(),
    }

    try {
      const res = await fetch("http://localhost:8000/mock/analysis", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })
      const analysis = await res.json()
      navigate("/resultado", { state: { analysis } })
    } catch {
      console.log("🌱 SafraViva — Demo Request (offline):", payload)
      setConfirmed(true)
    }
  }

  const canConfirm = points.length >= 3 && !!form.nome && !!form.email && !!form.cultura
  const areaPreview = calcAreaHa(points)
  const centroide = points.length >= 3 ? calcCentroid(points) : null

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* ── Header ── */}
      <header className="border-b bg-background/95 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto max-w-7xl px-4 h-14 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <div className="w-7 h-7 bg-primary rounded-lg flex items-center justify-center shrink-0">
              <Leaf className="w-3.5 h-3.5 text-primary-foreground" />
            </div>
            <span className="font-bold text-sm">SafraViva</span>
          </Link>
          <Button variant="ghost" size="sm" asChild>
            <Link to="/" className="gap-1.5">
              <ArrowLeft className="w-3.5 h-3.5" />
              Voltar
            </Link>
          </Button>
        </div>
      </header>

      {/* ── Layout principal ── */}
      <div className="flex-1 container mx-auto max-w-7xl px-4 py-6 grid lg:grid-cols-[360px_1fr] gap-6 items-start lg:h-[calc(100vh-56px)] lg:overflow-hidden lg:min-h-0">

        {/* ── Painel esquerdo: formulário ── */}
        <div className="flex flex-col gap-4 lg:h-full lg:overflow-y-auto lg:min-h-0">
          <div>
            <h1 className="text-xl font-bold">Solicitar Demo</h1>
            <p className="text-sm text-muted-foreground mt-0.5">
              Preencha seus dados e marque a área de interesse no mapa.
            </p>
          </div>

          {/* Formulário */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
                Seus dados
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="space-y-1">
                <Label htmlFor="nome">Nome completo *</Label>
                <Input
                  id="nome"
                  placeholder="João Silva"
                  value={form.nome}
                  onChange={(e) => setForm({ ...form, nome: e.target.value })}
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="empresa">Empresa</Label>
                <Input
                  id="empresa"
                  placeholder="Seguradora / Cooperativa"
                  value={form.empresa}
                  onChange={(e) =>
                    setForm({ ...form, empresa: e.target.value })
                  }
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="email">E-mail *</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="joao@empresa.com.br"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                />
              </div>
              <div className="space-y-1">
                <Label>Cultura *</Label>
                <Select
                  value={form.cultura}
                  onValueChange={(v) => setForm({ ...form, cultura: v })}
                  disabled={culturas.length === 0}
                >
                  <SelectTrigger>
                    <SelectValue placeholder={culturas.length === 0 ? "Carregando…" : "Selecione a cultura"} />
                  </SelectTrigger>
                  <SelectContent>
                    {culturas.map((c) => (
                      <SelectItem key={c.id} value={c.id}>
                        {c.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          {/* Status do polígono */}
          <Card className="flex-1 min-h-0">
            <CardContent className="p-4 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Área selecionada</span>
                <Badge
                  className={cn(
                    points.length >= 3
                      ? "bg-primary text-primary-foreground border-0"
                      : ""
                  )}
                  variant={points.length >= 3 ? "default" : "outline"}
                >
                  {points.length} pontos
                </Badge>
              </div>

              {points.length >= 3 && centroide ? (
                <>
                  <Separator />
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <p className="text-xs text-muted-foreground mb-0.5">
                        Área estimada
                      </p>
                      <p className="font-bold text-primary">
                        {areaPreview >= 10000
                          ? `${(areaPreview / 100).toFixed(1)} km²`
                          : `${areaPreview.toFixed(1)} ha`}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground mb-0.5">
                        Centroide
                      </p>
                      <p className="font-mono text-xs leading-relaxed">
                        {centroide.lat.toFixed(4)},
                        <br />
                        {centroide.lng.toFixed(4)}
                      </p>
                    </div>
                  </div>
                </>
              ) : (
                <p className="text-xs text-muted-foreground">
                  {points.length === 0
                    ? "Clique no mapa para começar."
                    : `Adicione mais ${3 - points.length} ponto${3 - points.length > 1 ? "s" : ""} para fechar o polígono.`}
                </p>
              )}
            </CardContent>
          </Card>

          {/* CTA / Sucesso */}
          <div className="mt-auto flex flex-col gap-2">
          {confirmed ? (
            <div className="space-y-2">
              <Alert className="border-primary/30 bg-primary/8">
                <CheckCircle2 className="h-4 w-4 text-primary" />
                <AlertDescription className="text-sm">
                  <span className="font-semibold text-primary block mb-0.5">
                    Parâmetros registrados!
                  </span>
                  Área e dados enviados com sucesso.
                </AlertDescription>
              </Alert>
              <Button className="w-full gap-2" asChild>
                <Link to="/resultado">Ver análise de risco</Link>
              </Button>
            </div>
          ) : (
            <Button
              className="w-full gap-2"
              disabled={!canConfirm}
              onClick={handleConfirm}
            >
              <CheckCircle2 className="w-4 h-4" />
              Confirmar e Registrar
            </Button>
          )}

          {!canConfirm && !confirmed && (
            <p className="text-xs text-muted-foreground text-center">
              {!form.nome || !form.email
                ? "Preencha nome e e-mail para continuar."
                : !form.cultura
                ? "Selecione a cultura."
                : "Marque pelo menos 3 pontos no mapa."}
            </p>
          )}
          </div>
        </div>

        {/* ── Painel direito: mapa ── */}
        <div className="flex flex-col gap-3 lg:h-full lg:overflow-hidden">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <MapPin className="w-4 h-4 text-primary" />
              <span className="text-sm font-semibold">
                Marque a área de interesse
              </span>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={undo}
                disabled={points.length === 0 || confirmed}
                className="gap-1.5"
              >
                <Undo2 className="w-3.5 h-3.5" />
                Desfazer
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={reset}
                disabled={points.length === 0}
                className="gap-1.5 text-destructive hover:text-destructive"
              >
                <Trash2 className="w-3.5 h-3.5" />
                Limpar
              </Button>
            </div>
          </div>

          <Alert className="py-2 border-primary/20 bg-primary/5">
            <Info className="h-3.5 w-3.5 text-primary" />
            <AlertDescription className="text-xs text-foreground/70">
              Clique no mapa para adicionar vértices do polígono. Com 3 ou mais
              pontos o contorno é desenhado automaticamente.
            </AlertDescription>
          </Alert>

          {/* Mapa Leaflet */}
          <div className="flex-1 min-h-0 rounded-xl overflow-hidden border shadow-sm" style={{ minHeight: 400 }}>
            <MapContainer
              center={[-12.7, -55.9]}
              zoom={6}
              style={{ height: "100%", width: "100%" }}
            >
              <TileLayer
                attribution='&copy; <a href="https://carto.com/">CARTO</a>'
                url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
              />

              <MapClickHandler onClick={addPoint} />

              {/* Preview da linha ainda aberta (< 3 pontos) */}
              {points.length >= 2 && (
                <Polyline
                  positions={points}
                  pathOptions={{
                    color: "#16a34a",
                    weight: 2,
                    dashArray: "6 4",
                    opacity: 0.7,
                  }}
                />
              )}

              {/* Polígono fechado (≥ 3 pontos) */}
              {points.length >= 3 && (
                <Polygon
                  positions={points}
                  pathOptions={{
                    color: "#16a34a",
                    weight: confirmed ? 3 : 2,
                    fillColor: "#16a34a",
                    fillOpacity: confirmed ? 0.3 : 0.12,
                  }}
                />
              )}

              {/* Marcadores de vértices */}
              {points.map((pt, i) => (
                <CircleMarker
                  key={i}
                  center={pt}
                  radius={i === 0 ? 8 : 5}
                  pathOptions={{
                    fillColor: "#16a34a",
                    color: "#ffffff",
                    weight: 2,
                    fillOpacity: 1,
                  }}
                />
              ))}
            </MapContainer>
          </div>
        </div>
      </div>
    </div>
  )
}
