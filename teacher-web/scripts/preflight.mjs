import { existsSync } from "node:fs";
import { resolve } from "node:path";

const version = process.versions.node.split(".").map(Number);
const valid = version[0] > 24 || (version[0] === 24 && (version[1] > 15 || (version[1] === 15 && version[2] >= 0)));
if (!valid) {
  console.error(`ERROR: Node ${process.version} detectado. KAWSAY AI requiere Node >=24.15.0. Cambia la versión antes de ejecutar npm ci.`);
  process.exitCode = 1;
} else {
  console.log(`OK: Node ${process.version}`);
}
if (!existsSync(resolve("package-lock.json"))) {
  console.error("ERROR: No se encontró package-lock.json; ejecuta desde teacher-web/.");
  process.exitCode = 1;
}
if (!existsSync(resolve("node_modules", "vite", "package.json"))) {
  console.log("Dependencias aún no instaladas. Ejecuta npm ci con acceso a registry.npmjs.org.");
}
