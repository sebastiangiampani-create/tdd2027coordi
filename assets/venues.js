(function(root){
 'use strict';
 const clean=v=>String(v??'').trim();
 function key(v){let s=clean(v);try{s=decodeURIComponent(s)}catch(_){}return s.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]/g,'')}
 function parseCsv(text){
  const rows=[];let row=[],value='',quoted=false;const s=String(text).replace(/^\uFEFF/,'');
  for(let i=0;i<s.length;i++){
   const ch=s[i];
   if(ch==='"'){if(quoted&&s[i+1]==='"'){value+='"';i++}else if(quoted||value==='')quoted=!quoted;else value+=ch}
   else if(ch===','&&!quoted){row.push(value);value=''}
   else if((ch==='\r'||ch==='\n')&&!quoted){if(ch==='\r'&&s[i+1]==='\n')i++;row.push(value);if(row.some(v=>clean(v)))rows.push(row);row=[];value=''}
   else value+=ch;
  }
  if(quoted)throw Error('La exportación CSV está incompleta.');
  row.push(value);if(row.some(v=>clean(v)))rows.push(row);
  return rows;
 }
 function catalog(values){
  if(!values.length)throw Error('Propuestas no tiene filas.');
  const headers=values[0].map(key),ci=headers.findIndex(h=>['codigo','cod'].includes(h)),mi=headers.indexOf('comision'),vi=headers.findIndex(h=>['sede','sededecapacitacion'].includes(h));
  if(ci<0||mi<0||vi<0)throw Error('Faltan las columnas Código, Comisión o Sede en Propuestas.');
  const byCode=new Map(),byPair=new Map(),byCommission=new Map(),venues=new Set();let records=0;
  function add(map,k,v){if(!k)return;if(!map.has(k))map.set(k,new Set());map.get(k).add(v)}
  for(const row of values.slice(1)){const code=key(row[ci]),commission=key(row[mi]),venue=clean(row[vi]);if(!code||!venue||code==='codigo')continue;records++;venues.add(venue);add(byCode,code,venue);if(commission){add(byPair,code+'|'+commission,venue);add(byCommission,commission,venue)}}
  if(!records)throw Error('Propuestas no contiene códigos y sedes válidos.');
  const index=new Map();for(const map of [byCode,byPair])for(const [k,v] of map)if(v.size===1)index.set(k,[...v][0]);
  // Solo recuperar por comisión cuando falta el código y la sede es inequívoca.
  for(const [k,v] of byCommission)if(v.size===1)index.set('commission:'+k,[...v][0]);
  return {index,records,codes:byCode.size,venues:venues.size};
 }
 function resolve(index,code,commission){const c=key(code),m=key(commission);return (c?(index.get(c+'|'+m)||index.get(c)):(m&&index.get('commission:'+m)))||'Sede sin identificar'}
 const api={key,parseCsv,catalog,resolve};if(typeof module==='object'&&module.exports)module.exports=api;else root.TDDVenues=api;
})(typeof globalThis!=='undefined'?globalThis:this);
