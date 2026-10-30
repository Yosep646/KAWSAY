import { useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { Card, ErrorBox, Loading } from "../components/ui";
import { Icon } from "../components/Icon";
import { useAsync } from "../hooks/useAsync";
import { api } from "../services/api";
import { errMsg } from "../utils/format";
import type { Language, StudentLanguages, StudentLanguagesInput } from "../types/api";
import "./student-preferences.css";

/** El alumno decide su lengua materna y el idioma en que prefiere aprender.
 * La configuración persiste en servidor y vuelve a sincronizar traducciones aprobadas.
 */
export function StudentLanguageSettings() {
  const languages = useAsync(() => api.get<Language[]>("/languages"), []);
  const preference = useAsync(() => api.get<StudentLanguages>("/students/me/languages"), []);
  const [mother, setMother] = useState("");
  const [variant, setVariant] = useState("");
  const [preferred, setPreferred] = useState("");
  const [saving, setSaving] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!preference.data) return;
    setMother(preference.data.mother_language ?? "");
    setVariant(preference.data.mother_variant_id ?? "");
    setPreferred(preference.data.preferred_language ?? "");
  }, [preference.data]);

  const variants = languages.data?.find(item => item.code === mother)?.variants ?? [];
  async function save(event: FormEvent) {
    event.preventDefault();
    if (saving || !languages.data?.length) return;
    const input: StudentLanguagesInput = {
      mother_language_code: mother || null,
      mother_variant_id: variant || null,
      preferred_language_code: preferred || null,
    };
    try {
      setSaving(true); setNotice(null); setError(null);
      const result = await api.put<StudentLanguages>("/students/me/languages", input);
      setMother(result.mother_language ?? "");
      setVariant(result.mother_variant_id ?? "");
      setPreferred(result.preferred_language ?? "");
      setNotice("Idioma guardado en tu cuenta. Las actividades se actualizarán al sincronizar. Solo se mostrarán traducciones educativas verificadas; de lo contrario, permanecerán en español.");
    } catch (reason) { setError(errMsg(reason)); }
    finally { setSaving(false); }
  }

  return <div className="student-language-settings">
    <header className="student-preference-hero">
      <p><Icon name="book"/> KAWSAY AI / MI APRENDIZAJE</p>
      <h2>Mi idioma</h2>
      <span>Elige el idioma en el que prefieres aprender.</span>
    </header>
    <Card title="Preferencias de idioma">
      <p>Selecciona solamente el idioma que tú o tu familia declaran. KAWSAY AI no lo adivina por tu ubicación.</p>
      <ErrorBox message={languages.error ?? preference.error ?? error}/>
      {notice && <p role="status" className="notice">{notice}</p>}
      {languages.loading || preference.loading ? <Loading/> : <form className="student-preference-form" onSubmit={e => void save(e)}>
        <label htmlFor="student-mother-language">Mi lengua materna
          <select id="student-mother-language" value={mother} onChange={e => { setMother(e.target.value); setVariant(""); }}>
            <option value="">Prefiero no indicar</option>
            {languages.data?.map(l => <option key={l.code} value={l.code}>{l.name}</option>)}
          </select>
        </label>
        {!!variants.length && <label htmlFor="student-language-variant">Mi variante de idioma
          <select id="student-language-variant" value={variant} onChange={e => setVariant(e.target.value)}>
            <option value="">Sin especificar</option>
            {variants.map(v => <option key={v.id} value={v.id}>{v.name}</option>)}
          </select>
        </label>}
        <label htmlFor="student-preferred-language">Idioma en que prefiero aprender
          <select id="student-preferred-language" value={preferred} onChange={e => setPreferred(e.target.value)}>
            <option value="">Sin especificar</option>
            {languages.data?.map(l => <option key={l.code} value={l.code}>{l.name}</option>)}
          </select>
        </label>
        <button type="submit" disabled={saving || !languages.data?.length}>
          {saving ? "Guardando…" : "Guardar mi idioma"}
        </button>
      </form>}
      <p className="student-preference-help">Cambiar el idioma requiere conexión para guardarlo en tu cuenta. Después puedes consultar sin Internet las actividades que ya tengas descargadas y traducidas. No se generan traducciones automáticas no revisadas.</p>
      <Link to="/estudiante/cursos">Volver a mis cursos <Icon name="arrow" /></Link>
    </Card>
  </div>;
}
