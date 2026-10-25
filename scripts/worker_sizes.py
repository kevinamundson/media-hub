#!/usr/bin/env python3
"""Refresh the SIZES map in worker/index.js from catalog/episodes.json.
Static-asset responses don't expose Content-Length to the Worker, so the Worker
uses this map to answer byte-range requests. Run after adding audio."""
import json, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
eps = json.load(open(os.path.join(ROOT, 'catalog/episodes.json')))
sizes = {e['audio']: e['bytes'] for e in eps}
p = os.path.join(ROOT, 'worker/index.js'); src = open(p).read()
src = re.sub(r'const SIZES = \{.*?\};', 'const SIZES = ' + json.dumps(sizes) + ';', src, count=1, flags=re.S)
open(p, 'w').write(src); print(f'{len(sizes)} sizes written')
