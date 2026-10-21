const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const src = fs.readFileSync(__dirname+'/pitv-auto-fullscreen.js','utf8');
async function runTest(host,pathname,expected) {
  let calls = 0, onPlaying=null, onVisibility=null, poll=null;
  const node = {getBoundingClientRect:()=>({width:1250,height:700,top:0,left:0,right:1250,bottom:700}), requestFullscreen:()=>{calls++;return Promise.resolve();}};
  const video = {paused:false,ended:false,readyState:4, parentElement: node, closest:()=>null, getBoundingClientRect:()=>({width:1250,height:700,top:0,left:0,right:1250,bottom:700})};
  const document={fullscreenElement:null,body:{},documentElement:{},hidden:false,
    querySelectorAll:(s)=>s==='video'?[video]:[],
    addEventListener:(event,fn)=>{if(event==='playing') onPlaying=fn; if(event==='visibilitychange')onVisibility=fn;}};
  const s={console,document,location:{hostname:host,pathname,href:'https://'+host+pathname},innerWidth:1280,innerHeight:720,
    clearTimeout:()=>{},setTimeout:(fn)=>{fn();return 1;},setInterval:(fn)=>{poll=fn;return 2;}};
  vm.runInNewContext(src,s);
  if(onPlaying)onPlaying();
  if(poll){poll();poll();}
  assert.equal(calls,expected,host+' '+pathname);
}
(async ()=>{
 await runTest('www.netflix.com','/browse',0);
 await runTest('www.netflix.com','/watch/12345',1);
 await runTest('www.disneyplus.com','/play/abc',1);
 await runTest('www.disneyplus.com','/home',0);
 await runTest('example.org','/watch/1',0);
 console.log('Video detection tests PASS: Netflix playback, Netflix browse, Disney playback, Disney home, unrelated sites');
})().catch(e=>{console.error(e);process.exit(1)});
