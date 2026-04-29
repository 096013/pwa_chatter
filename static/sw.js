const CACHE_NAME = "pwa-chat-cache-v2";
const STATIC_ASSETS = [
  "/static/manifest.json",
  "/static/sw.js",
  "/static/style.css"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => key !== CACHE_NAME)
          .map((key) => caches.delete(key))
      )
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") {
    return;
  }

  const url = new URL(event.request.url);
  const isDynamicPage =
    url.pathname === "/" ||
    url.pathname === "/register" ||
    url.pathname === "/board" ||
    url.pathname === "/settings" ||
    url.pathname.startsWith("/api/") ||
    url.pathname.startsWith("/like/");

  if (isDynamicPage) {
    event.respondWith(fetch(event.request, { cache: "no-store" }));
    return;
  }

  event.respondWith(
    caches.match(event.request).then((cached) => cached || fetch(event.request))
  );
});
