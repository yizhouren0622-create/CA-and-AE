#!/usr/bin/env python3
"""Build static bilingual pages. Browsing requires no Python or external services."""
from pathlib import Path
import hashlib, html, json, re
from math_typesetting import format_text, render_math

ROOT=Path(__file__).resolve().parent
def read(name): return json.loads((ROOT/'data'/name).read_text())
syllabus=read('syllabus.json'); lessons=read('lessons.json'); papers=read('exams.json')
library=read('exercises.json')
revision_files=[Path(__file__),ROOT/'math_typesetting.py']+sorted((ROOT/'data').glob('*.json'))
SITE_REVISION=hashlib.sha256(b''.join(p.read_bytes() for p in revision_files)).hexdigest()[:12]
courses={c['id']:c for c in syllabus['courses']}
def complete(solution): return bool(solution) and not solution.get('pendingSubparts')
def checked_count(lib): return sum(complete(s) for s in lib['solutions'].values())
def partial_count(lib): return sum(bool(s) and not complete(s) for s in lib['solutions'].values())
def esc(s): return html.escape(str(s),quote=True)
def text(s,language='zh'):return format_text(str(s),language)
def bi(zh,en,tag='div',cls=''):
    return f'<{tag} class="{cls}"><span data-lang="zh" lang="zh-CN">{text(zh,"zh")}</span><span data-lang="en" lang="en">{text(en,"en")}</span></{tag}>'
def b(o,tag='div',cls=''): return bi(o['zh'],o['en'],tag,cls)
def math(s): return '<div class="math-display">'+render_math(s,display=True)+'</div>'
def items(zh,en):
    assert len(zh)==len(en)
    return '<ol class="steps">'+''.join(bi(a,c,'li') for a,c in zip(zh,en))+'</ol>'
def figure(name,alt=None,source=False,caption_text=None):
    caption=b(caption_text) if caption_text else (bi('教材原图；版本与页码见本题来源。','Source textbook figure; see the edition and page references for this exercise.') if source else bi('示意图中的符号及取值以题干为准。','Use the definitions and values stated in the question.'))
    caption+=bi('点图查看原尺寸。','Select the figure to view it at full size.')
    image_revision=hashlib.sha256((ROOT/'assets'/name).read_bytes()).hexdigest()[:12]
    image_url=f'assets/{esc(name)}?v={image_revision}'
    return f'<figure><a class="figure-link" href="{image_url}" target="_blank" rel="noopener" title="查看原尺寸 · View full size"><img src="{image_url}" alt="{esc(alt or "电路或特性示意图 · Circuit or characteristic diagram")}" loading="lazy"></a><figcaption>'+caption+'</figcaption></figure>'
def reveal(label,label_en,body,kind='solution'):
    return f'<details class="reveal {kind}"><summary>'+bi(label,label_en,'span')+f'</summary><div class="reveal-body">{body}</div></details>'
def actions():
    return '<div class="exam-actions"><button data-print="questions">'+bi('打印题目','Print questions','span')+'</button><button data-print="solutions">'+bi('打印含解析版','Print with solutions','span')+'</button><button data-close-reveals>'+bi('收起提示和答案','Close hints & answers','span')+'</button></div>'
def subnav(cid):
    links=[(f'{cid}.html','课程首页','Course home'),(f'{cid}-study.html','知识与解题','Concepts & methods'),(f'{cid}-exam.html','模拟卷与查漏','Mock paper & diagnosis'),(f'{cid}-exercises.html','教材逐题','Textbook exercises')]
    return '<nav class="course-nav" aria-label="课程导航 · Course navigation">'+''.join(f'<a href="{url}">'+bi(zh,en,'span')+'</a>' for url,zh,en in links)+'</nav>'
