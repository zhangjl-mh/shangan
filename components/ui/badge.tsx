import { cn } from "@/lib/utils";

export function Badge({
  className,
  children,
}: {
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <span
      className={cn(
        "label-sans inline-flex rounded-full border border-[#ded8cc] bg-[#faf8f2] px-3 py-1 text-xs text-[#596a62]",
        className,
      )}
    >
      {children}
    </span>
  );
}
