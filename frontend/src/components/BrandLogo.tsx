import { cn } from "@/lib/utils"

type BrandLogoProps = {
  className?: string
  imageClassName?: string
  alt?: string
}

export default function BrandLogo({
  className,
  imageClassName,
  alt = "Logo SafraViva",
}: BrandLogoProps) {
  return (
    <span
      className={cn(
        "inline-flex shrink-0 items-center justify-center overflow-hidden rounded-xl border border-black/8 bg-white/96 p-1 shadow-[0_8px_24px_rgba(15,23,42,0.10)] backdrop-blur-sm dark:border-white/12 dark:bg-white/92",
        className,
      )}
    >
      <img
        src="/logo.jpeg"
        alt={alt}
        className={cn("h-full w-full rounded-[0.7rem] object-cover", imageClassName)}
      />
    </span>
  )
}