def page(filename,title,body,cid=None,kind='study'):
    nav=[('index.html','首页','Home'),('circuit.html','电路分析','Circuit Analysis'),('analog.html','模拟电路','Analog Electronics'),('scope.html','考试范围','Course scope')]
    top='<header class="site-top" id="siteTop"><div class="site-top-inner"><a class="site-brand" href="index.html">'+bi('电路与模电 · 学习站','Circuits & Analog · Study','span')+'</a><button class="site-menu-btn" type="button" aria-controls="siteLinks" aria-expanded="false">'+bi('菜单','Menu','span')+'</button><nav class="site-links" id="siteLinks" aria-label="全站导航 · Site navigation">'+''.join(f'<a href="{url}" data-page="{url}">'+bi(zh,en,'span')+'</a>' for url,zh,en in nav)+'</nav></div></header>'
    tools='<div class="site-tools"><label for="site-language">'+bi('语言','Language','span')+'</label><select id="site-language" aria-label="语言 · Language"><option value="both">中英对照 · Bilingual</option><option value="zh">中文</option><option value="en">English</option></select><a href="scope.html">'+bi('范围以授课计划为准','Scope follows the course plan','span')+'</a></div>'
    footer='<footer class="site-footer">'+bi('依据20260913授课计划及所提供课件整理。模拟卷为本站原创；教材解析分别列明来源与核验方式。阅读无需外部公式服务。','Based on the 20260913 course plan and supplied slides. Mock papers are original practice; textbook solutions list sources and verification. Equations require no external service.')+'</footer>'
    result='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#efeae2"><meta name="description" content="电路分析基础与模拟电子技术双语考试学习、模拟卷和教材逐题解析"><title>'+esc(title)+' · CA & AE</title><link rel="stylesheet" href="assets/site.css"><link rel="stylesheet" href="assets/course.css"></head><body><a class="skip" href="#content">跳至正文 · Skip to content</a>'+top+tools+(subnav(cid) if cid else '')+f'<main id="content" class="{kind}-page">{body}</main>'+footer+'<script defer src="assets/site.js"></script><script defer src="assets/course.js"></script></body></html>'
    for asset in ('site.css','course.css','site.js','course.js'):
        revision=hashlib.sha256((ROOT/'assets'/asset).read_bytes()).hexdigest()[:12]
        result=result.replace(f'assets/{asset}"',f'assets/{asset}?v={revision}"')
    result=re.sub(r'href="([\w-]+\.html)(#[^"]*)?"',lambda m:f'href="{m[1]}?v={SITE_REVISION}{m[2] or ""}"',result)
    (ROOT/filename).write_text(result)
def link(url,zh,en,desc,desc_en):
    return f'<a class="hub-link" href="{url}">'+bi(zh,en,'strong')+bi(desc,desc_en)+'</a>'

home=bi('电路分析基础与模拟电子技术','Circuit Analysis & Analog Electronics','h1')+bi('按考试范围学习，按解题步骤练习。先完成电路基础，再进入模拟电路。','Study within the course scope and practice a clear solution process. Start with circuits, then move to analog electronics.','p','lead')
home+='<div class="course-entries">'+link('circuit.html','01 · 电路分析基础','01 · Circuit Analysis','参考方向与定律、直流分析、一阶动态、正弦稳态。','References and laws, DC analysis, first-order transients, sinusoidal steady state.')+link('analog.html','02 · 模拟电子技术','02 · Analog Electronics','运放、二极管、MOSFET、BJT、反馈、滤波与比较器。','Op-amps, diodes, MOSFETs, BJTs, feedback, filters and comparators.')+'</div>'
tot=sum(len(v['items']) for v in library.values());done=sum(checked_count(v) for v in library.values())
home+='<div class="reading-note">'+bi(f'当前已建立{tot}道教材主习题的题号与页码清单，其中{done}道已有完整题干与核验解析，题目原有配图随题保留。其余逐题标注待整理。两门课各有一套100分基础诊断卷。',f'The inventory contains {tot} numbered textbook exercises; {done} currently have complete statements and checked solutions, with original figures retained where present. Remaining items are labeled pending. Each course has a 100-point diagnostic paper.')+'</div>'
page('index.html','电路分析与模拟电子技术','<article class="study-paper home">'+home+'</article>')

