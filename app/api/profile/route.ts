import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { NextResponse } from "next/server";
import { createEmptyProfile, normalizeProfile } from "@/lib/profile";
import { dataDirectory } from "@/lib/storage-paths";
import type { Profile } from "@/lib/types";

const profilePath = path.join(dataDirectory, "profile.local.json");

export async function GET() {
  try {
    const contents = await readFile(profilePath, "utf8");
    return NextResponse.json(normalizeProfile(JSON.parse(contents) as Profile));
  } catch {
    return NextResponse.json(createEmptyProfile());
  }
}

export async function PUT(request: Request) {
  const profile = (await request.json()) as Profile;

  if (!profile.basic || !profile.qualification || !profile.target || !profile.study) {
    return NextResponse.json({ message: "画像数据格式无效" }, { status: 400 });
  }

  await mkdir(path.dirname(profilePath), { recursive: true });
  const normalized = normalizeProfile(profile);
  await writeFile(profilePath, `${JSON.stringify(normalized, null, 2)}\n`, "utf8");

  return NextResponse.json(normalized);
}
