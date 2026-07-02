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
  studyPrinciples?: Array<{
    title: string;
    detail: string;
  }>;
  teacherGroups?: Array<{
    moduleId: string;
    module: string;
    selectionNote: string;
    teachers: Array<{
      name: string;
      institution?: string;
      role: string;
      stage: string;
      suitedFor: string;
      howToUse: string[];
      caution: string;
      sourceTitle?: string;
      sourceUrl?: string;
    }>;
  }>;
  teacherSelectionRules?: string[];
  dailyExecution?: Array<{
    period: string;
    focus: string;
    actions: string[];
    standard: string;
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
    candidateCount?: number;
    scopeNote?: string;
    selectionRule?: string;
    verifiedAt?: string;
  };
  date: string;
  title: string;
  summary: string;
  items: NewsItem[];
  candidateSources?: Array<{
    name: string;
    url: string;
    checkedAt: string;
    result: string;
  }>;
  candidatePool?: Array<{
    id: string;
    title: string;
    source: string;
    url: string;
    publishTime?: string;
    reason: string;
    selected: boolean;
  }>;
}

export type JobEligibility = "eligible" | "needs_confirmation";

export type JobCategory =
  | "civil_service"
  | "institution"
  | "military_civilian"
  | "state_owned_enterprise";

export type JobBatchStatus = "current" | "previous_reference";

export type JobApplicationStatus =
  | "upcoming"
  | "open"
  | "closed"
  | "unknown";

export type JobRequirementState =
  | "specified"
  | "unrestricted"
  | "missing"
  | "unparsed";

export type JobRecruitmentStageId =
  | "announcement"
  | "registration"
  | "exam"
  | "result"
  | "second_interview";

export interface JobRecruitmentCalendar {
  id: string;
  category: "state_owned_enterprise";
  title: string;
  recruitmentMode: "rolling";
  status: "forecast";
  description: string;
  sourcePortal: {
    label: string;
    url: string;
  };
  forecastBasis: Array<{
    label: string;
    url: string;
    publishedAt: string;
  }>;
  stages: Array<{
    id: JobRecruitmentStageId;
    label: string;
    timingType: "absolute_window" | "relative_window";
    display: string;
    startDate: string | null;
    endDate: string | null;
    status: "estimated";
    note: string;
  }>;
  disclaimer: string;
}

export interface JobRecruitmentCalendarData {
  schemaVersion: "1.0";
  updatedAt: string;
  calendars: JobRecruitmentCalendar[];
}

export interface JobPosition {
  id: string;
  sourceId: string;
  sourceLabel: string;
  category: JobCategory;
  cycle: string;
  batchStatus: JobBatchStatus;
  applicationStatus: JobApplicationStatus;
  examAt?: string | null;
  title: string;
  organization: string;
  department: string;
  positionCode: string;
  region: string;
  recruitCount: number;
  requirements: {
    major: string;
    education: string;
    degree: string;
    politicalStatus: string;
    grassrootsYears: string;
    serviceProject: string;
    freshGraduate: string;
    age: string;
    gender: string;
    household: string;
    certificate: string;
    remarks: string;
  };
  requirementStates: Record<string, JobRequirementState>;
  eligibility: JobEligibility;
  matchReasons: string[];
  confirmationFields: string[];
  exclusionReasons: string[];
  decisions: Array<{
    field: string;
    result: "pass" | "fail" | "unknown";
    reason: string;
  }>;
  registration: {
    opensAt: string | null;
    closesAt: string | null;
  };
  source: {
    attachmentId: string;
    url: string;
    portalUrl: string;
    evidenceUrl: string;
    member: string;
    sheet: string;
    row: number;
  };
}

export interface JobIndexCatalog {
  path: string;
  rowCount: number;
  sha256: string;
}

export interface JobIndex {
  schemaVersion: "4.0";
  generatedAt: string;
  asOf: string;
  eligibleCatalog: JobIndexCatalog;
  needsConfirmationCatalog: JobIndexCatalog;
  sources: Array<{
    sourceId: string;
    label: string;
    category: JobCategory;
    cycle: string;
    selectionMode: JobBatchStatus;
    examAt: string | null;
    portalUrl: string;
  }>;
  stats: {
    processed: number;
    eligible: number;
    needsConfirmation: number;
    excluded: number;
    currentCampaigns: number;
    referenceCampaigns: number;
    application: Record<JobApplicationStatus, number>;
  };
  coverage: {
    requiredCategories: JobCategory[];
    registeredCategories: JobCategory[];
    catalogCategories: JobCategory[];
    missingCatalogCategories: JobCategory[];
  };
}

export interface JobQuery {
  exam?: string;
  region?: string;
  category?: JobCategory | "all";
  eligibility?: JobEligibility;
  batch?: JobBatchStatus | "all";
  application?: JobApplicationStatus | "all";
  keyword?: string;
  page?: number;
  pageSize?: number;
  paginate?: boolean;
}

export interface JobQueryResult {
  items: JobPosition[];
  total: number;
  page: number;
  pageSize: number;
  pageCount: number;
  exams: Array<{ id: string; label: string }>;
  regions: string[];
  index: JobIndex | null;
}
