// media.kevinamundson.me
// Static assets serve the site. /audio/* runs through this Worker first so byte-range requests
// (needed for seeking and by Apple Podcasts / Safari) get proper 206 Partial Content responses.
const AUDIO_HEADERS = {
  'Accept-Ranges': 'bytes',
  'Cache-Control': 'public, max-age=31536000, immutable',
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Expose-Headers': 'Content-Length, Content-Range, Accept-Ranges',
  'X-Content-Type-Options': 'nosniff',
};

const SIZES = {"/audio/rst-2026-hermeneutics-exegesis/2026-09-06-introduction-overview-canon-and-presuppositions.mp3": 22644190, "/audio/rst-2026-hermeneutics-exegesis/2026-09-06-bibliology-inspiration-canon-and-analogy.mp3": 14891779, "/audio/rst-2026-hermeneutics-exegesis/2026-09-20-observation-genesis-16-and-reading-with-the-church.mp3": 20506771, "/audio/rst-2026-hermeneutics-exegesis/2026-09-20-case-studies-john-3-peter-and-the-magnificat.mp3": 16202993, "/audio/rst-2025-world-history-ad/2025-09-14-globus-crusiger-conquest-of-continents.mp3": 13993866, "/audio/rst-2025-world-history-ad/2025-09-14-saints-settlements-monks-merchants.mp3": 11167641, "/audio/rst-2025-world-history-ad/2025-09-28-church-in-the-east.mp3": 7287690, "/audio/rst-2025-world-history-ad/2025-09-28-church-in-the-west-part-1.mp3": 6958781, "/audio/rst-2025-world-history-ad/2025-09-28-church-in-the-west-part-2.mp3": 10956561, "/audio/rst-2025-world-history-ad/2025-10-05-puritan-planting-patriotism.mp3": 15780439, "/audio/rst-2025-world-history-ad/2025-10-19-christ-to-asia.mp3": 12843843, "/audio/rst-2025-world-history-ad/2025-10-19-christ-to-africa.mp3": 8331663, "/audio/rst-2025-world-history-ad/2025-11-16-history-the-mission-of-god-and-the-eschaton.mp3": 10873704, "/audio/rst-2025-world-history-bc/2025-01-19-chronology.mp3": 13061862, "/audio/rst-2025-world-history-bc/2025-02-02-giants-nephilim-rephaim-and-the-anakim.mp3": 14099620, "/audio/rst-2025-world-history-bc/2025-02-16-genealogies.mp3": 13180042, "/audio/rst-2025-world-history-bc/2025-03-02-language-and-alphabet.mp3": 12653237, "/audio/rst-2025-world-history-bc/2025-03-02-ancient-architecture.mp3": 9457800, "/audio/rst-2025-world-history-bc/2025-03-16-navigation-in-the-ancient-world.mp3": 15059162, "/audio/rst-2025-world-history-bc/2025-03-16-the-history-of-israel.mp3": 14395737, "/audio/rst-2025-world-history-bc/2025-03-30-the-history-of-egypt.mp3": 12612792, "/audio/rst-2024-missiology/2024-10-06-introduction-missio-dei-the-mission-of-god.mp3": 16983013, "/audio/rst-2024-missiology/2024-10-20-the-magnitude-of-the-mission.mp3": 18870301, "/audio/rst-2024-missiology/2024-11-17-unto-the-unity-of-the-faith.mp3": 12703939, "/audio/rst-2024-missiology/2024-11-17-cross-culture-missions.mp3": 10197115, "/audio/rst-2024-apologetics-worldview/2024-01-28-revelational-epistemology-adam-moses-christ-paul.mp3": 14754850, "/audio/rst-2024-apologetics-worldview/2024-02-18-christ-s-lordship-and-the-reign-of-god.mp3": 14502239, "/audio/rst-2024-apologetics-worldview/2024-03-10-law-civil-government.mp3": 13618122, "/audio/rst-2023-biblical-theology/2023-09-10-introduction.mp3": 10931100, "/audio/rst-2023-biblical-theology/2023-09-24-eden-mountain.mp3": 16178788, "/audio/rst-2023-biblical-theology/2023-10-08-city-kingdom.mp3": 15185924, "/audio/rst-2023-systematic-theology/2023-01-29-introduction-man-s-highest-good-the-knowledge-of-god.mp3": 9901618, "/audio/rst-2023-systematic-theology/2023-02-19-special-revelation-the-holy-scriptures-confessions.mp3": 12012209, "/audio/rst-2023-systematic-theology/2023-02-26-creation-and-providence.mp3": 15042010, "/audio/rst-2023-systematic-theology/2023-03-26-the-mediator-of-the-covenant.mp3": 13811371, "/audio/rst-2022-hermeneutics-exegesis/2022-09-11-grammatical-interpretation.mp3": 11201762, "/audio/rst-2022-hermeneutics-exegesis/2022-09-25-historical-interpretation.mp3": 14160492, "/audio/rst-2022-hermeneutics-exegesis/2022-11-20-new-testament-overview.mp3": 13970153, "/audio/rst-2022-christian-history/2022-01-30-beginnings-ad-i-325-part-1-introduction-establishing-the-church.mp3": 12742515, "/audio/rst-2022-christian-history/2022-01-30-beginnings-ad-i-325-part-1-challenges-to-the-new-faith.mp3": 10882994, "/audio/rst-2022-christian-history/2022-02-27-acceptance-and-conquest-ad-325-600-confession-and-victory-of-faith.mp3": 14147834, "/audio/rst-2022-christian-history/2022-04-24-cities-and-empires-ad-1789-1914-church-and-state.mp3": 13525870, "/audio/pentateuch/2024-09-08-genesis-introduction-creation-of-the-heavens-and-the-earth.mp3": 8985085, "/audio/pentateuch/2024-09-15-genesis-the-creation-of-man.mp3": 9174100, "/audio/pentateuch/2024-10-27-genesis-death-spreads-to-all-men.mp3": 9604229, "/audio/pentateuch/2025-02-02-exodus-giving-of-the-law-at-sinai.mp3": 8710593, "/audio/pentateuch/2025-04-13-introduction-to-sacrifices.mp3": 8555878, "/audio/christianity-and-civil-engagement/2024-10-06-the-history-of-civil-liberty.mp3": 13512567, "/audio/christianity-and-civil-engagement/2024-10-06-q-a.mp3": 15209133, "/audio/manhood-breakfast/2022-07-16-masculinity-headship-dominion-and-sex.mp3": 16379446, "/audio/manhood-breakfast/2022-09-17-masculinity-war-worship-and-worthiness.mp3": 7565698, "/audio/manhood-breakfast/2024-06-15-being-valorous-men-part-1-self-defense.mp3": 10374250, "/audio/manhood-breakfast/2026-06-14-the-tipping-point-when-patience-becomes-sin.m4a": 14229832, "/audio/arise-and-build/2023-09-08-the-mission-of-god.mp3": 7567991, "/audio/christ-over-all/2021-11-20-living-for-christ-in-the-civil-arena.mp3": 10744782, "/audio/evangelism-and-biopics/2026-03-29-kings-under-christ-charlemagne-king-alfred-the-great.mp3": 11838784, "/audio/rooted-and-flourishing/2026-02-07-the-covenantal-role-of-women-in-the-church.mp3": 6264633, "/audio/colossians/2025-10-19-colossians-2-6-15.mp3": 18333201, "/audio/colossians/2025-11-16-colossians-3-5-11.mp3": 20225512, "/audio/how-to-watch-a-movie/2025-04-27-how-to-watch-a-movie.mp3": 17574623, "/audio/psummer-of-psalms/2022-07-24-psalm-24-the-king-of-glory.mp3": 13304580, "/audio/psummer-of-psalms/2023-08-13-psalm-17-the-lord-will-hear-and-attend-to-a-just-cause.mp3": 7013619, "/audio/psummer-of-psalms/2024-07-14-psalm-30-confidently-plead-to-the-lord-for-mercy.mp3": 9984043, "/audio/psummer-of-psalms/2025-06-15-psalm-38-god-will-not-forsake-those-who-confess-their-sin.mp3": 19439350, "/audio/psummer-of-psalms/2025-07-13-psalm-44-god-demonstrates-his-steadfast-love-through-your-affliction.mp3": 17762300, "/audio/family-and-finance/2024-02-18-family-roles.mp3": 12085479, "/audio/isaiah/2023-10-08-how-god-uses-the-nations.mp3": 10235022, "/audio/isaiah/2023-10-29-sennacherib-hezekiah-babylon.mp3": 12229119, "/audio/isaiah/2023-12-10-the-new-covenant.mp3": 12670763, "/audio/sanctification/2023-04-02-the-means-and-experience-of-sanctification.mp3": 9476911, "/audio/church-history-and-our-place-in-it/2022-10-09-church-in-the-east.mp3": 10380844, "/audio/church-history-and-our-place-in-it/2022-11-27-colonial-christianity-revival-revivalism.mp3": 10871578, "/audio/god-the-gospel-and-culture/2022-03-20-revelation-theological-system.mp3": 10882902, "/audio/god-the-gospel-and-culture/2022-04-03-anthropology-nature-of-man.mp3": 10075179, "/audio/god-the-gospel-and-culture/2022-05-15-civil-government.mp3": 12691649, "/audio/god-the-gospel-and-culture/2022-05-29-panel-discussion.mp3": 12053861, "/audio/the-humility-of-christ/2021-11-28-humility-comes-before-honor.mp3": 9968815, "/audio/kings-of-israel/2021-05-02-the-prophets-of-israel.mp3": 9726057, "/audio/why-we-are-not/2020-02-16-why-we-are-monergist.mp3": 11241272, "/audio/why-we-are-not/2020-02-23-why-we-are-creationist.mp3": 10564092};

