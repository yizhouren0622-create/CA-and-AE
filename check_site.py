#!/usr/bin/env python3
"""Check static links, exercise provenance and the bilingual content contract."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
from collections import Counter
import json

ROOT = Path(__file__).resolve().parent
errors = []

class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.links, self.math, self.languages = [], [], 0, Counter()
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a: self.ids.append(a['id'])
        if tag in ('a', 'link') and a.get('href'): self.links.append(a['href'])
        if tag in ('img', 'script') and a.get('src'): self.links.append(a['src'])
        if tag == 'math': self.math += 1
        if tag == 'merror': errors.append('MathML error element')
        if a.get('data-lang'): self.languages[a['data-lang']] += 1

pages = {}
for path in ROOT.glob('*.html'):
    p = Page(); raw = path.read_text(); p.feed(raw); pages[path.name] = p
    if len(p.ids) != len(set(p.ids)): errors.append(f'{path.name}: duplicate ID')
    if not p.languages['zh'] or p.languages['zh'] != p.languages['en']:
        errors.append(f'{path.name}: unmatched bilingual blocks')
    if any(t in raw for t in ('/Users/', 'wxid_', 'privatePath', 'file://')):
        errors.append(f'{path.name}: private source path')
for name, p in pages.items():
    for url in p.links:
        parts = urlsplit(url)
        if parts.scheme or parts.netloc: continue
        path = unquote(parts.path) or name
        if not (ROOT / path).is_file(): errors.append(f'{name}: missing {path}')
        if parts.fragment and path in pages and unquote(parts.fragment) not in pages[path].ids:
            errors.append(f'{name}: missing anchor {url}')

def load(name): return json.loads((ROOT / 'data' / name).read_text())
def bilingual(value, where):
    if not isinstance(value, dict) or not all(isinstance(value.get(k), str) and value[k].strip() for k in ('zh', 'en')):
        errors.append(f'{where}: missing Chinese or English')

library = load('exercises.json'); lessons = load('lessons.json'); exams = load('exams.json')
scope = load('syllabus.json')
total = solved = 0
for cid, lib in library.items():
    ids = [e['id'] for e in lib['items']]; total += len(ids); solved += len(lib['solutions'])
    if len(ids) != len(set(ids)): errors.append(f'{cid}: duplicate exercise ID')
    if sum(c['count'] for c in lib['chapters']) != len(ids): errors.append(f'{cid}: chapter counts')
    for ex in lib['items']:
        if not all(isinstance(ex.get(k), int) and ex[k] > 0 for k in ('printedPage', 'pdfPage')):
            errors.append(f'{ex["id"]}: missing source page')
    for key, sol in lib['solutions'].items():
        if key not in ids: errors.append(f'{key}: not in inventory')
        for field in ('title', 'statement', 'recognition', 'answer'):
            bilingual(sol.get(field), f'{key}.{field}')
        bilingual(sol.get('verification', {}).get('methods'), f'{key}.verification')
        if not sol.get('steps'): errors.append(f'{key}: missing derivation')
        for step in sol.get('steps', []):
            bilingual(step.get('title'), f'{key}.step.title'); bilingual(step.get('text'), f'{key}.step.text')
        if sol.get('figure') and not (ROOT / 'assets' / sol['figure']).is_file(): errors.append(f'{key}: source figure missing')
    raw = json.dumps(lib, ensure_ascii=False)
    if any(s in raw for s in ('/Users/', 'wxid_', 'privatePath')): errors.append(f'{cid}: private source metadata')
for paper in exams:
    valid = {l['id'] for l in lessons if l['course'] == paper['course']}
    questions = paper['questions']
    if len(questions) != 10: errors.append(f'{paper["course"]}: paper needs 10 questions')
    for q in questions:
        for field in ('title', 'body', 'hint', 'answer', 'check'): bilingual(q.get(field), f'{q["id"]}.{field}')
        if not set(q['topics']).issubset(valid): errors.append(f'{q["id"]}: invalid diagnosis topic')
        if not q['steps']['zh'] or len(q['steps']['zh']) != len(q['steps']['en']): errors.append(f'{q["id"]}: incomplete bilingual derivation')
if errors: raise SystemExit('\n'.join(errors))
print(f'PASS: {len(pages)} pages; all internal links and bilingual blocks valid; {total} exercise IDs, {solved} checked solutions; {sum(p.math for p in pages.values())} MathML equations.')
