"""Curricular documents are stored by institution, grade and area, with staff access control."""
import io
import zipfile


def valid_docx() -> bytes:
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as z:
        z.writestr("[Content_Types].xml", '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"></Types>')
        z.writestr("word/document.xml", '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>')
    return out.getvalue()


def upload(client, headers, school_id: str, grade: int, name: str = "planificacion.docx", data: bytes | None = None):
    params = {
        "school_id": str(school_id), "academic_year": 2026,
        "education_level": "PRIMARIA", "grade_number": grade,
        "area": "Matemática", "filename": name,
    }
    return client.post(
        "/api/v1/curriculum/documents",
        params=params, headers={**headers, "Content-Type": "application/octet-stream"},
        content=valid_docx() if data is None else data,
    )


def test_admin_upload_grade_separation_approval_download(w):
    school = w.school()
    w.staff("ADMIN", "admin-docs@example.com")
    h = w.login("admin-docs@example.com")
    upload_response = upload(w.c,h,school.id,1)
    assert upload_response.status_code == 201, upload_response.text
    doc = upload_response.json()
    assert doc["grade_number"] == 1 and doc["status"] == "PENDING"
    assert doc["area"] == "Matemática"
    assert doc["file_size"] == len(valid_docx())
    listing = {
        "school_id": str(school.id), "academic_year": 2026,
        "education_level": "PRIMARIA", "grade_number": 1,
    }
    own = w.c.get("/api/v1/curriculum/documents",params=listing,headers=h)
    assert own.status_code == 200 and len(own.json()) == 1
    assert "file_data" not in own.json()[0]
    assert w.c.get("/api/v1/curriculum/documents",params={**listing,"grade_number":2},headers=h).json() == []
    downloaded = w.c.get(f"/api/v1/curriculum/documents/{doc['id']}/download",headers=h)
    assert downloaded.status_code == 200 and downloaded.content == valid_docx()
    assert downloaded.headers["content-type"].startswith("application/octet-stream")
    assert downloaded.headers["x-content-type-options"] == "nosniff"
    approved = w.c.post(f"/api/v1/curriculum/documents/{doc['id']}/review?approved=true",headers=h)
    assert approved.status_code == 200
    assert approved.json()["status"] == "APPROVED"


def test_teacher_is_restricted_to_own_school_and_cannot_approve(w):
    s1, s2 = w.school("Escuela 1"), w.school("Escuela 2")
    w.staff("ADMIN","owner-docs@example.com")
    w.staff("TEACHER","teacher-docs@example.com",s1)
    ht = w.login("teacher-docs@example.com")
    ha = w.login("owner-docs@example.com")
    schools = w.c.get("/api/v1/curriculum/documents/schools",headers=ht)
    assert schools.status_code == 200
    assert [row["id"] for row in schools.json()] == [str(s1.id)]
    assert upload(w.c,ht,s2.id,1).status_code == 403
    rejected = upload(w.c,ht,s1.id,1)
    assert rejected.status_code == 201, rejected.text
    did=rejected.json()["id"]
    assert w.c.get(f"/api/v1/curriculum/documents/{did}/download",headers=ht).status_code == 200
    assert w.c.post(f"/api/v1/curriculum/documents/{did}/review?approved=true",headers=ht).status_code == 403
    assert w.c.post(f"/api/v1/curriculum/documents/{did}/review?approved=false",headers=ha).status_code == 200
    assert w.c.get("/api/v1/curriculum/documents",params={
        "school_id":str(s2.id),"academic_year":2026,"education_level":"PRIMARIA","grade_number":1,
    },headers=ht).status_code == 403


def test_reject_fake_extension_broken_files_and_unauthed(w):
    school = w.school()
    w.staff("ADMIN","owner-files@example.com")
    h=w.login("owner-files@example.com")
    assert upload(w.c,h,school.id,1,name="plan.docx",data=b"not a zip").status_code == 422
    assert upload(w.c,h,school.id,1,name="plan.pdf",data=b"not a PDF").status_code == 422
    assert upload(w.c,h,school.id,1,name="plan.doc",data=b"not a docx").status_code == 422
    assert upload(w.c,h,school.id,1,name="../unsafe.docx").status_code == 422
    assert upload(w.c,h,school.id,1,name="plan.docx",data=b"x"*(4*1024*1024+1)).status_code == 413
    assert upload(w.c,{},school.id,1).status_code == 401
    resp=upload(w.c,h,school.id,6)
    assert resp.status_code == 201
    listing=w.c.get("/api/v1/curriculum/documents",params={
        "school_id":str(school.id),"academic_year":2026,"education_level":"SECUNDARIA","grade_number":6,
    },headers=h)
    assert listing.status_code == 422
