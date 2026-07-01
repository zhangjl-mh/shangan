import { NextRequest, NextResponse } from "next/server";
import type {
  JobApplicationStatus,
  JobBatchStatus,
  JobCategory,
  JobEligibility,
} from "@/app/types/content";
import { queryJobs } from "@/app/services/jobs";

function integer(value: string | null, fallback: number) {
  const parsed = Number.parseInt(value ?? "", 10);
  return Number.isFinite(parsed) ? parsed : fallback;
}

export async function GET(request: NextRequest) {
  const params = request.nextUrl.searchParams;
  const eligibility = params.get("eligibility") ?? "eligible";
  if (!["eligible", "needs_confirmation"].includes(eligibility)) {
    return NextResponse.json(
      { error: "eligibility must be eligible or needs_confirmation" },
      { status: 400 },
    );
  }
  const result = await queryJobs({
    exam: params.get("exam") ?? undefined,
    region: params.get("region") ?? undefined,
    category:
      (params.get("category") as JobCategory | "all" | null) ?? "all",
    eligibility: eligibility as JobEligibility,
    batch: (params.get("batch") as JobBatchStatus | "all" | null) ?? "all",
    application:
      (params.get("application") as
        | JobApplicationStatus
        | "all"
        | null) ?? "all",
    keyword: params.get("q") ?? undefined,
    page: integer(params.get("page"), 1),
    pageSize: integer(params.get("pageSize"), 20),
  });
  return NextResponse.json(result);
}
