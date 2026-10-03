// Behavior checks; browser verification remains pending.
const vm=require('node:vm'),fs=require('node:fs'),assert=require('node:assert/strict');
class Element{constructor(){this.style={};this.classList={toggle(){}};this.handlers={};this.children=[];this.textContent='';this.disabled=false;}setAttribute(){}append(...v){this.children.push(...v)}replaceChildren(...v){this.children=v}addEventListener(n,f){this.handlers[n]=f}showModal(){this.open=true}close(){this.open=false}click(){this.clicked=true}}
const els=new Map();const get=id=>{if(!els.has(id))els.set(id,new Element());return els.get(id)};const timeouts=[],intervals=[];const document={getElementById:get,createElement:()=>new Element(),createDocumentFragment:()=>new Element(),addEventListener(){},documentElement:{requestFullscreen:async()=>{}},exitFullscreen:async()=>{}};
const ctx={document,Date,Math,Number,JSON,Blob,URL,setTimeout:f=>{timeouts.push(f);return timeouts.length},clearTimeout(){},setInterval:f=>{intervals.push(f);return intervals.length},clearInterval(){}};vm.runInNewContext(fs.readFileSync(__dirname+'/app.js','utf8'),ctx);
assert.equal(get('hotspots').children.length,21);assert.equal(get('mobileModules').children.length,21);
get('hotspots').children[0].handlers.click();assert(get('details').open);assert.equal(get('moduleTitle').textContent,'AI & Risk Intelligence');
get('moduleScan').handlers.click();assert(get('moduleScan').disabled);timeouts.pop()();assert.equal(get('moduleResult').textContent,'Check passed · all capabilities operational');
get('close').handlers.click();assert(!get('details').open);
get('pause').handlers.click();assert.equal(get('pause').textContent,'Resume telemetry');get('pause').handlers.click();assert.equal(get('pause').textContent,'Pause telemetry');
get('speed').handlers.input({target:{value:'500'}});assert.equal(get('intervalValue').textContent,'0.5s');intervals.at(-1)();assert.match(get('health').textContent,/98\.\d{2}%/);
get('diagnostic').handlers.click();assert(get('diagnostic').disabled);timeouts.pop()();assert.match(get('diagnosticResult').textContent,/21\/21 modules passed/);assert(!get('diagnostic').disabled);
get('export').handlers.click();
console.log('Passed: modules, dialog open/close, module scan, pause/resume, interval, telemetry, diagnostics, export handler. DOM harness only.');
