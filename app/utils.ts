import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDisplayDate(date: Date) {
  return new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "full",
    timeZone: "Asia/Shanghai",
  }).format(date);
}

export function formatShortDate(value?: string) {
  if (!value) {
    return "--";
  }

  return value.slice(5, 10);
}
