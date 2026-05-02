#!/usr/bin/env python3
from __future__ import annotations
import argparse, datetime as dt, html.parser, json, re, sys, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / 'reports'
SOURCES = ['hackernews', 'github', 'huggingface']

class LinkParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[]; self._a=None
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            d=dict(attrs); href=d.get('href','')
            if href: self._a={'href':href,'text':''}
    def handle_data(self, data):
        if self._a is not None: self._a['text'] += data
    def handle_endtag(self, tag):
        if tag == 'a' and self._a is not None:
            self.links.append(self._a); self._a=None

def fetch_url(url: str) -> str:
    req = urllib.request.Request(url, headers={'User-Agent':'Draco-News-Aggregator/1.0'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode('utf-8', 'replace')

def hn(limit: int):
    url='https://hn.algolia.com/api/v1/search?tags=front_page'
    data=json.loads(fetch_url(url))
    out=[]
    for item in data.get('hits', [])[:limit]:
        oid=item.get('objectID')
        out.append({
            'source':'hackernews',
            'title':item.get('title') or item.get('story_title') or '',
            'url':item.get('url') or (f'https://news.ycombinator.com/item?id={oid}' if oid else ''),
            'hn_url':f'https://news.ycombinator.com/item?id={oid}' if oid else '',
            'points':item.get('points'),
            'comments':item.get('num_comments'),
            'created_at':item.get('created_at'),
        })
    return out

def github(limit: int):
    html=fetch_url('https://github.com/trending?since=daily')
    repos=[]
    for m in re.finditer(r'<h2[^>]*>\s*<a[^>]+href="/([^"/]+/[^"/]+)"[^>]*>(.*?)</a>', html, re.S):
        repo=m.group(1).strip(); raw=re.sub(r'<[^>]+>',' ',m.group(2)); title=' '.join(raw.split()).replace(' / ','/')
        repos.append({'source':'github_trending','title':title or repo,'repo':repo,'url':'https://github.com/'+repo,'signal':'today_trending'})
        if len(repos)>=limit: break
    return repos

def huggingface(limit: int):
    html=fetch_url('https://huggingface.co/papers')
    parser=LinkParser(); parser.feed(html)
    out=[]; seen=set()
    for a in parser.links:
        href=a['href']; text=' '.join(a['text'].split())
        if not text or '/papers/' not in href: continue
        url=urllib.parse.urljoin('https://huggingface.co', href)
        if url in seen: continue
        seen.add(url); out.append({'source':'huggingface_papers','title':text,'url':url})
        if len(out)>=limit: break
    return out

def save(source: str, items: list[dict]):
    day=dt.datetime.now().strftime('%Y-%m-%d')
    outdir=REPORTS/day; outdir.mkdir(parents=True, exist_ok=True)
    path=outdir/f'{source}.json'; path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding='utf-8')
    return path

def main():
    ap=argparse.ArgumentParser()
    sub=ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('sources')
    f=sub.add_parser('fetch'); f.add_argument('--source', required=True, choices=SOURCES); f.add_argument('--limit', type=int, default=10); f.add_argument('--save', action='store_true')
    s=sub.add_parser('smoke-test'); s.add_argument('--quick', action='store_true')
    args=ap.parse_args()
    if args.cmd=='sources':
        print('\n'.join(SOURCES))
        return 0
    if args.cmd=='smoke-test': print(json.dumps({'ok': True, 'sources': SOURCES, 'quick': bool(args.quick)}, ensure_ascii=False, indent=2)); return 0
    funcs={'hackernews':hn,'github':github,'huggingface':huggingface}
    items=funcs[args.source](args.limit)
    if args.save: save(args.source, items)
    print(json.dumps(items, ensure_ascii=False, indent=2)); return 0
if __name__ == '__main__': raise SystemExit(main())
