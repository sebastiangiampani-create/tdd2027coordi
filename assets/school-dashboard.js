(function(){
'use strict';
const $=id=>document.getElementById(id), N=TDDSchoolNumbers;
const SOURCE='1djc57JJz-pdqmLHV8x45QO_jhM8XWI76k0OdhZ5Lg3E';
const SOURCES=[['schools','201'],['shifts','204'],['metadata','202']];
const keys=['expected','e1','e2','e3','e4','any'];
let data=null,loading=false,chosenSchool='',chosenArea='',mode='all',schoolOptions=[],areaOptions=[];
const fmt=n=>Number(n||0).toLocaleString('es-AR');
const percent=(a,b)=>b>0?(100*a/b).toLocaleString('es-AR',{maximumFractionDigits:1})+' %':'Sin dato';
const el=(tag,cls,value)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(value!==undefined)n.textContent=value;return n};
const normalize=s=>String(s||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,' ').trim();
function options(){
 schoolOptions=[...new Map(data.details.map(r=>[r.schoolId,{value:r.schoolId,label:r.school,sub:r.dependency}])).values()].sort((a,b)=>a.label.localeCompare(b.label,'es',{numeric:true}));
 areaOptions=[...new Map(data.details.map(r=>[r.areaId,{value:r.areaId,label:r.area}])).values()].sort((a,b)=>a.label.localeCompare(b.label,'es'));
 $('native-school-list').replaceChildren(...schoolOptions.map(o=>new Option(o.label)));
 $('native-area-list').replaceChildren(...areaOptions.map(o=>new Option(o.label)));
}
function picker(id,opts,choose){
 const input=$(id),list=$(id+'-options');
 const show=()=>{
  const q=normalize(input.value);const found=opts().filter(o=>normalize(o.label+' '+(o.sub||'')).includes(q));
  list.replaceChildren(...found.map(o=>{const b=el('button','',o.label+(o.sub?' · '+o.sub:''));b.type='button';b.setAttribute('role','option');b.addEventListener('mousedown',event=>event.preventDefault());b.addEventListener('click',()=>{input.value=o.label;list.hidden=true;input.setAttribute('aria-expanded','false');choose(o.value);render()});return b}));
  if(!found.length)list.append(el('p','','No se encontraron coincidencias.'));
  list.hidden=false;input.setAttribute('aria-expanded','true');
 };
 input.addEventListener('focus',show);input.addEventListener('input',()=>{
 const exact=opts().find(o=>normalize(o.label)===normalize(input.value));
 choose(exact?exact.value:'');
 mode=chosenSchool?'school':chosenArea?'area':'all';render();if(!exact)show();else{list.hidden=true;input.setAttribute('aria-expanded','false')}
});
 input.addEventListener('keydown',e=>{if(e.key==='Escape'){list.hidden=true;input.setAttribute('aria-expanded','false')}if(e.key==='Enter'&&!list.hidden){const first=list.querySelector('button');if(first){e.preventDefault();first.click()}}});
 document.addEventListener('click',e=>{if(!input.parentElement.contains(e.target)){list.hidden=true;input.setAttribute('aria-expanded','false')}});
}
function subset(){
 let rows=data.details;
 if(chosenSchool)rows=rows.filter(r=>r.schoolId===chosenSchool);
 if(chosenArea)rows=rows.filter(r=>r.areaId===chosenArea);
 return rows;
}
function createKpi(label,value,hint,primary){
 const box=el('div','numbers-kpi'+(primary?' primary':''));box.append(el('span','',label),el('strong','',value),el('small','',hint));return box;
}
function progress(a,b){const track=el('div','numbers-progress'),fill=el('span');fill.style.width=(b?Math.min(100,100*a/b):0)+'%';track.append(fill);return track}
function makeCard(title,tag,row,sub,outside){
 const card=el('article','numbers-detail-card');card.append(el('span','numbers-card-tag',tag),el('h3','',title));
 if(sub)card.append(el('p','numbers-context',sub));
 for(const [label,value] of [['Esperados (POF)',fmt(row.expected)],['Participantes totales',fmt(row.any+outside.any)],['Cobertura de convocados',percent(row.any,row.expected)]]){
 const line=el('div','numbers-row');line.append(el('span','',label),el('b','',value));card.append(line)}
 card.append(progress(row.any,row.expected));
 const mini=el('div','numbers-mini-encounters');
 for(let i=1;i<=4;i++){const tile=el('div','', 'Enc. '+i);tile.append(el('b','',fmt(row['e'+i]+outside['e'+i])));mini.append(tile)}
 card.append(mini);
 return card;
}
function render(){
 if(!data)return;
 const rows=subset(),school=schoolOptions.find(o=>o.value===chosenSchool),area=areaOptions.find(o=>o.value===chosenArea);
 $('numbers-selection-label').textContent=school?school.label:area?'Escuelas · '+area.label:'Tableros por escuela';
 const groups=new Map();
 for(const row of rows){if(!groups.has(row.schoolId))groups.set(row.schoolId,{name:row.school,dep:row.dependency,rows:[]});groups.get(row.schoolId).rows.push(row)}
 $('numbers-result-count').textContent=groups.size+' escuelas · '+new Set(rows.map(r=>r.areaId)).size+' áreas';
 const panel=$('numbers-detail');
 const expanded=new Set([...panel.querySelectorAll('details[open]')].map(n=>n.dataset.schoolId));
 panel.replaceChildren();
 const sorted=[...groups.entries()].sort((a,b)=>a[1].name.localeCompare(b[1].name,'es',{numeric:true}));
 for(const [schoolId,g] of sorted){
  const total=N.sum(g.rows),outsideRows=data.outside.filter(r=>r.schoolId===schoolId&&(!chosenArea||r.areaId===chosenArea)),outsideTotal=N.sum(outsideRows),card=el('details','numbers-school-card');card.dataset.schoolId=schoolId;
  if(chosenSchool===schoolId||expanded.has(schoolId))card.open=true;
  const head=el('summary'),top=el('div','school-head'),name=el('div');
  name.append(el('span','numbers-card-tag',g.dep),el('h3','',g.name));top.append(name,el('span','school-open','Tocar para ver áreas ▾'));head.append(top);
  const stats=el('div','school-summary');
  for(const [label,value] of [['Esperados POF',fmt(total.expected)],['Participantes totales',fmt(total.any+outsideTotal.any)],['Cobertura de convocados',percent(total.any,total.expected)]]){const n=el('div','school-stat');n.append(el('span','',label),el('strong','',value));stats.append(n)}
  head.append(stats);card.append(head);
  const content=el('div','school-expanded'),encounters=el('div','school-encounters');
  for(let i=1;i<=4;i++){const n=el('div','school-encounter');n.append(el('span','','Encuentro '+i),el('strong','',fmt(total['e'+i]+outsideTotal['e'+i])),el('small','','Participantes totales'));encounters.append(n)}
  content.append(encounters,el('h4','school-areas-title','Desglose por área y por encuentro'));
  const areaGrid=el('div','school-area-grid');
  const areas=N.group(g.rows,['area']).sort((x,y)=>x.area.localeCompare(y.area,'es'));
  for(const r of areas){const extra=N.sum(outsideRows.filter(o=>o.areaId===g.rows.find(d=>d.area===r.area)?.areaId));areaGrid.append(makeCard(r.area,'ÁREA',r,'',extra))}
  content.append(areaGrid);card.append(content);panel.append(card);
 }
 if(!sorted.length)panel.append(el('p','numbers-empty','No se encontraron escuelas para esta selección.'));

}
async function load(){
 if(loading)return;loading=true;$('numbers-refresh').disabled=true;$('numbers-status').textContent='Actualizando datos agregados…';
 const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),35000);
 try{
 const tables=Object.fromEntries(await Promise.all(SOURCES.map(async([key,gid])=>{
 const url='https://docs.google.com/spreadsheets/d/'+SOURCE+'/export?'+new URLSearchParams({format:'csv',gid,_:String(Date.now())});
 const response=await fetch(url,{signal:controller.signal,credentials:'omit',cache:'no-store'});
 if(!response.ok)throw Error('La planilla respondió HTTP '+response.status);
 return [key,N.csv(await response.text())];
 })));
 data=N.parse(tables.schools,tables.shifts,tables.metadata,TDDCross);options();render();
 $('numbers-status').textContent='Actualizado: '+new Date().toLocaleString('es-AR')+' · '+schoolOptions.length+' escuelas disponibles.';
 }catch(err){$('numbers-status').textContent=(data?'No se pudo actualizar; se conservan los últimos datos. ':'No se pudieron cargar los resúmenes. ')+(err.name==='AbortError'?'La consulta tardó demasiado.':err.message)}
 finally{clearTimeout(timer);loading=false;$('numbers-refresh').disabled=false}
}
picker('numbers-school',()=>schoolOptions,value=>{chosenSchool=value;mode=value?'school':chosenArea?'area':'all'});
picker('numbers-area',()=>areaOptions,value=>{chosenArea=value;mode=value?'area':chosenSchool?'school':'all'});
// Pickers use dynamic option arrays after the first successful fetch.
$('numbers-all').addEventListener('click',()=>{chosenSchool='';chosenArea='';$('numbers-school').value='';$('numbers-area').value='';render()});
$('numbers-clear').addEventListener('click',()=>{chosenSchool='';chosenArea='';$('numbers-school').value='';$('numbers-area').value='';render()});
$('numbers-refresh').addEventListener('click',load);
setInterval(()=>{if(!document.hidden)load()},120000);
load();
})();