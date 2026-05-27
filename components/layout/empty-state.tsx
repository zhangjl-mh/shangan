import { FileQuestion } from "lucide-react";
import { cn } from "@/lib/utils";

export function EmptyState({
  title,
  description,
  className,
}: {
  title: string;
  description: string;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "label-sans flex min-h-40 flex-col items-center justify-center rounded-xl border border-dashed border-[#ddd5c7] bg-[#faf8f2]/60 px-5 text-center",
        className,
      )}
    >
      <FileQuestion className="mb-3 text-[#91a397]" size={27} strokeWidth={1.5} />
      <p className="text-[15px] font-medium text-[#35453e]">{title}</p>
      <p className="mt-2 max-w-md text-sm leading-6 text-[#737f79]">{description}</p>
    </div>
  );
}
