let user,state,page='dashboard',patient,visit,history=[],draft,liveTimer;
async function refresh(q=''){state=await api('state?q='+encodeURIComponent(q))}
