(function(){
 const link=document.getElementById('open-school-dashboard');
 if(!link)return;
 link.addEventListener('click',event=>{
  if(!sectionsUnlocked){event.preventDefault();return}
  try{const token=crypto.randomUUID();sessionStorage.setItem('tdd-school-dashboard-entry',token);link.href='tablero-escuelas.html#'+token}catch(_){link.href='tablero-escuelas.html'}
 });
})();
