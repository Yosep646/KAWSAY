import type { VariantStatus } from "../types/api";

export const STATUS_LABEL: Record<VariantStatus, string> = {
  DRAFT: "Borrador", AI_GENERATED: "Generado por IA (pendiente de revisión)", TEACHER_REVIEW: "En revisión docente",
  APPROVED: "Aprobado", PUBLISHED: "Publicado",
};
export const gradeLabel = (g: { level: string; number: number }): string => `${g.number}.º ${g.level === "PRIMARIA" ? "Primaria" : "Secundaria"}`;
export const percent = (s: number | null): string => (s === null ? "Sin evidencia suficiente" : `${Math.round(s * 100)} %`);
export const errMsg = (e: unknown): string => (e instanceof Error ? e.message : "Error inesperado");
