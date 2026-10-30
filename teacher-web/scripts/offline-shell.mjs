import { createHash } from "node:crypto";

/** The build names every emitted asset explicitly; no API response is cached. */
export function offlineShell() {
  return {
    name: "kawsay-offline-shell",
    apply: "build",
    enforce: "post",
    generateBundle(_options, bundle) {
      const assets = Object.keys(bundle).filter(name => /\.(js|css|svg|png|webp|woff2?)$/.test(name)).map(name => `/${name}`);
      const revision = createHash("sha256").update(assets.join("\n")).digest("hex").slice(0, 16);
      this.emitFile({ type: "asset", fileName: "sw.js", source: `
const CACHE = "kawsay-shell-${revision}";
const ASSETS = ${JSON.stringify(["/", ...assets])};
self.addEventListener("install", event => event.waitUntil((async () => {
  const cache = await caches.open(CACHE);
  await cache.addAll(ASSETS);
  await self.skipWaiting();
})()));
self.addEventListener("activate", event => event.waitUntil((async () => {
  for (const name of await caches.keys()) if (name.startsWith("kawsay-shell-") && name !== CACHE) await caches.delete(name);
  await self.clients.claim();
})()));
self.addEventListener("fetch", event => {
  const request = event.request;
  const url = new URL(request.url);
  if (request.method !== "GET" || url.origin !== self.location.origin || url.pathname.startsWith("/api/")) return;
  if (request.mode === "navigate") {
    event.respondWith(fetch(request).catch(async () => {
      const cached = await (await caches.open(CACHE)).match("/", { ignoreVary: true });
      return cached || Response.error();
    }));
  } else if (ASSETS.includes(url.pathname)) {
    event.respondWith((async () => (await (await caches.open(CACHE)).match(url.pathname, { ignoreVary: true })) || fetch(request))());
  }
});
` });
    },
  };
}
