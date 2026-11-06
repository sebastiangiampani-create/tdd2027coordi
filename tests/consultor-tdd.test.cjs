'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const vm=require('node:vm');
const app=path.resolve(__dirname,'../consultor-tdd');
const X=require(path.join(app,'assets/cross.js')).TDDCross;
const E=require(path.join(app,'assets/expected.js')).TDDExpected;
const XLSX=require(path.join(app,'assets/xlsx.full.min.js'));
const html=fs.readFileSync(path.join(app,'index.html'),'utf8');
const sha=data=>crypto.createHash('sha256').update(data).digest('hex');

test('los archivos provienen de la versión publicada, con un único texto de estado ajustado',()=>{
 const manifest=JSON.parse(fs.readFileSync(path.join(app,'RECUPERACION.json')));
 assert.equal(manifest.source_version,12);
 assert.equal(manifest.source_commit,'2c11e3a12ddfc11977b70577c88939ed5b4ed885');
 for(const item of manifest.source_files){let data=fs.readFileSync(path.join(app,item.path));if(item.path==='assets/cross.js')data=Buffer.from(data.toString().replace("ids.size?'Con registro':'Sin registro'","ids.size?'Con asistencia':'Sin registro'"));assert.equal(sha(data),item.sha256,item.path)}
});

test('cruza escuela/área/turno y conserva los 79 DNI sin convocatoria',()=>{
 const calls=[{school:'ET. RAGGIO',area:'Ciencias Sociales',shift:'Tarde',commission:'CS 7',date:'2026-11-03'}];
 const people=Array.from({length:1370},(_,i)=>({id:String(i+1),school:'Esc. Técnicas Raggio',area:i<1291?'Ciencias Sociales':'Artes',shift:'Tarde',dependency:'DET',commission:'Otra comisión',code:'OTRO-QR',date:'2026-11-17'}));
 const result=X.cross(calls,[...people,people[0]],[]);
 assert.equal(result.sourceTotal,1370);assert.equal(result.sourceWithCall,1291);assert.equal(result.sourceWithoutCall,79);
 assert.equal(new Set([...result.rowIds.values()].flatMap(ids=>[...ids])).size,1370);
 assert.equal(result.rows.find(r=>r.Convocada==='Sí')['Asistentes (DNI únicos)'],1291);
 assert.equal(result.rows.find(r=>r.Convocada==='No')['Asistentes (DNI únicos)'],79);
});

test('distingue los tres estados y filtra por dependencia funcional',()=>{
 const calls=[{school:'ET. RAGGIO',area:'Ciencias Sociales',shift:'Tarde'},{school:'Colegio 7',area:'Artes',shift:'Mañana'}];
 const people=[{id:'1',firstName:'Ana',lastName:'Pérez',school:'Esc. Técnicas Raggio',area:'Ciencias Sociales',shift:'Tarde',dependency:'Dirección de Educación Técnica'}];
 const filtered=X.cross(calls,people,[],{dependency:'DET',area:'Ciencias Sociales',shift:'Tarde'});
 assert.equal(filtered.rows.length,1);assert.equal(filtered.rows[0].Estado,'Con registro');
 assert.equal(filtered.rowParticipants.get(filtered.rows[0])[0].Nombre,'Ana');
 assert.equal(filtered.rowParticipants.get(filtered.rows[0])[0].Apellido,'Pérez');
 const zero=X.cross(calls,people,[],{schoolQuery:'Colegio 7',area:'Artes',shift:'Mañana'});assert.equal(zero.rows[0].Estado,'Sin registro');
 const noCall=X.cross(calls,people,[],{schoolQuery:'Raggio',area:'Artes',shift:'Vespertino'});assert.equal(noCall.rows[0].Estado,'Sin convocatoria para este turno');
 assert.notEqual(X.school('EEM 1 DE 20'),X.school('EEM 1 DE 16'));
});

test('los previstos no se inventan ni se distribuyen entre escuelas o filtros sin desglose',()=>{
 const rows=[{Escuela:'ET. RAGGIO','Dependencia funcional':'DET',Área:'Ciencias Sociales',Turno:'Tarde',Convocada:'Sí','Asistentes (DNI únicos)':1}];
 const people=[{DNI:'1',Escuela:'ET. RAGGIO','Dependencia funcional':'DET'}];
 let model=E.models(rows,people,'teachers',{dependency:'DET'});
 assert.equal(model.dependency[0].expected,1393);assert.equal(model.school[0].expected,null);
 model=E.models(rows,people,'teachers',{dependency:'DET',area:'Ciencias Sociales',shift:'Tarde'});assert.equal(model.dependency[0].expected,null);
 assert.equal(Object.values(E.UM).reduce((a,b)=>a+b),3853);
 const expected=E.parseExpected([['escuela','previstos','dependencia'],['ET. RAGGIO',4,'DET']]);
 model=E.models(rows,people,'teachers',{dependency:'DET'},expected);assert.equal(model.school[0].expected,4);assert.equal(model.school[0].coverage,25);
});

