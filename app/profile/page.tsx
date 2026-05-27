import { ProfileForm } from "@/components/profile/profile-form";
import { Reveal } from "@/components/ui/reveal";
import { readProfile } from "@/lib/content";
import { createEmptyProfile } from "@/lib/profile";

export const dynamic = "force-dynamic";

export default async function ProfilePage() {
  const profile = await readProfile();

  return (
    <main className="mx-auto max-w-[1160px] space-y-7 px-5 py-9 lg:px-6">
      <Reveal>
        <h1 className="ink-title text-[38px]">用户画像</h1>
        <p className="mt-3 text-lg text-[#56665e]">
          管理本地报考条件与学习情况，为 Skills 的岗位筛选提供基础。
        </p>
      </Reveal>
      <Reveal delay={0.05}>
        <ProfileForm initialProfile={profile ?? createEmptyProfile()} exists={Boolean(profile)} />
      </Reveal>
    </main>
  );
}
