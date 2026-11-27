const jobs = new Map();
const prefix = new URL("__download/", self.registration.scope).href;

self.addEventListener("install", (event) => event.waitUntil(self.skipWaiting()));
self.addEventListener("activate", (event) => event.waitUntil(self.clients.claim()));

self.addEventListener("message", (event) => {
  const { kind, id, readable } = event.data ?? {};
  const reply = event.ports[0];
  if (kind !== "zip" || typeof id !== "string" || !/^[0-9a-f-]{36}$/.test(id) ||
      !(readable instanceof ReadableStream) || !reply) return;
  const timer = setTimeout(() => {
    jobs.delete(id);
    reply.close();
    void readable.cancel().catch(() => {});
  }, 20000);
  jobs.set(id, { readable, timer, reply });
  reply.postMessage("ready");
});

self.addEventListener("fetch", (event) => {
  if (!event.request.url.startsWith(prefix)) return;
  const id = event.request.url.slice(prefix.length);
  const job = jobs.get(id);
  if (!job) {
    event.respondWith(new Response("The download has expired. Start it again.", { status: 404 }));
    return;
  }
  jobs.delete(id);
  clearTimeout(job.timer);
  job.reply.postMessage("started");
  job.reply.close();
  event.respondWith(new Response(job.readable, {
    headers: {
      "Content-Type": "application/zip",
      "Content-Disposition": 'attachment; filename="AFRO-nx.zip"',
      "Cache-Control": "no-store",
    },
  }));
});
