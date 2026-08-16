// Service worker minimal : ne fait pas de mise en cache agressive (l'app a besoin
// du réseau pour la plupart de ses fonctions), mais sa seule présence avec un
// gestionnaire 'fetch' est nécessaire pour que les navigateurs (Chrome/Android
// notamment) proposent l'installation en tant qu'application (PWA).
self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', (event) => {
  // Laisse passer toutes les requêtes normalement (pas de cache hors-ligne :
  // l'app nécessite le serveur Streamlit actif pour fonctionner).
  event.respondWith(fetch(event.request));
});
