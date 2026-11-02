/* PiTV 3.3 – directional TV navigation for Netflix / Disney+ web UIs.
 * Scope: visible, actionable DOM nodes only. Never changes streaming, DRM,
 * URLs, site storage, app credentials, or the PiTV API. No network requests.
 * Netflix/Disney can change their markup: no guarantee of native-TV parity.
 */
(() => {
  'use strict';
  if (globalThis.__pitvDpadV33Loaded) return;
  globalThis.__pitvDpadV33Loaded=true;
  const core=globalThis.PiTVNavCore;
  if (!core) { console.warn('PiTV: navigation-core.js saknas'); return; }
  const SELECTOR=[
    'a[href]', 'button', '[role="button"]', '[role="link"]', '[role="menuitem"]',
    '[role="option"]','[role="tab"]','[role="gridcell"]',
    'input:not([type="hidden"])','[tabindex]:not([tabindex="-1"])',
    '[data-uia*="title-card"]','[data-testid*="title-card"]'
  ].join(',');
  const ATTR='data-pitv-focus-v33';
  let current=null;
  let lastUrl=location.href;
  let followup=null;
  const style=document.createElement('style');
  style.textContent=`[${ATTR}="1"]{outline:4px solid #ffdf72!important;outline-offset:3px!important;box-shadow:0 0 0 7px rgba(0,0,0,.54)!important;border-radius:7px!important}`;
  (document.head||document.documentElement).appendChild(style);

  const editable = (node) => Boolean(node?.closest?.('input,textarea,select,[role="textbox"],[contenteditable="true"]')||node?.isContentEditable);
  function playerActive() {
    if (/netflix\.com$/.test(location.hostname) && /^\/watch\//.test(location.pathname)) return true;
    // Do not steal shortcuts while a full-screen player is open.
    const fullscreen=document.fullscreenElement;
    if(fullscreen?.querySelector?.('video')||fullscreen?.matches?.('video'))return true;
    if (!/(?:^|\/)(?:play|video|watch)(?:\/|$)/i.test(location.pathname)) return false;
    for(const v of document.querySelectorAll('video')){
      if(v.paused||v.ended||v.readyState<2)continue;
      const r=v.getBoundingClientRect();
      if(r.width >= innerWidth*.70 && r.height >= innerHeight*.47 && r.bottom>0 && r.top<innerHeight)return true;
    }
    return false;
  }
  function visible(el, allowOcclusionCheck=true) {
    if(!(el instanceof HTMLElement) || !el.isConnected || el.closest('[aria-hidden="true"],[inert]'))return false;
    if(el.matches(':disabled')||el.getAttribute('aria-disabled')==='true')return false;
    const s=getComputedStyle(el);
    if(s.display==='none'||s.visibility==='hidden'||Number(s.opacity)===0||s.pointerEvents==='none')return false;
    const r=el.getBoundingClientRect();
    if(r.width<9||r.height<9||r.width>innerWidth*.985||r.height>innerHeight*.94)return false;
    if(r.bottom<=0||r.top>=innerHeight||r.right<=0||r.left>=innerWidth)return false;
    if(allowOcclusionCheck) {
      const x=Math.max(2,Math.min(innerWidth-3,r.left+r.width/2));
      const y=Math.max(2,Math.min(innerHeight-3,r.top+r.height/2));
      const onTop=document.elementFromPoint(x,y);
      if(onTop&&!el.contains(onTop)&&!onTop.contains(el))return false;
    }
    return true;
  }
  function modalScope() {
    const dialogs=[...document.querySelectorAll('[role="dialog"],dialog[open],[aria-modal="true"]')];
    return dialogs.reverse().find(el=>{
      const s=getComputedStyle(el),r=el.getBoundingClientRect();
      return s.display!=='none' && s.visibility!=='hidden' && r.width>0 && r.height>0 &&
        r.bottom>0 && r.top<innerHeight && r.right>0 && r.left<innerWidth;
    })||document;
  }
  function candidates() {
    const elements=[...modalScope().querySelectorAll(SELECTOR)].filter(el=>visible(el));
    // Avoid parent/child duplicates with a bounded ancestor walk (not O(n^2)).
    const pool=new Set(elements),drop=new Set();
    for(const child of elements){
      const r=child.getBoundingClientRect();let parent=child.parentElement,depth=0;
      while(parent && depth++<8){
        if(pool.has(parent)){
          const p=parent.getBoundingClientRect();
          if(r.width>=p.width*.5 && r.height>=p.height*.5)drop.add(parent);
        }
        parent=parent.parentElement;
      }
    }
    return elements.filter(el=>!drop.has(el)).slice(0,1000);
  }
  function clearFocus() {
    if(current?.isConnected)current.removeAttribute(ATTR);
    current=null;
  }
  function select(el) {
    if(!el)return false;
    if(current && current!==el) current.removeAttribute(ATTR);
    current=el;
    current.setAttribute(ATTR,'1');
    const nativeFocus=/^(A|BUTTON|INPUT|SELECT|TEXTAREA)$/.test(el.tagName)||el.hasAttribute('tabindex');
    if(nativeFocus)try{el.focus({preventScroll:true});}catch(_){}
    el.scrollIntoView({block:'nearest',inline:'nearest',behavior:'instant'});
    return true;
  }
  function first(items) {
    const ordered=[...items].sort((a,b)=>{
      const x=a.getBoundingClientRect(),y=b.getBoundingClientRect();
      return (x.top-y.top)||(x.left-y.left);
    });
    return select(ordered[0]);
  }
  function refreshRoute() {
    if(lastUrl!==location.href){lastUrl=location.href;clearFocus();}
    if(current && !current.isConnected)clearFocus();
    if(playerActive())clearFocus();
  }
  function scrollForMore(direction) {
    if(!current)return false;
    let node=current.parentElement;
    const horizontal=direction==='ArrowRight'||direction==='ArrowLeft';
    const sign=direction==='ArrowRight'||direction==='ArrowDown'?1:-1;
    while(node && node!==document.documentElement){
      const cs=getComputedStyle(node);
      const overflow=horizontal?cs.overflowX:cs.overflowY;
      const remaining=horizontal?node.scrollWidth-node.clientWidth:node.scrollHeight-node.clientHeight;
      if(remaining>12 && /(auto|scroll)/.test(overflow)){
        const delta=(horizontal?node.clientWidth:node.clientHeight)*.7*sign;
        node.scrollBy(horizontal?{left:delta,behavior:'instant'}:{top:delta,behavior:'instant'});
        return true;
      }
      node=node.parentElement;
    }
    if(!horizontal && document.scrollingElement?.scrollHeight>innerHeight+12){
      window.scrollBy({top:innerHeight*.67*sign,behavior:'instant'});
      return true;
    }
    return false;
  }
  function move(direction) {
    refreshRoute();
    const items=candidates();
    if(!items.length)return false;
    if(!current||!items.includes(current))return first(items);
    const next=core.next(items,current,direction);
    if(next)return select(next);
    if(scrollForMore(direction)){
      clearTimeout(followup);
      const prior=current;
      followup=setTimeout(()=>{
        if(playerActive())return;
        const more=candidates(), found=core.next(more,prior,direction);
        if(found)select(found);
      },180);
      return true;
    }
    return false;
  }
  function activate() {
    refreshRoute();
    if(!current||!visible(current)){return first(candidates());}
    if(editable(current))return false; // Let native input handle Enter.
    current.click();
    // SPA navigation can take time; next D-pad event refreshes stale selection.
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
  document.addEventListener('visibilitychange',()=>{
    if(document.hidden)clearFocus();
  });
})();
