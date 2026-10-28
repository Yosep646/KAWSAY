import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { CreateAssignment } from "../pages/Assignments";
import { api } from "../services/api";

const grades = Array.from({length:6}, (_,i)=>({id:i+1,level:"PRIMARIA",number:i+1}));
const units = grades.map(g=>({
  id:`unit-${g.id}`, title:`Sumas grado ${g.number}`,
  grade_id:g.id,subject_id:"math",topics:[{id:`topic-${g.id}`,title:"Sumas",
    competency_id:"cantidad",learning_objective:"Resolver problemas de cantidad"}],
}));
vi.mock("../hooks/useAsync", () => ({
  useAsync: (load: () => Promise<unknown>) => {
    const source = String(load);
    const data = source.includes("/classrooms") ?
      [{id:"room-1",name:"Aula Multigrado",school_id:"school-1",academic_year:2026}] :
      source.includes("/curriculum/grades") ? grades :
      source.includes("/planning/active?classroom_id=") ?
      [{id:"version-1",plan_id:"plan-1",label:"v1",status:"ACTIVE",
        periods:[{id:"period-1",name:"Periodo",sequence:1,units}]}] : [];
    return {data,loading:false,error:null,reload:async()=>{},setData:()=>{}};
  },
}));

beforeEach(()=>window.sessionStorage.clear());
afterEach(()=>vi.restoreAllMocks());

describe("Adaptación de Matemática a los seis grados",()=>{
  it("selecciona temas compatibles y envía la operación original de 4.º al motor de reglas", async()=>{
    const send=vi.spyOn(api,"post").mockImplementation(async (path: string) => {
      if(path==="/assignments") return {id:"assignment-1",variants:[]};
      if(path==="/assignments/assignment-1/adapt-math") return {engine:"RULES",status:"TEACHER_REVIEW"};
      throw new Error("Petición inesperada: "+path);
    });
    render(<MemoryRouter><CreateAssignment/></MemoryRouter>);
    await userEvent.type(screen.getByRole("textbox",{name:/Título de la actividad/}),"Suma de números naturales");
    await userEvent.type(screen.getByRole("textbox",{name:/Actividad base/}),"Resolver sumas con ejemplos de mi comunidad.");
    await userEvent.click(screen.getByRole("checkbox",{name:/Adaptar Matemática según el grado/}));
    await userEvent.type(screen.getByRole("textbox",{name:/Ejercicio original del docente/}),"245 + 178");
    await userEvent.click(screen.getByRole("button",{name:/Seleccionar grados con la misma competencia/}));
    expect(screen.getAllByText("6",{selector:"strong"}).length).toBeGreaterThanOrEqual(1);
    const create=screen.getByRole("button",{name:/Crear variantes para revisión/});
    expect(create).toBeEnabled();
    await userEvent.click(create);
    await waitFor(()=>expect(send).toHaveBeenCalledTimes(2));
    expect(send).toHaveBeenNthCalledWith(1,"/assignments",expect.objectContaining({
      classroom_id:"room-1",
      grade_topics:grades.map(g=>({grade_id:g.id,topic_id:`topic-${g.id}`})),
    }));
    expect(send).toHaveBeenNthCalledWith(2,"/assignments/assignment-1/adapt-math",{
      source_grade_id:4,example:"245 + 178",
    });
  });
});
