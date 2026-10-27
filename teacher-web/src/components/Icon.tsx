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
  mail: "M3 5h18v14H3V5Zm0 2 9 7 9-7",
  lock: "M5 10h14v11H5V10Zm3 0V7a4 4 0 1 1 8 0v3M12 14v3",
  graduation: "M2 9 12 4l10 5-10 5L2 9Zm4 4v5c4 3 8 3 12 0v-5M22 9v7",
  chart: "M4 20V11m5 9V5m5 15v-8m5 8V3M2 20h20",
  "map-pin": "M20 10c0 5-8 12-8 12S4 15 4 10a8 8 0 1 1 16 0Zm-8-3a3 3 0 1 0 0 6 3 3 0 0 0 0-6Z",
  refresh: "M21 6v6h-6M3 18v-6h6m-5-2a8 8 0 0 1 14-4l3 6M3 12l3 6a8 8 0 0 0 14-4",
  search: "M11 19a8 8 0 1 0 0-16 8 8 0 0 0 0 16Zm6-2 5 5",
  bell: "M18 8a6 6 0 0 0-12 0c0 7-3 8-3 9h18c0-1-3-2-3-9ZM10 21h4",
  sun: "M12 3v2m0 14v2M3 12h2m14 0h2M5.6 5.6 7 7m10 10 1.4 1.4M18.4 5.6 17 7M7 17l-1.4 1.4M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8Z",
  moon: "M20 15.7A8.5 8.5 0 0 1 8.3 4 8.5 8.5 0 1 0 20 15.7Z",
  menu: "M3 6h18M3 12h18M3 18h18",
  x: "M5 5l14 14M19 5 5 19",
  shield: "M12 22c-7-4-9-8-9-15l9-4 9 4c0 7-2 11-9 15Zm-4-10 3 3 5-6",
  database: "M21 6c0 2-4 4-9 4S3 8 3 6s4-4 9-4 9 2 9 4Zm-18 0v6c0 2 4 4 9 4s9-2 9-4V6M3 12v6c0 2 4 4 9 4s9-2 9-4v-6",
  "eye-off": "m3 3 18 18M10.6 5.1A11 11 0 0 1 12 5c6 0 10 7 10 7a15.8 15.8 0 0 1-3.4 4.3M6.2 6.3A16 16 0 0 0 2 12s4 7 10 7a9.6 9.6 0 0 0 4.3-1M9.2 9.2A4 4 0 0 0 14.8 14.8",
} as const;

export type IconName = keyof typeof paths;

export function Icon({ name, className = "" }: { name: IconName; className?: string }) {
  return <svg className={`icon ${className}`} width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false"><path d={paths[name]} /></svg>;
}

export function Brand() {
  return <div className="brand"><span className="brand-mark"><Icon name="leaf" /></span><span>KAWSAY <em>AI</em><small>Educación que acompaña</small></span></div>;
}
