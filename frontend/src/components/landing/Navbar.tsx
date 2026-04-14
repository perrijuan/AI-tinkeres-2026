import { useState, useEffect } from "react"
import { Link } from "react-router-dom"
import {
  NavigationMenu,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
  navigationMenuTriggerStyle,
} from "@/components/ui/navigation-menu"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { Menu } from "lucide-react"
import BrandLogo from "@/components/BrandLogo"
import { cn } from "@/lib/utils"
import { trackCTAClick, trackNavClick } from "@/lib/analytics"

const navLinks = [
  { href: "#problema", label: "Problema" },
  { href: "#solucao", label: "Solução" },
  { href: "#como-funciona", label: "Como Funciona" },
  { href: "#para-quem", label: "Para Quem" },
  { href: "#mercado", label: "Mercado" },
]

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false)
  const [open, setOpen] = useState(false)

  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 20)
    window.addEventListener("scroll", handler)
    return () => window.removeEventListener("scroll", handler)
  }, [])

  return (
    <header
      className={cn(
        "fixed top-0 left-0 right-0 z-50 transition-all duration-300",
        scrolled
          ? "bg-background/95 backdrop-blur-md border-b shadow-sm"
          : "bg-transparent"
      )}
    >
      <nav className="container mx-auto flex h-16 max-w-7xl items-center justify-between gap-3 px-4">
        <a href="/" className="flex min-w-0 items-center gap-2.5">
          <BrandLogo className="h-9 w-9 rounded-[1rem]" imageClassName="rounded-[0.8rem]" />
          <div className="min-w-0 leading-none">
            <span
              className={cn(
                "block truncate font-bold text-base transition-colors",
                scrolled ? "text-foreground" : "text-white"
              )}
            >
              SafraViva
            </span>
            <span
              className={cn(
                "block truncate text-[10px] transition-colors",
                scrolled ? "text-muted-foreground" : "text-white/60"
              )}
            >
              Inteligência Climática
            </span>
          </div>
        </a>

        <div className="hidden md:flex items-center">
          <NavigationMenu>
            <NavigationMenuList>
              {navLinks.map((link) => (
                <NavigationMenuItem key={link.href}>
                  <NavigationMenuLink
                    id={`nav-link-${link.href.replace("#", "")}`}
                    href={link.href}
                    onClick={() => trackNavClick(link.label, link.href)}
                    className={cn(
                      navigationMenuTriggerStyle(),
                      !scrolled &&
                        "bg-transparent text-white/90 hover:bg-white/10 hover:text-white"
                    )}
                  >
                    {link.label}
                  </NavigationMenuLink>
                </NavigationMenuItem>
              ))}
            </NavigationMenuList>
          </NavigationMenu>
        </div>

        <div className="flex shrink-0 items-center gap-2">
          <Button className="hidden md:flex" asChild>
            <Link
              id="btn-nav-solicitar-demo-desktop"
              to="/solicitar-demo"
              onClick={() => trackCTAClick("btn-nav-solicitar-demo-desktop", "Solicitar Demo", "/solicitar-demo")}
            >
              Solicitar Demo
            </Link>
          </Button>

          <Sheet open={open} onOpenChange={setOpen}>
            <SheetTrigger asChild>
              <Button
                id="btn-nav-mobile-menu"
                variant="ghost"
                size="icon"
                className={cn(
                  "md:hidden",
                  !scrolled && "text-white hover:bg-white/10 hover:text-white"
                )}
              >
                <Menu className="w-5 h-5" />
              </Button>
            </SheetTrigger>
            <SheetContent side="right" className="w-[85vw] max-w-72">
              <div className="flex items-center gap-2.5 mb-6 mt-2">
                <BrandLogo className="h-9 w-9 rounded-[1rem]" imageClassName="rounded-[0.8rem]" />
                <span className="font-bold text-base">SafraViva</span>
              </div>
              <Separator className="mb-4" />
              <div className="flex flex-col gap-1">
                {navLinks.map((link) => (
                  <a
                    key={link.href}
                    id={`nav-mobile-link-${link.href.replace("#", "")}`}
                    href={link.href}
                    onClick={() => { setOpen(false); trackNavClick(link.label, link.href) }}
                    className="px-3 py-2.5 rounded-md text-sm hover:bg-accent transition-colors font-medium"
                  >
                    {link.label}
                  </a>
                ))}
              </div>
              <Separator className="my-4" />
              <Button className="w-full" asChild>
                <Link
                  id="btn-nav-solicitar-demo-mobile"
                  to="/solicitar-demo"
                  onClick={() => trackCTAClick("btn-nav-solicitar-demo-mobile", "Solicitar Demo", "/solicitar-demo")}
                >
                  Solicitar Demo
                </Link>
              </Button>
            </SheetContent>
          </Sheet>
        </div>
      </nav>
    </header>
  )
}
