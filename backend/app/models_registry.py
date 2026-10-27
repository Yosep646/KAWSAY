"""Importa todos los modelos para que Alembic (autogenerate) los vea."""
from app.modules.ai.models import AIGenerationRequest  # noqa: F401
from app.modules.assignments.models import Assignment, AssignmentVariant, Counter, Question, StudentAssignment  # noqa: F401
from app.modules.audit.models import AuditLog  # noqa: F401
from app.modules.auth.models import RefreshToken  # noqa: F401
from app.modules.automation.models import DomainEvent  # noqa: F401
from app.modules.classrooms.models import Classroom, ClassroomStudent, ClassroomTeacher  # noqa: F401
from app.modules.curriculum.models import (  # noqa: F401
    Capacity,
    Competency,
    CurriculumFramework,
    Grade,  # noqa: F401
    Subject,
)
from app.modules.interventions.models import TeacherIntervention  # noqa: F401
from app.modules.languages.models import Language, LanguageVariant, StudentLanguage, VariantTranslation  # noqa: F401
from app.modules.learning.models import LearningAttempt, StudentCompetencyProgress  # noqa: F401
from app.modules.planning.models import (  # noqa: F401
    AcademicPeriod,
    AcademicYear,
    CurriculumPlanVersion,
    CurriculumTopic,
    CurriculumUnit,
    SchoolCurriculumPlan,
)
from app.modules.schools.models import (
    School,  # noqa: F401
    UgelUnit,  # noqa: F401
)
from app.modules.students.models import StudentProfile  # noqa: F401
from app.modules.students.email_models import StudentEmailLogin  # noqa: F401
from app.modules.support_flags.models import SupportFlag  # noqa: F401
from app.modules.sync.models import SyncEvent  # noqa: F401
from app.modules.teachers.models import TeacherProfile  # noqa: F401
from app.modules.users.models import User  # noqa: F401
