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
}
function picker(id,opts,choose){
 const input=$(id),list=$(id+'-options');
 const show=()=>{
  const q=normalize(input.value);const found=opts().filter(o=>normalize(o.label+' '+(o.sub||'')).includes(q));
  list.replaceChildren(...found.map(o=>{const b=el('button','',o.label+(o.sub?' · '+o.sub:''));b.type='button';b.setAttribute('role','option');b.addEventListener('mousedown',event=>event.preventDefault());b.addEventListener('click',()=>{input.value=o.label;list.hidden=true;input.setAttribute('aria-expanded','false');choose(o.value);render()});return b}));
  if(!found.length)list.append(el('p','','No se encontraron coincidencias.'));
  list.hidden=false;input.setAttribute('aria-expanded','true');
 };
 input.addEventListener('focus',show);input.addEventListener('input',()=>{choose('');mode=chosenSchool?'school':chosenArea?'area':'all';render();show()});
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
function makeCard(title,tag,row,sub){
 const card=el('article','numbers-detail-card');card.append(el('span','numbers-card-tag',tag),el('h3','',title));
 if(sub)card.append(el('p','numbers-context',sub));
 for(const [label,value] of [['Esperados (POF)',fmt(row.expected)],['Participaron al menos una vez',fmt(row.any)],['Participación',percent(row.any,row.expected)]]){
 const line=el('div','numbers-row');line.append(el('span','',label),el('b','',value));card.append(line)}
 card.append(progress(row.any,row.expected));
 const mini=el('div','numbers-mini-encounters');
 for(let i=1;i<=4;i++){const tile=el('div','', 'Enc. '+i);tile.append(el('b','',fmt(row['e'+i])));mini.append(tile)}
 card.append(mini);return card;
}
function render(){
 if(!data)return;const rows=subset(),total=N.sum(rows);
 const school=schoolOptions.find(o=>o.value===chosenSchool),area=areaOptions.find(o=>o.value===chosenArea);
 $('numbers-selection-label').textContent=[school?.label,area?.label].filter(Boolean).join(' · ')||'Todas las escuelas y áreas';
 $('numbers-result-count').textContent=new Set(rows.map(r=>r.schoolId)).size+' escuelas · '+new Set(rows.map(r=>r.areaId)).size+' áreas';
 $('numbers-cards').replaceChildren(createKpi('Docentes esperados (POF)',fmt(total.expected),'Universo convocado',true),createKpi('Participaron al menos una vez',fmt(total.any),'Registro en uno o más encuentros'),createKpi('Participación',percent(total.any,total.expected),'Sobre docentes esperados'),createKpi('Sin registro',fmt(Math.max(0,total.expected-total.any)),'No equivale necesariamente a ausencia'));
 $('numbers-encounters').replaceChildren(...[1,2,3,4].map(i=>{const n=el('article','numbers-encounter');n.append(el('h3','','Encuentro '+i),el('strong','',fmt(total['e'+i])),el('p','',percent(total['e'+i],total.expected)+' de '+fmt(total.expected)+' esperados'),progress(total['e'+i],total.expected));return n}));
 const groupKey=chosenSchool?'area':'schoolId';const group=N.group(rows,[groupKey]);
 const lookup=new Map(rows.map(r=>[r.schoolId,{school:r.school,dependency:r.dependency}]));
 group.sort((a,b)=>(groupKey==='area'?a.area:lookup.get(a.schoolId)?.school||'').localeCompare(groupKey==='area'?b.area:lookup.get(b.schoolId)?.school||'','es',{numeric:true}));
 $('numbers-detail-title').textContent=chosenSchool?'Áreas de la escuela':chosenArea?'Escuelas del área':'Participación por escuela';
 const detail=$('numbers-detail');detail.replaceChildren(...group.map(r=>makeCard(groupKey==='area'?r.area:lookup.get(r.schoolId)?.school||r.schoolId,groupKey==='area'?'ÁREA':lookup.get(r.schoolId)?.dependency||'ESCUELA',r)));
 if(!rows.length)detail.append(el('p','numbers-empty','No hay datos para esta combinación. Elegí otra escuela o área.'));
 let out=data.outside;
 if(chosenSchool)out=out.filter(r=>r.schoolId===chosenSchool);
 if(chosenArea)out=out.filter(r=>r.areaId===chosenArea);
 const outside=$('numbers-outside');
 outside.replaceChildren(...out.map(r=>{const n=el('article','numbers-detail-card');n.append(el('span','numbers-card-tag','FUERA DEL PADRÓN'),el('h3','',r.school),el('p','numbers-context',r.area));const s=el('div','numbers-row');s.append(el('span','','Al menos un encuentro'),el('b','',fmt(r.any)));n.append(s);const m=el('div','numbers-mini-encounters');for(let i=1;i<=4;i++){const a=el('div','','Enc. '+i);a.append(el('b','',fmt(r['e'+i])));m.append(a)}n.append(m);return n}));
 if(!out.length)outside.append(el('p','numbers-empty','No hay registros fuera del padrón en esta selección.'));
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