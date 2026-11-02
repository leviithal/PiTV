/* PiTV 3.3.1: vertical-scroll fallback, guarded Netflix play-intent.
 * Runs ONLY on Netflix/Disney+ through PiTV extension manifest.
 * Does not read or transmit credentials, DRM, cookies or video content.
 */
(() => {
  'use strict';
  if (globalThis.__pitvDpadV331Loaded) return;
  globalThis.__pitvDpadV331Loaded = true;
  const core = globalThis.PiTVNavCore;
  if (!core) { console.warn('PiTV: navigation-core.js saknas'); return; }
  const NETFLIX = /(^|\.)netflix\.com$/i.test(location.hostname);
  const DISNEY = /(^|\.)disneyplus\.com$/i.test(location.hostname);
  const SELECTOR = [
    'a[href]', 'button', '[role="button"]', '[role="link"]', '[role="menuitem"]',
    '[role="option"]', '[role="tab"]', '[role="gridcell"]',
    'input:not([type="hidden"])', '[tabindex]:not([tabindex="-1"])',
    '[data-uia*="title-card"]', '[data-testid*="title-card"]'
  ].join(',');
  const ATTR='data-pitv-focus-v33'; // preserve CSS and old DOM test expectations
  const INTENT_KEY='pitv-netflix-play-intent-v331';
  const PLAY_WINDOW_MS=2800;
  let current=null, lastUrl=location.href, followup=null;
  const style=document.createElement('style');
  style.textContent=`[${ATTR}="1"]{outline:4px solid #ffdf72!important;outline-offset:3px!important;box-shadow:0 0 0 7px rgba(0,0,0,.54)!important;border-radius:7px!important}`;
  (document.head||document.documentElement).appendChild(style);

  const editable = node => Boolean(node?.closest?.('input,textarea,select,[role="textbox"],[contenteditable="true"]') || node?.isContentEditable);
  function playerActive() {
    if (NETFLIX && /^\/watch\//.test(location.pathname)) return true;
    const fullscreen=document.fullscreenElement;
    if(fullscreen?.querySelector?.('video') || fullscreen?.matches?.('video')) return true;
    if (!/(?:^|\/)(?:play|video|watch)(?:\/|$)/i.test(location.pathname)) return false;
    for (const v of document.querySelectorAll('video')) {
      if(v.paused || v.ended || v.readyState<2) continue;
      const r=v.getBoundingClientRect();
      if(r.width>=innerWidth*.70 && r.height>=innerHeight*.47 && r.bottom>0 && r.top<innerHeight) return true;
    }
    return false;
  }
  function visible(el, checkOcclusion=true) {
    if(!(el instanceof HTMLElement) || !el.isConnected || el.closest('[aria-hidden="true"],[inert]')) return false;
    if(el.matches(':disabled') || el.getAttribute('aria-disabled')==='true') return false;
    const s=getComputedStyle(el);
    if(s.display==='none'||s.visibility==='hidden'||Number(s.opacity)===0||s.pointerEvents==='none') return false;
    const r=el.getBoundingClientRect();
    if(r.width<9||r.height<9||r.width>innerWidth*.985||r.height>innerHeight*.94) return false;
    if(r.bottom<=0||r.top>=innerHeight||r.right<=0||r.left>=innerWidth) return false;
    if(checkOcclusion){
      const x=Math.max(2,Math.min(innerWidth-3,r.left+r.width/2));
      const y=Math.max(2,Math.min(innerHeight-3,r.top+r.height/2));
      const onTop=document.elementFromPoint(x,y);
      if(onTop&&!el.contains(onTop)&&!onTop.contains(el)) return false;
    }
    return true;
  }
  function modalScope() {
    const dialogs=[...document.querySelectorAll('[role="dialog"],dialog[open],[aria-modal="true"]')];
    return dialogs.reverse().find(el=>{
      const s=getComputedStyle(el),r=el.getBoundingClientRect();
      return s.display!=='none'&&s.visibility!=='hidden'&&r.width>0&&r.height>0&&r.bottom>0&&r.top<innerHeight;
    })||document;
  }
  function candidates() {
    const elements=[...modalScope().querySelectorAll(SELECTOR)].filter(el=>visible(el));
    const pool=new Set(elements),drop=new Set();
    for(const child of elements){
      const r=child.getBoundingClientRect();let parent=child.parentElement,depth=0;
      while(parent&&depth++<8){
        if(pool.has(parent)){
          const p=parent.getBoundingClientRect();
          if((r.width>=p.width*.5&&r.height>=p.height*.5) ||
             ((child.matches('a[href],button,[role="button"]')) && r.width>=p.width*.10 && r.height>=p.height*.10))drop.add(parent);
        }
        parent=parent.parentElement;
      }
    }
    return elements.filter(el=>!drop.has(el)).slice(0,1000);
  }
  function clearFocus(){if(current?.isConnected)current.removeAttribute(ATTR);current=null;}
  function select(el){
    if(!el)return false;
    if(current&&current!==el)current.removeAttribute(ATTR);
    current=el;current.setAttribute(ATTR,'1');
    if(/^(A|BUTTON|INPUT|SELECT|TEXTAREA)$/.test(el.tagName)||el.hasAttribute('tabindex')) {
      try{el.focus({preventScroll:true});}catch(_){ }
    }
    el.scrollIntoView({block:'nearest',inline:'nearest',behavior:'instant'});
    return true;
  }
  function first(items){
    const ordered=[...items].sort((a,b)=>{
      const x=a.getBoundingClientRect(),y=b.getBoundingClientRect();return (x.top-y.top)||(x.left-y.left);
    });
    return select(ordered[0]);
  }
  function refreshRoute(){
    if(lastUrl!==location.href){lastUrl=location.href;clearFocus();}
    if(current&&!current.isConnected)clearFocus();
    if(playerActive())clearFocus();
  }
  function canScroll(el, direction){
    const vertical=direction==='ArrowDown'||direction==='ArrowUp';
    if(!vertical && direction!=='ArrowLeft' && direction!=='ArrowRight')return false;
    const remaining=vertical?el.scrollHeight-el.clientHeight:el.scrollWidth-el.clientWidth;
    if(remaining<18)return false;
    const currentPos=vertical?el.scrollTop:el.scrollLeft;
    const max=remaining;
    const sign=(direction==='ArrowDown'||direction==='ArrowRight')?1:-1;
    return sign>0 ? currentPos<max-4 : currentPos>4;
  }
  // Disney+ frequently places its scrollable view outside the selected card's
  // ancestor chain. Search the *visible* scroll containers as a fallback.
  // CSS overflow:hidden is included: DOM scrollTop can still be moved directly.
  function scrollForMore(direction){
    if(!current)return false;
    const vertical=direction==='ArrowDown'||direction==='ArrowUp';
    const r=current.getBoundingClientRect();
    const containers=[],seen=new Set();
    function add(el,priority){
      if(!el||seen.has(el)||!canScroll(el,direction))return;
      seen.add(el);
      const rect=el===document.scrollingElement?
        {left:0,top:0,right:innerWidth,bottom:innerHeight,width:innerWidth,height:innerHeight}:
        el.getBoundingClientRect();
      if(rect.width<90||rect.height<90||rect.bottom<=0||rect.top>=innerHeight)return;
      const overlap=Math.max(0,Math.min(rect.right,r.right)-Math.max(rect.left,r.left));
      const distance=Math.abs((rect.left+rect.right)/2-(r.left+r.right)/2);
      containers.push({el,rank:priority+(overlap>20?80:0)-distance*.06});
    }
    let parent=current.parentElement,depth=0;
    while(parent&&depth++<25){add(parent,200-depth);parent=parent.parentElement;}
    add(document.scrollingElement,95);
    // Only search the broader layout if no direct scroll parent can advance.
    // Bound the query to avoid scanning a huge Netflix/Disney DOM indefinitely.
    if(vertical && !containers.some(c=>c.rank>=180)){
      const nodes=document.querySelectorAll('main,[role="main"],section,div,[data-testid],[data-uia]');
      const count=Math.min(nodes.length,2500);
      for(let i=0;i<count;i++){
        const el=nodes[i];
        if(el.clientHeight<innerHeight*.27 || el.clientWidth<innerWidth*.32)continue;
        add(el,40);
      }
    }
    containers.sort((a,b)=>b.rank-a.rank);
    const sign=(direction==='ArrowDown'||direction==='ArrowRight')?1:-1;
    for(const {el} of containers){
      const old=vertical?el.scrollTop:el.scrollLeft;
      const delta=(vertical?el.clientHeight:el.clientWidth)*.72*sign;
      if(vertical)el.scrollTop=old+delta;
      else el.scrollLeft=old+delta;
      const next=vertical?el.scrollTop:el.scrollLeft;
      if(Math.abs(next-old)>3)return true;
    }
    return false;
  }
  function selectAfterScroll(beforeRect,direction){
    if(playerActive())return;
    const list=candidates();
    if(!list.length)return;
    if(current && visible(current)){
      const next=core.next(list,current,direction);
      if(next){select(next);return;}
    }
    const goingDown=direction==='ArrowDown';
    const ordered=list.filter(el=>el!==current).map(el=>{
      const r=el.getBoundingClientRect();
      return {el, score:Math.abs((r.left+r.right)/2-(beforeRect.left+beforeRect.right)/2)*.4+
        Math.abs(r.top-beforeRect.top)+
        ((goingDown?r.top<beforeRect.top-120:r.top>beforeRect.top+120)?300:0)};
    }).sort((a,b)=>a.score-b.score);
    if(ordered.length)select(ordered[0].el);
  }
  function move(direction){
    refreshRoute();
    const items=candidates();
    if(!items.length)return false;
    if(!current||!items.includes(current))return first(items);
    const next=core.next(items,current,direction);
    if(next)return select(next);
    const rect=current.getBoundingClientRect();
    if(scrollForMore(direction)){
      clearTimeout(followup);
      followup=setTimeout(()=>selectAfterScroll(rect,direction),240);
      return true;
    }
    return false; // allow native arrow behavior if no custom scroll possible
  }
  function titleCard(el){
    if(!NETFLIX)return false;
    return Boolean(el.closest('[data-uia*="title-card"],[data-testid*="title-card"],.title-card,.slider-item,.title-card-container,[class*="title-card"]'));
  }
  function playButton(){
    // Only buttons explicitly labelled "Play/Spela" in a *visible detail panel*.
    // Never click preview/trailer or generic card-play actions on the browse page.
    const dialog=modalScope();
    const scope=dialog!==document?dialog:document.querySelector('[data-uia*="previewModal"],[class*="previewModal--container"],[class*="detailModal"]');
    if(!scope)return null;
    const buttons=[...scope.querySelectorAll('button,[role="button"]')];
    return buttons.find(btn=>{
      if(!visible(btn,false))return false;
      const label=[btn.getAttribute('aria-label'),btn.getAttribute('title'),btn.getAttribute('data-uia'),btn.textContent]
        .filter(Boolean).join(' ').trim();
      const text=label.toLocaleLowerCase();
      if(/trailer|preview|förhandsvisning|snabbtitt|teaser|information|mer info/.test(text))return false;
      return /(?:^|\b)(play|spela|spela upp)(?:\b|$)/i.test(text) || /play-button|playbtn/i.test(text);
    })||null;
  }
  let intentTimer=null;
  function tryAutoplay(){
    if(!NETFLIX||playerActive())return false;
    const deadline=Number(sessionStorage.getItem(INTENT_KEY)||0);
    if(!deadline||Date.now()>deadline){sessionStorage.removeItem(INTENT_KEY);return false;}
    const button=playButton();
    if(!button)return false;
    sessionStorage.removeItem(INTENT_KEY);clearTimeout(intentTimer);
    button.click(); // best effort; Chromium may require a fresh trusted gesture
    return true;
  }
  function scheduleAutoplay(){
    if(!NETFLIX)return;
    const deadline=Date.now()+PLAY_WINDOW_MS;
    try{sessionStorage.setItem(INTENT_KEY,String(deadline));}catch(_){return;}
    clearTimeout(intentTimer);
    let tries=0;
    function check(){
      if(tryAutoplay())return;
      if(++tries<13 && Date.now()<deadline)intentTimer=setTimeout(check,200);
    }
    intentTimer=setTimeout(check,120);
  }
  // A full page transition after selecting a card can still reveal the detail
  // panel; sessionStorage preserves the short-lived user intent on Netflix only.
  if(NETFLIX){
    setTimeout(tryAutoplay,180);
    window.addEventListener('pageshow',tryAutoplay);
  }
  function activate(){
    refreshRoute();
    if(!current||!visible(current))return first(candidates());
    if(editable(current))return false;
    if(NETFLIX && titleCard(current))scheduleAutoplay();
    const link = current.closest?.('a[target="_blank"]');
    if(NETFLIX && link instanceof HTMLAnchorElement){
      try{
        const dest=new URL(link.href,location.href);
        if(dest.hostname===location.hostname && dest.protocol==='https:'){
          location.assign(dest.href);return true; // no extra Chromium window for same-site links
        }
      }catch(_){ }
    }
    current.click();
    return true;
  }
  window.addEventListener('keydown',event=>{
    if(event.altKey||event.ctrlKey||event.metaKey||editable(event.target)||playerActive())return;
    if(event.key==='F9'){
      event.preventDefault();event.stopImmediatePropagation();first(candidates());return;
    }
    if(!['ArrowUp','ArrowDown','ArrowLeft','ArrowRight','Enter'].includes(event.key))return;
    const handled=event.key==='Enter'?activate():move(event.key);
    if(handled){event.preventDefault();event.stopImmediatePropagation();}
  },true);
  window.addEventListener('popstate',refreshRoute);
  window.addEventListener('hashchange',refreshRoute);
  document.addEventListener('pointerdown',event=>{
    const chosen=event.target?.closest?.(SELECTOR);
    if(chosen&&visible(chosen))select(chosen);
  },true);
  document.addEventListener('visibilitychange',()=>{if(document.hidden)clearFocus();});
})();
