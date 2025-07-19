const CACHE_NAME = 'radio-russell-v1';
const STATIC_ASSETS = [
  '/',
  '/static/styles.css',
  '/static/script_optimized.js',
  '/static/RadioCalicoLogoTM_optimized.png',
  '/static/RadioCalicoLogoTM.webp',
  'https://fonts.googleapis.com/css2?family=Montserrat:wght@500;600;700&family=Open+Sans:wght@400&display=swap',
  'https://cdn.jsdelivr.net/npm/hls.js@latest'
];

// Cache timeout for API responses (5 minutes)
const API_CACHE_TIME = 5 * 60 * 1000;

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('Caching static assets');
        return cache.addAll(STATIC_ASSETS.filter(url => !url.startsWith('http')));
      })
  );
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  
  // Handle API requests with stale-while-revalidate strategy
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      caches.open(CACHE_NAME).then(async (cache) => {
        const cachedResponse = await cache.match(event.request);
        const fetchPromise = fetch(event.request).then((response) => {
          if (response.ok) {
            // Add timestamp to track cache age
            const responseToCache = response.clone();
            responseToCache.headers.set('cached-at', Date.now().toString());
            cache.put(event.request, responseToCache);
          }
          return response;
        });

        // Return cached response if available and fresh (< 5 minutes)
        if (cachedResponse) {
          const cachedAt = cachedResponse.headers.get('cached-at');
          const age = Date.now() - parseInt(cachedAt || '0');
          
          if (age < API_CACHE_TIME) {
            // Return cached response and update in background
            fetchPromise.catch(() => {}); // Don't let background update errors affect the response
            return cachedResponse;
          }
        }

        // Return fresh response or cached if network fails
        return fetchPromise.catch(() => cachedResponse || new Response('Offline', { status: 503 }));
      })
    );
    return;
  }

  // Handle static assets with cache-first strategy
  if (STATIC_ASSETS.includes(url.pathname) || url.pathname.startsWith('/static/')) {
    event.respondWith(
      caches.match(event.request)
        .then((response) => {
          return response || fetch(event.request).then((response) => {
            if (response.ok) {
              const responseToCache = response.clone();
              caches.open(CACHE_NAME).then((cache) => {
                cache.put(event.request, responseToCache);
              });
            }
            return response;
          });
        })
    );
    return;
  }

  // Handle metadata with network-first strategy (more dynamic)
  if (url.hostname === 'd3d4yli4hf5bmh.cloudfront.net' && url.pathname.includes('metadata')) {
    event.respondWith(
      fetch(event.request, {
        cache: 'no-cache' // Always fetch fresh metadata
      }).catch(() => {
        // Fallback to cache if network fails
        return caches.match(event.request);
      })
    );
    return;
  }

  // Handle cover art with cache-first strategy
  if (url.hostname === 'd3d4yli4hf5bmh.cloudfront.net' && url.pathname.includes('cover')) {
    event.respondWith(
      caches.match(event.request)
        .then((response) => {
          if (response) {
            return response;
          }
          return fetch(event.request).then((response) => {
            if (response.ok) {
              const responseToCache = response.clone();
              caches.open(CACHE_NAME).then((cache) => {
                cache.put(event.request, responseToCache);
              });
            }
            return response;
          });
        })
    );
    return;
  }
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});
