/* PiTV D-pad. Local unpacked Chromium extension. No permissions and no network requests. */
(()=>{'use strict';
let active=null;
const rules=document.createElement('style');
rules.textContent='[data-pitv-selected="yes"]{outline:5px solid #ffe071!important;outline-offset:2px!important;box-shadow:0 0 0 8px rgba(0,0,0,.6)!important;z-index:2147483600!important;position:relative!important}';
(document.head||document.documentElement).appendChild(rules);
const selector='a[href],button,[role="button"],[role="link"],[role="menuitem"],[role="option"],[role="tab"],[role="gridcell"],input:not([type="hidden"]),[tabindex]:not([tabindex="-1"]),[data-uia*="title-card"],[data-testid*="title-card"]';
function elementVisible(el){
 if(!(el instanceof HTMLElement)||el.closest('[aria-hidden="true"],[inert]'))return false;
 let s=getComputedStyle(el); if(s.display==='none'||s.visibility==='hidden'||Number(s.opacity)===0)return false;
 if(el.matches(':disabled')||el.getAttribute('aria-disabled')==='true')return false;
 let r=el.getBoundingClientRect();return r.width>=8&&r.height>=8&&r.width<innerWidth*.98&&r.height<innerHeight*.92&&r.bottom>0&&r.right>0&&r.top<innerHeight&&r.left<innerWidth;
}
function candidates(){
 let found=[...document.querySelectorAll(selector)].filter(elementVisible);
 // Use the most specific actionable child when interactive wrappers overlap.
 return found.filter(el=>!found.some(child=>child!==el&&el.contains(child)&&child.getBoundingClientRect().width>=el.getBoundingClientRect().width*.5&&child.getBoundingClientRect().height>=el.getBoundingClientRect().height*.5)).slice(0,1800);
}
function remember(el){
 if(active && active!==el)active.removeAttribute('data-pitv-selected');
 if(!el)return;active=el;el.setAttribute('data-pitv-selected','yes');
 if(!el.matches('a,button,input,select,textarea,[tabindex]'))el.setAttribute('tabindex','-1');
 try{el.focus({preventScroll:true})}catch(_){};
 el.scrollIntoView({block:'nearest',inline:'nearest',behavior:'instant'});
}
function first(){
 let list=candidates();if(!list.length)return;
 list.sort((a,b)=>{const A=a.getBoundingClientRect(),B=b.getBoundingClientRect();return (A.top-B.top)||A.left-B.left});
 remember(list[0]);
}
function move(dir){
 let list=candidates(); if(!list.length)return false;
 if(!active||!list.includes(active)){first();return true}
 const r=active.getBoundingClientRect();const cx=r.x+r.width/2,cy=r.y+r.height/2;
 let options=[];
 for(const el of list){if(el===active)continue;let v=el.getBoundingClientRect(),x=v.x+v.width/2-cx,y=v.y+v.height/2-cy;
 let forward=dir==='ArrowRight'?x:dir==='ArrowLeft'?-x:dir==='ArrowDown'?y:-y;
 if(forward<=5)continue;
 let sideways=(dir==='ArrowRight'||dir==='ArrowLeft')?Math.abs(y):Math.abs(x);
 const crossLimit=(dir==='ArrowRight'||dir==='ArrowLeft')?Math.max(r.height,v.height)*2:Math.max(r.width,v.width)*2;
 const score=forward+sideways*(sideways<crossLimit?.85:2.6);
 options.push({el,score})}
 if(!options.length)return false;
 options.sort((a,b)=>a.score-b.score);remember(options[0].el);return true;
}
function isPlayer(){
 if(/youtube\.com$/.test(location.hostname)&&location.pathname==='/watch')return true;
 if(/netflix\.com$/.test(location.hostname)&&/\/watch\//.test(location.pathname))return true;
 const vids=[...document.querySelectorAll('video')];
 return vids.some(v=>{const r=v.getBoundingClientRect();return v.readyState>0&&r.width>innerWidth*.65&&r.height>innerHeight*.5&&r.bottom>0});
}
function editable(el){return !!(el&&(el.closest('input,textarea,select,[contenteditable="true"],[role="textbox"]')||el.isContentEditable));}
window.addEventListener('keydown',e=>{
 if(e.altKey||e.ctrlKey||e.metaKey||editable(e.target))return;
 if(e.key==='F9'){e.preventDefault();e.stopImmediatePropagation();first();return;}
 if(!['ArrowUp','ArrowDown','ArrowLeft','ArrowRight','Enter'].includes(e.key))return;
 if(isPlayer())return; // Preserve Netflix video shortcuts (seeking, volume, play/pause).
 if(e.key==='Enter'){
  if(active&&document.contains(active)){e.preventDefault();e.stopImmediatePropagation();active.click();}
  return;
 }
 if(move(e.key)){e.preventDefault();e.stopImmediatePropagation();}
},true);
document.addEventListener('visibilitychange',()=>{if(document.hidden){for(const v of document.querySelectorAll('video')){try{if(!v.paused)v.pause()}catch(_){}}}});
})();
