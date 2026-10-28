import type { ReactNode } from "react";
import { Icon, type IconName } from "./Icon";

interface Props {
  kicker: string;
  title: string;
  description: string;
  icon: IconName;
  children?: ReactNode;
}

/** Shared visual header for the teacher's workflow screens; no simulated metrics. */
export function TeacherPageIntro({ kicker, title, description, icon, children }: Props) {
  return <header className="teacher-flow-hero">
    <span className="teacher-flow-hero-icon" aria-hidden="true"><Icon name={icon}/></span>
    <div className="teacher-flow-hero-main">
      <p className="teacher-flow-kicker">{kicker}</p>
      <h2>{title}</h2>
      <p>{description}</p>
      {children && <div className="teacher-flow-hero-actions">{children}</div>}
    </div>
    <div className="teacher-flow-hero-art" aria-hidden="true"><Icon name="leaf"/></div>
  </header>;
}