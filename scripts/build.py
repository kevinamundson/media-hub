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
# Channel-level show description for the main feed (all.xml / all.rss); blank line = paragraph break.
SHOW_DESCRIPTION = ('Equipping Christians with resources to develop a biblical worldview and take every thought captive to obey Jesus Christ.\n\n'
                    '\u201cThe kingdom of the world has become the kingdom of our Lord and of his Christ, and he shall reign forever and ever.\u201d\n'
                    '\u2014 Revelation 11:15')
# Official brand marks (Simple Icons v16.36.0, CC0 paths; trademarks of their owners), in each brand's color.
BRAND_ICONS = {
    'applepodcasts': '<svg class="brand-ic" viewBox="0 0 24 24" width="24" height="24" aria-hidden="true" focusable="false"><rect x="1.5" y="1.5" width="21" height="21" rx="4" fill="#fff"/><path fill="#9933CC" d="M5.34 0A5.328 5.328 0 000 5.34v13.32A5.328 5.328 0 005.34 24h13.32A5.328 5.328 0 0024 18.66V5.34A5.328 5.328 0 0018.66 0zm6.525 2.568c2.336 0 4.448.902 6.056 2.587 1.224 1.272 1.912 2.619 2.264 4.392.12.59.12 2.2.007 2.864a8.506 8.506 0 01-3.24 5.296c-.608.46-2.096 1.261-2.336 1.261-.088 0-.096-.091-.056-.46.072-.592.144-.715.48-.856.536-.224 1.448-.874 2.008-1.435a7.644 7.644 0 002.008-3.536c.208-.824.184-2.656-.048-3.504-.728-2.696-2.928-4.792-5.624-5.352-.784-.16-2.208-.16-3 0-2.728.56-4.984 2.76-5.672 5.528-.184.752-.184 2.584 0 3.336.456 1.832 1.64 3.512 3.192 4.512.304.2.672.408.824.472.336.144.408.264.472.856.04.36.03.464-.056.464-.056 0-.464-.176-.896-.384l-.04-.03c-2.472-1.216-4.056-3.274-4.632-6.012-.144-.706-.168-2.392-.03-3.04.36-1.74 1.048-3.1 2.192-4.304 1.648-1.737 3.768-2.656 6.128-2.656zm.134 2.81c.409.004.803.04 1.106.106 2.784.62 4.76 3.408 4.376 6.174-.152 1.114-.536 2.03-1.216 2.88-.336.43-1.152 1.15-1.296 1.15-.023 0-.048-.272-.048-.603v-.605l.416-.496c1.568-1.878 1.456-4.502-.256-6.224-.664-.67-1.432-1.064-2.424-1.246-.64-.118-.776-.118-1.448-.008-1.02.167-1.81.562-2.512 1.256-1.72 1.704-1.832 4.342-.264 6.222l.413.496v.608c0 .336-.027.608-.06.608-.03 0-.264-.16-.512-.36l-.034-.011c-.832-.664-1.568-1.842-1.872-2.997-.184-.698-.184-2.024.008-2.72.504-1.878 1.888-3.335 3.808-4.019.41-.145 1.133-.22 1.814-.211zm-.13 2.99c.31 0 .62.06.844.178.488.253.888.745 1.04 1.259.464 1.578-1.208 2.96-2.72 2.254h-.015c-.712-.331-1.096-.956-1.104-1.77 0-.733.408-1.371 1.112-1.745.224-.117.534-.176.844-.176zm-.011 4.728c.988-.004 1.706.349 1.97.97.198.464.124 1.932-.218 4.302-.232 1.656-.36 2.074-.68 2.356-.44.39-1.064.498-1.656.288h-.003c-.716-.257-.87-.605-1.164-2.644-.341-2.37-.416-3.838-.218-4.302.262-.616.974-.966 1.97-.97z"/></svg>',
    'spotify': '<svg class="brand-ic" viewBox="0 0 24 24" width="24" height="24" aria-hidden="true" focusable="false"><circle cx="12" cy="12" r="10" fill="#fff"/><path fill="#1DB954" d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z"/></svg>',
    'youtube': '<svg class="brand-ic" viewBox="0 0 24 24" width="24" height="24" aria-hidden="true" focusable="false"><path d="M9.5 8.3v7.4l6.4-3.7z" fill="#fff"/><path fill="#FF0000" d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>',
    # Amazon Music: Simple Icons v14.15.0 (removed from v15+); brand guidelines https://artists.amazonmusic.com/brand-guidelines
    'amazonmusic': '<svg class="brand-ic" viewBox="0 0 24 24" width="24" height="24" aria-hidden="true" focusable="false"><path fill="#46C3D0" d="M14.8454 9.4083c-1.3907 1.0194-3.405 1.563-5.1424 1.563a9.333 9.333 0 0 1-6.2768-2.3835c-.1313-.117-.0143-.277.1415-.1846a12.693 12.693 0 0 0 6.285 1.6574c1.5384 0 3.2348-.318 4.7917-.9764.2359-.0985.4328.1538.203.324h-.002zm.5784-.6564c-.1784-.2257-1.1753-.1087-1.6225-.0554-.1374.0164-.158-.1026-.0349-.1867.796-.5558 2.0984-.3958 2.2502-.2092.1539.1867-.041 1.4872-.7856 2.1087-.1149.0964-.2236.0451-.1723-.082.1682-.4165.5436-1.3498.3651-1.5754zm-1.5917-4.1702v-.5394c0-.082.0615-.1375.1374-.1375h2.4348c.078 0 .1395.0554.1395.1354v.4636c0 .078-.0656.1805-.1846.3405L15.0997 6.635c.4677-.0102.9641.0595 1.3887.2974.0964.0534.123.1334.1292.2113v.5744c0 .082-.0882.1723-.1784.123a2.8163 2.8163 0 0 0-2.5723.0062c-.0861.0451-.1743-.0451-.1743-.1251v-.5477c0-.0882.002-.238.0902-.3713l1.4626-2.0881h-1.2718c-.078 0-.1415-.0534-.1436-.1354l.002.002zm4.808-.7466c1.0995 0 1.6944.9395 1.6944 2.1333 0 1.1528-.6564 2.0676-1.6943 2.0676-1.079 0-1.6656-.9395-1.6656-2.1087 0-1.1774.5948-2.0922 1.6656-2.0922zm.0062.7713c-.5456 0-.5805.7384-.5805 1.202 0 .4615-.0061 1.4481.5744 1.4481.5743 0 .601-.7958.601-1.282 0-.318-.0144-.6994-.1108-1.001-.082-.2625-.2482-.3671-.4841-.3671zm-6.008 3.3414c-.0493.041-.1395.0451-.1744.0164-.2543-.1949-.4246-.4923-.4246-.4923-.4061.4123-.6954.5374-1.2225.5374-.6215 0-1.1077-.3835-1.1077-1.1486a1.2512 1.2512 0 0 1 .7897-1.2041c.402-.1764.9641-.2072 1.3928-.2564 0 0 .0349-.4615-.0902-.6297a.521.521 0 0 0-.4164-.1908c-.2728 0-.5395.1477-.5928.4328-.0144.082-.0739.1518-.1395.1436L9.945 5.08a.1292.1292 0 0 1-.1108-.1537c.1641-.8657.9498-1.1282 1.6554-1.1282.361 0 .8307.0964 1.1158.3671.359.3344.3262.7795.3262 1.2677v1.1487c0 .3446.1436.4964.279.681.0471.0677.0574.1477-.002.197-.1519.125-.5703.4881-.5703.4881zm-.7467-1.7969v-.16c-.5353 0-1.1015.115-1.1015.7426 0 .318.1662.5333.4513.5333.2051 0 .3938-.1272.5128-.3344.1436-.2564.1374-.4943.1374-.7815zM2.9278 7.948c-.0472.041-.1375.045-.1723.0163-.2544-.1949-.4246-.4923-.4246-.4923-.4082.4123-.6954.5374-1.2226.5374-.6235 0-1.1076-.3835-1.1076-1.1486a1.2512 1.2512 0 0 1 .7897-1.2041c.402-.1764.964-.2072 1.3928-.2564 0 0 .0348-.4615-.0903-.6297a.521.521 0 0 0-.4164-.1908c-.2748 0-.5395.1477-.5928.4328-.0143.082-.0759.1518-.1395.1436L.2345 5.08a.1292.1292 0 0 1-.1087-.1537c.162-.8657.9497-1.1282 1.6553-1.1282.361 0 .8308.0964 1.1159.3671.359.3344.324.7795.324 1.2677v1.1487c0 .3446.1437.4964.279.681.0472.0677.0575.1477-.002.197-.1518.125-.5702.4881-.5702.4881zm-.7446-1.797v-.16c-.5354 0-1.1015.115-1.1015.7426 0 .318.164.5333.4512.5333.2052 0 .3939-.1272.5128-.3344.1436-.2564.1375-.4943.1375-.7815zm2.9127-.3343v2.002a.1379.1379 0 0 1-.1395.1374H4.218a.1374.1374 0 0 1-.1395-.1374v-3.766a.1379.1379 0 0 1 .1395-.1375h.6913a.1374.1374 0 0 1 .1374.1374v.482h.0143c.1805-.4758.519-.6994.9744-.6994.4636 0 .7528.2236.962.6995a1.0523 1.0523 0 0 1 1.0215-.6995c.3118 0 .6502.1272.8574.4143.236.318.1867.7795.1867 1.1857v2.3855c0 .076-.0636.1354-.1436.1354H8.181a.1374.1374 0 0 1-.1334-.1354v-2.004c0-.16.0144-.558-.0205-.7077-.0554-.2564-.2215-.3282-.4369-.3282a.4923.4923 0 0 0-.441.3118c-.076.1908-.0698.5087-.0698.724v2.0041c0 .076-.0635.1354-.1435.1354h-.7385a.1374.1374 0 0 1-.1333-.1354v-2.004c0-.4226.0677-1.042-.4574-1.042-.5334 0-.5128.603-.5128 1.042h.002zm16.8077 2.002a.1374.1374 0 0 1-.1374.1374h-.7405a.1374.1374 0 0 1-.1374-.1374v-3.766a.1374.1374 0 0 1 .1374-.1375h.683c.0821 0 .1396.0636.1396.1067v.5764h.0143c.2051-.517.4964-.7631 1.0092-.7631.3323 0 .6564.119.8636.4451.1928.3036.1928.8123.1928 1.1774V7.837a.1395.1395 0 0 1-.1415.119h-.7426a.1395.1395 0 0 1-.1313-.119V5.552c0-.763-.2933-.7856-.4635-.7856-.197 0-.357.1538-.4246.2953a1.7025 1.7025 0 0 0-.1231.722l.002 2.0349zM.1914 20.0582c-.1271 0-.1907-.0615-.1907-.1907v-4.4491c0-.1272.0636-.1908.1907-.1908H.616c.0616 0 .1129.0144.1477.039.0349.0246.0595.0738.0718.1436l.0575.3035c.6133-.4184 1.2102-.6276 1.7907-.6276.5948 0 .9969.2256 1.2081.6769.6318-.4513 1.2636-.677 1.8954-.677.441 0 .7794.1231 1.0153.3693.236.2502.3549.603.3549 1.0584v3.3538c0 .1271-.0656.1907-.1928.1907h-.5641c-.1272 0-.1928-.0615-.1928-.1907v-3.085c0-.318-.0616-.5539-.1805-.7057-.1231-.1538-.3139-.2297-.5744-.2297-.4677 0-.9353.1436-1.4092.4307a.997.997 0 0 1 .0103.1416v3.448c0 .1272-.0636.1908-.1908.1908H3.297c-.1272 0-.1908-.0615-.1908-.1907v-3.085c0-.318-.0615-.5539-.1825-.7057-.1231-.1538-.3139-.2297-.5744-.2297-.4861 0-.9517.1395-1.399.4205v3.5999c0 .1271-.0615.1907-.1907.1907H.1914zm9.731.1436c-.4533 0-.8-.1272-1.044-.3815-.242-.2544-.3631-.6133-.3631-1.0769v-3.321c0-.1292.0615-.1927.1908-.1927h.564c.1293 0 .1929.0635.1929.1907v3.0215c0 .3425.0656.5948.201.7569.1333.162.3487.242.642.242.4595 0 .923-.1518 1.3887-.4574v-3.565c0-.1272.0615-.1908.1908-.1908h.564c.1293 0 .1929.0636.1929.1908v4.4511c0 .1252-.0636.1887-.1928.1887h-.4103c-.0636 0-.1149-.0123-.1497-.0369-.0349-.0266-.0575-.0738-.0718-.1436l-.0657-.3323c-.5948.437-1.204.6564-1.8297.6564zm5.4399 0c-.5374 0-1.0195-.0882-1.4461-.2666a.3754.3754 0 0 1-.158-.1047c-.0287-.039-.043-.0984-.043-.1805v-.2687c0-.1148.0369-.1723.1148-.1723.0452 0 .1231.0205.238.0575.4225.1333.8615.199 1.3128.199.3138 0 .5517-.0616.7138-.1806.164-.121.244-.2954.244-.523a.4923.4923 0 0 0-.1476-.3734 1.606 1.606 0 0 0-.5415-.285l-.8144-.3037c-.7097-.2605-1.0625-.7056-1.0625-1.3333 0-.4143.16-.7487.484-1.001.3221-.2543.7447-.3815 1.2677-.3815a3.487 3.487 0 0 1 1.2164.2195c.076.0246.1313.0574.1641.0985.0308.041.0472.1025.0472.1846v.2584c0 .1149-.041.1723-.123.1723a.8615.8615 0 0 1-.2216-.0472 3.5495 3.5495 0 0 0-1.0359-.1538c-.6112 0-.919.2072-.919.6195 0 .164.0514.2953.154.3897.1025.0964.3035.201.603.3159l.7466.2872c.3774.1436.6482.318.8144.519.1661.1989.2482.4574.2482.7753 0 .4513-.1682.8102-.5067 1.0769-.3385.2666-.7877.4-1.3497.4v.002zm3.0645-.1436c-.1272 0-.1928-.0615-.1928-.1907v-4.4491c0-.1272.0656-.1908.1928-.1908h.5641c.1272 0 .1928.0636.1928.1908v4.4511c0 .1251-.0656.1887-.1928.1887h-.564zm.2872-5.688c-.1846 0-.3303-.0513-.437-.1559a.558.558 0 0 1-.1579-.4143c0-.1724.0534-.3098.158-.4144a.5907.5907 0 0 1 .4369-.158c.1846 0 .3282.0534.4349.158.1066.1026.1579.242.1579.4144 0 .1702-.0513.3076-.158.4143-.1046.1026-.2502.1559-.4348.1559zm4.002 5.7926c-.7529 0-1.3293-.2133-1.7272-.642-.4-.4307-.599-1.0502-.599-1.8625 0-.8061.2052-1.4318.6175-1.8728.4102-.441.9948-.6625 1.7476-.6625.3446 0 .683.0615 1.0154.1825.0697.0247.119.0554.1477.0944s.043.1026.043.1908v.2564c0 .1271-.041.1907-.123.1907-.0329 0-.082-.0082-.1539-.0287a2.8307 2.8307 0 0 0-.7959-.1128c-.5353 0-.923.1333-1.1589.404s-.3528.6996-.3528 1.2924v.123c0 .5764.119 1.001.359 1.2718.24.2687.6174.404 1.1343.404.2666 0 .5538-.043.8615-.1332.0718-.0206.119-.0288.1436-.0288.082 0 .1251.0636.1251.1908v.2585c0 .082-.0123.1435-.039.1805-.0246.0369-.0759.0718-.1518.1025-.3138.1354-.6769.201-1.0933.201z"/></svg>',
}
# Podcast directory listings shown as "Listen on" buttons on /feeds/. Add Spotify, Amazon Music, YouTube here when live.
PLATFORMS = [
    {'id': 'apple', 'icon': BRAND_ICONS['applepodcasts'], 'name': 'Apple Podcasts', 'url': 'https://podcasts.apple.com/us/podcast/the-kingdom-of-our-lord/id6827272164'},
    {'id': 'spotify', 'icon': BRAND_ICONS['spotify'], 'name': 'Spotify', 'url': 'https://open.spotify.com/show/3NMs6JMDaOckjwyFZafcFh'},
    {'id': 'youtube', 'icon': BRAND_ICONS['youtube'], 'name': 'YouTube', 'url': 'https://www.youtube.com/playlist?list=PLV_QUMWPQMLQ'},
    {'id': 'amazon', 'icon': BRAND_ICONS['amazonmusic'], 'name': 'Amazon Music', 'url': 'https://music.amazon.com/podcasts/cca4b19b-bc72-40c4-a558-5aea2097819b/the-kingdom-of-our-lord'},
]
PODCAST_ICON = '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="11" r="2.2"/><path d="M12 14.5v6"/><path d="M8.5 15.5a5 5 0 1 1 7 0"/><path d="M6 18.5a8.5 8.5 0 1 1 12 0"/></svg>'
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
<link rel="icon" href="/favicon.ico" sizes="48x48"><link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png"><link rel="icon" type="image/png" sizes="16x16" href="/favicon-16.png"><link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png"><link rel="manifest" href="/site.webmanifest"><link rel="preload" href="/fonts/Vollkorn.ttf" as="font" type="font/ttf" crossorigin>
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
        else: src = ''
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
            links = f'<h2>Audio</h2><p class="dim" style="font-size:.85rem">Streamed from the original show.</p><div class="vgrid" data-list id="links">{acards}</div>'
        body = f'''<section class="hero wrap" data-pagefind-body><div class="bar"></div><div class="kicker">{e_(v["collection"])}</div><h1>{e_(v["title"])}</h1>
<p>{len(v["videos"])} video{"s" if len(v["videos"]) != 1 else ""}{f" · {len(v['links'])} audio" if v.get("links") else ""}{(" · " + src) if src else ""}</p><div class="vgrid">{cards}</div>{links}</section>'''
        page(f'/video/{v["id"]}/', v['title'], body, f'{v["title"]} — {v["collection"]} video{" series" if v.get("playlist") else "s"} by Kevin R. Amundson.' if v['collection'] != 'ExploreHistory.Live' else f'{v["title"]} — ExploreHistory.Live video series by Kevin R. Amundson.', active='video')

    rows = ''.join(f'<tr><td><a href="{s["url"]}">{e_(s["title"])}</a><div class="dim" style="font-size:.82rem">{len(s["eps"])} episodes</div></td><td><code>{BASE}{s["feed"]}</code></td><td><button class="copy" data-copy="{BASE}{s["feed"]}">Copy</button></td></tr>' for s in series)
    listen = (f'<div class="listen" aria-label="Listen on podcast apps"><span class="listen-k">Listen on</span><ul>'
              + ''.join(f'<li><a class="listen-btn {p["id"]}" href="{e_(p["url"])}" rel="noopener" target="_blank">{p.get("icon") or PODCAST_ICON}<span>{e_(p["name"])}</span></a></li>' for p in PLATFORMS)
              + '</ul></div>') if PLATFORMS else ''
    body = f'''<section class="hero wrap feeds"><div class="bar"></div><h1>Podcast feeds</h1><p>Paste a feed URL into any podcast app (Apple Podcasts → Library → Follow a show by URL; Pocket Casts, Overcast, AntennaPod, etc.). The <em>{e_(PODCAST)}</em> feed includes every recording; the series feeds below are parts of the same podcast.</p>
{listen}<table><thead><tr><th>Feed</th><th>URL</th><th></th></tr></thead><tbody>
<tr><td><strong>{e_(PODCAST)}</strong> <span class="dim">(all recordings)</span><div class="dim" style="font-size:.82rem">{len(episodes)} episodes</div></td><td><code>{BASE}/feeds/all.xml</code></td><td><button class="copy" data-copy="{BASE}/feeds/all.xml">Copy</button></td></tr>{rows}</tbody></table></section>'''
    page('/feeds/', 'Podcast feeds', body, 'RSS podcast feeds for every lecture series by Kevin R. Amundson.', active='feeds')
    page('/search/', 'Search', '<section class="hero wrap"><div class="bar"></div><h1>Search</h1><div id="search"></div></section>', 'Search all lectures and videos.', active='search')
    page('/404.html', 'Not found', '<section class="hero wrap"><div class="bar"></div><h1>Not found</h1><p>That page does not exist. <a href="/">Go home</a>.</p></section>', index=False)

