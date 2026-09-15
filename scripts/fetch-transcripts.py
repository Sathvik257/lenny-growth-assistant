"""Fetch actual upstream transcripts; never fabricate seed evidence."""
import argparse
import concurrent.futures
import json
import urllib.request
from pathlib import Path
from urllib.parse import quote

REPO = 'https://api.github.com/repos/ChatPRD/lennys-podcast-transcripts'


def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'LennyGrowthAssistant/1.0'})
    with urllib.request.urlopen(req, timeout=60) as response:
        return response.read()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--limit', type=int, default=0, help='0 downloads all transcripts')
    p.add_argument('--revision', default='main', help='Git commit or branch to fetch')
    args = p.parse_args()
    tree = json.loads(fetch(REPO + '/git/trees/' + quote(args.revision, safe='') + '?recursive=1'))
    paths = [x['path'] for x in tree['tree'] if x['path'].startswith('episodes/') and x['path'].endswith('/transcript.md')]
    preferred = ['sean-ellis', 'rahul-vohra', 'brian-balfour', 'elena-verna', 'april-dunford', 'shreyas-doshi', 'teresa-torres', 'marty-cagan']
    paths.sort(key=lambda x: (not any('/'+s+'/' in x for s in preferred), x))
    if args.limit:
        paths = paths[:args.limit]
    root = Path('data/transcripts')
    def save(path):
        dest = root / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(fetch('https://raw.githubusercontent.com/ChatPRD/lennys-podcast-transcripts/'+tree['sha']+'/'+quote(path)))
        return path
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        completed = list(pool.map(save, paths))
    root.mkdir(parents=True, exist_ok=True)
    (root/'manifest.json').write_text(json.dumps({'repository':REPO, 'revision':tree['sha'], 'files':completed}, indent=2))
    print(f'Downloaded {len(completed)} transcripts at revision {tree["sha"]}.')


if __name__ == '__main__':
    main()
