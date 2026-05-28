import type { Metadata } from "next";
import "@/app/globals.css";
import { SiteHeader } from "@/components/layout/site-header";

export const metadata: Metadata = {
  title: "上岸 | 公考备考驾驶舱",
  description: "本地数据驱动的公考备考展示系统",
  applicationName: "上岸",
  icons: {
    icon: "/icon.svg",
    shortcut: "/icon.svg",
    apple: "/icon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body>
        <div aria-hidden="true" className="page-atmosphere" />
        <SiteHeader />
        {children}
      </body>
    </html>
  );
}