def feed(path, title, desc, eps, cover, link, category, kind='episodic', cdata=False):
    cd = lambda t: '<![CDATA[' + t.replace(']]>', ']]]]><![CDATA[>') + ']]>'
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
<description>{cd(desc) if cdata else xesc(desc)}</description><itunes:summary>{cd(desc) if cdata else xesc(desc)}</itunes:summary><language>en-us</language><copyright>© Kevin R. Amundson</copyright>
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
    feed('/feeds/all.xml', PODCAST, SHOW_DESCRIPTION,
         sorted(episodes, key=lambda e: e['date']), '/covers/kingdom-of-our-lord-1500.jpg', '/', 'Christianity', cdata=True)
    # Identical copy at /feeds/all.rss (only atom:link self differs) for directories that prefer .rss
    src = open(os.path.join(DIST, 'feeds/all.xml')).read()
    selfx = f'<atom:link href="{BASE}/feeds/all.xml" rel="self"'
    assert src.count(selfx) == 1
    open(os.path.join(DIST, 'feeds/all.rss'), 'w').write(src.replace(selfx, f'<atom:link href="{BASE}/feeds/all.rss" rel="self"'))

def build_misc():
    urls = ['/', '/series/', '/video/', '/feeds/', '/search/'] + [s['url'] for s in series] + [e['url'] for e in episodes] + [f'/video/{v["id"]}/' for v in videos]
    open(os.path.join(DIST, 'sitemap.xml'), 'w').write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join(f'<url><loc>{BASE}{u}</loc></url>' for u in urls) + '</urlset>\n')
    open(os.path.join(DIST, 'robots.txt'), 'w').write(f'User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n')
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
