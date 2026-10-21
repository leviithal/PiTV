/* PiTV V3.2 - conservative video-only auto fullscreen.
 * No API tokens, no network calls, no changes to playback or to site DRM.
 * Uses the platform Fullscreen API only for an actual, visible, playing movie.
 */
(() => {
  'use strict';
  const host = location.hostname;
  if (!/^(www\.)?netflix\.com$|^(www\.)?disneyplus\.com$/.test(host)) return;
  const isNetflix = /netflix\.com$/.test(host);
  const attempted = new WeakMap();
  let lastUrl = location.href;
  let routeEpoch = 0;
  let timer = null;

  function movieRoute() {
    if (isNetflix) return /^\/watch\/[^/]+/.test(location.pathname);
    // Disney+ changes routes more often. Require a player-like route *and* a large playing video.
    return /(?:^|\/)play(?:\/|$)|(?:^|\/)video(?:\/|$)|(?:^|\/)watch(?:\/|$)/i.test(location.pathname);
  }

  function playerCandidate() {
    if (!movieRoute() || document.fullscreenElement) return null;
    const videos = document.querySelectorAll('video');
    for (const video of videos) {
      if (video.paused || video.ended || video.readyState < 2) continue;
      const r = video.getBoundingClientRect();
      if (r.width < innerWidth * 0.70 || r.height < innerHeight * 0.43) continue;
      if (r.right <= 0 || r.bottom <= 0 || r.left >= innerWidth || r.top >= innerHeight) continue;
      return video;
    }
    return null;
  }

  function fullscreenTarget(video) {
    // Prefer a large player container: it is more likely to contain captions and controls.
    // Never fullscreen the entire page/document, as kiosk mode already handles that.
    const known = video.closest('.watch-video, [data-uia="video-player"], [data-testid="video-player"], [class*="video-player"], [class*="VideoPlayer"]');
    if (known && known !== document.body && known !== document.documentElement && known.requestFullscreen) return known;
    let node = video.parentElement;
    for (let depth = 0; node && depth < 6; depth++, node = node.parentElement) {
      if (node === document.body || node === document.documentElement) break;
      const r = node.getBoundingClientRect();
      if (r.width >= innerWidth * .85 && r.height >= innerHeight * .70 && node.requestFullscreen) return node;
    }
    return video;
  }

  function attempt() {
    if (location.href !== lastUrl) { lastUrl = location.href; routeEpoch++; }
    const video = playerCandidate();
    if (!video) return;
    if (attempted.get(video) === routeEpoch) return;
    attempted.set(video, routeEpoch); // One attempt per movie route, no retry-loop or fullscreen flicker.
    const target = fullscreenTarget(video);
    try {
      const result = target.requestFullscreen({navigationUI:'hide'});
      if (result && typeof result.catch === 'function') {
        result.catch(err => console.info('PiTV: automatisk filmhelskärm nekades:', err.name));
      }
    } catch (err) { console.info('PiTV: automatisk filmhelskärm ej tillgänglig:', err.name); }
  }

  function queueAttempt() {
    clearTimeout(timer);
    timer = setTimeout(attempt, 450);
  }
  // Capture playing from video even when Netflix/Disney load player nodes dynamically.
  document.addEventListener('playing', queueAttempt, true);
  // Single-page applications can replace routes without full reload.
  setInterval(attempt, 1500);
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) queueAttempt();
  });
})();
