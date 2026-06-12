import assert from "node:assert/strict";
import { readFile, readdir, stat } from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

async function read(relativePath) {
  return readFile(path.join(root, relativePath), "utf8");
}

async function exists(relativePath) {
  try {
    await stat(path.join(root, relativePath));
    return true;
  } catch {
    return false;
  }
}

async function sourceFiles(directory) {
  const absoluteDirectory = path.join(root, directory);
  const entries = await readdir(absoluteDirectory, { withFileTypes: true });
  const files = [];

  for (const entry of entries) {
    const relativePath = path.join(directory, entry.name);
    if (entry.isDirectory()) {
      files.push(...await sourceFiles(relativePath));
    } else if (/\.(?:ts|tsx|js|jsx|mjs)$/.test(entry.name)) {
      files.push(relativePath);
    }
  }

  return files;
}

test("core App Router routes are present", async () => {
  const pageRoutes = [
    "app/page.tsx",
    "app/news/page.tsx",
    "app/jobs/page.tsx",
    "app/shenlun/page.tsx",
    "app/xingce/page.tsx",
  ];
  const apiRoutes = [
    "app/api/export/shenlun/route.ts",
    "app/api/export/xingce/route.ts",
    "app/api/jobs/route.ts",
  ];

  for (const route of [...pageRoutes, ...apiRoutes]) {
    assert.equal(await exists(route), true, `missing core route: ${route}`);
  }
  for (const route of pageRoutes) {
    assert.match(await read(route), /\bexport\s+default\b/, `${route} lacks a page export`);
  }
  for (const route of apiRoutes) {
    assert.match(
      await read(route),
      /\bexport\s+async\s+function\s+GET\s*\(/,
      `${route} lacks a GET handler`,
    );
  }
});

test("components, types, and services live under app", async () => {
  const requiredFiles = [
    "app/components/home/module-card.tsx",
    "app/components/layout/site-header.tsx",
    "app/components/ui/button.tsx",
    "app/news/components/news-browser.tsx",
    "app/shenlun/components/question-type-explorer.tsx",
    "app/xingce/components/module-explorer.tsx",
    "app/services/content.ts",
    "app/services/export.ts",
    "app/services/jobs.ts",
    "app/services/storage-paths.ts",
    "app/types/content.ts",
    "app/utils.ts",
  ];

  for (const file of requiredFiles) {
    assert.equal(await exists(file), true, `missing app-owned module: ${file}`);
  }

  for (const oldRoot of ["components", "lib"]) {
    assert.equal(
      await exists(oldRoot),
      false,
      `legacy root directory must be removed: ${oldRoot}/`,
    );
  }
});

test("app imports do not target legacy component or service roots", async () => {
  const files = await sourceFiles("app");
  const oldAliases = [
    ["@", "components"].join("/"),
    ["@", "lib"].join("/"),
  ];

  for (const file of files) {
    const contents = await read(file);
    for (const oldAlias of oldAliases) {
      assert.equal(
        contents.includes(oldAlias),
        false,
        `${file} imports obsolete alias ${oldAlias}`,
      );
    }
    assert.equal(
      contents.includes(["_", "components"].join("")),
      false,
      `${file} imports a private component directory`,
    );
  }
});

test("legacy Harness and component directories are absent", async () => {
  const legacyDirectories = [
    [".agents", "harness"].join("/"),
    ["docs", "harness"].join("/"),
    ["docs", "herness"].join("/"),
    ["app", ["_", "components"].join("")].join("/"),
    ["app", "news", ["_", "components"].join("")].join("/"),
    ["app", "shenlun", ["_", "components"].join("")].join("/"),
    ["app", "xingce", ["_", "components"].join("")].join("/"),
  ];

  for (const directory of legacyDirectories) {
    assert.equal(
      await exists(directory),
      false,
      `legacy directory must be removed: ${directory}`,
    );
  }
});

test("frontend filesystem access is read-only and confined to data", async () => {
  const files = await sourceFiles("app");
  const fsUsers = [];
  const mutatingFsApi =
    /\b(?:appendFile|chmod|chown|copyFile|cp|link|mkdir|open|rename|rm|rmdir|symlink|truncate|unlink|utimes|writeFile)\b/;

  for (const file of files) {
    const contents = await read(file);
    if (/["']node:fs(?:\/promises)?["']/.test(contents)) {
      fsUsers.push(file.replaceAll("\\", "/"));
      assert.equal(
        mutatingFsApi.test(contents),
        false,
        `${file} imports a mutating filesystem API`,
      );
    }
  }

  assert.deepEqual(fsUsers, ["app/services/content.ts"]);

  const storagePaths = await read("app/services/storage-paths.ts");
  assert.match(storagePaths, /path\.join\(process\.cwd\(\),\s*["']data["']\)/);
  assert.doesNotMatch(storagePaths, /\bcontent[\\/]/);

  const contentService = await read("app/services/content.ts");
  assert.match(contentService, /from\s+["']node:fs\/promises["']/);
  assert.match(contentService, /\b(?:readFile|readdir)\b/);
  assert.doesNotMatch(contentService, /\bfetch\s*\(/);
});

test("Harness has exactly eight stages and three fix rounds", async () => {
  const configPath = "docs/manifest.json";
  assert.equal(await exists(configPath), true, `missing ${configPath}`);

  const config = JSON.parse(await read(configPath));
  const stages = config.stages ?? config.pipeline?.stages;
  const maxRepairRounds = config.execution?.maxRepairRounds;

  assert.ok(Array.isArray(stages), "Harness stages must be an array");
  assert.equal(stages.length, 8, "Harness must have exactly eight stages");
  assert.equal(
    maxRepairRounds,
    3,
    "Harness execution.maxRepairRounds must be 3",
  );
  assert.equal(config.runDirectory, "docs/runs");

  const referencedPaths = [
    config.policy,
    ...Object.values(config.templates ?? {}),
    ...stages.map((stage) => stage.prompt),
  ];
  for (const referencedPath of referencedPaths) {
    assert.equal(
      await exists(referencedPath),
      true,
      `Harness path does not exist: ${referencedPath}`,
    );
  }
});

test("package scripts expose validation, tests, scans, and full checks", async () => {
  const packageJson = JSON.parse(await read("package.json"));
  const scripts = packageJson.scripts ?? {};

  assert.equal(scripts["validate:project"], "python scripts/validate_project.py");
  assert.equal(scripts.test, "node --test tests/project.test.mjs");
  assert.equal(
    scripts["scan:today"],
    "python .agents/skills/daily-news/scripts/today_scan.py",
  );
  assert.equal(
    scripts["jobs:all"],
    "python .agents/skills/job-filter/scripts/job_pipeline.py all",
  );

  for (const command of [
    "npm run validate:project",
    "npm run lint",
    "npm run typecheck",
    "npm test",
    "npm run build",
  ]) {
    assert.ok(scripts.check?.includes(command), `check script omits: ${command}`);
  }
});