scope=bi('考试范围与资料依据','Course scope & source hierarchy','h1')+bi('最高依据为授课计划第2–5页；课件提供讲解，教材提供题目。讲授范围以外的章节保留在全书习题清单中，但不进入默认考试路线。','The plan, slides 2–5, controls coverage. Lecture slides support explanations and textbooks supply exercises. Chapters outside coverage remain in the full-book inventory but are not in the default exam route.','p')
scope+='<div class="scope-note">'+bi('评价构成：考勤与课堂表现15%，课后作业15%，期末闭卷70%。纲领未给出期末题型、时长或各章分值；本站100分诊断卷及80分钟建议是自测设置。','Assessment: attendance/class participation 15%, homework 15%, closed-book final 70%. The plan does not specify final question types, duration or chapter weights. The 100-point papers and suggested 80 minutes are site practice settings.')+'</div>'
scope+=b(syllabus['editionNote'],'p')
for cid,c in courses.items():
    scope+=bi(c['zh'],c['en'],'h2')+'<ul class="scope-list">'+''.join(bi(s['zh'],s['en'],'li') for s in c['scope'])+'</ul>'+b(c['excluded'],'p','reading-note')
    scope+=bi('指定作业','Assigned exercises','h3')+'<div class="table-scroll"><table><thead><tr><th>'+bi('章','Chapter','span')+'</th><th>'+bi('题号与指定小问','IDs & assigned subparts','span')+'</th></tr></thead><tbody>'
    for ch,ids in c['homework'].items():
        anchors=[]
        for id in ids:
            base=re.match(r'^[\d.-]+',id).group()
            target=('CA-' if cid=='circuit' else 'AE-')+base
            translated={'4.5.1（源电压增益不要求）':'4.5.1 (source voltage gain not required)','8.4.1（闭环电压增益）':'8.4.1 (closed-loop voltage gain)'}
            label=bi(id,translated[id],'span') if id in translated else esc(id)
            anchors.append(f'<a href="{cid}-exercises.html#{target}">{label}</a>')
        scope+=f'<tr><td>{ch}</td><td>'+', '.join(anchors)+'</td></tr>'
    scope+='</tbody></table></div>'
scope+='<div class="scope-note">'+bi('注意：习题编号与小节编号不同。模电作业10.8.2、10.8.4属于比较器习题；不能因为小节10.8.2方波发生器不在讲授范围就排除它们。部分章习题未逐题判定范围前，会标注“待映射”。','Exercise and subsection numbering differ. Assigned 10.8.2 and 10.8.4 are comparator exercises; the exclusion of waveform-generator subsection 10.8.2 does not exclude them. Exercises in partially covered chapters remain “scope mapping pending” until checked individually.')+'</div>'
page('scope.html','考试范围','<article class="study-paper">'+scope+'</article>')

