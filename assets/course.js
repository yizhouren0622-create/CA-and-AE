(() => {
  'use strict';
  const KEY='ca-ae-progress-v1';
  let state={version:1,exercises:{},scores:{},timers:{}};
  try {
    const saved=JSON.parse(localStorage.getItem(KEY)||'null');
    if(saved?.version===1) for(const k of ['exercises','scores','timers']) if(saved[k] && typeof saved[k]==='object' && !Array.isArray(saved[k])) state[k]=saved[k];
  } catch {}
  function save(){try{localStorage.setItem(KEY,JSON.stringify(state));}catch{message('当前浏览器无法保存记录，请导出备份。','This browser cannot save progress; export a backup.');}}
  function bilingual(zh,en,tag='div') {
    const el=document.createElement(tag);
    for(const [lang,value] of [['zh',zh],['en',en]]) {
      const span=document.createElement('span'); span.dataset.lang=lang; span.lang=lang==='zh'?'zh-CN':'en';span.textContent=value;el.append(span);
    } return el;
  }
  function message(zh,en) {
    const el=document.querySelector('#progress-message');
    if(el) el.replaceChildren(bilingual(zh,en));
  }
  const scoreUpdaters=[];
  for(const diagnostic of document.querySelectorAll('[data-paper]')) {
  const scoreInputs=[...diagnostic.closest('[data-exam]').querySelectorAll('[data-score]')];
  function updateScores() {
    if(!diagnostic)return;
    let sum=0,count=0,scoredMax=0;const weak=new Map();
    const total=scoreInputs.reduce((n,el)=>n+Number(el.closest('.question').dataset.points),0);
    for(const el of scoreInputs) {
      const saved=state.scores[el.dataset.score];
      const max=Number(el.closest('.question').dataset.points);
      el.value=Number.isInteger(saved)&&saved>=0&&saved<=max?String(saved):'';
      if(el.value==='')continue;
      sum+=Number(el.value);count++;scoredMax+=max;
      if(Number(el.value)<0.7*max)for(const topic of el.closest('.question').dataset.topics.split(',')) {
        const a=el.closest('.question').querySelector('.topic-links a[href$="#'+topic+'"]');
        if(a)weak.set(topic,a);
      }
    }
    diagnostic.querySelector('[data-score-summary]').replaceChildren(bilingual(
      '已自评 '+count+' 题（共'+scoreInputs.length+'题），已评得分 '+sum+' 分（已评题满分 '+scoredMax+' 分，全卷'+total+'分）。低于该题70%分值时提示回看知识点。',
      count+' of '+scoreInputs.length+' questions self-scored; '+sum+' points out of '+scoredMax+' on scored questions ('+total+' for the full paper). Scores below 70% flag topics to revisit.'
    ));
    const box=diagnostic.querySelector('[data-weak-topics]');box.replaceChildren();
    if(!count)box.append(bilingual('完成题目后按解析评分，薄弱知识点会显示在这里。','Self-score after working the questions; topics to revisit will appear here.'));
    else if(weak.size) {
      box.append(bilingual('建议回看：','Suggested review:'));
      for(const a of weak.values())box.append(a.cloneNode(true));
    } else box.append(bilingual('已评题目均达到7分；继续完成尚未评分的题目。','All scored questions reached 7 points; continue with any unscored questions.'));
  }
  for(const el of scoreInputs) el.addEventListener('change',()=>{
    if(el.value==='')delete state.scores[el.dataset.score];else state.scores[el.dataset.score]=Number(el.value);
    save();updateScores();
  });
  updateScores();
  scoreUpdaters.push(updateScores);
  if(diagnostic) {
    const id=diagnostic.dataset.paper;
    let timer=state.timers[id];
    if(!timer || !Number.isFinite(timer.elapsed) || timer.elapsed<0)timer={elapsed:0,startedAt:null};
    if(!Number.isFinite(timer.startedAt))timer.startedAt=null;
    state.timers[id]=timer;
    const elapsed=()=>timer.elapsed+(timer.startedAt===null?0:Math.max(0,Date.now()-timer.startedAt));
    const start=diagnostic.querySelector('[data-timer-start]'),pause=diagnostic.querySelector('[data-timer-pause]');
    function renderTimer() {
      const sec=Math.floor(elapsed()/1000),min=Math.floor(sec/60);
      diagnostic.querySelector('[data-timer]').textContent=String(min).padStart(2,'0')+':'+String(sec%60).padStart(2,'0');
      start.disabled=timer.startedAt!==null;pause.disabled=timer.startedAt===null;
    }
    start.addEventListener('click',()=>{if(timer.startedAt===null){timer.startedAt=Date.now();save();renderTimer();}});
    pause.addEventListener('click',()=>{if(timer.startedAt!==null){timer.elapsed=elapsed();timer.startedAt=null;save();renderTimer();}});
    renderTimer();setInterval(renderTimer,1000);
  }
  }
  const exercises=[...document.querySelectorAll('.exercise-item')];
  const chapter=document.querySelector('#chapter-filter'),status=document.querySelector('#status-filter'),search=document.querySelector('#exercise-search');
  const progressInputs=[...document.querySelectorAll('[data-progress]')];
  function restoreProgress() {
    for(const el of progressInputs)el.value=['new','done','revisit'].includes(state.exercises[el.dataset.progress])?state.exercises[el.dataset.progress]:'new';
  }
  function filter() {
    if(!chapter)return;
    const query=search.value.trim().toLowerCase();let visible=0;
    for(const ex of exercises) {
      const mode=status.value,solved=ex.dataset.solved==='true',complete=ex.dataset.complete==='true';
      const matching=(chapter.value==='all'||chapter.value===ex.dataset.chapter)
        &&(!query||ex.dataset.id.toLowerCase().includes(query))
        &&(mode==='all'||mode==='homework'&&ex.dataset.homework==='true'||mode==='solved'&&solved||mode==='complete'&&complete||mode==='partial'&&solved&&!complete||mode==='pending'&&!complete||mode==='weak'&&state.exercises[ex.dataset.id]==='revisit');
      ex.hidden=!matching;if(matching)visible++;
    }
    document.querySelector('#filter-count').replaceChildren(bilingual(visible+'道 · 共'+exercises.length+'道',visible+' shown · '+exercises.length+' total','span'));
  }
  for(const el of progressInputs)el.addEventListener('change',()=>{state.exercises[el.dataset.progress]=el.value;save();filter();});
  for(const el of [chapter,status,search])if(el)el.addEventListener(el===search?'input':'change',filter);
  restoreProgress();filter();
  function openHash() {
    if(!chapter||!location.hash)return;
    let id;try{id=decodeURIComponent(location.hash.slice(1));}catch{return;}
    const ex=document.getElementById(id);
    if(ex?.classList.contains('exercise-item')) {
      chapter.value='all';status.value='all';search.value='';filter();ex.open=true;
      requestAnimationFrame(()=>ex.scrollIntoView({block:'start'}));
    }
  }
  window.addEventListener('hashchange',openHash);openHash();
  const exporter=document.querySelector('[data-export-progress]');
  if(exporter)exporter.addEventListener('click',()=>{
    const blob=new Blob([JSON.stringify({...state,exportedAt:new Date().toISOString()},null,2)],{type:'application/json'});
    const url=URL.createObjectURL(blob),a=document.createElement('a');
    a.href=url;a.download='ca-ae-progress.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
    message('练习记录已导出。','Progress exported.');
  });
  const importer=document.querySelector('[data-import-progress]');
  if(importer)importer.addEventListener('change',async()=>{
    const file=importer.files?.[0];if(!file)return;
    try {
      if(file.size>200000)throw new Error('size');
      const obj=JSON.parse(await file.text());
      if(obj.version!==1||typeof obj.exercises!=='object'||obj.exercises===null||typeof obj.scores!=='object'||obj.scores===null)throw new Error('schema');
      const nextEx={},nextScores={};
      for(const [k,v] of Object.entries(obj.exercises))if(/^(CA-\d+-\d+|AE-\d+\.\d+\.\d+)$/.test(k)&&['new','done','revisit'].includes(v))nextEx[k]=v;
      for(const [k,v] of Object.entries(obj.scores))if(/^(ca|ae)-(?:b-)?q(?:[1-9]|10)$/.test(k)&&Number.isInteger(v)&&v>=0&&v<=10)nextScores[k]=v;
      state.exercises={...state.exercises,...nextEx};state.scores={...state.scores,...nextScores};
      save();restoreProgress();filter();for(const update of scoreUpdaters)update();message('记录已导入并合并。','Progress imported and merged.');
    }catch{message('文件格式不正确，原有记录已保留。','Invalid file format; existing progress was preserved.');}
    importer.value='';
  });
  const menu=document.querySelector('.site-menu-btn'),top=document.querySelector('.site-top');
  document.addEventListener('keydown',e=>{if(e.key==='Escape'&&top?.classList.contains('open')){top.classList.remove('open');menu.setAttribute('aria-expanded','false');menu.focus();}});
})();
