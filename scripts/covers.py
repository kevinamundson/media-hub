"""Generate podcast cover art (1400x1400 JPEG) for each series plus a default OG image."""
import json, os, shutil, textwrap
from PIL import Image, ImageDraw, ImageFont
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = os.path.join(ROOT, 'static', 'fonts')
OUT = os.path.join(ROOT, 'static', 'covers')
os.makedirs(OUT, exist_ok=True)
BG, FG, MUTED, RED = (23, 23, 23), (250, 250, 250), (186, 186, 186), (132, 1, 14)

def font(name, size, wght):
    f = ImageFont.truetype(os.path.join(F, name), size)
    try: f.set_variation_by_axes([wght] if name.startswith('Vollkorn') else [14 if size < 60 else 32, wght])
    except Exception: pass
    return f

def bg(w, h):
    im = Image.new('RGB', (w, h), BG)
    d = ImageDraw.Draw(im)
    for y in range(h):  # subtle vertical vignette
        t = y / h; c = int(23 + 14 * (1 - abs(0.35 - t)))
        d.line([(0, y), (w, y)], fill=(c, c - 2, c - 2))
    return im, d

def wrap(d, text, f, maxw):
    words, lines, cur = text.split(), [], ''
    for wd in words:
        t = (cur + ' ' + wd).strip()
        if d.textlength(t, font=f) <= maxw: cur = t
        else: lines.append(cur); cur = wd
    lines.append(cur); return lines

def cover(title, kicker, sub, path, size=1400):
    im, d = bg(size, size); m = 120
    d.rectangle([m, m, m + 140, m + 14], fill=RED)
    d.text((m, m + 50), 'KEVIN R. AMUNDSON', font=font('Inter.ttf', 46, 600), fill=MUTED)
    for fs in (150, 130, 112, 96, 84):
        tf = font('Vollkorn.ttf', fs, 700); lines = wrap(d, title, tf, size - 2 * m)
        if len(lines) <= 4: break
    y = size // 2 - (len(lines) * fs * 1.12) / 2 + 40
    for ln in lines:
        d.text((m, y), ln, font=tf, fill=FG); y += fs * 1.12
    d.text((m, size - m - 130), kicker.upper(), font=font('Inter.ttf', 40, 700), fill=(200, 60, 70))
    sf = font('Inter.ttf', 40, 400)
    d.text((m, size - m - 70), wrap(d, sub, sf, size - 2 * m)[0], font=sf, fill=MUTED)
    im.save(path, 'JPEG', quality=88, optimize=True, progressive=True)

if __name__ == '__main__':
    series = json.load(open(os.path.join(ROOT, 'catalog', 'series.json')))
    for s in series:
        kicker = 'Redemption School of Theology' if s['id'].startswith('rst-') else 'Lectures & Recordings'
        cover(s['title'], kicker, s['subtitle'].split(' · ')[-1], os.path.join(OUT, s['id'] + '.jpg'))
    # Official podcast cover supplied by Kevin (1500x1500 RGB JPEG), used as-is.
    shutil.copyfile(os.path.join(ROOT, 'static', 'brand', 'kingdom-cover-1500.jpg'), os.path.join(OUT, 'kingdom-of-our-lord-1500.jpg'))
    src = Image.open(os.path.join(ROOT, 'static', 'brand', 'kingdom-cover-1500.jpg')).convert('RGB')
    # 1200x630 social image: the podcast cover centered on its own off-white background
    im = Image.new('RGB', (1200, 630), src.getpixel((4, 4)))
    im.paste(src.resize((630, 630), Image.LANCZOS), (285, 0))
    im.save(os.path.join(OUT, 'og.jpg'), 'JPEG', quality=88, optimize=True)
    print('covers written to', OUT)
