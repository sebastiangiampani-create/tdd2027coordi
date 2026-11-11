(function(){
 'use strict';
 const tab=document.getElementById('bue-sheet-tab');
 if(!tab)return;
 const frame=document.getElementById('bue-sheet-frame');
 const auto=document.getElementById('bue-sheet-auto');
 const status=document.getElementById('bue-sheet-status');
 const refresh=document.getElementById('bue-sheet-refresh');
 const url='https://docs.google.com/spreadsheets/d/1sE2rqVyibJjUQa-UKxunKsuQ3uD85LSuUitkRBAKu0k/preview';
 let loaded=false;
 function visible(){return tab.open&&!tab.closest('[hidden]')&&!document.hidden;}
 function reload(){
  if(!visible())return;
  frame.src=url+'?t='+Date.now();
  loaded=true;
  status.textContent='Última recarga del visor: '+new Date().toLocaleTimeString('es-AR',{hour:'2-digit',minute:'2-digit'})+'. Google verifica el permiso de tu cuenta BUE.';
 }
 tab.addEventListener('toggle',()=>{if(!loaded&&visible())reload()});
 refresh.addEventListener('click',reload);
 setInterval(()=>{if(auto.checked&&visible())reload()},120000);
})();
