"use client";

import { useState } from "react";
import { Check, Save } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import type { Profile } from "@/lib/types";

type Group = keyof Profile;

export function ProfileForm({
  initialProfile,
  exists,
}: {
  initialProfile: Profile;
  exists: boolean;
}) {
  const [profile, setProfile] = useState(initialProfile);
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);

  function update(group: Group, field: string, value: string | number | boolean | null | string[]) {
    setSaved(false);
    setProfile((current) => ({
      ...current,
      [group]: {
        ...current[group],
        [field]: value,
      },
    }));
  }

  async function save() {
    setSaving(true);
    setSaved(false);
    const response = await fetch("/api/profile", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(profile),
    });
    setSaving(false);
    setSaved(response.ok);
  }

  return (
    <div className="space-y-5">
      {!exists ? (
        <Card className="label-sans border-[#d6dfd3] bg-[#f0f4ed] px-5 py-4 text-sm text-[#50675a]">
          当前尚无本地画像。保存此表单后会写入 <code>data/profile.local.json</code>；也可以由 Skills 问询后生成同一文件。
        </Card>
      ) : null}
      <Card className="p-6">
        <FormSection title="基本信息">
          <TextField label="姓名" value={profile.basic.name} onChange={(value) => update("basic", "name", value)} />
          <TextField label="性别" value={profile.basic.gender} onChange={(value) => update("basic", "gender", value)} />
          <NumberField label="年龄" value={profile.basic.age} onChange={(value) => update("basic", "age", value)} />
          <TextField label="学历" value={profile.basic.education} onChange={(value) => update("basic", "education", value)} />
          <TextField label="学位" value={profile.basic.degree} onChange={(value) => update("basic", "degree", value)} />
          <TextField label="专业" value={profile.basic.major} onChange={(value) => update("basic", "major", value)} />
          <NumberField label="毕业年份" value={profile.basic.graduationYear} onChange={(value) => update("basic", "graduationYear", value)} />
          <BooleanField label="是否应届" value={profile.basic.isFreshGraduate} onChange={(value) => update("basic", "isFreshGraduate", value)} />
          <TextField label="政治面貌" value={profile.basic.politicalStatus} onChange={(value) => update("basic", "politicalStatus", value)} />
        </FormSection>
      </Card>
      <Card className="p-6">
        <FormSection title="当前任职">
          <TextField label="当前单位类型" value={profile.employment.currentUnitType} onChange={(value) => update("employment", "currentUnitType", value)} />
          <TextField label="工作状态" value={profile.employment.workStatus} onChange={(value) => update("employment", "workStatus", value)} />
        </FormSection>
      </Card>
      <Card className="p-6">
        <FormSection title="资格条件">
          <TextField label="英语等级" value={profile.qualification.englishLevel} onChange={(value) => update("qualification", "englishLevel", value)} />
          <TextField label="计算机等级" value={profile.qualification.computerLevel} onChange={(value) => update("qualification", "computerLevel", value)} />
          <ListField label="证书" value={profile.qualification.certificates} onChange={(value) => update("qualification", "certificates", value)} />
          <BooleanField label="基层经历" value={profile.qualification.grassrootsExperience} onChange={(value) => update("qualification", "grassrootsExperience", value)} />
          <TextField label="户籍" value={profile.qualification.householdRegistration} onChange={(value) => update("qualification", "householdRegistration", value)} />
          <TextField label="生源地" value={profile.qualification.studentOrigin} onChange={(value) => update("qualification", "studentOrigin", value)} />
        </FormSection>
      </Card>
      <Card className="p-6">
        <FormSection title="报考目标">
          <ListField label="目标地区" value={profile.target.targetRegions} onChange={(value) => update("target", "targetRegions", value)} />
          <ListField label="目标单位类型" value={profile.target.targetUnitTypes} onChange={(value) => update("target", "targetUnitTypes", value)} />
          <ListField label="目标岗位类型" value={profile.target.targetJobTypes} onChange={(value) => update("target", "targetJobTypes", value)} />
          <BooleanField label="接受基层" value={profile.target.acceptGrassroots} onChange={(value) => update("target", "acceptGrassroots", value)} />
          <BooleanField label="接受异地" value={profile.target.acceptOtherCity} onChange={(value) => update("target", "acceptOtherCity", value)} />
        </FormSection>
      </Card>
      <Card className="p-6">
        <FormSection title="学习情况">
          <NumberField label="每天学习时间（小时）" value={profile.study.dailyStudyHours} onChange={(value) => update("study", "dailyStudyHours", value)} />
          <TextField label="申论基础" value={profile.study.shenlunLevel} onChange={(value) => update("study", "shenlunLevel", value)} />
          <TextField label="行测基础" value={profile.study.xingceLevel} onChange={(value) => update("study", "xingceLevel", value)} />
          <ListField label="薄弱模块" value={profile.study.weakModules} onChange={(value) => update("study", "weakModules", value)} />
          <TextField label="考试时间" type="date" value={profile.study.examDate} onChange={(value) => update("study", "examDate", value)} />
        </FormSection>
      </Card>
      <div className="no-print flex justify-end gap-4">
        {saved ? (
          <p className="label-sans flex items-center gap-2 text-sm text-[#50715c]">
            <Check size={16} />
            已保存到本地画像文件
          </p>
        ) : null}
        <Button onClick={save} disabled={saving}>
          <Save size={17} />
          {saving ? "正在保存" : "保存画像"}
        </Button>
      </div>
    </div>
  );
}

