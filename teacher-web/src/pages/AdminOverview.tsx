import { useState, type CSSProperties } from 'react';
import { Link } from 'react-router-dom';
import { Icon, type IconName } from '../components/Icon';
import './admin-overview.css';

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
  const max=Math.max(1,...cumul.flat());
  const colors=['#03e3b4','#2a9fff','#ffc654'];
  const names=['Estudiantes','Docentes','Instituciones'];
  const px=(i:number)=>36+i*418/11;
  const py=(v:number)=>177-150*v/max;
  return <>
    <header className="kd-panel-heading"><h3>Crecimiento mensual</h3><span className="kd-year">{year}</span></header>
    <p className="kd-subtext">Altas acumuladas durante {year} (no totales históricos).</p>
    <svg className="kd-line-chart" viewBox="0 0 485 210" role="img" aria-label={'Evolución mensual de registros durante '+year} onMouseLeave={()=>setFocus(null)}>
      {[0,.25,.5,.75,1].map(t=><g key={t}><line x1="36" y1={py(max*t)} x2="458" y2={py(max*t)} stroke="#25435e" strokeDasharray="3 4"/><text x="29" y={py(max*t)+3} fill="#90a7ba" textAnchor="end" fontSize="9">{Math.round(max*t)}</text></g>)}
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
export function AdminOverview({schools,audits,stats,loading,errors,onRefresh}:Props){
  const [filter,setFilter]=useState('');const [busy,setBusy]=useState(false);
  const tiles:{icon:IconName;title:string;value:number|undefined;desc:string;to:string}[]=[
    {icon:'classroom',title:'Instituciones registradas',value:stats?.institutions,desc:'Escuelas en el sistema',to:'/admin/instituciones'},
    {icon:'students',title:'Docentes registrados',value:stats?.teachers,desc:'Cuentas activas',to:'/admin/docentes'},
    {icon:'graduation',title:'Estudiantes activos',value:stats?.students,desc:'Cuentas activas',to:'/admin/estudiantes'},
    {icon:'tasks',title:'Tareas asignadas',value:stats?.student_assignments,desc:'Asignaciones registradas',to:'/admin/tareas'},
  ];
  const filtered=schools?.filter(s=>s.name.toLocaleLowerCase('es').includes(filter.toLocaleLowerCase('es')))??[];
  async function refresh(){if(busy)return;setBusy(true);try{await onRefresh();}finally{setBusy(false);}}
  return <div className="kd-overview">
    <section className="kd-hero"><div className="kd-hero-copy"><div className="kd-hero-kicker">KAWSAY AI · APRENDER, CRECER Y ACOMPAÑAR</div><h1>Bienvenido, <em>Administrador</em></h1><h2>Gestiona las instituciones, docentes y recursos de KAWSAY AI.</h2><p>Más educación para más comunidades.</p><div className="kd-motto"><span><Icon name="book"/> APRENDER</span><span><Icon name="leaf"/> CRECER</span><span><Icon name="students"/> ACOMPAÑAR</span></div></div><div className="kd-hero-quote">Educación sin límites<br/>para un mejor mañana</div></section>
    {errors.length>0&&<div className="kd-warning" role="alert">No se pudieron consultar todas las estadísticas. <button type="button" onClick={()=>void refresh()}>Reintentar</button></div>}
    <div className="kd-kpis">{tiles.map((t,i)=><Link className={'kd-kpi tone-'+tones[i]} to={t.to} key={t.title}><div className="kd-kpi-icon"><CounterIcon icon={t.icon}/></div><div className="kd-kpi-copy"><span>{t.title}</span><strong>{t.value??(loading?'…':'—')}</strong><small>{t.desc}</small></div><div className="kd-kpi-watermark"><CounterIcon icon={t.icon}/></div></Link>)}</div>
    <div className="kd-row kd-row-top">
      <section className="kd-panel kd-shortcuts"><header className="kd-panel-heading"><h3>Accesos rápidos</h3><button className="kd-refresh" onClick={()=>void refresh()} disabled={busy} type="button"><Icon name="refresh"/>{busy?'Actualizando…':'Actualizar'}</button></header><div className="kd-shortcut-grid">{quick.map((item,i)=><Link to={item.to} key={item.to} className={'kd-shortcut tone-'+tones[i]}><span className="kd-shortcut-icon"><CounterIcon icon={item.icon}/></span><strong>{item.label}</strong><p>{item.detail}</p><span className="kd-shortcut-arrow"><Icon name="arrow"/></span></Link>)}</div></section>
      <section className="kd-panel kd-map-panel"><header className="kd-panel-heading"><h3>Mapa de instituciones</h3><Link className="kd-outline" to="/admin/instituciones">Ver instituciones</Link></header><MapPreview/></section>
    </div>
    <div className="kd-row kd-row-bottom"><section className="kd-panel kd-growth">{stats?<Chart data={stats.monthly_new} year={stats.year}/>:<p className="kd-empty">{loading?'Cargando estadísticas…':'No se pudo obtener la serie de crecimiento.'}</p>}</section><section className="kd-panel kd-grades">{stats?<Donut data={stats.grades} total={stats.students}/>:<p className="kd-empty">{loading?'Cargando distribución…':'Distribución no disponible.'}</p>}</section><section className="kd-panel kd-audit"><header className="kd-panel-heading"><h3>Actividad reciente</h3><Link className="kd-outline" to="/admin/sistema">Ver todos</Link></header><div className="kd-audit-list">{audits?.slice(0,5).map((a,i)=><div className="kd-audit-row" key={a.id}><span className={'kd-audit-symbol tone-'+tones[i%4]}><Icon name="activity"/></span><div><strong>{a.action.replace(/[._]/g,' ')}</strong><small>{a.target_type} · {new Date(a.created_at).toLocaleDateString('es-PE')}</small></div></div>)}{audits?.length===0&&<p className="kd-empty">Todavía no hay movimientos registrados.</p>}{!audits&&<p className="kd-empty">{loading?'Consultando actividad…':'Actividad no disponible.'}</p>}</div></section></div>
    <section className="kd-panel kd-institutions"><header className="kd-panel-heading"><div><h3>Instituciones en KAWSAY AI</h3><p>Información de instituciones existentes. El mapa requiere ubicaciones verificadas.</p></div><Link className="kd-outline" to="/admin/instituciones">Administrar</Link></header><label className="kd-search"><Icon name="search"/><input type="search" aria-label="Buscar instituciones" placeholder="Buscar institución…" value={filter} onChange={e=>setFilter(e.target.value)}/><span>{filtered.length} resultados</span></label><div className="kd-school-list">{filtered.slice(0,6).map(s=><div key={s.id}><Icon name="classroom"/><span><strong>{s.name}</strong><small>{s.region||'Región no indicada'}</small></span><Link to="/admin/instituciones" aria-label={'Administrar '+s.name}><Icon name="arrow"/></Link></div>)}{schools&&filtered.length===0&&<p className="kd-empty">{filter?'Sin coincidencias.':'No hay instituciones registradas.'}</p>}</div></section>
  </div>;
}