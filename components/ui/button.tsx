import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "label-sans inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg text-sm transition-colors disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default:
          "bg-accent px-5 py-3 text-white shadow-[0_4px_14px_rgba(186,100,82,.25)] hover:bg-[#ae5949]",
        outline:
          "border border-[#ded6c9] bg-white/55 px-4 py-2 text-[#46564f] hover:bg-white",
        ghost: "px-3 py-2 text-[#52645d] hover:bg-[#e9ede7]",
      },
      size: {
        default: "h-11",
        sm: "h-9 text-[13px]",
        icon: "size-10 p-0",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

function Button({
  className,
  variant,
  size,
  asChild = false,
  ...props
}: React.ComponentProps<"button"> &
  VariantProps<typeof buttonVariants> & {
    asChild?: boolean;
  }) {
  const Comp = asChild ? Slot : "button";

  return (
    <Comp
      data-slot="button"
      className={cn(buttonVariants({ variant, size }), className)}
      {...props}
    />
  );
}

export { Button, buttonVariants };
