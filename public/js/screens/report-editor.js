let editingCorrection = false;
function editor(correction = false) {
  editingCorrection = correction;
  draft = visit.report ? JSON.parse(visit.report) : {values:{},color:'',findings:DEFAULT_REPORT,conclusion:DEFAULT_CONCLUSION,columns:['Parameter','Result','Notes'],rows:[],lines:[]};
  const locked = (visit.status === 'final' && !correction) || user.role !== 'operator';
  const mayCorrect = visit.status === 'final' && visit.operator_id === user.id;
  $('#content').innerHTML = `<button class="ghost" id="recordBack">&larr; Patient Record</button><div class="hero"><div><small>${esc(patient.reg_no)} &middot; Token ${token(visit)}</small><h2>${esc(patient.name)}</h2></div><span class="badge">${correction ? 'Editing correction' : visit.status === 'final' ? 'Finalized' : 'Manual report / draft'}</span></div><form id="report"><fieldset ${locked ? 'disabled' : ''}><div class="panel doctor-first"><div class="section-kicker">REPORTING DOCTOR</div><label>Select Doctor<select id="doctor"><option value="">Select doctor first</option>${state.doctors.map(d => `<option value="${d.id}" ${String(draft.doctor_id) === String(d.id) ? 'selected' : ''}>${esc(d.name)} &middot; ${esc(d.qualification)}</option>`).join('')}</select></label></div><div class="panel measurements-workspace"><div class="title-row"><div><div class="section-kicker">ECHO MEASUREMENTS</div><h3>Parameters &amp; Values</h3><p>Enter values in order. Add rows or columns beside the measurements.</p></div></div><div id="measurementGroups" class="measuregrid"></div><div class="measurement-extras"><div class="actions"><button type="button" id="addrow" class="light">+ Custom row</button><button type="button" id="addline" class="light">+ Note</button></div><div id="custom"></div></div></div><div class="panel editor"><h3>Color Flow Mapping</h3>${flowControls()}<label>Color Flow<textarea id="color" placeholder="Use + / - above, or enter additional findings">${esc(draft.color || '')}</textarea></label><h3>Report findings</h3><label>REPORT <small>Click below to edit the report text</small><textarea id="findings" class="large">${esc(draft.findings ?? DEFAULT_REPORT)}</textarea></label><label>CONCLUSION<textarea id="conclusion">${esc(draft.conclusion ?? DEFAULT_CONCLUSION)}</textarea></label></div>${correction ? '<div class="panel"><label>Correction reason<textarea id="correctionReason" minlength="5" maxlength="500" required placeholder="Explain the correction. The previous report stays in the audit history."></textarea></label></div>' : ''}</fieldset><div class="panel final-actions">${locked ? `<button type="button" id="printReport">Print Report</button>${mayCorrect ? ' <button type="button" id="editReport" class="light">Edit Report</button>' : ''}` : correction ? '<button>Save Correction &amp; Print</button> <button type="button" id="cancelCorrection" class="light">Cancel</button>' : '<div class="actions"><button type="button" class="light" id="save">Save Draft</button><button>Finalize &amp; Print</button><button type="button" class="danger" id="release">Release Patient</button></div>'}</div></form>`;
  const previous = history.filter(row => row.status === 'final' && row.id !== visit.id && row.finalized <= visit.created);
  const panel = document.createElement('section');
  panel.className = 'panel previous-echo-reports';
  panel.innerHTML = `<h3>Previous Echo Reports</h3>${previous.length ? previous.map(row => `<div class="visit"><div><b>${fmtDate(row.finalized)}</b> &middot; ${esc(row.operator || '')}</div><button type="button" class="light" data-preview-echo="${row.id}">Preview Report</button></div>`).join('') : '<p>No previous completed echo report.</p>'}`;
  $('#report').before(panel);
  panel.querySelectorAll('[data-preview-echo]').forEach(button => button.onclick = () => previewReport(previous.find(row => row.id === +button.dataset.previewEcho)));
  renderMeasurements(); renderCustom(); bindFlow();
  $('#recordBack').onclick = () => openPatient(patient.id);
  $('#addrow').onclick = () => { capture(); draft.rows.push(draft.columns.map(() => '')); renderCustom(); };
  $('#addline').onclick = () => { capture(); draft.lines.push(''); renderCustom(); };
  if ($('#save')) $('#save').onclick = () => save(false);
  if ($('#release')) $('#release').onclick = async () => {
    try { await api('release', {id:visit.id}); await refresh(); page='queue'; render(); } catch(error) { toast(error.message); }
  };
  if ($('#printReport')) $('#printReport').onclick = printReport;
  if ($('#editReport')) $('#editReport').onclick = () => editor(true);
  if ($('#cancelCorrection')) $('#cancelCorrection').onclick = () => editor();
  $('#report').onsubmit = e => { e.preventDefault(); if (confirm(correction ? 'Save this correction with its audit history?' : 'Finalize this report?')) save(true); };
}
function capture() {
  draft.columns = $$('[data-col]').map(x => x.value);
  draft.rows = $$('[data-row]').map(row => [...row.querySelectorAll('input')].map(x => x.value));
  draft.lines = $$('[data-line]').map(x => x.value);
  captureMeasurements();
  ['color','findings','conclusion'].forEach(key => draft[key] = $('#' + key).value.trim());
  draft.doctor_id = $('#doctor').value;
}
async function save(final) {
  const buttons = $$('.final-actions button'); buttons.forEach(b => b.disabled = true);
  try {
    capture();
    const correction = editingCorrection;
    const data = {id: visit.id, report: draft, final};
    if (correction) { data.reason = $('#correctionReason').value; data.expected_revision = visit.report_revision || 0; }
    await api(correction ? 'report/amend' : 'report', data);
    await refresh(); history = await api('history', {id:patient.id}); visit = history.find(v => v.id === visit.id);
    if (final) { toast(correction ? 'Correction saved with previous version' : 'Report completed and saved'); editor(); await printReport(); }
    else { toast('Report saved in Draft Reports'); page = 'drafts'; render(); }
  } catch(error) { toast(error.message); }
  finally { buttons.forEach(b => b.disabled = false); }
}
