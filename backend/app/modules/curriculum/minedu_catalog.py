"""Curated public MINEDU primary resources (not an API or a curriculum import).

Public documents are externally hosted. No scraping, credential transfer, or
automatic pedagogical approvals. References need human review for each school.
Sources checked against MINEDU public resource page on 2026-10-28.
"""

MINEDU_PRIMARY_SOURCES = {
    "country": "PE",
    "level": "PRIMARIA",
    "source_label": "Ministerio de Educación del Perú (MINEDU)",
    "curriculum": {
        "name": "Programa curricular de Educación Primaria",
        "year": 2016,
        "url": "https://repositorio.minedu.gob.pe/handle/20.500.12799/4549",
    },
    "national_framework": {
        "name": "Currículo Nacional de la Educación Básica (CNEB)",
        "year": 2016,
        "url": "https://repositorio.minedu.gob.pe/handle/20.500.12799/4551",
    },
    "resource_index_url": "https://www.minedu.gob.pe/curriculo/recursos.php",
    "institutional_guidance_url": "https://repositorio.minedu.gob.pe/handle/20.500.12799/8725",
    "status": "REFERENCIA_PUBLICA",
    "notice": (
        "Los ejemplos anuales del MINEDU son orientativos y no obligatorios. "
        "No constituyen una planificación aprobada de la institución. "
        "El docente y la dirección educativa deben revisar y contextualizar "
        "los contenidos antes de activar tareas o generar ejercicios."
    ),
    "grades": [
        {
            "number": number,
            "name": f"{number}.º de primaria",
            "planning_pdf_url": f"https://minedu.gob.pe/curriculo/pdf/planificacion-anual-{slug}-grado.pdf",
            "planning_word_url": f"https://minedu.gob.pe/curriculo/pdf/planificacion-anual-{slug}-grado.docx",
            "example_status": "EJEMPLO_NO_OBLIGATORIO",
        }
        for number, slug in enumerate(("primer", "segundo", "tercer", "cuarto", "quinto", "sexto"), start=1)
    ],
    # Official names of the 4 competencies in primary Mathematics, not
    # a fabricated list of performances or an educational sequence.
    "math_competencies": [
        "Resuelve problemas de cantidad",
        "Resuelve problemas de regularidad, equivalencia y cambio",
        "Resuelve problemas de forma, movimiento y localización",
        "Resuelve problemas de gestión de datos e incertidumbre",
    ],
}
