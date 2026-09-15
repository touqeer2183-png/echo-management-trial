// Application lifecycle. Screens and transport live in their own files.
async function boot() {
  clearInterval(liveTimer);
  const session = await api('session');
  user = session.user;
  page = 'dashboard'; patient = visit = draft = undefined; history = [];
  if (!user) { state = undefined; return auth(session.setup); }
  await refresh(); render();
  liveTimer = setInterval(async () => {
    try {
      await refresh();
      if (['dashboard','queue','drafts','historyPage'].includes(page)) render();
    } catch (error) { if (error.status !== 401) toast(error.message); }
  }, 3000);
}
window.addEventListener('session-expired', () => {
  clearInterval(liveTimer); user = state = patient = visit = draft = undefined;
  history = []; page = 'dashboard'; auth(false);
});
boot().catch(error => toast(error.message));
