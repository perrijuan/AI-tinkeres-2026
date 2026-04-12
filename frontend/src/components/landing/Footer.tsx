import { Separator } from "@/components/ui/separator"
import { Badge } from "@/components/ui/badge"
import BrandLogo from "@/components/BrandLogo"

const links = {
  Produto: [
    "Como Funciona",
    "Para Seguradoras",
    "Para Produtores",
    "Modelo de Negócio",
  ],
  Empresa: ["Sobre a SafraViva", "Impacto", "Tecnologia", "Contato"],
  Legal: ["Termos de Uso", "Privacidade", "Política de Cookies"],
}

export default function Footer() {
  return (
    <footer className="bg-slate-950 text-slate-400">
      <div className="container mx-auto max-w-7xl px-4 pt-16 pb-8">
        <div className="grid md:grid-cols-4 gap-10 mb-12">
          <div className="space-y-4">
            <div className="flex items-center gap-2.5">
              <BrandLogo className="h-9 w-9 rounded-[1rem] border-white/10 bg-white/95 shadow-[0_10px_28px_rgba(0,0,0,0.22)]" imageClassName="rounded-[0.8rem]" />
              <span className="font-bold text-white text-base">SafraViva</span>
            </div>
            <p className="text-sm leading-relaxed">
              Inteligência climática para decisões mais seguras no
              agronegócio brasileiro.
            </p>
            <div className="flex gap-1.5 flex-wrap">
              {["ODS 2", "ODS 13", "ODS 17"].map((ods) => (
                <Badge
                  key={ods}
                  variant="outline"
                  className="border-slate-700 text-slate-500 text-[10px]"
                >
                  {ods}
                </Badge>
              ))}
            </div>
          </div>

          {Object.entries(links).map(([section, items]) => (
            <div key={section} className="space-y-4">
              <h4 className="text-white font-semibold text-sm">{section}</h4>
              <ul className="space-y-2.5">
                {items.map((item) => (
                  <li key={item}>
                    <a
                      href="#"
                      className="text-sm hover:text-white transition-colors"
                    >
                      {item}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <Separator className="bg-slate-800 mb-8" />

        <div className="flex flex-col sm:flex-row justify-between items-center gap-3 text-xs text-slate-600">
          <p>© 2026 SafraViva. Todos os direitos reservados.</p>
          <p>Feito com dedicação para o agronegócio brasileiro 🌱</p>
        </div>
      </div>
    </footer>
  )
}
