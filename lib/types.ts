export interface Profile {
  basic: {
    name: string;
    gender: string;
    age: number | null;
    education: string;
    degree: string;
    major: string;
    graduationYear: number | null;
    isFreshGraduate: boolean | null;
    politicalStatus: string;
  };
  qualification: {
    englishLevel: string;
    computerLevel: string;
    certificates: string[];
    grassrootsExperience: boolean | null;
    householdRegistration: string;
    studentOrigin: string;
  };
  employment: {
    currentUnitType: string;
    workStatus: string;
  };
  target: {
    targetRegions: string[];
    targetUnitTypes: string[];
    targetJobTypes: string[];
    acceptGrassroots: boolean | null;
    acceptOtherCity: boolean | null;
  };
  study: {
    dailyStudyHours: number | null;
    shenlunLevel: string;
    xingceLevel: string;
    weakModules: string[];
    examDate: string;
  };
}

export interface RoadmapStage {
  id: string;
  title: string;
  level?: string;
  goal: string;
  duration?: string;
  tasks: string[];
  knowledgePoints?: string[];
  outputs?: string[];
  current?: boolean;
  milestone?: string;
}

export interface StudyRoadmap {
  meta?: {
    type?: string;
    subject?: string;
    version?: string;
    updatedAt?: string;
    contentKind?: string;
  };
  title: string;
  description: string;
  stages: RoadmapStage[];
  suggestions?: string[];
  materials?: Array<{
    id: string;
    title: string;
    type?: string;
    url?: string;
  }>;
  basisNote?: string;
  examGuide?: {
    syllabusTitle: string;
    syllabusDate: string;
    syllabusUrl: string;
    durationMinutes: number;
    score: number;
    notice: string;
    paperTypes: Array<{
      title: string;
      focus: string;
      abilities: string[];
    }>;
    answerRules: string[];
  };
  coreWorkflow?: Array<{
    id: string;
    title: string;
    purpose: string;
    actions: string[];
    output: string;
  }>;
  questionTypes?: Array<{
    id: string;
    title: string;
    subtitle: string;
    taskSignals: string[];
    coreGoal: string;
    answerFramework: string[];
    pointMethods: string[];
    pitfalls: string[];
    drills: string[];
  }>;
  readingMethod?: {
    passes: Array<{
      title: string;
      time: string;
      actions: string[];
    }>;
    markerLegend: Array<{
      symbol: string;
      meaning: string;
      examples: string;
    }>;
    processingRules: string[];
  };
  documentTypes?: Array<{
    title: string;
    audience: string;
    structure: string[];
    focus: string;
  }>;
  essayMethod?: {
    positioning: string[];
    structure: Array<{
      part: string;
      method: string;
    }>;
    argumentTools: string[];
    pitfalls: string[];
  };
  topicToolkit?: Array<{
    topic: string;
    angles: string[];
    usableExpressions: string[];
  }>;
  trainingPlans?: Array<{
    title: string;
    suitedFor: string;
    weeks: Array<{
      period: string;
      focus: string;
      deliverable: string;
    }>;
  }>;
  examTiming?: Array<{
    phase: string;
    minutes: string;
    action: string;
  }>;
  reviewChecklist?: Array<{
    category: string;
    items: string[];
  }>;
  references?: Array<{
    title: string;
    publisher: string;
    kind: string;
    url: string;
    note: string;
    accessedAt: string;
  }>;
}

export interface XingceRoadmap extends StudyRoadmap {
  examProfile?: {
    syllabusTitle: string;
    syllabusDate: string;
    syllabusUrl: string;
    durationMinutes: number;
    score: number;
    questionNature: string;
    officialModules: string[];
    notice: string;
  };
  moduleGuides?: Array<{
    id: string;
    title: string;
    ability: string;
    topics: string[];
    methods: string[];
    pitfalls: string[];
    drills: string[];
  }>;
  formulaCards?: Array<{
    title: string;
    rules: string[];
  }>;
  timePlan?: Array<{
    phase: string;
    target: string;
    method: string;
  }>;
  practiceChecklist?: Array<{
    title: string;
    items: string[];
  }>;
}

export interface NewsItem {
  id: string;
  title: string;
  source: string;
  url: string;
  publishTime: string;
  summary: string;
  keywords: string[];
  policyBackground?: string;
  shenlunAngles?: Array<{ title: string; explanation: string }>;
  xingceLinks?: Array<{
    module: string;
    point: string;
    explanation: string;
  }>;
  materials?: string[];
  examQuestions?: string[];
  importance?: number;
  tags?: string[];
  verification?: {
    verifiedAt: string;
    status: "verified";
    note: string;
  };
}

export interface DailyNews {
  meta?: {
    date?: string;
    generatedAt?: string;
    sourceCount?: number;
    itemCount?: number;
    scopeNote?: string;
    verifiedAt?: string;
  };
  date: string;
  title: string;
  summary: string;
  items: NewsItem[];
}

export interface EligiblePosition {
  id: string;
  title: string;
  organization: string;
  category: string;
  department?: string;
  positionCode?: string;
  recruitmentType?: string;
  region: string;
  district?: string;
  recruitCount?: number;
  responsibilities?: string;
  educationRequirement?: string;
  majorRequirement?: string;
  freshGraduateRequirement?: string;
  matchScore?: number;
  matchLevel?: string;
  riskLevel?: string;
  recommendation?: string;
  matchReasons?: string[];
  riskReminders?: string[];
  studyAdvice?: string[];
  benefits?: string[];
  housingReference?: string;
  householdReference?: string;
  officialOnlyNotice?: string;
  eligibilityBasis?: string[];
  advantages?: string[];
  risks?: string[];
  applicationNotes?: string[];
  historicalReferences?: Array<{
    year: string;
    finalEntryScore?: string;
    applicationRatio?: string;
    recruitmentCount?: string;
    note?: string;
    sourceName: string;
    sourceUrl: string;
  }>;
  compensationReference?: {
    text: string;
    source?: string;
    sourceUrl?: string;
    disclaimer?: string;
  };
  announcementDate?: string;
  registrationStartDate?: string;
  registrationEndDate?: string;
  examDate?: string;
  status: "即将报名" | "报名中" | "已截止" | "已结束" | string;
  sourceName: string;
  sourceUrl: string;
  capturedAt: string;
}

export interface EligibleJobsReport {
  generatedAt: string;
  sourceScope?: string[];
  referencePolicy?: string;
  regionalScanNote?: string;
  screeningNote?: string;
  searchedSources?: Array<{
    name: string;
    url: string;
    checkedAt: string;
    result: string;
  }>;
  positions: EligiblePosition[];
}

export type JobTrackingStatus =
  | "未处理"
  | "已收藏"
  | "准备报名"
  | "已报名"
  | "待考试"
  | "已结束"
  | "放弃";

export interface JobTrackingItem {
  positionId: string;
  status: JobTrackingStatus;
  appliedAt?: string;
  examDate?: string;
  notes?: string;
  positionSnapshot?: EligiblePosition;
}

export interface JobTrackingData {
  updatedAt: string;
  items: JobTrackingItem[];
}
