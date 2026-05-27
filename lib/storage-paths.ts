import "server-only";

import path from "node:path";

export const dataDirectory = process.env.GONGKAO_DATA_DIR
  ? path.resolve(process.env.GONGKAO_DATA_DIR)
  : path.join(process.cwd(), "data");

export const localContentDirectory = process.env.GONGKAO_CONTENT_DIR
  ? path.resolve(process.env.GONGKAO_CONTENT_DIR)
  : path.join(process.cwd(), "content", "local");

export const libraryContentDirectory = path.join(process.cwd(), "content", "library");
