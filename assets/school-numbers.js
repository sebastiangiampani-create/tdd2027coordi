(function(root){
 'use strict';
 const clean=v=>String(v??'').trim();
 function csv(text){const rows=[];let row=[],cell='',q=false;const s=String(text).replace(/^\uFEFF/,'');for(let i=0;i<s.length;i++){const c=s[i];if(c==='"'){if(q&&s[i+1]==='"'){cell+='"';i++}else if(q||!cell)q=!q;else cell+=c}else if(c===','&&!q){row.push(cell);cell=''}else if((c==='\n'||c==='\r')&&!q){if(c==='\r'&&s[i+1]==='\n')i++;row.push(cell);if(row.some(v=>clean(v)))rows.push(row);row=[];cell=''}else cell+=c}if(q)throw Error('Respuesta CSV incompleta');row.push(cell);if(row.some(v=>clean(v)))rows.push(row);return rows}
 function count(value){const s=clean(value).replace(/\s/g,'').replace(/\.(?=\d{3}(?:\D|$))/g,'').replace(',','.');if(!s)return 0;const n=Number(s);if(!Number.isSafeInteger(n)||n<0)throw Error('La fuente contiene una cantidad no válida: '+clean(value));return n}
 function measures(row,start){return {expected:count(row[start]),e1:count(row[start+1]),e2:count(row[start+3]),e3:count(row[start+5]),e4:count(row[start+7]),any:count(row[start+9])}}
 function parse(schools,shifts,bySchool,normalizers){
  const sourceSchoolKey=normalizers.school,areaKey=normalizers.areaKey;
  // Two labels used for the same institution in this workbook's own summaries.
  const ribera=schools.some(row=>clean(row[1])==='EEM 7 - ESCUELA DE LA RIBERA');
  const schoolKey=name=>ribera&&sourceSchoolKey(name)==='eem:7:4'?sourceSchoolKey('EEM 7 - ESCUELA DE LA RIBERA'):sourceSchoolKey(name);
  if(clean(schools[2]?.[3])!=='Esperados (POF)'||clean(shifts[2]?.[2])!=='Esperados (POF)')throw Error('Cambió la estructura de los resúmenes de la planilla.');
  const details=[],turns=[],outside=[],schoolNames=new Map(),dependencies=new Map();
  for(const row of schools.slice(3)){const dep=clean(row[0]),school=clean(row[1]),area=clean(row[2]);if(!school||!area||/^TOTAL\b/i.test(area)||!['DEM','DET','DENS','DEA'].includes(dep))continue;const schoolId=schoolKey(school);details.push({dependency:dep,school,schoolId,area,areaId:areaKey(area),...measures(row,3)});schoolNames.set(schoolId,school);if(!dependencies.has(schoolId))dependencies.set(schoolId,new Set());dependencies.get(schoolId).add(dep)}
  for(const row of bySchool.slice(3)){const school=clean(row[15]),dep=normalizers.dependency(row[14]);if(school&&dep&&dep!=='Sin identificar'){const id=schoolKey(school);if(!dependencies.has(id))dependencies.set(id,new Set());dependencies.get(id).add(dep)}}
  for(const row of schools.slice(3)){const school=clean(row[15]),area=clean(row[16]);if(!school||!area)continue;const schoolId=schoolKey(school);outside.push({school:schoolNames.get(schoolId)||school,schoolId,area,areaId:areaKey(area),dependencies:[...(dependencies.get(schoolId)||[])],any:count(row[17]),e1:count(row[18]),e2:count(row[19]),e3:count(row[20]),e4:count(row[21])})}
  for(const row of shifts.slice(3)){const shift=clean(row[0]),area=clean(row[1]);if(!shift||!area||/^TOTAL\b/i.test(area))continue;turns.push({shift,area,areaId:areaKey(area),...measures(row,2)})}
  const control=schools.find(row=>clean(row[0])==='TOTAL GENERAL');if(!control||!details.length)throw Error('No se encontró el resumen completo por escuela.');const expected=measures(control,3),actual=sum(details);for(const key of ['expected','e1','e2','e3','e4','any'])if(expected[key]!==actual[key])throw Error('El resumen de escuelas está incompleto: no coincide el total de '+key+'.');
  const turnControl=shifts.find(row=>clean(row[0])==='TOTAL GENERAL');if(!turnControl)throw Error('Falta el total por turno.');const turnTotal=sum(turns),turnExpected=measures(turnControl,2);for(const key of ['expected','e1','e2','e3','e4','any'])if(turnTotal[key]!==turnExpected[key]||turnTotal[key]!==actual[key])throw Error('El resumen por turno no coincide con el resumen de escuelas.');
  return {details,turns,outside};
 }
 function sum(rows){const result={expected:0,e1:0,e2:0,e3:0,e4:0,any:0};for(const r of rows)for(const k of Object.keys(result))result[k]+=r[k]||0;return result}
 function select(data,f={}){const isShift=f.view==='shift';const rows=(isShift?data.turns:data.details).filter(r=>(!f.area||r.areaId===f.area)&&(!isShift?(!f.dependency||r.dependency===f.dependency)&&(!f.school||r.schoolId===f.school):(!f.shift||r.shift===f.shift)));const extra=isShift?[]:data.outside.filter(r=>(!f.area||r.areaId===f.area)&&(!f.school||r.schoolId===f.school)&&(!f.dependency||r.dependencies.includes(f.dependency)));return {rows,outside:extra,total:sum(rows),outsideTotal:sum(extra),outsideAvailable:!isShift}}
 function group(rows,keys){const map=new Map();for(const row of rows){const id=JSON.stringify(keys.map(k=>row[k]));if(!map.has(id))map.set(id,Object.assign(Object.fromEntries(keys.map(k=>[k,row[k]])),sum([])));const value=map.get(id);for(const k of ['expected','e1','e2','e3','e4','any'])value[k]+=row[k]||0}return [...map.values()]}
 const api={csv,count,parse,sum,select,group};if(typeof module==='object'&&module.exports)module.exports=api;else root.TDDSchoolNumbers=api;
})(typeof globalThis!=='undefined'?globalThis:this);
