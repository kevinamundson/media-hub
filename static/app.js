/* Media Hub: persistent audio player (queue, resume, speed), soft navigation, lite YouTube embeds. */
(() => {
  'use strict';
  const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const LS = { get(k, d) { try { const v = localStorage.getItem('mh:' + k); return v === null ? d : JSON.parse(v); } catch { return d; } },
               set(k, v) { try { localStorage.setItem('mh:' + k, JSON.stringify(v)); } catch {} } };
  const fmt = s => { s = Math.max(0, Math.floor(s || 0)); const h = Math.floor(s / 3600), m = Math.floor(s % 3600 / 60), x = String(s % 60).padStart(2, '0'); return h ? `${h}:${String(m).padStart(2, '0')}:${x}` : `${m}:${x}`; };
  const ICON = { play: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M7 4.5v15l13-7.5z"/></svg>', pause: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M6 4h4v16H6zM14 4h4v16h-4z"/></svg>' };
  const SPEEDS = [1, 1.25, 1.5, 1.75, 2, 0.75];

  const audio = new Audio(); audio.preload = 'metadata';
  let queue = LS.get('queue', []), idx = LS.get('idx', 0), lastSave = 0;
  const P = $('#player');
  const ui = { t: $('#p-title'), s: $('#p-series'), img: $('#p-cover'), pp: $('#p-pp'), seek: $('#p-seek'), cur: $('#p-cur'), dur: $('#p-dur'), spd: $('#p-speed'), q: $('#queue') };
  const pos = src => LS.get('pos', {})[src] || 0;
  const setPos = (src, t, d) => { const all = LS.get('pos', {}); if (d && t > d - 15) delete all[src]; else all[src] = Math.floor(t); LS.set('pos', all); };
  const cur = () => queue[idx];

  function load(i, autoplay = true) {
    if (!queue[i]) return; idx = i; LS.set('idx', idx);
    const e = cur(); audio.src = e.src; audio.playbackRate = LS.get('speed', 1);
    const start = pos(e.src); const seekTo = () => { if (start) audio.currentTime = start; audio.removeEventListener('loadedmetadata', seekTo); };
    audio.addEventListener('loadedmetadata', seekTo);
    ui.t.textContent = e.title; ui.t.title = e.title; ui.t.href = e.url; ui.s.textContent = e.series; ui.s.title = e.series; ui.s.href = e.seriesUrl; ui.img.src = e.cover;
    P.classList.add('on'); document.documentElement.classList.add('player-on'); renderQueue(); mark();
    if ('mediaSession' in navigator) navigator.mediaSession.metadata = new MediaMetadata({ title: e.title, artist: 'Kevin R. Amundson', album: e.series, artwork: [{ src: e.cover, sizes: '1400x1400', type: 'image/jpeg' }] });
    if (autoplay) audio.play().catch(() => {});
  }
  function playList(list, i) { queue = list; LS.set('queue', queue); load(i); }
  function toggle() { if (!audio.src) return load(idx); audio.paused ? audio.play() : audio.pause(); }
  function step(n) { const j = idx + n; if (queue[j]) load(j); }

  audio.addEventListener('play', () => { ui.pp.innerHTML = ICON.pause; ui.pp.setAttribute('aria-label', 'Pause'); mark(); });
  audio.addEventListener('pause', () => { ui.pp.innerHTML = ICON.play; ui.pp.setAttribute('aria-label', 'Play'); mark(); if (cur()) setPos(cur().src, audio.currentTime, audio.duration); });
  audio.addEventListener('timeupdate', () => {
    const d = audio.duration || cur()?.duration || 0; ui.cur.textContent = fmt(audio.currentTime); ui.dur.textContent = fmt(d);
    if (!ui.seek.dragging) ui.seek.value = d ? (audio.currentTime / d) * 1000 : 0;
    if (Date.now() - lastSave > 5000 && cur()) { lastSave = Date.now(); setPos(cur().src, audio.currentTime, d); progress(); }
  });
  audio.addEventListener('ended', () => { if (cur()) setPos(cur().src, 0, 1); progress(); if (queue[idx + 1]) load(idx + 1); });
  ui.pp.onclick = toggle;
  $('#p-prev').onclick = () => (audio.currentTime > 5 ? (audio.currentTime = 0) : step(-1));
  $('#p-next').onclick = () => step(1);
  $('#p-back').onclick = () => (audio.currentTime -= 15);
  $('#p-fwd').onclick = () => (audio.currentTime += 30);
  ui.seek.oninput = () => { ui.seek.dragging = true; ui.cur.textContent = fmt(ui.seek.value / 1000 * (audio.duration || 0)); };
  ui.seek.onchange = () => { ui.seek.dragging = false; if (audio.duration) audio.currentTime = ui.seek.value / 1000 * audio.duration; };
  const showSpeed = () => (ui.spd.textContent = LS.get('speed', 1) + '×');
  ui.spd.onclick = () => { const s = SPEEDS[(SPEEDS.indexOf(LS.get('speed', 1)) + 1) % SPEEDS.length]; LS.set('speed', s); audio.playbackRate = s; showSpeed(); };
  $('#p-queue').onclick = () => ui.q.classList.toggle('open');
  if ('mediaSession' in navigator) {
    const ms = navigator.mediaSession;
    ms.setActionHandler('play', () => audio.play()); ms.setActionHandler('pause', () => audio.pause());
    ms.setActionHandler('previoustrack', () => step(-1)); ms.setActionHandler('nexttrack', () => step(1));
    ms.setActionHandler('seekbackward', () => (audio.currentTime -= 15)); ms.setActionHandler('seekforward', () => (audio.currentTime += 30));
  }
  document.addEventListener('keydown', ev => { if (ev.target.closest('input,textarea,select,[contenteditable]')) return; if (ev.code === 'Space' && audio.src) { ev.preventDefault(); toggle(); } });
  window.addEventListener('pagehide', () => cur() && setPos(cur().src, audio.currentTime, audio.duration));

  function renderQueue() {
    ui.q.innerHTML = '<h4>Up next</h4>';
    queue.forEach((e, i) => { const b = document.createElement('button'); b.textContent = `${i + 1}. ${e.title}`; if (i === idx) b.className = 'cur'; b.onclick = () => load(i); ui.q.append(b); });
  }
  function mark() {
    const src = cur()?.src;
    $$('[data-ep]').forEach(li => { const on = li.dataset.src === src; li.classList.toggle('playing', on); const b = $('.pbtn', li); if (b) b.innerHTML = on && !audio.paused ? ICON.pause : ICON.play; });
  }
  function progress() {
    const all = LS.get('pos', {});
    $$('[data-ep]').forEach(li => { const bar = $('.prog i', li); const d = +li.dataset.duration; if (bar && d) bar.style.width = Math.min(100, (all[li.dataset.src] || 0) / d * 100) + '%'; });
  }
  const epOf = el => ({ src: el.dataset.src, title: el.dataset.title, series: el.dataset.series, seriesUrl: el.dataset.seriesUrl, url: el.dataset.url, cover: el.dataset.cover, duration: +el.dataset.duration });

  function initPage() {
    const items = $$('[data-ep]');
    items.forEach((li, i) => {
      const b = $('.pbtn', li); if (!b) return;
      b.onclick = () => { if (li.dataset.src === cur()?.src && audio.src) return toggle(); const group = $$('[data-ep]', li.closest('[data-list]') || document); playList(group.map(epOf), group.indexOf(li)); };
    });
    $$('.athumb').forEach(t => (t.onclick = ev => { if (!ev.target.closest('.pbtn, a')) $('.pbtn', t)?.click(); }));
    $$('[data-playall]').forEach(b => (b.onclick = () => { const g = $$('[data-ep]', $(b.dataset.playall)); if (g.length) playList(g.map(epOf), 0); }));
    $$('.lite-yt').forEach(el => { el.style.backgroundImage = `url(${el.dataset.thumb || `https://i.ytimg.com/vi/${el.dataset.id}/hqdefault.jpg`})`;
      el.onclick = () => { if ($('iframe', el)) return; const f = document.createElement('iframe'); f.allow = 'accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture; fullscreen'; f.allowFullscreen = true; f.title = el.dataset.title || 'YouTube video';
        f.src = `https://www.youtube-nocookie.com/embed/${el.dataset.id}?autoplay=1&rel=0` + (el.dataset.list ? `&list=${el.dataset.list}` : ''); el.append(f); audio.pause(); }; });
    $$('[data-copy]').forEach(b => (b.onclick = () => navigator.clipboard?.writeText(b.dataset.copy).then(() => { b.textContent = 'Copied'; setTimeout(() => (b.textContent = 'Copy'), 1500); })));
    if ($('#search') && !window.__pf) { window.__pf = 1; const l = document.createElement('link'); l.rel = 'stylesheet'; l.href = '/pagefind/pagefind-ui.css'; document.head.append(l);
      const s = document.createElement('script'); s.src = '/pagefind/pagefind-ui.js'; s.onload = () => new PagefindUI({ element: '#search', showSubResults: true, showImages: false, autofocus: true }); document.head.append(s); }
    else if ($('#search') && window.PagefindUI) new PagefindUI({ element: '#search', showSubResults: true, showImages: false, autofocus: true });
    mark(); progress();
  }

  /* Soft navigation keeps audio playing across pages. */
  async function go(url, push = true) {
    try {
      const r = await fetch(url, { headers: { Accept: 'text/html' } }); if (!r.ok) throw 0;
      const doc = new DOMParser().parseFromString(await r.text(), 'text/html');
      $('main').replaceWith(doc.querySelector('main')); document.title = doc.title;
      $$('nav.main a').forEach(a => a.toggleAttribute('aria-current', a.getAttribute('href') === new URL(url, location).pathname));
      if (push) history.pushState({}, '', url); window.scrollTo(0, 0); initPage();
    } catch { location.href = url; }
  }
  document.addEventListener('click', ev => {
    const a = ev.target.closest('a'); if (!a || ev.defaultPrevented || ev.button || ev.metaKey || ev.ctrlKey || ev.shiftKey || a.target || a.hasAttribute('download')) return;
    const u = new URL(a.href, location); if (u.origin !== location.origin || /\.(xml|mp3|m4a|jpg|png|json)$/.test(u.pathname) || u.pathname.startsWith('/audio/')) return;
    if (u.pathname === location.pathname && u.hash) return; ev.preventDefault(); go(u.href);
  });
  window.addEventListener('popstate', () => go(location.href, false));

  /* Mobile menu: toggle button, Esc / link click / outside click close it. */
  const nav = $('nav.main'), menuBtn = $('.menu-btn', nav);
  if (menuBtn) {
    const setMenu = o => { nav.classList.toggle('open', o); menuBtn.setAttribute('aria-expanded', String(o)); };
    menuBtn.onclick = () => setMenu(!nav.classList.contains('open'));
    $$('.nav-items a', nav).forEach(a => a.addEventListener('click', () => setMenu(false)));
    document.addEventListener('keydown', ev => { if (ev.key === 'Escape' && nav.classList.contains('open')) { setMenu(false); menuBtn.focus(); } });
    document.addEventListener('click', ev => { if (nav.classList.contains('open') && !nav.contains(ev.target)) setMenu(false); });
  }

  showSpeed();
  if (queue.length && queue[idx]) load(idx, false);
  initPage();
})();
