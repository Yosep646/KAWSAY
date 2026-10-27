const { spawnSync } = require("node:child_process");
const { resolve } = require("node:path");

const root = resolve(__dirname, "../..");
const python = resolve(root, process.platform === "win32" ? ".venv/Scripts/python.exe" : ".venv/bin/python");
const result = spawnSync(python, [resolve(root, "scripts/browser_e2e.py"), ...process.argv.slice(2)], {
  cwd: root,
  stdio: "inherit",
  env: { ...process.env, PYTHONIOENCODING: "utf-8" },
});
if (result.error) console.error(result.error.message);
process.exit(result.status ?? 1);
