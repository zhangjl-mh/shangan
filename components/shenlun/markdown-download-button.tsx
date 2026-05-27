import Link from "next/link";
import { Download } from "lucide-react";
import { Button } from "@/components/ui/button";

export function ShenlunMarkdownDownloadButton() {
  return (
    <Button asChild className="no-print" variant="outline" size="sm">
      <Link href="/api/export/shenlun">
        <Download size={15} />
        导出 Markdown
      </Link>
    </Button>
  );
}
