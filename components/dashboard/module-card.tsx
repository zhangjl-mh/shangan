import Link from "next/link";
import type { LucideIcon } from "lucide-react";
import { Card } from "@/components/ui/card";

export function ModuleCard({
  icon: Icon,
  title,
  description,
  note,
  href,
  tint,
}: {
  icon: LucideIcon;
  title: string;
  description: string;
  note: string;
  href: string;
  tint: string;
}) {
  return (
    <Link href={href}>
      <Card className="hover-lift flex h-full min-h-[116px] items-center gap-5 px-6 py-5">
        <span className={`flex size-[62px] shrink-0 items-center justify-center rounded-2xl text-white ${tint}`}>
          <Icon size={32} strokeWidth={1.7} />
        </span>
        <span className="min-w-0">
          <span className="block text-[21px] font-semibold tracking-[.1em] text-[#293631]">{title}</span>
          <span className="muted-copy mt-1 block truncate text-sm">{description}</span>
          <span className="muted-copy mt-1 block truncate text-sm">{note}</span>
        </span>
      </Card>
    </Link>
  );
}
