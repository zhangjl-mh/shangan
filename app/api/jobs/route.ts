import { NextRequest, NextResponse } from "next/server";
import type { JobEligibility } from "@/app/types/content";
import { queryJobs } from "@/app/services/jobs";

function integer(value: string | null, fallback: number) {
  const parsed = Number.parseInt(value ?? "", 10);
  return Number.isFinite(parsed) ? parsed : fallback;
}

export async function GET(request: NextRequest) {
  const params = request.nextUrl.searchParams;
  const result = await queryJobs({
    exam: params.get("exam") ?? undefined,
    region: params.get("region") ?? undefined,
    eligibility: (params.get("eligibility") as JobEligibility | "default" | "all" | null) ?? "eligible",
    timing: (params.get("timing") as "active" | "historical" | "all" | null) ?? "all",
    keyword: params.get("q") ?? undefined,
    page: integer(params.get("page"), 1),
    pageSize: integer(params.get("pageSize"), 20),
  });
  return NextResponse.json(result);
}