function FormSection({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <>
      <h2 className="section-title mb-6">{title}</h2>
      <div className="label-sans grid gap-x-5 gap-y-5 sm:grid-cols-2 lg:grid-cols-3">
        {children}
      </div>
    </>
  );
}

function TextField({
  label,
  value,
  onChange,
  type = "text",
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: "text" | "date";
}) {
  return (
    <label className="space-y-2 text-sm text-[#5e6c65]">
      <span>{label}</span>
      <input
        type={type}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="block h-11 w-full rounded-lg border bg-white/72 px-3 text-[#2b3833] outline-none focus:border-[#86a091]"
      />
    </label>
  );
}

function NumberField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: number | null;
  onChange: (value: number | null) => void;
}) {
  return (
    <label className="space-y-2 text-sm text-[#5e6c65]">
      <span>{label}</span>
      <input
        type="number"
        value={value ?? ""}
        onChange={(event) => onChange(event.target.value ? Number(event.target.value) : null)}
        className="block h-11 w-full rounded-lg border bg-white/72 px-3 text-[#2b3833] outline-none focus:border-[#86a091]"
      />
    </label>
  );
}

function ListField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string[];
  onChange: (value: string[]) => void;
}) {
  return (
    <label className="space-y-2 text-sm text-[#5e6c65]">
      <span>{label}（逗号分隔）</span>
      <input
        value={value.join("，")}
        onChange={(event) => onChange(event.target.value.split(/[,，]/).map((item) => item.trim()).filter(Boolean))}
        className="block h-11 w-full rounded-lg border bg-white/72 px-3 text-[#2b3833] outline-none focus:border-[#86a091]"
      />
    </label>
  );
}

function BooleanField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: boolean | null;
  onChange: (value: boolean | null) => void;
}) {
  return (
    <label className="space-y-2 text-sm text-[#5e6c65]">
      <span>{label}</span>
      <select
        value={value === null ? "" : String(value)}
        onChange={(event) => onChange(event.target.value === "" ? null : event.target.value === "true")}
        className="block h-11 w-full rounded-lg border bg-white/72 px-3 text-[#2b3833] outline-none focus:border-[#86a091]"
      >
        <option value="">未填写</option>
        <option value="true">是</option>
        <option value="false">否</option>
      </select>
    </label>
  );
}
