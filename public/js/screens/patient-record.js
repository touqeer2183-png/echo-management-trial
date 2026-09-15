function record() {
  const last = history.find(v => v.status === 'final');
  const permission = `<div class="early-token-fields"><h4>Early repeat echo</h4><p>For a token before the normal interval, enter both fields below.</p><label>Reason<textarea name="reason" maxlength="500" placeholder="Why is an early echo needed?"></textarea></label><label>Ordered by<input name="ordered_by" maxlength="120" placeholder="Ordering doctor / clinician"></label>${user.role === 'operator' ? '<label>Permission allowed date<input type="date" name="allowed_date"></label>' : ''}</div>`;
  $('#content').innerHTML = `<button class="ghost" id="back">&larr; Patient Registry</button><div class="hero"><div><small>${esc(patient.reg_no)}</small><h2>${esc(patient.name)}</h2><p>${esc(patient.relation_type)} ${esc(patient.relation_name)} &middot; ${esc(patient.age)} &middot; ${esc(patient.sex)}</p></div>${user.role === 'receptionist' ? '<button id="editPatient" class="light">Edit Patient</button>' : ''}</div><div class="two"><div class="panel"><h3>Echo History</h3>${history.map(v => `<div class="visit"><div><b>Token ${token(v)}</b> &middot; ${fmtDate(v.created)}<br><small>${esc(v.status)} &middot; ${esc(v.operator || v.creator)}</small></div><div>${v.status === 'final' ? (user.role === 'operator' ? `<button class="light" data-view="${v.id}">Preview Report</button>` : '') : `<button class="light" data-reprint="${v.id}">Reprint Token</button>`}</div></div>`).join('') || '<div class="empty">No previous echo.</div>'}</div><div class="panel"><h3>Issue New Token</h3><p>Previous echo: <b>${fmtDate(last?.finalized)}</b><br>Normal interval: <b>${state.months} month(s)</b></p><form id="issue">${permission}<button>Issue Token</button>${user.role === 'operator' ? '<button type="button" id="savePermission" class="light">Save Permission Only</button>' : ''}</form></div></div>`;
  $('#back').onclick = () => { page = 'patients'; render(); };
  $$('[data-reprint]').forEach(b => b.onclick = () => { visit = history.find(v => v.id === +b.dataset.reprint); printTokens([visit]); });
  $$('[data-view]').forEach(b => b.onclick = () => { previewReport(history.find(v => v.id === +b.dataset.view)); });
  $('#issue').onsubmit = async e => {
    e.preventDefault();
    try {
      const result = await api('token', {patient_id: patient.id, ...fd(e.target)});
      await refresh(); history = await api('history', {id: patient.id});
      visit = history.find(v => v.id === result.id); await printTokens([visit]); record();
    } catch (error) { toast(error.message); }
  };
  if ($('#savePermission')) $('#savePermission').onclick = async () => {
    const data = fd($('#issue'));
    try {
      await api('permission', {patient_id: patient.id, reason: data.reason, allowed_date: data.allowed_date});
      toast('One-time early permission saved');
    } catch (error) { toast(error.message); }
  };
  if ($('#editPatient')) $('#editPatient').onclick = async () => {
    const name = prompt('Patient name', patient.name);
    if (!name) return;
    try {
      const id = patient.id;
      await api('patient-edit', {id, name});
      await refresh();
      patient = await api('patient', {id});
      record(); toast('Patient updated');
    } catch (error) { toast(error.message); }
  };
}
