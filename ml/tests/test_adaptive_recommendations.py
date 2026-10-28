import unittest

from ml.adaptive_recommendations import CompetencyEvidence, recommend


class AdaptiveRecommendationTests(unittest.TestCase):
    def test_insufficient_evidence(self):
        r = recommend(5, "fractions5", [])
        self.assertEqual(r.target_grade, 5)
        self.assertTrue(r.requires_teacher_approval)

    def test_student_with_mastery_stays_in_grade(self):
        r = recommend(5, "fractions5", [CompetencyEvidence("fractions5", 5, 10, 9)])
        self.assertEqual(r.target_grade, 5)

    def test_prerequisite_refuerzo(self):
        data = [CompetencyEvidence("fractions5", 5, 10, 3),
                CompetencyEvidence("fractions4", 4, 8, 2, "fractions5")]
        r = recommend(5, "fractions5", data, ml_risk=0.9)
        self.assertEqual((r.target_grade, r.competency_id), (4, "fractions4"))

    def test_no_evidence_no_automatic_grade_drop(self):
        r = recommend(5, "fractions5", [CompetencyEvidence("fractions5", 5, 10, 2)])
        self.assertEqual(r.target_grade, 5)

    def test_invalid_counts_rejected(self):
        with self.assertRaises(ValueError):
            CompetencyEvidence("x", 5, 2, 3)


if __name__ == "__main__":
    unittest.main()
