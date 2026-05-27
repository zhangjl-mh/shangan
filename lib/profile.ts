import type { Profile } from "@/lib/types";

type StoredProfile = Partial<Omit<Profile, "target">> & {
  target?: Partial<Profile["target"]> & {
    targetRegion?: string;
    targetUnitType?: string;
    targetJobType?: string;
  };
};

export function createEmptyProfile(): Profile {
  return {
    basic: {
      name: "",
      gender: "",
      age: null,
      education: "",
      degree: "",
      major: "",
      graduationYear: null,
      isFreshGraduate: null,
      politicalStatus: "",
    },
    qualification: {
      englishLevel: "",
      computerLevel: "",
      certificates: [],
      grassrootsExperience: null,
      householdRegistration: "",
      studentOrigin: "",
    },
    employment: {
      currentUnitType: "",
      workStatus: "",
    },
    target: {
      targetRegions: [],
      targetUnitTypes: [],
      targetJobTypes: [],
      acceptGrassroots: null,
      acceptOtherCity: null,
    },
    study: {
      dailyStudyHours: null,
      shenlunLevel: "",
      xingceLevel: "",
      weakModules: [],
      examDate: "",
    },
  };
}

export function normalizeProfile(input: StoredProfile): Profile {
  const empty = createEmptyProfile();
  const target = input.target ?? {};

  return {
    basic: { ...empty.basic, ...input.basic },
    qualification: { ...empty.qualification, ...input.qualification },
    employment: { ...empty.employment, ...input.employment },
    target: {
      ...empty.target,
      ...target,
      targetRegions:
        target.targetRegions ??
        (target.targetRegion ? [target.targetRegion] : []),
      targetUnitTypes:
        target.targetUnitTypes ??
        (target.targetUnitType ? [target.targetUnitType] : []),
      targetJobTypes:
        target.targetJobTypes ??
        (target.targetJobType ? [target.targetJobType] : []),
    },
    study: { ...empty.study, ...input.study },
  };
}

export const focusRegions = [
  "北京",
  "天津",
  "雄安新区",
  "石家庄市井陉县",
  "石家庄市鹿泉区",
  "石家庄市井陉矿区",
  "石家庄市藁城区",
  "石家庄市栾城区",
  "石家庄市正定县",
];
