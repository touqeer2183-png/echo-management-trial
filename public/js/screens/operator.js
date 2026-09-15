async function openEncounter(row) {
  try {
    const person = await api('patient', {id: row.patient_id});
    const encounters = await api('history', {id: person.id});
    patient = person; history = encounters;
    visit = encounters.find(v => v.id === row.id);
    if (!visit) throw new Error('Encounter not found');
    page = 'editor'; render();
  } catch (error) { toast(error.message); }
}
function queue() {
  const operator = user.role === 'operator';
  const inProgress = operator && page === 'queue';
  const active = state.active.filter(v => !v.report);
  const activeHtml = active.map(v => `<div class="visit"><b>${token(v)} &middot; ${esc(v.patient_name)} &middot; ${esc(v.reg_no)}</b><button data-openactive="${v.id}">Continue</button></div>`).join('') || '<div class="empty">No echoes in progress.</div>';
  $('#content').innerHTML = (operator ? stats() : '') + `<div class="panel queue-panel"><div class="title-row"><div><div class="section-kicker">LIVE WORKLIST</div><h3>${inProgress ? 'My Active Echo' : operator ? 'Pending Patients' : 'Today Issued Tokens'}</h3></div><span class="live-dot">&#9679; REAL TIME</span></div>${inProgress ? activeHtml : (operator ? `<div class="today-queue"><h3>Today &middot; ${fmtDate(state.today)} <span class="badge">${state.waiting.filter(v => v.token_date === state.today).length} waiting</span></h3>${workTable(state.waiting.filter(v => v.token_date === state.today), true)}</div>${state.waiting.some(v => v.token_date !== state.today) ? `<details class="older-queue" open><summary>Earlier pending tokens (${state.waiting.filter(v => v.token_date !== state.today).length})</summary>${workTable(state.waiting.filter(v => v.token_date !== state.today), true)}</details>` : ''}` : workTable(state.issued, true))}</div>${operator && !inProgress && active.length ? `<div class="panel"><h3>My Active Echo</h3>${activeHtml}</div>` : ''}`;
  $$('[data-start]').forEach(b => b.onclick = async () => {
    try {
      await api('claim', {id: +b.dataset.start}); await refresh();
      const row = state.active.find(v => v.id === +b.dataset.start);
      if (!row) throw new Error('Refresh the queue to open this encounter');
      await openEncounter(row);
    } catch (error) { toast(error.message); }
  });
  $$('[data-openactive]').forEach(b => b.onclick = () => openEncounter(active.find(v => v.id === +b.dataset.openactive)));
  $$('[data-reprint]').forEach(b => b.onclick = async () => {
    try {
      const row = state.issued.find(v => v.id === +b.dataset.reprint);
      patient = await api('patient', {id: row.patient_id});
      history = await api('history', {id: patient.id}); visit = row; printTokens([row]);
    } catch (error) { toast(error.message); }
  });
}
function drafts() {
  const rows = state.drafts;
  $('#content').innerHTML = `<div class="panel draft-panel"><div class="title-row"><div><div class="section-kicker">SAVED FOR LATER</div><h3>Draft Reports</h3><p>Draft patient Pending Queue mein nahi dikhay ga. Finalize hoty hi yahan se remove ho jay ga.</p></div><b class="draft-count">${rows.length}</b></div>${rows.map(v => `<div class="draft-row"><div><b>${token(v)} &middot; ${esc(v.patient_name)}</b><br><small>Reg ${esc(v.reg_no)} &middot; Saved by ${esc(v.assigned_operator)}</small></div><button data-draft="${v.id}">Open Draft</button></div>`).join('') || '<div class="empty">No draft reports.</div>'}</div>`;
  $$('[data-draft]').forEach(b => b.onclick = () => openEncounter(rows.find(v => v.id === +b.dataset.draft)));
}
function historyPage() {
  $('#content').innerHTML = `<div class="panel"><div class="section-kicker">FINALIZED ECHOS</div><h3>Completed / History</h3><div class="table"><table><thead><tr><th>Date</th><th>Patient</th><th>Reg No.</th><th>Operator</th><th></th></tr></thead><tbody>${state.history.map(v => `<tr><td>${fmtDate(v.finalized)}</td><td>${esc(v.patient_name)}</td><td>${esc(v.reg_no)}</td><td>${esc(v.operator)}</td><td><button class="light" data-history="${v.id}">Open</button></td></tr>`).join('')}</tbody></table></div></div>`;
  $$('[data-history]').forEach(b => b.onclick = () => openEncounter(state.history.find(v => v.id === +b.dataset.history)));
}
