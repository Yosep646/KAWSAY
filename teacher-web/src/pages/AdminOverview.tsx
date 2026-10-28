import { useState, type CSSProperties } from 'react';
import { Link } from 'react-router-dom';
import { Icon, type IconName } from '../components/Icon';
import './admin-overview.css';
import './admin-refinement.css';

export interface AdminStatistics {
  year: number;
  institutions: number;
  teachers: number;
  students: number;
  published_assignments: number;
  student_assignments: number;
  grades: { level: string; grade: number; count: number }[];
  monthly_new: { month: number; schools_new: number; teachers_new: number; students_new: number }[];
  map_available: boolean;
  map_message: string;
}
type School = { id: string; name: string; region?: string | null };
type Staff = { id: string; role: string; display_name: string; is_active: boolean };
type Audit = { id: string; action: string; target_type: string; created_at: string };
type Ev = { id: string; type: string; status: string };
interface Props {
  schools: School[] | null; staff: Staff[] | null; audits: Audit[] | null; events: Ev[] | null;
  stats: AdminStatistics | null; loading: boolean; errors: string[]; onRefresh: () => Promise<void>;
}
const tones = ['blue','green','gold','purple'];
const quick: { label: string; detail: string; to: string; icon: IconName }[] = [
  {label:'Gestionar instituciones',detail:'Registra y administra colegios y sedes.',to:'/admin/instituciones',icon:'classroom'},
  {label:'Registrar docentes',detail:'Crea y administra cuentas docentes.',to:'/admin/docentes',icon:'students'},
  {label:'Revisar currículo',detail:'Gestiona contenidos y malla educativa.',to:'/admin/curriculo',icon:'book'},
  {label:'Reportes y estadísticas',detail:'Revisa indicadores educativos reales.',to:'/admin/reportes',icon:'chart'},
];
const months = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'];
function CounterIcon({icon}:{icon:IconName}){return <Icon name={icon}/>;}
function Chart({data,year}:{data:AdminStatistics['monthly_new'];year:number}){
  const [focus,setFocus]=useState<number|null>(null);
  const cumul = [0,1,2].map((s)=>{
    let sum=0;
    const keys = ['students_new','teachers_new','schools_new'] as const;
    return months.map((_,i)=>{const key=keys[s]??'students_new';sum+=data.find(v=>v.month===i+1)?.[key]??0;return sum;});
  });
  const observedMax=Math.max(0,...cumul.flat());
  const tickStep=observedMax<=4?1:Math.ceil(observedMax/4);
  const axisMax=Math.max(1,Math.ceil(observedMax/tickStep)*tickStep);
  const tickValues=Array.from({length:Math.floor(axisMax/tickStep)+1},(_,i)=>i*tickStep);
  const colors=['#03e3b4','#2a9fff','#ffc654'];
  const names=['Estudiantes','Docentes','Instituciones'];
  const px=(i:number)=>36+i*418/11;
  const py=(v:number)=>177-150*v/axisMax;
  return <>
    <header className="kd-panel-heading"><h3>Crecimiento mensual</h3><span className="kd-year">{year}</span></header>
    <p className="kd-subtext">Altas acumuladas durante {year} (no totales históricos).</p>
    <svg className="kd-line-chart" viewBox="0 0 485 210" role="img" aria-label={'Evolución mensual de registros durante '+year} onMouseLeave={()=>setFocus(null)}>
      {tickValues.map(v=><g key={v}><line x1="36" y1={py(v)} x2="458" y2={py(v)} stroke="#214961" strokeDasharray="3 4"/><text x="28" y={py(v)+3} fill="#a2c9d3" textAnchor="end" fontSize="10">{v}</text></g>)}
      {months.map((m,i)=><text key={m} x={px(i)} y="196" fill="#9cb2c5" textAnchor="middle" fontSize="10">{m}</text>)}
      {cumul.map((list,s)=><g key={s}><polyline points={list.map((v,i)=>`${px(i)},${py(v)}`).join(' ')} fill="none" stroke={colors[s]} strokeWidth="2.7" strokeLinejoin="round" strokeLinecap="round"/>{list.map((v,i)=><circle key={i} cx={px(i)} cy={py(v)} r={focus===i?4:2.6} fill={colors[s]} stroke="#06182e" strokeWidth="1.2"/>)}</g>)}
      {months.map((m,i)=><rect key={m} x={px(i)-16} y="24" width="32" height="159" fill="transparent" onMouseEnter={()=>setFocus(i)}/>)}
      {focus!==null&&<g><line x1={px(focus)} x2={px(focus)} y1="25" y2="179" stroke="#b3cde1" opacity=".6" strokeDasharray="3 3"/><rect x={Math.min(px(focus)+8,350)} y="19" width="111" height="62" rx="7" fill="#143754" stroke="#45718b"/><text x={Math.min(px(focus)+17,359)} y="34" fontSize="10" fill="white">{months[focus]}</text>{names.map((n,i)=><text key={n} x={Math.min(px(focus)+17,359)} y={47+i*11} fontSize="9" fill={colors[i]}>{n}: {cumul[i]?.[focus]??0}</text>)}</g>}
      {cumul.every(a=>a.every(v=>v===0))&&<text x="245" y="100" textAnchor="middle" fill="#b7c9d5" fontSize="12">Sin altas registradas en {year}</text>}
    </svg>
    <div className="kd-legend">{names.map((n,i)=><span key={n}><i style={{background:colors[i]}}/>{n}</span>)}</div>
  </>;
}
function Donut({data,total}:{data:AdminStatistics['grades'];total:number}){
  const colors=['#00c7f2','#0fd3a5','#2c86fa','#febc44','#ee3274','#9e7be8','#62dfed','#549ffe','#edcb5c','#d38ad2','#fb9571'];
  const rows=data.filter(g=>g.count>0).map((g,i)=>({label:`${g.grade}.° ${g.level.toLowerCase()}`,count:g.count,color:colors[i%colors.length]}));
  const n=rows.reduce((acc,x)=>acc+x.count,0);let cursor=0;
  const gradient=rows.length?rows.map(r=>{const start=cursor;cursor+=r.count/n*100;return `${r.color} ${start}% ${cursor}%`;}).join(', '):'#1c3550 0 100%';
  return <>
    <header className="kd-panel-heading"><h3>Distribución por nivel educativo</h3></header>
    <p className="kd-subtext">Estudiantes activos por grado, según la base de datos.</p>
    <div className="kd-donut-layout"><div className="kd-donut" style={{'--kd-gradient':`conic-gradient(${gradient})`} as CSSProperties}><span><strong>{total}</strong><small>Estudiantes</small></span></div>
      <div className="kd-donut-legend">{rows.length?rows.slice(0,8).map(r=><div key={r.label}><i style={{background:r.color}}/><span>{r.label}</span><b>{Math.round(r.count/n*100)}%</b></div>):<p className="kd-empty">Sin estudiantes registrados.</p>}{rows.length>8&&<small>Y {rows.length-8} grados adicionales</small>}</div>
    </div>
  </>;
}
function MapPreview(){return <div className="kd-map" aria-label="Ilustración de Perú; ubicaciones institucionales aún no disponibles">
  <svg viewBox="0 0 460 255" preserveAspectRatio="xMidYMid meet" aria-hidden="true"><defs><linearGradient id="kdPeru" x1="0" y1="0" x2="1" y2="1"><stop stopColor="#0a5576"/><stop offset="1" stopColor="#17a76b"/></linearGradient><pattern id="kdGrid" width="22" height="22" patternUnits="userSpaceOnUse"><path d="M22 0H0V22" fill="none" stroke="#10324f" strokeWidth=".8"/></pattern></defs><rect width="460" height="255" fill="#06182d"/><rect width="460" height="255" fill="url(#kdGrid)"/><path d="M163 8L184 40 178 65 199 87 197 113 221 135 217 153 241 180 237 203 260 232 242 251 216 224 200 201 183 173 164 151 156 126 137 111 119 87 132 72 143 52Z" fill="url(#kdPeru)" stroke="#6de8b4" strokeWidth="2" strokeLinejoin="round"/><path d="M145 61 164 84 156 110 176 144 181 165 198 195 236 237M181 39 173 85 194 111 193 145 214 173" fill="none" stroke="#b0f6bb" strokeWidth="1.5" opacity=".6"/><path d="M145 86 164 101 159 127 178 157" fill="none" stroke="#e4c969" strokeDasharray="5 5" strokeWidth="2"/><text x="290" y="78" fontSize="17" fill="#d4e7ef" fontWeight="700">PERÚ</text><text x="290" y="99" fontSize="12" fill="#99bdcb">Vista ilustrativa</text></svg>
  <p><Icon name="map-pin"/> Aún no se han registrado coordenadas de instituciones.</p>
</div>;}
export function AdminOverview({schools,staff,audits,stats,loading,errors,onRefresh}:Props){
  const [filter,setFilter]=useState('');
  const [busy,setBusy]=useState(false);
  const tiles:{icon:IconName;image:string;title:string;value:number|undefined;desc:string;to:string}[]=[
    {icon:'classroom',image:'/kawsay-card-instituciones.webp',title:'Instituciones',value:stats?.institutions,desc:'Registradas',to:'/admin/instituciones'},
    {icon:'students',image:'/kawsay-card-docentes.webp',title:'Docentes',value:stats?.teachers,desc:'Registrados',to:'/admin/docentes'},
    {icon:'graduation',image:'/kawsay-card-estudiantes.webp',title:'Estudiantes',value:stats?.students,desc:'Activos',to:'/admin/estudiantes'},
    {icon:'tasks',image:'/kawsay-card-tareas_asignadas.webp',title:'Tareas asignadas',value:stats?.student_assignments,desc:'Registros',to:'/admin/tareas'},
  ];
  const filtered=schools?.filter(s=>s.name.toLocaleLowerCase('es').includes(filter.toLocaleLowerCase('es')))??[];
  const records=staff?.filter(s=>s.role!=='STUDENT').slice(0,4)??[];
  async function refresh(){if(busy)return;setBusy(true);try{await onRefresh();}finally{setBusy(false);}}
  return <div className="kd-overview kd-design-2026">
    <div className="kd-mobile-brandbar">
      <span className="kd-mobile-brand"><Icon name="leaf"/><span>KAWSAY <em>AI</em><small>Educación que acompaña</small></span></span>
      <Link aria-label="Auditoría y notificaciones" to="/admin/sistema"><Icon name="bell"/></Link>
    </div>
    <section className="kd-hero" aria-label="Bienvenida al panel de administración">
      <div className="kd-hero-copy">
        <p className="kd-hero-kicker">APRENDER · CRECER · ACOMPAÑAR</p>
        <h1>Bienvenido,<br/><em>Administrador</em></h1>
        <h2>Gestiona las instituciones, docentes, estudiantes y recursos de KAWSAY AI.</h2>
        <div className="kd-motto">
          <span><Icon name="book"/> APRENDER</span>
          <span><Icon name="leaf"/> CRECER</span>
          <span><Icon name="students"/> ACOMPAÑAR</span>
        </div>
      </div>
      <p className="kd-hero-quote">Más educación<br/>para más comunidades.</p>
    </section>
    {errors.length>0&&<div className="kd-warning" role="alert">
      No se pudieron consultar todos los indicadores.
      <button type="button" onClick={()=>void refresh()} disabled={busy}>Reintentar</button>
    </div>}
    <div className="kd-kpis" aria-label="Indicadores reales de la plataforma">{tiles.map((t,i)=>
      <Link className={'kd-kpi tone-'+tones[i]} to={t.to} key={t.to}>
        <span className="kd-kpi-icon">
          <img className="kd-kpi-art" src={t.image} width={96} height={96} alt="" decoding="async"
            onError={(event) => { event.currentTarget.closest('.kd-kpi-icon')?.classList.add('kd-art-missing'); }} />
          <span className="kd-kpi-fallback" aria-hidden="true"><CounterIcon icon={t.icon}/></span>
        </span>
        <span className="kd-kpi-copy"><span>{t.title}</span><strong>{t.value===undefined?(loading?'…':'—'):t.value.toLocaleString('es-PE')}</strong><small>{t.desc}</small></span>
        <span className="kd-kpi-arrow" aria-hidden="true"><Icon name="arrow"/></span>
      </Link>
    )}</div>
    <div className="kd-dash-grid kd-analytics">
      <section className="kd-panel kd-growth">
        {stats?<Chart data={stats.monthly_new} year={stats.year}/>:<p className="kd-empty">{loading?'Cargando crecimiento de registros…':'Datos de crecimiento no disponibles.'}</p>}
      </section>
      <section className="kd-panel kd-grades">
        {stats?<Donut data={stats.grades} total={stats.students}/>:<p className="kd-empty">{loading?'Cargando distribución…':'Distribución no disponible.'}</p>}
      </section>
      <section className="kd-panel kd-audit">
        <header className="kd-panel-heading"><h3>Actividad reciente</h3><Link className="kd-textlink" to="/admin/sistema">Ver todo <Icon name="arrow"/></Link></header>
        <div className="kd-audit-list">
          {audits?.slice(0,5).map((a,i)=><div className="kd-audit-row" key={a.id}>
            <span className={'kd-audit-symbol tone-'+tones[i%4]}><Icon name={i%2?'tasks':'check'}/></span>
            <div><strong>{a.action.replace(/[._]/g,' ')}</strong><small>{a.target_type} · {new Date(a.created_at).toLocaleString('es-PE',{dateStyle:'short',timeStyle:'short'})}</small></div>
          </div>)}
          {audits?.length===0&&<div className="kd-empty-activity"><span><Icon name="activity"/></span><strong>Sin movimientos recientes</strong><p>Las acciones del sistema aparecerán aquí cuando se registren.</p><Link to="/admin/sistema">Consultar auditoría <Icon name="arrow"/></Link></div>}
          {!audits&&<p className="kd-empty">{loading?'Consultando actividad…':'Actividad no disponible.'}</p>}
        </div>
      </section>
    </div>
    <div className="kd-dash-grid kd-management">
      <section className="kd-panel kd-map-panel">
        <header className="kd-panel-heading"><h3>Mapa de instituciones</h3><Link className="kd-textlink" to="/admin/instituciones">Ver todas <Icon name="arrow"/></Link></header>
        <MapPreview/>
      </section>
      <section className="kd-panel kd-reminders">
        <header className="kd-panel-heading"><h3>Tareas y recordatorios</h3><Link className="kd-textlink" to="/admin/tareas">Ver tareas <Icon name="arrow"/></Link></header>
        <div className="kd-reminder-list">
          <Link to="/admin/reportes"><span className="kd-taskmark"><Icon name="chart"/></span>Revisar reportes de aprendizaje <Icon name="arrow"/></Link>
          <Link to="/admin/instituciones"><span className="kd-taskmark"><Icon name="classroom"/></span>Gestionar instituciones <Icon name="arrow"/></Link>
          <Link to="/admin/curriculo"><span className="kd-taskmark"><Icon name="book"/></span>Actualizar contenidos y currículo <Icon name="arrow"/></Link>
          <Link to="/admin/sistema"><span className="kd-taskmark"><Icon name="shield"/></span>Consultar registros del sistema <Icon name="arrow"/></Link>
        </div>
        <p className="kd-subtext">Acciones de gestión · sin fechas límite asignadas.</p>
      </section>
      <section className="kd-panel kd-users">
        <header className="kd-panel-heading"><h3>Usuarios del sistema</h3><Link className="kd-textlink" to="/admin/usuarios">Ver todos <Icon name="arrow"/></Link></header>
        <div className="kd-user-list">
          {records.map(s=><div key={s.id}><span className="kd-user-avatar"><Icon name="students"/></span><span className="kd-user-info"><strong>{s.display_name}</strong><small>{s.role==='ADMIN'?'Administrador':s.role==='TEACHER'?'Docente':s.role}</small></span><span className={'kd-user-status '+(s.is_active?'is-active':'is-inactive')}>{s.is_active?'Activo':'Inactivo'}</span></div>)}
          {staff?.length===0&&<p className="kd-empty">No hay usuarios registrados.</p>}
          {!staff&&<p className="kd-empty">{loading?'Cargando usuarios…':'Usuarios no disponibles.'}</p>}
        </div>
      </section>
    </div>
    <div className="kd-dash-grid kd-actions">
      <section className="kd-panel kd-shortcuts">
        <header className="kd-panel-heading"><h3>Accesos rápidos</h3><button className="kd-refresh" onClick={()=>void refresh()} disabled={busy} type="button"><Icon name="refresh"/>{busy?'Actualizando…':'Actualizar'}</button></header>
        <div className="kd-shortcut-grid">{quick.map((item,i)=><Link to={item.to} key={item.to} className={'kd-shortcut tone-'+tones[i]}>
          <span className="kd-shortcut-icon"><CounterIcon icon={item.icon}/></span><strong>{item.label}</strong><span className="kd-shortcut-arrow"><Icon name="arrow"/></span>
        </Link>)}</div>
      </section>
      <section className="kd-panel kd-help"><Icon name="leaf"/><h3>KAWSAY AI</h3><p>Educación adaptativa con inteligencia artificial y decisiones humanas.</p><Link to="/admin/configuracion">Configurar plataforma <Icon name="arrow"/></Link></section>
    </div>
    <section className="kd-panel kd-institutions">
      <header className="kd-panel-heading"><div><h3>Instituciones de KAWSAY AI</h3><p>Datos registrados; el mapa se mantiene ilustrativo hasta contar con coordenadas verificadas.</p></div><Link className="kd-outline" to="/admin/instituciones">Administrar</Link></header>
      <label className="kd-search"><Icon name="search"/><input type="search" aria-label="Buscar instituciones" placeholder="Buscar institución…" value={filter} onChange={e=>setFilter(e.target.value)}/><span>{filtered.length} resultados</span></label>
      <div className="kd-school-list">{filtered.slice(0,6).map(s=><div key={s.id}><Icon name="classroom"/><span><strong>{s.name}</strong><small>{s.region||'Región no indicada'}</small></span><Link to="/admin/instituciones" aria-label={'Administrar '+s.name}><Icon name="arrow"/></Link></div>)}{schools&&filtered.length===0&&<p className="kd-empty">{filter?'Sin coincidencias.':'No hay instituciones registradas.'}</p>}</div>
    </section>
    <div className="kd-bottom-slogan"><Icon name="book"/><span><strong>Juntos transformamos comunidades</strong><small>Educación, tecnología e identidad cultural.</small></span><em>Más educación para más comunidades.</em></div>
    <nav className="kd-mobile-bottom-nav" aria-label="Accesos de administración">
      <Link to="/admin" aria-current="page"><Icon name="dashboard"/><span>Inicio</span></Link>
      <Link to="/admin/instituciones"><Icon name="classroom"/><span>Instituciones</span></Link>
      <Link to="/admin/tareas"><Icon name="tasks"/><span>Tareas</span></Link>
      <Link to="/admin/reportes"><Icon name="chart"/><span>Reportes</span></Link>
      <Link to="/admin/usuarios"><Icon name="menu"/><span>Más</span></Link>
    </nav>
  </div>;
}
