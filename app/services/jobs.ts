import "server-only";

import { readFile } from "node:fs/promises";
import path from "node:path";
import type {
  JobIndex,
  JobPosition,
  JobQuery,
  JobQueryResult,
} from "@/app/types/content";
import { jobsDirectory } from "@/app/services/storage-paths";

let catalogPromise: Promise<{
  index: JobIndex | null;
  positions: JobPosition[];
}> | null = null;

async function loadCatalog() {
  if (!catalogPromise) {
    catalogPromise = (async () => {
      try {
        const index = JSON.parse(
          await readFile(path.join(jobsDirectory, "index.json"), "utf8"),
        ) as JobIndex;
        const catalogPath = path.join(process.cwd(), index.catalog.path);
        const contents = await readFile(catalogPath, "utf8");
        const positions = contents
          .split(/\r?\n/)
          .filter(Boolean)
          .map((line) => JSON.parse(line) as JobPosition);
        return { index, positions };
      } catch {
        return { index: null, positions: [] };
      }
    })();
  }
  return catalogPromise;
}

export async function queryJobs(query: JobQuery = {}): Promise<JobQueryResult> {
  const { index, positions } = await loadCatalog();
  const keyword = query.keyword?.trim().toLocaleLowerCase("zh-CN") ?? "";
  const pageSize = Math.min(Math.max(query.pageSize ?? 20, 1), 100);
  const page = Math.max(query.page ?? 1, 1);

  const filtered = positions.filter((position) => {
    if (query.exam && query.exam !== "all" && position.examId !== query.exam) {
      return false;
    }
    if (
      query.region &&
      query.region !== "all" &&
      !position.region.includes(query.region)
    ) {
      return false;
    }
    if (
      query.eligibility &&
      query.eligibility !== "all" &&
      query.eligibility !== "default" &&
      position.eligibility !== query.eligibility
    ) {
      return false;
    }
    if (
      (!query.eligibility || query.eligibility === "default") &&
      position.eligibility === "ineligible"
    ) {
      return false;
    }
    if (
      query.timing &&
      query.timing !== "all" &&
      position.timingStatus !== query.timing
    ) {
      return false;
    }
    if (!keyword) {
      return true;
    }
    return [
      position.title,
      position.organization,
      position.department,
      position.positionCode,
      position.region,
      position.requirements.major,
    ].some((value) => value.toLocaleLowerCase("zh-CN").includes(keyword));
  });

  const pageCount = Math.max(Math.ceil(filtered.length / pageSize), 1);
  const normalizedPage = Math.min(page, pageCount);
  const start = (normalizedPage - 1) * pageSize;
  const exams = Array.from(
    new Map(
      positions.map((position) => [
        position.examId,
        { id: position.examId, label: position.examLabel },
      ]),
    ).values(),
  );
  const regions = Array.from(
    new Set(positions.map((position) => position.region).filter(Boolean)),
  ).sort((a, b) => a.localeCompare(b, "zh-CN"));

  return {
    items: filtered.slice(start, start + pageSize),
    total: filtered.length,
    page: normalizedPage,
    pageSize,
    pageCount,
    exams,
    regions,
    index,
  };
}

export function resetJobCatalogCacheForTests() {
  catalogPromise = null;
}
