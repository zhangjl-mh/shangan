import "server-only";

import path from "node:path";

export const dataDirectory = process.env.GONGKAO_DATA_DIR
  ? path.resolve(process.env.GONGKAO_DATA_DIR)
  : path.join(process.cwd(), "data");

export const dailyNewsDirectory = path.join(dataDirectory, "daily-news");
export const jobsDirectory = path.join(dataDirectory, "jobs");
