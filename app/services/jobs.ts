import "server-only";

import { readFile, stat } from "node:fs/promises";
import path from "node:path";
import type {
  JobApplicationStatus,
  JobIndex,
  JobIndexCatalog,
  JobPosition,
  JobQuery,
  JobQueryResult,
} from "@/app/types/content";
import { jobsDirectory } from "@/app/services/storage-paths";

let indexPromise: Promise<JobIndex | null> | null = null;
let eligibleCatalogPromise: Promise<JobPosition[]> | null = null;
let confirmationCatalogPromise: Promise<JobPosition[]> | null = null;
let indexMtimeMs = -1;

const regionOptions = ["北京", "天津", "河北", "雄安新区", "石家庄"];
const preferredRegions = ["北京", "天津", "雄安", "石家庄"];
const eligibleCatalogPath = "data/jobs/catalog/eligible.jsonl";
const confirmationCatalogPath =
  "data/jobs/catalog/needs-confirmation.jsonl";

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
    eligibleCatalogPromise = null;
    confirmationCatalogPromise = null;
    indexPromise = (async () => {
      try {
        const value = JSON.parse(await readFile(indexPath, "utf8")) as JobIndex;
        return value.schemaVersion === "4.0" ? value : null;
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
  const relative = path.relative(jobsDirectory, catalogPath);
  if (relative.startsWith("..") || path.isAbsolute(relative)) {
    throw new Error("Job catalog path escapes data/jobs");
  }
  const contents = await readFile(catalogPath, "utf8");
  return contents
    .split(/\r?\n/)
    .filter(Boolean)
    .map((line) => JSON.parse(line) as JobPosition);
}

async function loadPositions(index: JobIndex | null, query: JobQuery) {
  if (!index) {
    return [];
  }
  if (query.eligibility === "needs_confirmation") {
    confirmationCatalogPromise ??= readCatalog(
      index.needsConfirmationCatalog,
      confirmationCatalogPath,
    ).catch(() => []);
    return confirmationCatalogPromise;
  }
  eligibleCatalogPromise ??= readCatalog(
    index.eligibleCatalog,
    eligibleCatalogPath,
  ).catch(() => []);
  return eligibleCatalogPromise;
}

const applicationOrder: Record<JobApplicationStatus, number> = {
  open: 0,
  upcoming: 1,
  unknown: 2,
  closed: 3,
};

function preferenceRank(position: JobPosition) {
  const index = preferredRegions.findIndex((region) =>
    position.region.includes(region),
  );
  return index === -1 ? preferredRegions.length : index;
}

function comparePositions(left: JobPosition, right: JobPosition) {
  const batch =
    Number(left.batchStatus === "previous_reference") -
    Number(right.batchStatus === "previous_reference");
  if (batch) return batch;
  const application =
    applicationOrder[left.applicationStatus] -
    applicationOrder[right.applicationStatus];
  if (application) return application;
  const preference = preferenceRank(left) - preferenceRank(right);
  if (preference) return preference;
  return (
    left.sourceLabel.localeCompare(right.sourceLabel, "zh-CN") ||
    left.organization.localeCompare(right.organization, "zh-CN") ||
    left.positionCode.localeCompare(right.positionCode, "zh-CN")
  );
}

export async function queryJobs(query: JobQuery = {}): Promise<JobQueryResult> {
  const index = await loadIndex();
  const normalizedQuery: JobQuery = {
    ...query,
    eligibility: query.eligibility ?? "eligible",
  };
  const positions = await loadPositions(index, normalizedQuery);
  const keyword = query.keyword?.trim().toLocaleLowerCase("zh-CN") ?? "";
  const pageSize = Math.min(Math.max(query.pageSize ?? 20, 1), 100);
  const page = Math.max(query.page ?? 1, 1);

  const filtered = positions
    .filter((position) => {
      if (
        query.exam &&
        query.exam !== "all" &&
        position.sourceId !== query.exam
      ) {
        return false;
      }
      if (
        query.category &&
        query.category !== "all" &&
        position.category !== query.category
      ) {
        return false;
      }
      if (query.region && query.region !== "all") {
        const matchesHebei =
          query.region === "河北" &&
          position.sourceId === "hebei-civil-service";
        if (!matchesHebei && !position.region.includes(query.region)) {
          return false;
        }
      }
      if (
        query.batch &&
        query.batch !== "all" &&
        position.batchStatus !== query.batch
      ) {
        return false;
      }
      if (
        query.application &&
        query.application !== "all" &&
        position.applicationStatus !== query.application
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
      ].some((value) =>
        value.toLocaleLowerCase("zh-CN").includes(keyword),
      );
    })
    .sort(comparePositions);

  const pageCount = Math.max(Math.ceil(filtered.length / pageSize), 1);
  const normalizedPage = Math.min(page, pageCount);
  const exams =
    index?.sources.map((source) => ({
      id: source.sourceId,
      label: source.label,
    })) ??
    Array.from(
      new Map(
        positions.map((position) => [
          position.sourceId,
          { id: position.sourceId, label: position.sourceLabel },
        ]),
      ).values(),
    );
  return {
    items: filtered.slice(
      startIndex(normalizedPage, pageSize),
      normalizedPage * pageSize,
    ),
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
  eligibleCatalogPromise = null;
  confirmationCatalogPromise = null;
  indexMtimeMs = -1;
}
