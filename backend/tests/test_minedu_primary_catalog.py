"""Official-source references, without silently changing school plans."""

def test_minedu_primary_catalog_is_authenticated_and_grade_specific(w):
    assert w.c.get("/api/v1/curriculum/minedu/primaria").status_code == 401
    w.staff("ADMIN", "minedu-admin@example.com")
    auth = w.login("minedu-admin@example.com")
    result = w.c.get("/api/v1/curriculum/minedu/primaria", headers=auth)
    assert result.status_code == 200, result.text
    body = result.json()
    assert body["source_label"] == "Ministerio de Educación del Perú (MINEDU)"
    assert body["level"] == "PRIMARIA"
    assert body["status"] == "REFERENCIA_PUBLICA"
    assert [g["number"] for g in body["grades"]] == [1, 2, 3, 4, 5, 6]
    assert len({g["planning_pdf_url"] for g in body["grades"]}) == 6
    for g in body["grades"]:
        assert g["example_status"] == "EJEMPLO_NO_OBLIGATORIO"
        assert g["planning_pdf_url"].startswith("https://minedu.gob.pe/curriculo/pdf/")
        assert g["planning_word_url"].endswith(".docx")
    assert len(body["math_competencies"]) == 4
    assert "no obligatorios" in body["notice"].lower()
    assert "repositorio.minedu.gob.pe" in body["curriculum"]["url"]