function parseRange(h, size) {
  const m = /^bytes=(\d*)-(\d*)$/.exec((h || '').trim());
  if (!m || (m[1] === '' && m[2] === '')) return null;
  let start, end;
  if (m[1] === '') { const n = +m[2]; if (!n) return 'bad'; start = Math.max(0, size - n); end = size - 1; }
  else { start = +m[1]; end = m[2] === '' ? size - 1 : Math.min(+m[2], size - 1); }
  if (start >= size || start > end) return 'bad';
  return { start, end };
}

function slice(body, start, end) {
  let pos = 0;
  const len = end - start + 1;
  const { readable, writable } = new FixedLengthStream(len);
  body.pipeThrough(new TransformStream({
    transform(chunk, ctl) {
      const cs = pos, ce = pos + chunk.byteLength; pos = ce;
      if (cs > end) { ctl.terminate(); return; }
      if (ce <= start) return;
      ctl.enqueue(chunk.subarray(Math.max(0, start - cs), Math.min(chunk.byteLength, end - cs + 1)));
      if (ce > end) ctl.terminate();
    },
  })).pipeTo(writable).catch(() => {});
  return readable;
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (!url.pathname.startsWith('/audio/')) return env.ASSETS.fetch(request);
    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: { ...AUDIO_HEADERS, 'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS', 'Access-Control-Allow-Headers': 'Range' } });
    if (request.method !== 'GET' && request.method !== 'HEAD') return new Response('Method not allowed', { status: 405 });

    const asset = await env.ASSETS.fetch(new Request(url.toString(), { method: 'GET' }));
    if (!asset.ok) return asset;
    const size = +asset.headers.get('Content-Length') || SIZES[decodeURIComponent(url.pathname)] || 0;
    const headers = new Headers(AUDIO_HEADERS);
    headers.set('Content-Type', asset.headers.get('Content-Type') || 'audio/mpeg');
    const etag = asset.headers.get('ETag'); if (etag) headers.set('ETag', etag);

    const range = size ? parseRange(request.headers.get('Range'), size) : null;
    if (range === 'bad') { asset.body?.cancel(); headers.set('Content-Range', `bytes */${size}`); return new Response(null, { status: 416, headers }); }
    if (!range) {
      if (size) headers.set('Content-Length', String(size));
      if (request.method === 'HEAD') { asset.body?.cancel(); return new Response(null, { status: 200, headers }); }
      return new Response(asset.body, { status: 200, headers });
    }
    headers.set('Content-Range', `bytes ${range.start}-${range.end}/${size}`);
    headers.set('Content-Length', String(range.end - range.start + 1));
    if (request.method === 'HEAD') { asset.body?.cancel(); return new Response(null, { status: 206, headers }); }
    return new Response(slice(asset.body, range.start, range.end), { status: 206, headers });
  },
};
