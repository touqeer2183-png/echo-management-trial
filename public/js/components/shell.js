function render() {
  page = allowedPage(page);
  const quick = user.role === 'receptionist' ? `<div class="quick"><button data-go="register">&#xff0b; Register Patient</button><button data-go="issue">&#9635; Issue Token</button></div>` : '';
  $('#app').innerHTML = `<div class="shell"><aside><div class="brand"><span>&hearts;</span><b>AFZAL HEART CENTRE</b><small>ECHO MANAGEMENT SYSTEM</small></div>${quick}<nav>${nav().map(([p,t]) => `<button class="${page === p ? 'active' : ''}" data-page="${p}">${t}</button>`).join('')}</nav><footer><b>${esc(user.name)}</b><br>${esc(user.role)} &middot; &#9679; Online<br>Connected in real time</footer></aside><main>${appHeader()}<section id="content"></section><footer class="app-company-footer">${companyCredit()}</footer></main></div>`;
  $$('[data-page]').forEach(b => b.onclick = () => { page = b.dataset.page; render(); });
  $$('[data-go]').forEach(b => b.onclick = () => {
    page = 'patients'; render();
    (b.dataset.go === 'register' ? $('[name=identity]') : $('#search'))?.focus();
  });
  $('#logout').onclick = async () => { try { await api('logout', {}); boot(); } catch (error) { toast(error.message); } };
  routeScreen();
}
