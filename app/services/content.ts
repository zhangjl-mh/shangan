import "server-only";

import { readdir, readFile } from "node:fs/promises";
import path from "node:path";
import type {
  DailyNews,
  JobFilterResult,
  StudyRoadmap,
} from "@/app/types/content";
import {
  dailyNewsDirectory,
  dataDirectory,
  jobsDirectory,
} from "@/app/services/storage-paths";

async function readJsonFile<T>(filePath: string): Promise<T | null> {
  try {
    const contents = await readFile(filePath, "utf8");
    return JSON.parse(contents) as T;
  } catch {
    return null;
  }
}

export async function readRoadmap<T extends StudyRoadmap = StudyRoadmap>(
  subject: "shenlun" | "xingce",
) {
  return readJsonFile<T>(path.join(dataDirectory, subject, "route.json"));
}

export async function readLatestNews() {
  const dates = await listDailyNewsDates();
  return dates[0] ? readNewsByDate(dates[0]) : null;
}

export async function listDailyNewsDates() {
  try {
    return (await readdir(dailyNewsDirectory))
      .filter((fileName) => /^\d{4}-\d{2}-\d{2}\.json$/.test(fileName))
      .map((fileName) => fileName.replace(/\.json$/, ""))
      .sort()
      .reverse();
  } catch {
    return [];
  }
}

export async function readNewsByDate(date: string) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) {
    return null;
  }

  return readJsonFile<DailyNews>(
    path.join(dailyNewsDirectory, `${date}.json`),
  );
}

export async function readJobFilterResult() {
  return readJsonFile<JobFilterResult>(
    path.join(jobsDirectory, "national-civil-service.json"),
  );
}
