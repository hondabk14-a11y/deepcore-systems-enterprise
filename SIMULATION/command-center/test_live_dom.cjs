'use strict';
// Dependency-free frontend behavior smoke harness. Not a browser layout or accessibility test.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
class El{
 constructor(tag='div'){this.tagName=tag;this.children=[];this.handlers={};this.attributes={};this.style={};this.dataset={};this.textContent='';this.value='';this.checked=true;this.disabled=false;this.classes=new Set();this.classList={toggle:(v,on)=>{if(on===undefined? !this.classes.has(v):on)this.classes.add(v);else this.classes.delete(v)},add:v=>this.classes.add(v)};}
 setAttribute(k,v){this.attributes[k]=v;if(k==='class')v.split(' ').forEach(x=>this.classes.add(x));if(k==='data-id')this.dataset.id=v;}
 getAttribute(k){return this.attributes[k]}
 append(...v){this.children.push(...v)}
 replaceChildren(...v){this.children=[...v]}
 addEventListener(k,fn){this.handlers[k]=fn}
 scrollIntoView(){}
 click(){this.clicked=true}
 closest(){return this}
}
const registry={},els=new Map();function get(id){if(!els.has(id))els.set(id,new El());return els.get(id)}
get('source').value='demo';get('timeWindow').value='live';get('eventFilter').value='ALL';get('animations').checked=true;
const document={getElementById:get,createElement:tag=>new El(tag),createElementNS:(ns,tag)=>{const el=new El(tag);registry.nodes??=[];if(tag==='g')registry.nodes.push(el);return el},querySelectorAll:selector=>selector==='.node-circle'?(registry.nodes||[]).filter(x=>x.classes.has('node-circle')):[],};
const fetchCalls=[];
const ctx={document,Date,Number,Math,String,JSON,Intl,Blob,console,setInterval:()=>1,clearInterval(){},setTimeout:fn=>{ /* no auto-timeout */return 2;},clearTimeout(){},URL:{createObjectURL:()=> 'blob:mock',revokeObjectURL(){}},AbortController,fetch:async(...args)=>{fetchCalls.push(args);return {ok:false,status:503}},};
vm.runInNewContext(fs.readFileSync(__dirname+'/live.js','utf8'),ctx);
assert.equal(get('connectionText').textContent,'DEMO');
assert.equal(get('totalNodes').textContent,'1,248');
assert.equal(get('events').children.length,6);
assert.equal(get('meshNodes').children.length,12);
const firstNode=get('meshNodes').children[0];firstNode.handlers.click();assert.match(get('selectedNode').textContent,/N-001/);
get('nodeSearch').handlers.input({target:{value:'N-812'}});assert.match(get('selectedNode').textContent,/N-812/);
get('eventFilter').value='RISK';get('eventFilter').handlers.change();assert.equal(get('events').children.length,1);
get('source').handlers.change({target:{value:'live'}});
setImmediate(()=>{
 assert.equal(get('totalNodes').textContent,'--','live mode must not display demo totals');
 assert.equal(get('connectionText').textContent,'ERROR');
 assert.equal(fetchCalls.length,1);
 get('pause').handlers.click();assert.equal(get('pause').textContent,'▶ Resume');
 get('refresh').handlers.click();setImmediate(()=>{assert.equal(fetchCalls.length,2,'manual refresh should work while paused');console.log('PASS: sample rendering, node selection, event filter, missing upstream, pause and manual refresh');});
});