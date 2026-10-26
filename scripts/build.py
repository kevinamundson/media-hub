"""Static site + podcast feed generator for media.kevinamundson.me.

Usage:  python3 scripts/build.py [--media ../files]
Writes dist/. Audio files are NOT in git; pass --media (folder containing audio/...) to copy them into dist
for a Workers Static Assets deploy. Run `npx pagefind --site dist` afterwards for search.
"""
import json, os, sys, shutil, html, datetime, email.utils
from zoneinfo import ZoneInfo
from xml.sax.saxutils import escape as xesc

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, 'dist')
BASE = 'https://media.kevinamundson.me'
AUTHOR = 'Kevin R. Amundson'
PODCAST = 'The Kingdom of Our Lord'
OWNER_EMAIL = 'thekingdomofourlord@proton.me'  # public in feeds; used by Apple/Spotify ownership checks
SITE = 'Kevin Amundson — Media Hub'
TZ = ZoneInfo('America/Chicago')
e_ = lambda s: html.escape(str(s), quote=True)

series = json.load(open(os.path.join(ROOT, 'catalog', 'series.json')))
episodes = json.load(open(os.path.join(ROOT, 'catalog', 'episodes.json')))
videos = json.load(open(os.path.join(ROOT, 'catalog', 'video.json')))
S = {s['id']: s for s in series}
for s in series:
    s['eps'] = [e for e in episodes if e['series'] == s['id']]
    s['url'] = f"/series/{s['id']}/"
    s['feed'] = f"/feeds/{s['id']}.xml"
    s['seconds'] = sum(e['duration'] for e in s['eps'])
for s in series:
    for n, e in enumerate(s['eps'], 1):
        e['seq'] = n
        e['url'] = f"{s['url']}{e['id']}/"
        e['label'] = f"Lecture {e['number']}" if e.get('number') and s['id'] not in ('manhood-breakfast',) else ''

def hms(sec):
    sec = int(sec); h, m, s = sec // 3600, sec % 3600 // 60, sec % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
def human(sec):
    sec = int(sec); h, m = sec // 3600, sec % 3600 // 60
    return f"{h} hr {m} min" if h else f"{m} min"
def nice_date(d): return datetime.date.fromisoformat(d).strftime('%b %-d, %Y')
def rfc822(d): return email.utils.format_datetime(datetime.datetime.fromisoformat(d + 'T10:00:00').replace(tzinfo=TZ))
def mb(b): return f"{b/1e6:.1f} MB"

def page(path, title, body, desc='', image='/covers/og.jpg', active='', og_type='website', index=True, extra_head=''):
    url = BASE + path
    nav = ''.join(f'<a href="{h}"{" aria-current" if active == k else ""}{c}>{t}</a>' for k, h, t, c in [
        ('home', '/', 'Home', ''), ('audio', '/series/', 'Audio', ''), ('video', '/video/', 'Video', ''), ('feeds', '/feeds/', 'Podcast feeds', ' class="opt"'), ('search', '/search/', 'Search', '')])
    full_title = title if title == SITE else f"{title} · {SITE}"
    doc = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><script>document.documentElement.classList.add('js')</script><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{e_(full_title)}</title><meta name="description" content="{e_(desc)}"><link rel="canonical" href="{url}">
