/* PiTV 3.3 – small, pure spatial navigation helpers. No network access. */
(() => {
  'use strict';
  const center = (r) => ({x:r.left+r.width/2, y:r.top+r.height/2});
  const score = (from, to, direction) => {
    const a=center(from), b=center(to);
    const dx=b.x-a.x, dy=b.y-a.y;
    let forward, sideways, measure;
    if (direction==='ArrowRight') { forward=dx; sideways=Math.abs(dy); measure=Math.max(from.height,to.height); }
    else if (direction==='ArrowLeft') { forward=-dx; sideways=Math.abs(dy); measure=Math.max(from.height,to.height); }
    else if (direction==='ArrowDown') { forward=dy; sideways=Math.abs(dx); measure=Math.max(from.width,to.width); }
    else if (direction==='ArrowUp') { forward=-dy; sideways=Math.abs(dx); measure=Math.max(from.width,to.width); }
    else return null;
    if(forward<=5) return null;
    // Same row/column strongly preferred; wide jumps are possible, but costly.
    const penalty = sideways <= measure * 0.9 ? 0.55 : 2.9;
    return forward + sideways * penalty;
  };
  const next = (items, selected, direction) => {
    if (!selected) return null;
    let best=null, bestScore=Infinity;
    for (const item of items) {
      if(item===selected)continue;
      const s=score(selected.getBoundingClientRect(),item.getBoundingClientRect(),direction);
      if(s!==null && s<bestScore){bestScore=s;best=item;}
    }
    return best;
  };
  const exported=Object.freeze({score,next});
  if(typeof module!=='undefined' && module.exports) module.exports=exported;
  else globalThis.PiTVNavCore=exported;
})();
