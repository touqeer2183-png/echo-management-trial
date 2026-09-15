// Route access mirrors the server's permission boundary.
function allowedPage(target) {
  const allowed = nav().map(([key]) => key);
  if (['receptionist','operator'].includes(user.role)) allowed.push('record');
  if (user.role === 'operator') allowed.push('editor');
  return allowed.includes(target) ? target : 'dashboard';
}
function routeScreen() {
  const screens = {dashboard,patients,totalPatients,queue,drafts,historyPage,performance,operatorPerformance,analytics,settings,record,editor};
  Promise.resolve(screens[page]()).catch(error => toast(error.message));
}
