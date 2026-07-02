"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/app/utils";

const navigation = [
  { label: "首页", href: "/" },
  { label: "申论", href: "/shenlun" },
  { label: "行测", href: "/xingce" },
  { label: "时政", href: "/news" },
  { label: "岗位", href: "/jobs" },
];

export function SiteHeader() {
  const pathname = usePathname();
  const usesJobsLayout = pathname.startsWith("/jobs");

  return (
    <header className="sticky top-0 z-20 border-b border-[#e5ded2]/85 bg-[#faf8f3]/92 backdrop-blur-md">
      <div
        className={cn(
          "mx-auto flex items-center px-5",
          usesJobsLayout
            ? "h-[94px] max-w-[1800px] lg:px-10"
            : "h-[74px] max-w-[1480px] lg:px-10",
        )}
      >
        <Link
          href="/"
          className={cn(
            "flex shrink-0 items-center",
            usesJobsLayout ? "gap-4" : "gap-3.5",
          )}
          aria-label="上岸 首页"
        >
          <Image
            src="/assets/brand-mark.svg"
            alt="上岸 Logo"
            width={usesJobsLayout ? 54 : 42}
            height={usesJobsLayout ? 54 : 42}
            priority
          />
          <span
            className={cn(
              "ink-title",
              usesJobsLayout
                ? "text-[28px] lg:text-[32px]"
                : "text-xl lg:text-[25px]",
            )}
          >
            上岸
          </span>
        </Link>
        <nav
          className={cn(
            "mx-auto hidden h-full items-center md:flex",
            usesJobsLayout
              ? "gap-10 lg:gap-16 2xl:translate-x-[70px]"
              : "gap-8 lg:gap-12",
          )}
        >
          {navigation.map((item) => {
            const active =
              item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);

            return (
              <Link
                href={item.href}
                key={item.href}
                className={cn(
                  "relative flex h-full items-center tracking-[.14em] text-[#303b37] transition-colors",
                  usesJobsLayout
                    ? "px-3 text-[20px]"
                    : "px-2 text-[17px]",
                  active && "text-deep-green",
                )}
              >
                {item.label}
                {active ? (
                  <span className="absolute inset-x-0 bottom-0 h-[3px] bg-[#59796c]" />
                ) : null}
              </Link>
            );
          })}
        </nav>
        <div
          className={cn("ml-auto", usesJobsLayout ? "w-[54px]" : "w-[42px]")}
          aria-hidden="true"
        />
      </div>
    </header>
  );
}
