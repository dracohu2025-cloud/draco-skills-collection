#!/usr/bin/env python3
from pathlib import Path
import json

root = Path(__file__).resolve().parents[1]
manifest = json.loads((root / 'templates/open-slide-template-pack/manifest.json').read_text(encoding='utf-8'))
print(f"{manifest['name']} v{manifest['version']}")
print(manifest['counts'])
for d in manifest['decks']:
    print(f"{d['category']:22} {d['pages']:>3}  {d['slug']}")