<meta property="og:type" content="{og_type}"><meta property="og:site_name" content="{e_(SITE)}"><meta property="og:title" content="{e_(title)}"><meta property="og:description" content="{e_(desc)}"><meta property="og:url" content="{url}"><meta property="og:image" content="{BASE}{image}">
<meta name="twitter:card" content="summary_large_image"><meta name="theme-color" content="#171717">{'' if index else '<meta name="robots" content="noindex">'}
<link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="preload" href="/fonts/Vollkorn.ttf" as="font" type="font/ttf" crossorigin>
<link rel="stylesheet" href="/style.css"><link rel="alternate" type="application/rss+xml" title="{e_(PODCAST)}" href="{BASE}/feeds/all.xml">{extra_head}
</head><body>
<header class="site"><div class="wrap"><a class="brand" href="/">Kevin Amundson <span>Media</span></a><nav class="main" aria-label="Main"><button class="menu-btn" type="button" aria-expanded="false" aria-controls="nav-items" aria-label="Menu"><svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg></button><div class="nav-items" id="nav-items">{nav}<span class="sep" aria-hidden="true">|</span><a href="https://thekingdomofourlord.substack.com/">Substack</a></div></nav></div></header>
<main>{body}</main>
<footer class="site"><div class="wrap">© {datetime.date.today().year} Kevin R. Amundson · <a href="https://kevinamundson.me">kevinamundson.me</a> · <a href="https://www.youtube.com/c/KevinAmundson">YouTube</a> · <a href="/feeds/">Podcast feeds</a><br>
<span class="dim">Lectures recorded at Redemption City Church and the Redemption School of Theology, shared with permission.</span></div></footer>
<div id="queue" aria-label="Queue"></div>
<div id="player" role="region" aria-label="Audio player"><div class="wrap">
 <div class="now"><img id="p-cover" alt="" width="52" height="52" src="/covers/kingdom-of-our-lord-1500.jpg"><div><a id="p-title" class="t" href="#">—</a><br><a id="p-series" class="s" href="#"></a></div></div>
 <div class="ctl"><button id="p-prev" aria-label="Previous"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M6 5h2v14H6zM20 5v14L9 12z"/></svg></button>
  <button id="p-back" class="skip" aria-label="Back 15 seconds"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5"/><text x="8" y="16" font-size="8" fill="currentColor" stroke="none" font-family="Inter">15</text></svg></button>
  <button id="p-pp" class="pp" aria-label="Play"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M7 4.5v15l13-7.5z"/></svg></button>
  <button id="p-fwd" class="skip" aria-label="Forward 30 seconds"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12a9 9 0 1 1-3-6.7L21 8"/><path d="M21 3v5h-5"/><text x="7" y="16" font-size="8" fill="currentColor" stroke="none" font-family="Inter">30</text></svg></button>
  <button id="p-next" aria-label="Next"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M16 5h2v14h-2zM4 5v14l11-7z"/></svg></button></div>
 <div class="seek"><span id="p-cur">0:00</span><input id="p-seek" type="range" min="0" max="1000" value="0" aria-label="Seek"><span id="p-dur">0:00</span></div>
 <div class="xtra"><button id="p-speed" aria-label="Playback speed">1×</button><button id="p-queue" aria-label="Queue">Queue</button></div>
