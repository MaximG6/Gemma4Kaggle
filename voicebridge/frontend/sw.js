/**
 * VoiceBridge Service Worker — offline routing (Task 2.5).
 *
 * Strategy:
 *   /intake requests → try remote server first.
 *   If the network fetch fails (offline), rewrite the URL to
 *   localhost:8080 (the llama.cpp edge server running on-device)
 *   and retry locally.
 *
 * All other requests use a cache-first strategy so the UI loads
 * fully offline after the first visit.
 */

const CACHE_NAME = "voicebridge-v1";
const REMOTE_ORIGIN = "https://voicebridge.app";
const LOCAL_ORIGIN  = "http://localhost:8080";

// Assets to pre-cache on install
const PRECACHE_URLS = ["/ui/", "/ui/index.html"];

// ─── Install ────────────────────────────────────────────────────────────────
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(PRECACHE_URLS))
  );
  self.skipWaiting();
});

// ─── Activate ───────────────────────────────────────────────────────────────
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((k) => k !== CACHE_NAME)
          .map((k) => caches.delete(k))
      )
    )
  );
  self.clients.claim();
});

// ─── Fetch ──────────────────────────────────────────────────────────────────
self.addEventListener("fetch", (event) => {
  const url = event.request.url;

  // Intake API calls: network-first, fall back to local edge server
  if (url.includes("/intake")) {
    event.respondWith(networkFirstWithEdgeFallback(event.request));
    return;
  }

  // Everything else: cache-first (offline UI support)
  event.respondWith(cacheFirst(event.request));
});

/**
 * Try the network; on failure rewrite the host to the local edge server.
 */
async function networkFirstWithEdgeFallback(request) {
  try {
    return await fetch(request);
  } catch (_networkError) {
    // Build a new request pointing at the local llama.cpp server
    const localUrl = request.url.replace(REMOTE_ORIGIN, LOCAL_ORIGIN);
    const localRequest = new Request(localUrl, {
      method:  request.method,
      headers: request.headers,
      body:    request.method !== "GET" ? await request.clone().blob() : undefined,
      mode:    "cors",
    });
    return fetch(localRequest);
  }
}

/**
 * Try cache first; fall back to network and cache the response.
 */
async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return cached;

  try {
    const response = await fetch(request);
    if (response && response.status === 200 && response.type === "basic") {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch (_err) {
    return new Response("Offline — resource not cached.", { status: 503 });
  }
}
