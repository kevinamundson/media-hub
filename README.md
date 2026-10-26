# media-hub — media.kevinamundson.me

Kevin Amundson's lectures, sermons and courses in one place: a free, installable-nothing web app with
podcast RSS feeds. Live at **https://media.kevinamundson.me**.

- Static site generated from `catalog/*.json` by `scripts/build.py` (plain Python, no framework)
- Persistent audio player (queue, resume, speed, ±15/30 s skip, lock-screen controls) that keeps playing across pages
- Pagefind full-text search, lite YouTube embeds (video stays on YouTube)
- Per-series and all-content podcast feeds with iTunes tags: `/feeds/<series>.xml`, `/feeds/all.xml`
- Hosted on Cloudflare Workers Static Assets (free). `worker/index.js` runs only for `/audio/*` and
  answers HTTP Range requests with 206 Partial Content (needed for seeking and for Apple Podcasts)

**Audio files are not in git.** Originals live outside the repo (`../files/audio/<series>/<date>-<slug>.mp3`)
and are copied into `dist/audio/` at build time. Workers assets allow up to 25 MiB per file and 20,000 files.

## Build

```sh
python3 scripts/covers.py                 # only when series change (needs Pillow)
python3 scripts/build.py --media ../files # -> dist/
npx -y pagefind@latest --site dist        # search index
python3 scripts/worker_sizes.py           # after adding audio
```

## Deploy

```sh
npx wrangler deploy
```

## Adding an episode

1. Put the file at `../files/audio/<series-id>/<YYYY-MM-DD>-<slug>.mp3`
2. Add an entry to `catalog/episodes.json` (id, series, title, date, audio, mime, bytes, duration)
3. Build, run `scripts/worker_sizes.py`, deploy. Feeds update automatically.

## Original cover art and linked guest appearances

- A series with `cover_original` (source image URL) uses that original art, saved as-is at `static/covers/<id>.<ext>`;
  `scripts/covers.py` skips it and only generates typographic covers for the other series.
- `catalog/video.json` groups may have `"playlist": null` (standalone videos; `source` links the original page) and a
  `links` list of externally hosted audio (guest appearances). Linked audio streams from the original host and is
  never copied into `/audio/` or added to the podcast feeds.
- Files over 25 MiB can't be served as Workers assets. Re-encode them to fit (Psalm 38 and Psalm 44 are 64 kbps CBR mono
  44.1 kHz MP3s made from the 156 kbps originals with `ffmpeg -ac 1 -ar 44100 -c:a libmp3lame -b:a 64k -map_metadata 0`).

## Moving audio to R2 later

Keep the `/audio/...` paths. Serve the bucket at the same paths (or proxy from the Worker) so feed
enclosure URLs never change.
