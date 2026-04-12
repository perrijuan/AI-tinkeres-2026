// Logos reais das tecnologias e organizações integradas ao SafraViva.
// Os arquivos SVG/PNG ficam em /public/logos/.

interface LogoPartner {
  src: string
  alt: string
  label: string
  desc: string
  /** Cor de fundo do container do logo (usado quando o logo é branco) */
  bgColor?: string
  /** Altura do elemento img em px */
  height?: number
}

interface TextPartner {
  abbr: string
  label: string
  desc: string
  color: string
}

const logoPartners: LogoPartner[] = [
  {
    src: "/logos/google.svg",
    alt: "Google",
    label: "Google Earth Engine",
    desc: "Infraestrutura geoespacial",
    height: 22,
  },
  {
    src: "/logos/gemini.svg",
    alt: "Google Gemini",
    label: "Gemini",
    desc: "IA generativa · Safrinia",
    height: 28,
  },
  {
    src: "/logos/nasa.svg",
    alt: "NASA",
    label: "NASA · MODIS",
    desc: "Vegetação e temperatura",
    height: 40,
  },
  {
    src: "/logos/noaa.svg",
    alt: "NOAA",
    label: "NOAA · GFS",
    desc: "Previsão climática global",
    bgColor: "#003087",
    height: 36,
  },
  {
    src: "/logos/esa.svg",
    alt: "ESA",
    label: "ESA · Sentinel-2",
    desc: "Satélite óptico Copernicus",
    height: 36,
  },
  {
    src: "/logos/alphaearth.png",
    alt: "AlphaEarth",
    label: "AlphaEarth",
    desc: "Cluster territorial",
    height: 32,
  },
]

const textPartners: TextPartner[] = [
  {
    abbr: "ZARC",
    label: "MAPA · Brasil",
    desc: "Zoneamento agrícola de risco",
    color: "#2E7D32",
  },
]

export default function TechPartnersSection() {
  return (
    <section className="py-10 bg-white border-b border-border/50">
      <div className="container mx-auto max-w-7xl px-4">
        <p className="text-center text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground/50 mb-8">
          Dados e infraestrutura que sustentam cada análise
        </p>

        <div className="flex flex-wrap justify-center items-center gap-x-10 gap-y-6">
          {logoPartners.map((p) => (
            <div
              key={p.alt}
              className="group flex flex-col items-center gap-2 cursor-default"
              title={p.desc}
            >
              {/* Container do logo */}
              <div
                className="flex items-center justify-center rounded-xl px-3 transition-all duration-200 group-hover:shadow-sm"
                style={{
                  backgroundColor: p.bgColor ?? "transparent",
                  height: 52,
                  minWidth: 64,
                  padding: p.bgColor ? "8px 12px" : undefined,
                }}
              >
                <img
                  src={p.src}
                  alt={p.alt}
                  style={{
                    height: p.height ?? 32,
                    width: "auto",
                    objectFit: "contain",
                    // NOAA tem fundo colorido próprio, não aplicar filtro
                    filter: p.bgColor
                      ? "brightness(0) invert(1)"
                      : "grayscale(100%) opacity(0.45)",
                    transition: "filter 0.2s",
                  }}
                  className="group-hover:[filter:grayscale(0%)_opacity(1)!important]"
                />
              </div>
              {/* Label abaixo */}
              <div className="text-center">
                <p className="text-[11px] font-semibold text-foreground/60 group-hover:text-foreground transition-colors leading-none">
                  {p.label}
                </p>
                <p className="text-[10px] text-muted-foreground/50 mt-0.5 leading-none">
                  {p.desc}
                </p>
              </div>
            </div>
          ))}

          {textPartners.map((p) => (
            <div
              key={p.abbr}
              className="group flex flex-col items-center gap-2 cursor-default"
              title={p.desc}
            >
              <div
                className="flex items-center justify-center rounded-xl px-4 transition-all duration-200 group-hover:shadow-sm"
                style={{
                  backgroundColor: `${p.color}18`,
                  border: `1.5px solid ${p.color}30`,
                  height: 52,
                  minWidth: 64,
                }}
              >
                <span
                  className="text-lg font-black tracking-tight"
                  style={{ color: p.color, opacity: 0.6 }}
                >
                  {p.abbr}
                </span>
              </div>
              <div className="text-center">
                <p className="text-[11px] font-semibold text-foreground/60 group-hover:text-foreground transition-colors leading-none">
                  {p.label}
                </p>
                <p className="text-[10px] text-muted-foreground/50 mt-0.5 leading-none">
                  {p.desc}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
