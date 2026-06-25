import "server-only";

import { readFile, stat } from "node:fs/promises";
import path from "node:path";
import type {
  JobIndex,
  JobIndexCatalog,
  JobPosition,
  JobQuery,
  JobQueryResult,
} from "@/app/types/content";
import { jobsDirectory } from "@/app/services/storage-paths";

let indexPromise: Promise<JobIndex | null> | null = null;
let allCatalogPromise: Promise<JobPosition[]> | null = null;
let eligibleCatalogPromise: Promise<JobPosition[]> | null = null;
let indexMtimeMs = -1;

const regionOptions = ["北京", "天津", "河北", "雄安新区", "石家庄"];
const allCatalogPath = "data/jobs/catalog/positions.jsonl";
const eligibleCatalogPath = "data/jobs/catalog/eligible.jsonl";

async function loadIndex() {
  const indexPath = path.join(jobsDirectory, "index.json");
  let nextIndexMtimeMs: number;
  try {
    nextIndexMtimeMs = (await stat(indexPath)).mtimeMs;
  } catch {
    return null;
  }
  if (!indexPromise || nextIndexMtimeMs !== indexMtimeMs) {
    indexMtimeMs = nextIndexMtimeMs;
    allCatalogPromise = null;
    eligibleCatalogPromise = null;
    indexPromise = (async () => {
      try {
        return JSON.parse(await readFile(indexPath, "utf8")) as JobIndex;
      } catch {
        return null;
      }
    })();
  }
  return indexPromise;
}

async function readCatalog(
  artifact: JobIndexCatalog | undefined,
  expectedPath: string,
) {
  if (!artifact || artifact.path !== expectedPath) {
    throw new Error("Unexpected job catalog path");
  }
  const catalogPath = path.join(
    jobsDirectory,
    ...artifact.path.replace(/^data\/jobs\//, "").split("/"),
  );
  const contents = await readFile(catalogPath, "utf8");
  return contents
    .split(/\r?\n/)
    .filter(Boolean)
    .map((line) => JSON.parse(line) as JobPosition);
}

async function loadPositions(
  index: JobIndex | null,
  useEligibleCatalog: boolean,
) {
  if (!index) {
    return [];
  }
  if (useEligibleCatalog) {
    eligibleCatalogPromise ??= readCatalog(
      index.eligibleCatalog,
      eligibleCatalogPath,
    ).catch(() => readCatalog(index.catalog, allCatalogPath).then((positions) => (
      positions.filter((position) => position.eligibility === "eligible")
    )));
    return eligibleCatalogPromise;
  }
  allCatalogPromise ??= readCatalog(index.catalog, allCatalogPath).catch(() => []);
  return allCatalogPromise;
}

export async function queryJobs(query: JobQuery = {}): Promise<JobQueryResult> {
  const index = await loadIndex();
  const eligibility = query.eligibility ?? "eligible";
  const positions = await loadPositions(index, eligibility === "eligible");
  const keyword = query.keyword?.trim().toLocaleLowerCase("zh-CN") ?? "";
  const pageSize = Math.min(Math.max(query.pageSize ?? 20, 1), 100);
  const page = Math.max(query.page ?? 1, 1);

  const filtered = positions.filter((position) => {
    if (query.exam && query.exam !== "all" && position.examId !== query.exam) {
      return false;
    }
    if (query.region && query.region !== "all") {
      const matchesHebei =
        query.region === "河北" && position.examId === "hebei-civil-service";
      if (!matchesHebei && !position.region.includes(query.region)) {
        return false;
      }
    }
    if (
      eligibility &&
      eligibility !== "all" &&
      eligibility !== "default" &&
      position.eligibility !== eligibility
    ) {
      return false;
    }
    if (
      eligibility === "default" &&
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
  const exams = index?.sources.map((source) => ({
    id: source.examId,
    label: source.label,
  })) ?? Array.from(
    new Map(
      positions.map((position) => [
        position.examId,
        { id: position.examId, label: position.examLabel },
      ]),
    ).values(),
  );
  return {
    items: filtered.slice(startIndex(normalizedPage, pageSize), normalizedPage * pageSize),
    total: filtered.length,
    page: normalizedPage,
    pageSize,
    pageCount,
    exams,
    regions: regionOptions,
    index,
  };
}

function startIndex(page: number, pageSize: number) {
  return (page - 1) * pageSize;
}

export function resetJobCatalogCacheForTests() {
  indexPromise = null;
  allCatalogPromise = null;
  eligibleCatalogPromise = null;
  indexMtimeMs = -1;
}