for cid,c in courses.items():
    ls=[l for l in lessons if l['course']==cid];lib=library[cid];solutions=lib['solutions']
    s=bi(c['zh'],c['en'],'h1')+bi('先建立知识之间的联系，再按题型完成训练。提示与答案均可独立展开。','Connect the concepts first, then practice by problem type. Hints and answers open independently.','p','lead')
    s+='<div class="hub-grid">'+link(f'{cid}-study.html','知识梳理与解题路径','Concepts & solution methods',f'{len(ls)}个主题，含模型条件、判断步骤、易错点与图示。',f'{len(ls)} topics with assumptions, decisions, common errors and diagrams.')+link(f'{cid}-exam.html','模拟卷 · 查漏补缺','Mock exam · Diagnosis','实际题目、逐题提示、完整解析；记录自评分并回到薄弱知识点。','Work actual questions, reveal hints/solutions and record self-scores linked to weak topics.')+link(f'{cid}-exercises.html','教材习题 · 逐题完成','Textbook exercises · Work in order',f'{len(lib["items"])}道主习题清单；{checked_count(lib)}道已整理并核验。保留题干和原图。',f'{len(lib["items"])} numbered exercises; {checked_count(lib)} have transcribed statements, source figures and checked solutions.')+link('scope.html','学习范围与指定作业','Coverage & assigned homework','直接查看纲领中的包含、排除和仅概念要求。','Check included, excluded and concepts-only material against the plan.')+'</div>'
    s+=bi('建议顺序','Suggested order','h2')+'<ol class="route">'+''.join(f'<li><a href="{cid}-study.html#{l["id"]}">'+bi(l['zh'],l['en'],'span')+'</a></li>' for l in ls)+'</ol>'
    page(f'{cid}.html',c['zh'],'<article class="study-paper">'+s+'</article>',cid)
    toc='<aside class="lesson-toc">'+bi('一次学习一个主题','One topic at a time','strong')+'<ol>'+''.join(f'<li><a href="#{l["id"]}">'+bi(l['zh'],l['en'],'span')+'</a></li>' for l in ls)+'</ol></aside>'
    body=bi(c['zh']+' · 知识与解题',c['en']+' · Concepts & methods','h1')+bi('中文与英文均包含本页完整知识要点和步骤。每节最后先独立回答，再展开检查。','Both languages contain the complete essentials and steps on this page. Try the self-check before revealing it.','p')
    for l in ls:
        body+=f'<section class="lesson" id="{l["id"]}">'+bi(l['zh'],l['en'],'h2')+f'<p class="source-line">{esc(l["scope"])} · {esc(l["source"])}</p>'+bi(l['concept'],l['concept_en'],'p')
        if l.get('figure'):body+=figure(l['figure'])
        body+=''.join(math(f) for f in l['formulas'])+bi('解题顺序','Solution process','h3')+items(l['steps'],l['steps_en'])+'<div class="scope-note">'+bi(l['traps'],l['traps_en'])+'</div>'
        body+=reveal('一分钟检查','One-minute check',bi(l['check'],l['check_en']))
        body+=f'<a class="related" href="{cid}-exam.html">'+bi('用模拟卷检查掌握情况','Check understanding on the paper','span')+'</a></section>'
    page(f'{cid}-study.html',c['zh']+'知识与解题','<div class="reading-layout">'+toc+'<article class="study-paper">'+body+'</article></div>',cid,kind='reading')
    p=next(p for p in papers if p['course']==cid)
    body=b(p['title'],'h1')+bi(f'10题 · 100分 · 建议{p["minutes"]}分钟 · 闭卷自测',f'10 questions · 100 points · Suggested {p["minutes"]} minutes · Closed-book practice','p','exam-meta')+b(p['origin'],'p','scope-note')
    body+=bi('先独立作答，再展开解析按评分点自评。分数与练习状态只保存在当前浏览器；系统不自动判定自由书写答案。','Attempt first, then self-score against the rubric. Scores and progress stay in this browser; free-written answers are not automatically graded.','p')
    body+=actions()+'<div class="diagnosis" data-paper="'+cid+'"><div class="timer-tools"><button data-timer-start>'+bi('开始计时','Start timer','span')+'</button><button data-timer-pause>'+bi('暂停','Pause','span')+'</button><output data-timer aria-live="off">00:00</output></div><div data-score-summary aria-live="polite"></div><div data-weak-topics></div></div>'
    body+='<nav class="exam-toc" aria-label="题号 · Questions">'+''.join(f'<a href="#{q["id"]}">{i}</a>' for i,q in enumerate(p['questions'],1))+'</nav>'
    for i,q in enumerate(p['questions'],1):
        body+=f'<section class="question" id="{q["id"]}" data-points="{q["points"]}" data-topics="{esc(",".join(q["topics"]))}">'+bi(f'{i}. {q["title"]["zh"]}',f'{i}. {q["title"]["en"]}','h2')+bi('10分','10 points','p','muted')+b(q['body'],'p')
        if q.get('figure'):body+=figure(q['figure'])
        body+=reveal('提示','Hint',b(q['hint']),kind='hint')
        body+=reveal('答案、步骤与检查','Answer, working & checks',items(q['steps']['zh'],q['steps']['en'])+b(q['answer'],'p','key')+b(q['check'],'p'))
        body+='<div class="topic-links">'+''.join(f'<a href="{cid}-study.html#{topic}">'+bi(next(l['zh'] for l in ls if l['id']==topic),next(l['en'] for l in ls if l['id']==topic),'span')+'</a>' for topic in q['topics'])+'</div>'
        body+=f'<label class="self-score" for="score-{q["id"]}">'+bi('自评分','Self-score','span')+f'<select id="score-{q["id"]}" data-score="{q["id"]}"><option value="">—</option>'+''.join(f'<option value="{n}">{n} 分 · {n} points</option>' for n in range(11))+'</select></label></section>'
    page(f'{cid}-exam.html',c['zh']+'诊断卷','<article class="exam-paper">'+body+'</article>',cid,kind='exam')
    body=bi(c['zh']+' · 教材逐题',c['en']+' · Textbook exercise library','h1')+bi(f'全书{len(lib["items"])}道主习题清单，含范围外章节；现有{checked_count(lib)}道完整题干与核验解析。计数按主习题，不把小问另算一题。',f'{len(lib["items"])} numbered exercises across the full book, including chapters outside exam coverage. {checked_count(lib)} currently have complete statements and checked solutions. Subparts are not counted as separate main exercises.','p')
    body+=bi('“清单已核对”只表示题号与来源页已收录，不表示题干已抄录或答案已完成。部分章的范围需要逐题确认。','“Inventory checked” means that an ID and source page are indexed; it does not mean the statement or solution is complete. Coverage in partially taught chapters needs individual mapping.','p','scope-note')
    if partial_count(lib):body+=bi(f'另有{partial_count(lib)}道题提供部分小问解析；未完成的小问及原因随题列出，未计入完整题数。',f'A further {partial_count(lib)} exercises have checked solutions for some subparts. Pending parts and reasons are listed explicitly and excluded from the complete count.','p','scope-note')
    chapters=lib['chapters']
    body+='<div class="library-filters"><label for="chapter-filter">'+bi('章节','Chapter','span')+'</label><select id="chapter-filter"><option value="all">全部 · All</option>'+''.join(f'<option value="{ch["number"]}">{ch["number"]} · {esc(ch["title"]["zh"])} · {esc(ch["title"]["en"])}</option>' for ch in chapters)+'</select><label for="status-filter">'+bi('显示','Show','span')+'</label><select id="status-filter"><option value="all">全书清单 · Full inventory</option><option value="homework" selected>指定作业 · Assigned</option><option value="solved">已有解析（含部分） · Available solutions</option><option value="complete">完整解析 · Complete solutions</option><option value="partial">部分小问解析 · Partial solutions</option><option value="pending">尚未完整 · Not complete</option><option value="weak">重做 · Revisit</option></select><label for="exercise-search">'+bi('题号','Exercise ID','span')+'</label><input id="exercise-search" type="search" placeholder="1-5 · 2.3.2" autocomplete="off"><output id="filter-count" aria-live="polite"></output><div><button data-export-progress>'+bi('导出练习记录','Export progress','span')+'</button><label class="import-label">'+bi('导入记录','Import progress','span')+'<input type="file" data-import-progress accept="application/json"></label></div></div>'
    body+='<p id="progress-message" role="status"></p><div class="exercise-list">'
    for ex in lib['items']:
        id=ex['id'];sol=solutions.get(id); hw=ex.get('priorityHomework',False)
        badge=bi('指定作业' if hw else '全书习题','Assigned' if hw else 'Book exercise','span','exercise-badge')
        state=bi(('已抄题并核验解析' if complete(sol) else '部分小问已核验') if sol else '清单已核对 · 题干与解析待整理',('Transcribed & solution checked' if complete(sol) else 'Some subparts checked') if sol else 'Inventory checked · transcription and solution pending','span','status')
        body+=f'<details class="exercise-item" id="{id}" data-id="{id}" data-chapter="{ex["chapter"]}" data-homework="{str(hw).lower()}" data-solved="{str(bool(sol)).lower()}" data-complete="{str(complete(sol)).lower()}"><summary><strong>{esc(ex["bookId"])}</strong>{badge}{state}</summary><div class="exercise-content">'
        src=ex.get('printedPage','?');pdf=ex.get('pdfPage','?')
        body+=bi(f'来源：{c["book"]} · 书第{src}页／PDF第{pdf}页。范围状态：{ex.get("scopeLabelZh","待逐题映射")}。',f'Source: {lib["sourceTitleEn"]} · printed p. {src} · PDF p. {pdf}. Coverage: {ex.get("scopeLabelEn","individual mapping pending")}.','p','source-line')
        if hw and ex.get('assignedNote'):body+=bi('指定要求：'+ex['assignedNote'],'Assigned requirement: '+ex.get('assignedNoteEn',ex['assignedNote']),'p')
        if sol:
            body+=b(sol['title'],'h3')+bi('题目原文','Transcribed question','h4')+b(sol['statement'],'p')
            if sol.get('completionNote'):body+=b(sol['completionNote'],'p','source-line')
            if sol.get('figure'):
                source_caption={'zh':'教材原题截图；版本与页码见本题来源。','en':'Original textbook statement crop; see this exercise’s edition and page references.'} if sol['diagram'].get('kind')=='statement-crop' else None
                body+=figure(sol['figure'],sol['diagram']['alt']['zh']+' · '+sol['diagram']['alt']['en'],source=True,caption_text=source_caption)+b(sol['diagram']['alt'],'p','diagram-description')
            if sol.get('source',{}).get('figurePdfPage'):body+=bi(f'本题图在书第{sol["source"]["figurePrintedPage"]}页／PDF第{sol["source"]["figurePdfPage"]}页。',f'The source figure is on printed p. {sol["source"]["figurePrintedPage"]} · PDF p. {sol["source"]["figurePdfPage"]}.','p','source-line')
            hint=(bi('前置知识','Prerequisites','h4')+b(sol['prerequisites']) if isinstance(sol.get('prerequisites'),dict) else '')+b(sol['recognition'])
            body+=reveal('先想：怎么识别与起步','Hint: recognition and first step',hint,kind='hint')
            steps=''
            for st in sol['steps']:
                steps+=b(st['title'],'h4')+b(st['text'],'p')
                if st.get('formula'):steps+=math(st['formula'])
            for diagram in sol.get('solutionDiagrams',[]):
                caption=diagram.get('caption') or ({'zh':'实际SPICE数据；运行条件和模型见本题解析。','en':'Executed SPICE data; see this solution for model and run conditions.'} if diagram.get('kind','').startswith('executed-spice') else None)
                steps+=figure(diagram['figure'],diagram['alt']['zh']+' · '+diagram['alt']['en'],caption_text=caption)+b(diagram['alt'],'p','diagram-description')
            steps+=b(sol['answer'],'p','key')+bi('易错点','Common errors','h4')+'<ul>'+''.join(b(x,'li') for x in sol['pitfalls'])+'</ul>'+bi('核验依据','Verification','h4')
            if isinstance(sol['verification'].get('assumptions'),dict):steps+=b(sol['verification']['assumptions'],'p','scope-note')
            steps+=b(sol['verification']['methods'],'p')
            if sol['verification'].get('externalReferences'):
                steps+=bi('参考模型依据','Model references','h4')+'<ul>'+''.join(f'<li><a href="{esc(ref["url"])}" target="_blank" rel="noopener">{esc(ref["title"])}</a></li>' for ref in sol['verification']['externalReferences'])+'</ul>'
            if sol.get('simulation',{}).get('netlists'):
                steps+=bi('下载SPICE网表','Download SPICE netlists','h4')+'<ul>'+''.join(f'<li><a href="assets/{esc(n["file"])}" download>'+b(n['label'],'span')+'</a></li>' for n in sol['simulation']['netlists'])+'</ul>'
            elif sol.get('simulation',{}).get('netlist'):
                steps+=f'<p><a href="assets/{esc(sol["simulation"]["netlist"])}" download>'+bi('下载本题SPICE网表','Download this exercise’s SPICE netlist','span')+'</a></p>'
            if sol.get('simulation',{}).get('instructions'):steps+=b(sol['simulation']['instructions'],'p','scope-note')
            body+=reveal('完整解析与结果核验' if complete(sol) else '已完成小问的解析与核验','Full solution & verification' if complete(sol) else 'Checked subpart solutions & verification',steps)
            body+=f'<label for="progress-{id}">'+bi('我的练习状态','My practice state','span')+f'<select id="progress-{id}" data-progress="{id}"><option value="new">未做 · Not attempted</option><option value="done">已独立完成 · Completed independently</option><option value="revisit">需要重做 · Revisit</option></select></label>'
        else:
            body+=bi('本题尚未完成题干抄录、图形核对和推导。不会用未核验的自动答案占位。按指定作业优先逐题补齐。','Statement transcription, figure checking and derivation are pending for this item. It has no unverified automatic answer. Assigned homework is prioritized.','p')
        body+='</div></details>'
    body+='</div>'+bi('当前筛选没有匹配题目。','No exercises match these filters.','p','empty-results')
    page(f'{cid}-exercises.html',c['zh']+'教材逐题','<article class="study-paper">'+body+'</article>',cid)
print('Built 10 static pages,',len(lessons),'lessons,',sum(len(p['questions']) for p in papers),'mock questions,',tot,'exercise IDs,',done,'checked solutions.')
