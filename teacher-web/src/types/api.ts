export type Role = "STUDENT" | "TEACHER" | "ADMIN";
export interface UserBrief { id: string; role: Role; display_name: string }
export interface TokenOut { access_token: string; refresh_token: string; expires_in: number; user: UserBrief }
export interface Grade { id: number; level: string; number: number }
export interface Classroom { id: string; school_id: string; name: string; academic_year: number }
export interface StudentBrief { id: string; display_name: string; grade_id: number; grade_level: string; grade_number: number }
export interface ClassroomDetail extends Classroom { students: StudentBrief[]; grades_present: string[] }
export interface StudentCredentials { id: string; display_name: string; grade_id: number; login_code: string; pin: string }
export interface StudentDetail { id: string; display_name: string; grade_id: number; login_code: string | null }
export interface LanguageVariant { id: string; code: string; name: string; note: string | null }
export interface Language { code: string; name: string; variants: LanguageVariant[] }
export interface StudentLanguages { mother_language: string | null; mother_variant_id: string | null; preferred_language: string | null }
export interface StudentLanguagesInput { mother_language_code: string | null; mother_variant_id: string | null; preferred_language_code: string | null }
export interface Summary {
  classroom: { id: string; name: string; academic_year: number };
  students_total: number; students_by_grade: Record<string, number>; published_assignments: number;
  attempts_total: number; students_with_activity: number; open_support_flags: number;
}
export interface FlagResult { question_id: string; score: number; correct: boolean; attempts: number; hints: number; at: string; topic?: string | null }
export interface SupportFlag {
  id: string; status: "OPEN" | "ACKNOWLEDGED" | "RESOLVED" | "DISMISSED";
  student: { id: string; display_name: string; grade: string | null };
  competency: { id: string; name: string };
  rule_id: string; rule_version: string; message: string; recommendation: string | null;
  evidence: { window: number; difficult: number; hints_total: number; wrong_attempts_total: number; distinct_days: number; topics: string[]; results: FlagResult[] };
}
export interface Strength { student: { id: string; display_name: string; grade: string }; competency: { id: string; name: string | null }; strengths: { rule_id: string; name: string; evidence: Record<string, number> }[] }
export interface CompetencyProgress { competency_id: string; name: string; score: number | null; evidence_count: number; state: string | null; note: string | null; difficulty_recommendation?: { action: 'LOWER' | 'MAINTAIN' | 'RAISE' | 'INSUFFICIENT_EVIDENCE'; suggested_difficulty: number | null; reason: string; source: 'RULES'; method_version: string; requires_teacher_decision: boolean } }
export interface Question {
  id?: string; type: "MULTIPLE_CHOICE" | "NUMERIC" | "SHORT_TEXT"; prompt: string; options: string[] | null;
  correct_answer: Record<string, unknown>; hints: string[]; explanation: string | null; difficulty: number;
}
export type VariantStatus = "DRAFT" | "AI_GENERATED" | "TEACHER_REVIEW" | "APPROVED" | "PUBLISHED";
export interface Variant {
  id: string; grade_id: number; topic_id: string; learning_objective: string; title: string; instructions: string;
  status: VariantStatus; source: "TEACHER" | "AI" | "AI_EDITED"; generated_by: string | null;
  validation_status: "NOT_CHECKED" | "OK" | "NEEDS_REVIEW"; validation_notes: string[] | null; questions: Question[];
}
export interface AssignmentDetail { id: string; classroom_id: string; title: string; mode: string; status: string; variants: Variant[] }
export interface AssignmentBrief { id: string; classroom_id: string; title: string; status: string; mode: string }
export interface PlanTopic { id: string; title: string; learning_objective: string; competency_id: string }
export interface PlanUnit { id: string; title: string; grade_id: number; subject_id: string; topics: PlanTopic[] }
export interface PlanVersionTree { id: string; plan_id: string; label: string; status: string; periods: { id: string; name: string; sequence: number; units: PlanUnit[] }[] }
export interface PlanBrief { id: string; name: string; school_id: string; framework_id: string; versions: { id: string; label: string; status: string }[] }
export interface Framework { id: string; name: string; version_label: string; is_demo: boolean }
export interface FrameworkTree extends Framework { subjects: { id: string; name: string; competencies: { id: string; name: string; capacities: { id: string; name: string }[] }[] }[] }
export interface AdaptResult { assignment_id: string; results: { variant_id: string; grade_id: number; status: string; reasons: string[] }[] }
export interface ForecastItem { student: { id: string; display_name: string }; competency: { id: string; name: string | null }; probability: number; above_threshold: boolean; model_id: string; model_status: string; warning: string | null; advisory: string; inference_ms?: number }
export interface Forecast { available: boolean; experimental?: boolean; reason?: string; items: ForecastItem[] }
