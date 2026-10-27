const paths = {
  leaf: "M12 21v-9m0 4C4 17 2 10 3 4c7 0 10 4 9 12Zm0-3c0-6 4-10 9-10 1 6-2 11-9 10Z",
  dashboard: "M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z",
  classroom: "M3 21V5l9-3 9 3v16M8 21v-6h8v6M7 8h2m6 0h2M7 11h2m6 0h2M1 21h22",
  students: "M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2m20 0v-2a4 4 0 0 0-3-3.87M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8Zm8-7.87a4 4 0 0 1 0 7.75",
  book: "M12 5v16M3 3c4-1 7 0 9 2 2-2 5-3 9-2v16c-4-1-7 0-9 2-2-2-5-3-9-2Z",
  tasks: "M9 4H5v17h14V4h-4M9 2h6v4H9zM8 11h8m-8 5h5",
  alert: "M12 3 2 21h20ZM12 9v5m0 3v.1",
  settings: "M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8Zm0-6v3m0 14v3M2 12h3m14 0h3M5 5l2 2m10 10 2 2M5 19l2-2M17 7l2-2",
  arrow: "M4 12h16m-6-6 6 6-6 6",
  logout: "M9 4H3v16h6m0-8h12m-5-5 5 5-5 5",
  activity: "M2 12h5l3-8 4 16 3-8h5",
  spark: "m12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5Z",
  check: "m5 12 4 4L19 6",
  eye: "M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12Zm10-3a3 3 0 1 0 0 6 3 3 0 0 0 0-6Z",
} as const;

export type IconName = keyof typeof paths;

export function Icon({ name, className = "" }: { name: IconName; className?: string }) {
  return <svg className={`icon ${className}`} width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false"><path d={paths[name]} /></svg>;
}

export function Brand() {
  return <div className="brand"><span className="brand-mark"><Icon name="leaf" /></span><span>KAWSAY <em>AI</em><small>Educación que acompaña</small></span></div>;
}
