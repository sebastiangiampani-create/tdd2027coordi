(function(root){
'use strict';
const text=v=>String(v??'').trim(), words=v=>{try{v=decodeURIComponent(text(v))}catch{}return text(v).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,' ').trim()}, compact=v=>words(v).replace(/ /g,'');
function commission(label,formation=''){
 const s=words(label),c=compact(label),number=(s.match(/\b(?:aula)\s*(\d+)/)||s.match(/(\d+)/)||[])[1];if(!number)return '';
 let type='';
 if(/^(or)?cnagrya/.test(c))type='orcn';else if(/^(or)?csh/.test(c))type='orcsh';else if(/^(or)?eco/.test(c))type='oreco';else if(/^(or)?com\d|^comunicacion/.test(c))type='orcom';else if(/^(or)?educ\d/.test(c))type='oreduc';else if(/^(or)?tur\d|^turismo/.test(c))type='ortur';else if(/^orarte|^orartes/.test(c))type='orarte';
 else if(/^esp.*comp/.test(c))type='espcomp';else if(/^esp.*quim/.test(c))type='espquim';else if(/^esp.*gado/.test(c))type='espgado';else if(/^tdr|^tecno.*representacion/.test(c))type='tdr';else if(/^et\d|^educaciontecnologica/.test(c))type='et';else if(/^ar\d|^artes?/.test(c))type=/orientad/.test(words(formation))?'orarte':'ar';else if(/^cn\d|^cienciasnaturales/.test(c))type='cn';else if(/^cs\d|^cienciassociales/.test(c))type='cs';else if(/^ef\d|^educacionfisica/.test(c))type='ef';else if(/^la\d|^lenguasadicionales/.test(c))type='la';else if(/^lyl\d|^lenguayliteratura/.test(c))type='lyl';else if(/^mat\d|^matematica/.test(c))type='mat';
 return type?type+':'+Number(number):'';
}
function school(name){const s=words(name),c=compact(name),nums=(s.match(/\d+/g)||[]).map(Number);
 if(/nini/.test(s)&&/mar.*all/.test(s))return 'nombre:marschall';
 for(const key of ['raggio','hicken','lola mora','yrurtia','manuel belgrano','marschall'])if(s.includes(key))return 'nombre:'+key;
 let type='';if(/^eem/.test(c)||/educ\w*.*media/.test(s))type='eem';else if(/^ens/.test(c)||/normal/.test(s))type='ens';else if(/^et\d/.test(c)||/tecnica/.test(s))type='et';else if(/comercio/.test(s))type='comercio';else if(/^colegio/.test(s))type='colegio';else if(/^liceo/.test(s))type='liceo';
 if(type&&nums.length){if(type==='eem')return nums.length>=2?type+':'+nums[0]+':'+nums[1]:'sinidentidad:'+c;return type+':'+nums[0]}return 'texto:'+c;
}
const dayNames=['Domingo','Lunes','Martes','Miércoles','Jueves','Viernes','Sábado'];
function day(date){const d=new Date(text(date)+'T00:00:00Z');return Number.isNaN(+d)?'':compact(dayNames[d.getUTCDay()])}
function shift(value){const s=compact(value);return /manana|^tm$/.test(s)?'Mañana':/tarde|^tt$/.test(s)?'Tarde':/vesp|noche|^tv$/.test(s)?'Vespertino':text(value)}
function proposals(raw){return raw.filter(r=>/^C0890-\d+/.test(text(r[0]))).map(r=>{const hours=text(r[2]),hour=Number((hours.match(/\d+/)||[])[0]);return {code:text(r[0]),label:text(r[1]),key:commission(r[1],r[5]),area:text(r[3]),venue:text(r[4]),shift:hour<12?'Mañana':hour<18?'Tarde':'Vespertino',days:new Set(r.slice(6,10).map(v=>compact(text(v).split(/\s/)[0]).slice(0,3)).filter(Boolean))}})}
function dateKey(value){const raw=text(value);let m=raw.match(/^Date\((\d{4}),(\d+),(\d+)/);if(m)return m[1]+'-'+String(+m[2]+1).padStart(2,'0')+'-'+m[3].padStart(2,'0');if(/^\d{4}-\d{2}-\d{2}$/.test(raw))return raw;return ''}
function completeCalls(calls){const datesByCommission=new Map();for(const c of calls){if(!c.date)continue;const k=[compact(c.commission),shift(c.shift),compact(c.day),c.encounter].join('|');if(!datesByCommission.has(k))datesByCommission.set(k,new Set());datesByCommission.get(k).add(c.date)}return calls.map(c=>{if(c.date)return {...c,dateOrigin:c.dateOrigin||'Convocatoria'};const dates=datesByCommission.get([compact(c.commission),shift(c.shift),compact(c.day),c.encounter].join('|'));return dates?.size===1?{...c,date:[...dates][0],dateOrigin:'Fecha de las otras escuelas de la misma comisión, turno y encuentro'}:{...c,dateOrigin:'Sin fecha verificable'}})}
function areaKey(value){const s=compact(value).replace(/orientacionen/g,'orientacion');
 if(/orientacion.*educacionfisica/.test(s))return 'ef';
 if(/orientacion|orientada/.test(s)){if(/art/.test(s))return 'orarte';if(/social|humanidad/.test(s))return 'orcsh';if(/natural|agro|energia/.test(s))return 'orcn';if(/econom|administracion/.test(s))return 'oreco';if(/comunicacion/.test(s))return 'orcom';if(/turismo/.test(s))return 'ortur';if(/educacion/.test(s))return 'oreduc';return s}
 if(/especialidad|especializacion/.test(s)){if(/compu/.test(s))return 'espcomp';if(/quim/.test(s))return 'espquim';if(/gado|gestion.*organizacion/.test(s))return 'espgado'}
 if(s==='arte'||s==='artes')return 'ar';if(/cienciasnaturales/.test(s))return 'cn';if(/cienciassociales/.test(s))return 'cs';if(/educacionfisica/.test(s))return 'ef';if(/lenguas?adicional/.test(s))return 'la';if(/lenguayliteratura/.test(s))return 'lyl';if(/matematica/.test(s))return 'mat';if(/representacion/.test(s))return 'tdr';if(/tecnologia|eductecno/.test(s))return 'et';return s;
}
function dependency(value){const s=words(value);const code=s.match(/\b(dem|det|dens|dea)\b/);if(code)return code[1].toUpperCase();if(/normal/.test(s))return 'DENS';if(/artistica/.test(s))return 'DEA';if(/tecnica/.test(s))return 'DET';if(/media/.test(s))return 'DEM';return 'Sin identificar'}
function inferredDependency(name){const id=school(name);if(id.startsWith('ens:'))return 'DENS';if(id.startsWith('et:')||/raggio|hicken/.test(id))return 'DET';if(/lola mora|yrurtia|manuel belgrano|marschall/.test(id))return 'DEA';if(/^(eem|colegio|comercio|liceo):/.test(id))return 'DEM';return 'Sin identificar'}
function cross(calls,attendance,defs,filters={}){
 const byCode=new Map(defs.map(d=>[d.code,d])),index=new Map(),people=new Map(),groups=new Map(),schools=new Map(),aliases=new Map(),sourceIds=new Set(),schoolDeps=new Map();
 const key=(area,sch,turn)=>[area,school(sch),shift(turn)].join('|');
 function remember(name){const id=school(name);if(!schools.has(id))schools.set(id,name);if(!aliases.has(id))aliases.set(id,new Set());aliases.get(id).add(compact(name))}
 for(const a of attendance){const d=dependency(a.dependency),id=school(a.school);if(d==='Sin identificar')continue;if(!schoolDeps.has(id))schoolDeps.set(id,new Set());schoolDeps.get(id).add(d)}
 for(const c of calls){remember(c.school);const k=key(areaKey(c.area),c.school,c.shift);if(!groups.has(k))groups.set(k,{...c,invited:true})}
 for(const a of attendance){if(!a.id||!a.school)continue;sourceIds.add(a.id);remember(a.school);const d=dependency(a.dependency),official=byCode.get(text(a.code)),area=text(a.area)?areaKey(a.area):official?.key.split(':')[0]||'sinarea',k=key(area,a.school,a.shift);if(!groups.has(k))groups.set(k,{school:a.school,area:a.area||official?.area||'Sin área',shift:shift(a.shift),invited:false});if(filters.dependency&&d!==filters.dependency)continue;
 if(!index.has(k)){index.set(k,new Set());people.set(k,new Map())}index.get(k).add(a.id);const records=people.get(k);if(!records.has(a.id))records.set(a.id,{id:a.id,firstName:text(a.firstName),lastName:text(a.lastName),dependency:d,dates:new Set()});const person=records.get(a.id);if(!person.firstName&&a.firstName)person.firstName=text(a.firstName);if(!person.lastName&&a.lastName)person.lastName=text(a.lastName);if(a.date)person.dates.add(a.date)}
 if(filters.area&&filters.shift){for(const name of schools.values()){const k=key(areaKey(filters.area),name,filters.shift);if(!groups.has(k))groups.set(k,{school:name,area:filters.area,shift:shift(filters.shift),invited:false})}}
 const calledIds=new Set();for(const [k,g] of groups)if(g.invited)for(const id of index.get(k)||[])calledIds.add(id);
 const rows=[],rowIds=new Map(),rowParticipants=new Map();for(const [k,g] of groups){const schoolId=school(g.school),deps=schoolDeps.get(schoolId)||new Set([inferredDependency(g.school)]);if(filters.dependency&&!deps.has(filters.dependency))continue;if(filters.schoolQuery&&![...(aliases.get(schoolId)||[])].some(name=>name.includes(compact(filters.schoolQuery))))continue;if(filters.area&&areaKey(g.area)!==areaKey(filters.area))continue;if(filters.shift&&shift(g.shift)!==shift(filters.shift))continue;
 const ids=index.get(k)||new Set(),row={Escuela:schools.get(schoolId)||g.school,'Dependencia funcional':[...deps].sort().join(' / '),Área:g.area,Turno:shift(g.shift),Convocada:g.invited?'Sí':'No','Asistentes (DNI únicos)':ids.size,Estado:!g.invited?'Sin convocatoria para este turno':ids.size?'Con registro':'Sin registro'};rows.push(row);rowIds.set(row,ids);rowParticipants.set(row,[...(people.get(k)?.values()||[])].map(p=>({DNI:p.id,Apellido:p.lastName||'Sin dato',Nombre:p.firstName||'Sin dato',Escuela:row.Escuela,'Dependencia funcional':p.dependency,Área:row.Área,Turno:row.Turno,Convocada:row.Convocada,'Fechas registradas':[...p.dates].sort().join(' / ')})))}
 return {rows,rowIds,rowParticipants,sourceTotal:sourceIds.size,sourceWithCall:calledIds.size,sourceWithoutCall:[...sourceIds].filter(id=>!calledIds.has(id)).length};
}

root.TDDCross={commission,school,shift,day,dateKey,completeCalls,proposals,areaKey,dependency,inferredDependency,cross};
})(typeof module!=='undefined'?module.exports:window);
