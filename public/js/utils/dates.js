const reg=p=>p?.reg_no||'',fmtDate=s=>s?new Date(s).toLocaleDateString('en-GB',{day:'2-digit',month:'short',year:'numeric'}):'—',token=v=>String(v.token_no||0).padStart(2,'0');
