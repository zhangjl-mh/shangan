import { access, copyFile, mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const currentDirectory = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(currentDirectory, "..");

const seeds = [
  {
    label: "申论系统学习手册",
    source: path.join(projectRoot, "content", "library", "shenlun", "roadmap.json"),
    destination: path.join(projectRoot, "content", "local", "shenlun", "roadmap.json"),
  },
  {
    label: "行测系统训练手册",
    source: path.join(projectRoot, "content", "library", "xingce", "roadmap.json"),
    destination: path.join(projectRoot, "content", "local", "xingce", "roadmap.json"),
  },
];

async function exists(filePath) {
  try {
    await access(filePath);
    return true;
  } catch {
    return false;
  }
}

for (const seed of seeds) {
  if (await exists(seed.destination)) {
    console.log(`[保留] ${seed.label}：已有 local 数据，未覆盖。`);
    continue;
  }

  await mkdir(path.dirname(seed.destination), { recursive: true });
  await copyFile(seed.source, seed.destination);
  console.log(`[生成] ${seed.label} -> ${path.relative(projectRoot, seed.destination)}`);
}

console.log("[完成] 本地学习内容初始化已完成。");