</div></div>
<script src="/app.js" defer></script></body></html>'''
    out = os.path.join(DIST, path.strip('/'), 'index.html') if path.endswith('/') else os.path.join(DIST, path.lstrip('/'))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, 'w').write(doc)

PLAY = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M7 4.5v15l13-7.5z"/></svg>'
def ep_li(e, show_series=False):
    s = S[e['series']]
    meta = ' · '.join(x for x in [e['label'], nice_date(e['date']), e['speaker'] if e['speaker'] != 'Kevin Amundson' else '', s['title'] if show_series else ''] if x)
    return (f'<li data-ep data-src="{e_(e["audio"])}" data-title="{e_(e["title"])}" data-series="{e_(s["title"])}" data-series-url="{s["url"]}" '
            f'data-url="{e["url"]}" data-cover="{s["cover"]}" data-duration="{int(e["duration"])}">'
            f'<button class="pbtn" aria-label="Play {e_(e["title"])}">{PLAY}</button>'
            f'<div class="ep-t"><a href="{e["url"]}">{e_(e["title"])}</a><div class="ep-m">{e_(meta)}</div><div class="prog"><i></i></div></div>'
            f'<span class="dur">{hms(e["duration"])}</span></li>')

def series_card(s):
    return (f'<a class="card" href="{s["url"]}"><img src="{s["cover"]}" alt="" loading="lazy" width="700" height="700"><div class="b">'
            f'<div class="kicker">{e_(s["subtitle"].split(" · ")[0])}</div><h3>{e_(s["title"])}</h3>'
            f'<div class="m">{len(s["eps"])} recording{"s" if len(s["eps"]) != 1 else ""} · {human(s["seconds"])}</div></div></a>')

def video_card(v):
    first = v['videos'][0]['id'] if v['videos'] else ''
    return (f'<a class="card video" href="/video/{v["id"]}/"><img src="https://i.ytimg.com/vi/{first}/hqdefault.jpg" alt="" loading="lazy" width="480" height="270"><div class="b">'
            f'<div class="kicker">{e_(v["collection"])}</div><h3>{e_(v["title"])}</h3><div class="m">{len(v["videos"])} video{"s" if len(v["videos"]) != 1 else ""} on YouTube{f" · {len(v['links'])} audio" if v.get("links") else ""}</div></div></a>')

def build_pages():
    total = sum(e['duration'] for e in episodes)
    latest = sorted(episodes, key=lambda e: e['date'], reverse=True)[:8]
    body = f'''<section class="hero wrap home"><div><div class="bar"></div><div class="kicker">Media Producer · Writer · Historian · Elder</div>