class Element{
 constructor(tag='div',document){this.tagName=tag.toLowerCase();this.document=document;this.children=[];this.attributes={};this.value='';this.listeners={};this.hidden=false;this._text='';}
 set textContent(value){this._text=String(value);this.children=[]}
 get textContent(){return this._text+this.children.map(c=>c.textContent||'').join('')}
 append(...children){this.children.push(...children);if(this===this.document.head)for(const child of children)this.document.loadScript(child)}
 replaceChildren(...children){this._text='';this.children=children}
 setAttribute(k,v){this.attributes[k]=String(v)}
 getAttribute(k){return this.attributes[k]??null}
 addEventListener(type,fn){(this.listeners[type]??=[]).push(fn)}
 async emit(type){for(const fn of this.listeners[type]||[])await fn({target:this})}
 click(){if(this.tagName==='a'&&this.download)this.document.downloads.push({name:this.download,url:this.href});return this.onclick?.({target:this})}
 remove(){} focus(){}
 querySelector(tag){for(const child of this.children){if(child.tagName===tag)return child;const found=child.querySelector?.(tag);if(found)return found}return null}
 get outerHTML(){return '<'+this.tagName+'>'+this.textContent+'</'+this.tagName+'>'}
}
function table(labels,rows){return {status:'ok',table:{cols:labels.map((label,i)=>({id:String.fromCharCode(65+i),label})),rows:rows.map(row=>({c:row.map(v=>({v}))}))}}}
function fixture(){
 const attendanceLabels=['Fecha','DNI','Nombre','Apellido','Correo','Dep. Fun','DE/Región','Establecimiento','Tipo de Formación','Área','Codigo','Comision','Encuentro','Fecha','Turno'];
 const person=(id,name,last,school,dependency,area,turn)=>['03/11/2026 09:00:00',id,name,last,'',dependency,'',school,'',area,'OTRO-QR','Otra comisión','1','03/11',turn];
 const people=[person('1','Ana','Pérez','Esc. Técnicas Raggio','Dirección de Educación Técnica','Ciencias Sociales','Tarde'),person('2','Luis','Gómez','Esc. Técnicas Raggio','Dirección de Educación Técnica','Ciencias Sociales','Tarde'),person('3','Juan','Prueba','Colegio 7','Dirección de Educación Media','Artes','Mañana')];
 return {attendance:table(attendanceLabels,[...people,people[0]]),calls:table(['Comisión','Escuelas','AREA','TURNO','Dia','Horario','SEDE'],[['CS 7','ET. RAGGIO','Ciencias Sociales','TARDE','MARTES','14 A 17','Sede'],['AR 1','Colegio 7','Artes','MAÑANA','MARTES','9 A 12','Sede'],['AR 2','Colegio 7','Artes','VESPERTINO','MARTES','18 A 21','Sede']]),proposals:table(['Código','Comisión','Horario','Área','Sede','Formación','Encuentro 1'],[['C0890-055','Ciencias Sociales Aula 6','14 a 17','Ciencias Sociales','Sede','General','Mar 03/11 - 14 a 17']])};
}
async function openApp(data=fixture()){
 const elements=new Map(),callbacks=new Map(),downloads=[],blobs=new Map(),timers=new Map();let timerId=0,blobId=0,context;
 const document={downloads,getElementById(id){if(!elements.has(id))elements.set(id,new Element('div',document));return elements.get(id)},createElement(tag){return new Element(tag,document)},createElementNS(ns,tag){return new Element(tag,document)},createTextNode(value){return {textContent:String(value)}},addEventListener(type,fn){(callbacks.get(type)||callbacks.set(type,[]).get(type)).push(fn)},dispatchEvent(event){for(const fn of callbacks.get(event.type)||[])fn(event)},loadScript(tag){if(!tag.src)return;const url=new URL(tag.src),cb=url.searchParams.get('tqx').match(/responseHandler:([^;]+)/)[1];const response=url.searchParams.get('sheet')==='Propuestas'?data.proposals:url.pathname.includes('1x-cRhsulmABI8wyB87xKeZw4Kq1GIMb4XCEzfaYozww')?data.calls:data.attendance;const page=(url.searchParams.get('tq')||'').match(/limit (\d+) offset (\d+)/);const delivered=page?{...response,table:{...response.table,rows:response.table.rows.slice(Number(page[2]),Number(page[2])+Number(page[1]))}}:response;queueMicrotask(()=>context[cb](delivered))}};
 document.head=new Element('head',document);document.body=new Element('body',document);
 for(const match of html.matchAll(/<select\b[^>]*id="([^"]+)"[^>]*>([\s\S]*?)<\/select>/g)){const options=[...match[2].matchAll(/<option(?:\s+value="([^"]*)")?([^>]*)>([^<]*)<\/option>/g)];const chosen=options.find(o=>/selected/.test(o[2]))||options[0];document.getElementById(match[1]).value=chosen?(chosen[1]??chosen[3]):''}
 class TestURL extends URL{static createObjectURL(blob){const key='blob:test-'+(++blobId);blobs.set(key,blob);return key}static revokeObjectURL(){}}
 const sandbox={document,URL:TestURL,URLSearchParams,Blob,XLSX,TDDCross:X,TDDExpected:E,Event:class{constructor(type){this.type=type}},localStorage:{getItem(){return null},setItem(){},removeItem(){}},setTimeout(fn){timers.set(++timerId,fn);return timerId},clearTimeout(id){timers.delete(id)},console,window:null};sandbox.window=sandbox;sandbox.window.print=()=>{};context=vm.createContext(sandbox);
 for(const match of html.matchAll(/<script>([\s\S]*?)<\/script>/g))vm.runInContext(match[1],context,{timeout:10000});
 for(let i=0;i<6;i++)await new Promise(resolve=>setImmediate(resolve));
 return {document,elements,blobs,downloads,context};
}
function descendants(element,tag){return element.children.flatMap(child=>[...(child.tagName===tag?[child]:[]),...(child.children?descendants(child,tag):[])])}

