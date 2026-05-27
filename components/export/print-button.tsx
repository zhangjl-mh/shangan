"use client";

import { Printer } from "lucide-react";
import { Button } from "@/components/ui/button";

export function PrintButton({ label = "导出 PDF" }: { label?: string }) {
  return (
    <Button className="no-print" variant="outline" size="sm" onClick={() => window.print()}>
      <Printer size={15} />
      {label}
    </Button>
  );
}