<h1>Lectures, recordings &amp; video</h1><p>Every lecture and recording by Kevin R. Amundson in one place: theology and history courses from the Redemption School of Theology, talks, and the ExploreHistory.Live video series. Listen here, or subscribe in any podcast app.</p>
<div class="actions"><a class="btn" href="/series/">Browse audio</a><a class="btn ghost" href="/video/">Watch video</a><a class="btn ghost" href="/feeds/">Subscribe</a></div>
<p class="dim" style="font-size:.9rem;margin-top:16px">{len(episodes)} audio recordings · {len(series)} series · {int(total//3600)} hours · {sum(len(v["videos"]) for v in videos)} videos</p></div>
<a class="podcast-art" href="/feeds/" title="Subscribe to {e_(PODCAST)}"><img src="/covers/kingdom-of-our-lord-1500.jpg" width="260" height="260" alt="{e_(PODCAST)} podcast"><span>Subscribe to the podcast</span></a></section>
<section class="wrap"><h2>Latest recordings</h2><ol class="eps" data-list id="latest">{"".join(ep_li(e, True) for e in latest)}</ol>
<h2>Audio series</h2><div class="grid">{"".join(series_card(s) for s in series)}</div>
<h2>Video series</h2><div class="grid">{"".join(video_card(v) for v in videos)}</div></section>'''
    page('/', SITE, body, 'Lectures, recordings, and video by Kevin R. Amundson: theology and history courses, talks, and ExploreHistory.Live.', active='home')

    rst = [s for s in series if s['id'].startswith('rst-')]; other = [s for s in series if not s['id'].startswith('rst-')]
    body = f'''<section class="hero wrap"><div class="bar"></div><h1>Audio</h1><p>{len(episodes)} recordings across {len(series)} series.</p>
<h2>Redemption School of Theology</h2><div class="grid">{"".join(series_card(s) for s in rst)}</div>
<h2>Sunday school, talks &amp; conferences</h2><div class="grid">{"".join(series_card(s) for s in other)}</div></section>'''
    page('/series/', 'Audio series', body, 'All audio lecture series by Kevin R. Amundson.', active='audio')

    for s in series:
        body = f'''<div class="wrap" data-pagefind-body><section class="series-head"><img src="{s["cover"]}" alt="{e_(s["title"])} cover" width="700" height="700">
<div><div class="kicker">{e_(s["subtitle"])}</div><h1>{e_(s["title"])}</h1><p class="muted">{e_(s["description"])}</p>
<p class="dim">{len(s["eps"])} recording{"s" if len(s["eps"]) != 1 else ""} · {human(s["seconds"])} · Kevin R. Amundson</p>
<div class="actions"><button class="btn" data-playall="#eps">{PLAY[:4]} style="width:16px;height:16px"{PLAY[4:]} Play all</button><a class="btn ghost" href="{s["feed"]}">RSS feed</a><button class="btn ghost copy-feed" data-copy="{BASE}{s["feed"]}">Copy</button></div></div></section>
<ol class="eps" data-list id="eps">{"".join(ep_li(e) for e in s["eps"])}</ol>
<p class="dim" style="font-size:.85rem">Originally published at <a href="{e_(s["source"])}">{e_(s["source"].split("//")[1])}</a>.</p></div>'''
        page(s['url'], s['title'], body, s['description'], image=s['cover'], active='audio')
        for e in s['eps']:
            body = f'''<div class="wrap ep-page" data-pagefind-body><section class="series-head"><img src="{s["cover"]}" alt="" width="700" height="700">
<div><div class="kicker"><a href="{s["url"]}" style="color:inherit;text-decoration:none">{e_(s["title"])}</a>{(" · " + e_(e["label"])) if e["label"] else ""}</div><h1>{e_(e["title"])}</h1>
<dl class="meta"><dt>Speaker</dt><dd>{e_(e["speaker"])}</dd><dt>Recorded</dt><dd>{nice_date(e["date"])}</dd><dt>Length</dt><dd>{hms(e["duration"])}</dd><dt>File</dt><dd>{"MP3" if e["mime"] == "audio/mpeg" else "M4A"} · {mb(e["bytes"])}</dd></dl>
<div class="actions"><button class="btn" data-playall="#one">{PLAY[:4]} style="width:16px;height:16px"{PLAY[4:]} Play</button><a class="btn ghost" href="{e["audio"]}" download>Download</a><a class="btn ghost" href="{s["url"]}">All in series</a></div></div></section>
<ol class="eps" data-list id="one">{ep_li(e)}</ol>
<p class="muted">{e_(s["description"])}</p></div>'''
            page(e['url'], e['title'], body, f"{e['title']} — {s['title']}. {e['speaker']}, {nice_date(e['date'])}.", image=s['cover'], og_type='music.song', active='audio',
                 extra_head=f'<meta property="og:audio" content="{BASE}{e["audio"]}"><meta property="og:audio:type" content="{e["mime"]}">')

    body = f'''<section class="hero wrap"><div class="bar"></div><h1>Video</h1><p>ExploreHistory.Live series, talks and guest appearances, hosted on YouTube. Tap any video to play it here.</p>
<div class="actions"><a class="btn ghost" href="https://www.youtube.com/playlist?list=PLP7nXp5O0E-Q">YouTube channel</a></div><div class="grid">{"".join(video_card(v) for v in videos)}</div></section>'''
    page('/video/', 'Video', body, 'ExploreHistory.Live video series by Kevin R. Amundson.', active='video')
    for v in videos:
        # v["playlist"] may be null for standalone videos (no YouTube playlist); v["links"] holds externally hosted
        # audio (guest appearances) that is linked, not rehosted, and never added to the podcast feeds.
        lst = f'&list={v["playlist"]}' if v.get('playlist') else ''
        cards = ''.join(f'<div><div class="lite-yt{" vertical" if x.get("vertical") else ""}" data-id="{x["id"]}" data-title="{e_(x["title"])}"{f' data-thumb="{x["thumb"]}"' if x.get("thumb") else ""}><button aria-label="Play {e_(x["title"])}"></button><span class="cap">{e_(x["title"])}</span></div>'
                        f'<div class="d">{nice_date(x["date"])}{(" · " + e_(x["channel"])) if x.get("channel") else ""} · <a href="{f'https://www.youtube.com/shorts/{x["id"]}' if x.get("vertical") else f'https://www.youtube.com/watch?v={x["id"]}{lst}'}">Watch on YouTube</a></div></div>' for x in v['videos'])
        if v.get('playlist'): src = f'<a href="https://www.youtube.com/playlist?list={v["playlist"]}">Open playlist on YouTube</a>'
        elif v.get('source'): src = f'Originally shared at <a href="{e_(v["source"])}">{e_(v["source"].split("//")[1])}</a>'
        else: src = 'Hosted on YouTube'
        links = ''
        if v.get('links'):
            url = f'/video/{v["id"]}/'
            # Audio appearances render as 16:9 thumbnail cards using the original show's artwork (square art fit inside
            # a blurred backdrop, pre-rendered into a["thumb"]); the play button streams the original MP3 in the site player.
            acards = ''.join(f'<div class="acard"><div class="athumb" data-ep data-src="{e_(a["audio"])}" data-title="{e_(a["title"])}" data-series="{e_(a["show"])}" data-series-url="{url}" data-url="{url}" data-cover="{a["cover"]}" data-duration="{int(a["duration"])}">'
                          f'<img src="{a.get("thumb") or a["cover"]}" alt="{e_(a["show"])} show artwork" width="1280" height="720" loading="lazy">'
                          f'<span class="abadge"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><path d="M3 14v-2a9 9 0 0 1 18 0v2"/><path d="M21 15a2 2 0 0 1-2 2h-1v-6h1a2 2 0 0 1 2 2zM3 15a2 2 0 0 0 2 2h1v-6H5a2 2 0 0 0-2 2z"/></svg>Audio</span>'
                          f'<button class="pbtn" aria-label="Play {e_(a["title"])}">{PLAY}</button><span class="cap">{e_(a["title"])}</span><span class="dur">{hms(a["duration"])}</span><div class="prog"><i></i></div></div>'
                          f'<div class="d">{nice_date(a["date"])} · {e_(a["show"])} · <a href="{e_(a["page"])}">Original episode page</a></div>'
                          f'<div class="d">{e_(a["speaker"])}</div></div>' for a in v['links'])
            links = f'<h2>Audio</h2><p class="dim" style="font-size:.85rem">Streamed from the original show. Not part of the podcast feeds.</p><div class="vgrid" data-list id="links">{acards}</div>'
        body = f'''<section class="hero wrap" data-pagefind-body><div class="bar"></div><div class="kicker">{e_(v["collection"])}</div><h1>{e_(v["title"])}</h1>
<p>{len(v["videos"])} video{"s" if len(v["videos"]) != 1 else ""}{f" · {len(v['links'])} audio" if v.get("links") else ""} · {src}</p><div class="vgrid">{cards}</div>{links}</section>'''
        page(f'/video/{v["id"]}/', v['title'], body, f'{v["title"]} — {v["collection"]} video{" series" if v.get("playlist") else "s"} by Kevin R. Amundson.' if v['collection'] != 'ExploreHistory.Live' else f'{v["title"]} — ExploreHistory.Live video series by Kevin R. Amundson.', active='video')

    rows = ''.join(f'<tr><td><a href="{s["url"]}">{e_(s["title"])}</a><div class="dim" style="font-size:.82rem">{len(s["eps"])} episodes</div></td><td><code>{BASE}{s["feed"]}</code></td><td><button class="copy" data-copy="{BASE}{s["feed"]}">Copy</button></td></tr>' for s in series)
    body = f'''<section class="hero wrap feeds"><div class="bar"></div><h1>Podcast feeds</h1><p>Paste a feed URL into any podcast app (Apple Podcasts → Library → Follow a show by URL; Pocket Casts, Overcast, AntennaPod, etc.). The <em>{e_(PODCAST)}</em> feed includes every recording; the series feeds below are parts of the same podcast.</p>
<table><thead><tr><th>Feed</th><th>URL</th><th></th></tr></thead><tbody>
<tr><td><strong>{e_(PODCAST)}</strong> <span class="dim">(all recordings)</span><div class="dim" style="font-size:.82rem">{len(episodes)} episodes</div></td><td><code>{BASE}/feeds/all.xml</code></td><td><button class="copy" data-copy="{BASE}/feeds/all.xml">Copy</button></td></tr>{rows}</tbody></table></section>'''
    page('/feeds/', 'Podcast feeds', body, 'RSS podcast feeds for every lecture series by Kevin R. Amundson.', active='feeds')
    page('/search/', 'Search', '<section class="hero wrap"><div class="bar"></div><h1>Search</h1><div id="search"></div></section>', 'Search all lectures and videos.', active='search')
    page('/404.html', 'Not found', '<section class="hero wrap"><div class="bar"></div><h1>Not found</h1><p>That page does not exist. <a href="/">Go home</a>.</p></section>', index=False)

def feed(path, title, desc, eps, cover, link, category, kind='episodic'):
    cats = {'Christianity': '<itunes:category text="Religion &amp; Spirituality"><itunes:category text="Christianity"/></itunes:category>',
            'History': '<itunes:category text="History"/><itunes:category text="Religion &amp; Spirituality"><itunes:category text="Christianity"/></itunes:category>'}[category]
    items = []
    for e in eps:
        s = S[e['series']]
        t = e['title'] if path != '/feeds/all.xml' else f"{s['title']}: {e['title']}"
        d = f"{e['title']} — {s['title']}{(' (' + e['label'] + ')') if e['label'] else ''}. {e['speaker']}. Recorded {nice_date(e['date'])}. {s['description']}"
        items.append(f'''<item><title>{xesc(t)}</title><description>{xesc(d.replace('&', '&amp;'))}</description><itunes:summary>{xesc(d)}</itunes:summary><link>{BASE}{e["url"]}</link>
<guid isPermaLink="false">{BASE}{e["audio"]}</guid><pubDate>{rfc822(e["date"])}</pubDate>
<enclosure url="{xesc(BASE + e["audio"])}" length="{e["bytes"]}" type="{"audio/mpeg" if e["mime"] == "audio/mpeg" else "audio/x-m4a"}"/>
<itunes:duration>{int(e["duration"])}</itunes:duration><itunes:explicit>false</itunes:explicit><itunes:episodeType>full</itunes:episodeType>{f"<itunes:episode>{e['seq']}</itunes:episode>" if path != '/feeds/all.xml' else ''}
{'' if path == '/feeds/all.xml' else f'<itunes:image href="{BASE}{s["cover"]}"/>'}<itunes:author>{xesc(AUTHOR)}</itunes:author></item>''')
    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:podcast="https://podcastindex.org/namespace/1.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">
<channel><title>{xesc(title)}</title><link>{BASE}{link}</link><atom:link href="{BASE}{path}" rel="self" type="application/rss+xml"/>
<description>{xesc(desc)}</description><itunes:summary>{xesc(desc)}</itunes:summary><language>en-us</language><copyright>© Kevin R. Amundson</copyright>
<itunes:author>{xesc(AUTHOR)}</itunes:author><itunes:owner><itunes:name>{xesc(AUTHOR)}</itunes:name><itunes:email>{OWNER_EMAIL}</itunes:email></itunes:owner><managingEditor>{OWNER_EMAIL} ({xesc(AUTHOR)})</managingEditor>
<itunes:image href="{BASE}{cover}"/><image><url>{BASE}{cover}</url><title>{xesc(title)}</title><link>{BASE}{link}</link></image>
{cats}<itunes:explicit>false</itunes:explicit><itunes:type>{kind}</itunes:type><podcast:locked>no</podcast:locked>
<lastBuildDate>{email.utils.format_datetime(datetime.datetime.now(TZ))}</lastBuildDate>
{"".join(items if kind == 'serial' else reversed(items))}
</channel></rss>'''
    out = os.path.join(DIST, path.lstrip('/')); os.makedirs(os.path.dirname(out), exist_ok=True); open(out, 'w').write(xml)

def build_feeds():
    for s in series:
        kind = 'serial' if s['id'].startswith('rst-') or s['id'] == 'pentateuch' else 'episodic'
        feed(s['feed'], f"{PODCAST}: {s['title']}", s['description'] + ' Lectures by Kevin R. Amundson.', s['eps'], s['cover'], s['url'], s['category'], kind)
    feed('/feeds/all.xml', PODCAST, 'Every lecture and recording by Kevin R. Amundson: Redemption School of Theology courses in theology and history, Sunday school, and talks.',
         sorted(episodes, key=lambda e: e['date']), '/covers/kingdom-of-our-lord-1500.jpg', '/', 'Christianity')
    # Identical copy at /feeds/all.rss (only atom:link self differs) for directories that prefer .rss
    src = open(os.path.join(DIST, 'feeds/all.xml')).read()
    selfx = f'<atom:link href="{BASE}/feeds/all.xml" rel="self"'
    assert src.count(selfx) == 1
    open(os.path.join(DIST, 'feeds/all.rss'), 'w').write(src.replace(selfx, f'<atom:link href="{BASE}/feeds/all.rss" rel="self"'))

def build_misc():
    urls = ['/', '/series/', '/video/', '/feeds/', '/search/'] + [s['url'] for s in series] + [e['url'] for e in episodes] + [f'/video/{v["id"]}/' for v in videos]
    open(os.path.join(DIST, 'sitemap.xml'), 'w').write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join(f'<url><loc>{BASE}{u}</loc></url>' for u in urls) + '</urlset>\n')
    open(os.path.join(DIST, 'robots.txt'), 'w').write(f'User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n')
    open(os.path.join(DIST, 'favicon.svg'), 'w').write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#171717"/><rect x="12" y="14" width="18" height="5" fill="#84010e"/><text x="12" y="50" font-family="Georgia,serif" font-weight="700" font-size="34" fill="#fafafa">KA</text></svg>')
    open(os.path.join(DIST, '_headers'), 'w').write('''/audio/*
  Cache-Control: public, max-age=31536000, immutable
  Accept-Ranges: bytes
  Access-Control-Allow-Origin: *
/covers/*
  Cache-Control: public, max-age=604800
/fonts/*
  Cache-Control: public, max-age=31536000, immutable
''' + ''.join(f'/feeds/{n}\n  Content-Type: application/rss+xml; charset=utf-8\n  Cache-Control: public, max-age=900\n  Access-Control-Allow-Origin: *\n' for n in ['all.xml', 'all.rss'] + [s['id'] + '.xml' for s in series]) + '''/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
''')
    json.dump(dict(series=[{k: v for k, v in s.items() if k != 'eps'} for s in series], episodes=episodes, video=videos), open(os.path.join(DIST, 'catalog.json'), 'w'), ensure_ascii=False)

if __name__ == '__main__':
    media = sys.argv[sys.argv.index('--media') + 1] if '--media' in sys.argv else None
    shutil.rmtree(DIST, ignore_errors=True); shutil.copytree(os.path.join(ROOT, 'static'), DIST)
    build_pages(); build_feeds(); build_misc()
    if media:
        for e in episodes:
            src = os.path.join(media, e['audio'].lstrip('/')); dst = os.path.join(DIST, e['audio'].lstrip('/'))
            os.makedirs(os.path.dirname(dst), exist_ok=True); os.link(src, dst) if os.stat(src).st_dev == os.stat(os.path.dirname(dst)).st_dev else shutil.copy2(src, dst)
    print(f'built {len(series)} series, {len(episodes)} episodes, {len(videos)} video series -> {DIST}')
