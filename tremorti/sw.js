// Tremorti: minimal service worker, used only to show the daily reminder notification
// (Android Chrome allows page notifications only through a service worker). No fetch handler: nothing is cached or intercepted.
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (e) => e.waitUntil(self.clients.claim()));
self.addEventListener('notificationclick', (e) => {
  e.notification.close();
  e.waitUntil(self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((list) => {
    const open = list.find((c) => c.url.includes('/tremorti'));
    return open ? open.focus() : self.clients.openWindow('./');
  }));
});
