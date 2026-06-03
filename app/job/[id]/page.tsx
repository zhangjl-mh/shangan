import { notFound } from "next/navigation";
import { JobDetailView } from "@/components/job/job-detail-view";
import { readEligibleJobs } from "@/lib/content";

export const dynamic = "force-dynamic";

export default async function JobDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const report = await readEligibleJobs();
  const positionId = decodeURIComponent(id);
  const position = report?.positions.find((item) => item.id === positionId);

  if (!position) {
    notFound();
  }

  return (
    <main className="mx-auto max-w-[1320px] px-5 py-9 lg:px-6">
      <JobDetailView position={position} />
    </main>
  );
}