test('ejecuta el frontend original: carga, filtros combinados, gráficos, ordenamiento y XLSX nominal',async()=>{
 const appState=await openApp(),q=id=>appState.document.getElementById(id);
 assert(q('xc-results').querySelector('table'),'la tabla original debe renderizar con datos');
 q('xc-dependency').value='DET';q('xc-area').value='Ciencias Sociales';q('xc-shift').value='Tarde';await q('xc-dependency').emit('change');
 let rows=descendants(q('xc-results').querySelector('tbody'),'tr');assert.equal(rows.length,1);assert.equal(rows[0].children[0].textContent,'ET. RAGGIO');assert.equal(rows[0].children[5].textContent,'2');assert.equal(rows[0].children[6].textContent,'Con registro');
 const graph=q('chart-dependency').querySelector('svg');assert(graph);const actualBars=descendants(graph,'rect').filter(b=>b.getAttribute('data-series')==='Participación');assert.equal(actualBars.length,1);assert.equal(actualBars[0].getAttribute('data-count'),'1');
 const sortButton=descendants(q('xc-results').querySelector('thead'),'button').find(b=>b.title==='Ordenar por Asistentes (DNI únicos)');sortButton.click();assert(q('xc-results').querySelector('table'));
 q('xc-excel').click();const downloaded=appState.downloads.at(-1);assert.equal(downloaded.name,'tdd2027-informe.xlsx');const bytes=await appState.blobs.get(downloaded.url).arrayBuffer(),book=XLSX.read(bytes,{type:'array'});assert(book.SheetNames.includes('Docentes'));const participants=XLSX.utils.sheet_to_json(book.Sheets.Docentes);assert.equal(participants.length,2);assert(participants.every(p=>p['Dependencia funcional']==='DET'&&p.Área==='Ciencias Sociales'&&p.Turno==='Tarde'));assert(participants.some(p=>p.Nombre==='Ana'&&p.Apellido==='Pérez'));const filters=XLSX.utils.sheet_to_json(book.Sheets.Filtros,{header:1});assert(filters.some(r=>r[0]==='Dependencia funcional'&&r[1]==='DET'));
 q('chart-metric').value='teachers';await q('chart-metric').emit('change');const teacherGraph=q('chart-dependency').querySelector('svg'),teacherBars=descendants(teacherGraph,'rect').filter(b=>b.getAttribute('data-series')==='Participación');assert.equal(teacherBars[0].getAttribute('data-count'),'2');assert(q('chart-school-caption').textContent.includes('sin previsión'));
});
module.exports={openApp,fixture,descendants};
