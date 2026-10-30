#!/usr/bin/env python3
"""Check static links, exercise provenance and the bilingual content contract."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
from collections import Counter
import json, re

ROOT = Path(__file__).resolve().parent
errors = []

class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.links, self.math, self.languages = [], [], 0, Counter()
        self.exercise, self.tables, self.exercise_table_rows = None, [], {}
        self.math_depth=self.literal_depth=self.hidden_depth=0; self.current_tag=None; self.notation_leaks=[]
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.current_tag=tag
        if tag=='math':self.math_depth+=1
        if tag=='code':self.literal_depth+=1
        if tag in ('script','style'):self.hidden_depth+=1
        if 'id' in a: self.ids.append(a['id'])
        if tag=='details' and a.get('id','').startswith(('CA-','AE-')): self.exercise=a['id']
        if tag=='mtable': self.tables.append([self.exercise,0])
        if tag=='mtr' and self.tables: self.tables[-1][1]+=1
        if tag in ('a', 'link') and a.get('href'): self.links.append(a['href'])
        if tag in ('img', 'script') and a.get('src'): self.links.append(a['src'])
        if tag == 'math': self.math += 1
        if tag == 'merror': errors.append('MathML error element')
        if a.get('data-lang'): self.languages[a['data-lang']] += 1
    def handle_data(self,data):
        if self.hidden_depth or self.literal_depth:return
        if re.search(r'[_^₀-₉⁰¹²³⁴⁵⁶⁷⁸⁹]',data) and not self.math_depth:
            self.notation_leaks.append(data[:120])
        if self.math_depth and re.search(r'[_^/\\]',data):self.notation_leaks.append('unstacked division: '+data)
    def handle_endtag(self,tag):
        if tag=='math':self.math_depth-=1
        if tag=='code':self.literal_depth-=1
        if tag in ('script','style'):self.hidden_depth-=1
        if tag=='mtable' and self.tables:
            exercise,rows=self.tables.pop()
            if exercise:self.exercise_table_rows.setdefault(exercise,[]).append(rows)

pages = {}
for path in ROOT.glob('*.html'):
    p = Page(); raw = path.read_text(); p.feed(raw); pages[path.name] = p
    if p.notation_leaks:errors.append(f'{path.name}: raw mathematical notation: {p.notation_leaks[:5]}')
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
    if isinstance(value,dict) and any(re.search(r'[\x00-\x09\x0b-\x1f]',v) for v in value.values() if isinstance(v,str)):
        errors.append(f'{where}: invalid control character; check escaped TeX')
    if not isinstance(value, dict) or not all(isinstance(value.get(k), str) and value[k].strip() for k in ('zh', 'en')):
        errors.append(f'{where}: missing Chinese or English')

library = load('exercises.json'); lessons = load('lessons.json'); exams = load('exams.json')
scope = load('syllabus.json')
total = solved = partial = 0
for cid, lib in library.items():
    ids = [e['id'] for e in lib['items']]; total += len(ids)
    solved += sum(not s.get('pendingSubparts') for s in lib['solutions'].values())
    partial += sum(bool(s.get('pendingSubparts')) for s in lib['solutions'].values())
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
        if sol.get('pendingSubparts'):
            bilingual(sol.get('completionNote'), f'{key}.completionNote')
            if not isinstance(sol['pendingSubparts'],list): errors.append(f'{key}: pending parts must be listed')
        if not sol.get('steps'): errors.append(f'{key}: missing derivation')
        for step in sol.get('steps', []):
            bilingual(step.get('title'), f'{key}.step.title'); bilingual(step.get('text'), f'{key}.step.text')
        expected_rows=Counter(1+step['formula'].count('\\\\') for step in sol['steps'] if '\\begin{cases}' in step.get('formula',''))
        actual_rows=Counter(pages[cid+'-exercises.html'].exercise_table_rows.get(key,[]))
        if expected_rows-actual_rows: errors.append(f'{key}: piecewise formula rows missing or collapsed')
        if sol.get('figure') and not (ROOT / 'assets' / sol['figure']).is_file(): errors.append(f'{key}: source figure missing')
    raw = json.dumps(lib, ensure_ascii=False)
    if any(s in raw for s in ('/Users/', 'wxid_', 'privatePath')): errors.append(f'{cid}: private source metadata')
question_ids=[];paper_ids=[]
for paper in exams:
    paper_ids.append(paper.get('id',paper['course']))
    valid = {l['id'] for l in lessons if l['course'] == paper['course']}
    questions = paper['questions']
    if len(questions) != 10: errors.append(f'{paper["course"]}: paper needs 10 questions')
    if sum(q['points'] for q in questions)!=paper['points']:errors.append(f'{paper["course"]}: paper point total')
    for q in questions:
        question_ids.append(q['id'])
        for field in ('title', 'body', 'hint', 'answer', 'check'): bilingual(q.get(field), f'{q["id"]}.{field}')
        if not set(q['topics']).issubset(valid): errors.append(f'{q["id"]}: invalid diagnosis topic')
        if not q['steps']['zh'] or len(q['steps']['zh']) != len(q['steps']['en']): errors.append(f'{q["id"]}: incomplete bilingual derivation')
if len(question_ids)!=len(set(question_ids)):errors.append('Mock papers share a question/progress ID')
if len(paper_ids)!=len(set(paper_ids)):errors.append('Mock papers share a timer ID')
if errors: raise SystemExit('\n'.join(errors))
print(f'PASS: {len(pages)} pages; all internal links and bilingual blocks valid; {total} exercise IDs, {solved} complete checked solutions, {partial} partial solutions; {sum(p.math for p in pages.values())} MathML equations.')
