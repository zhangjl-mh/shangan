import "server-only";

import { readdir, readFile } from "node:fs/promises";
import path from "node:path";
import type {
  DailyNews,
  EligibleJobsReport,
  Profile,
  StudyRoadmap,
} from "@/lib/types";
import { normalizeProfile } from "@/lib/profile";
import {
  dataDirectory,
  libraryContentDirectory,
  localContentDirectory,
} from "@/lib/storage-paths";

async function readJsonFile<T>(filePath: string): Promise<T | null> {
  try {
    const contents = await readFile(filePath, "utf8");
    return JSON.parse(contents) as T;
  } catch {
    return null;
  }
}

export async function readProfile() {
  const profile = await readJsonFile<Profile>(path.join(dataDirectory, "profile.local.json"));
  return profile ? normalizeProfile(profile) : null;
}

export async function readRoadmap<T extends StudyRoadmap = StudyRoadmap>(
  subject: "shenlun" | "xingce",
) {
  const localRoadmap = await readJsonFile<T>(
    path.join(localContentDirectory, subject, "roadmap.json"),
  );

  if (localRoadmap) {
    return localRoadmap;
  }

  return readJsonFile<T>(
    path.join(libraryContentDirectory, subject, "roadmap.json"),
  );
}

export async function readEligibleJobs() {
  return readJsonFile<EligibleJobsReport>(
    path.join(localContentDirectory, "job", "eligible-jobs.json"),
  );
}

export async function readLatestNews() {
  const dates = await listDailyNewsDates();
  return dates[0] ? readNewsByDate(dates[0]) : null;
}

export async function listDailyNewsDates() {
  const newsDirectory = path.join(localContentDirectory, "news");

  try {
    return (await readdir(newsDirectory))
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
    path.join(localContentDirectory, "news", `${date}.json`),
  );
}
