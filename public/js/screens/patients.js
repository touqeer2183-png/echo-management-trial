function totalPatients() {
  $('#content').innerHTML = `<div class="panel"><div class="title-row"><div><h3>Total Registered Patients</h3><p>Permanent patient registry</p></div><strong class="big-total">${state.counts.total_patients}</strong></div>${patientRows(state.patients)}</div>`;
  bindPatients();
}
function patients() {
  const register = user.role === 'receptionist' ? `<div class="panel form-panel register-panel"><div class="section-kicker">NEW PERMANENT RECORD</div><h3>Register Patient</h3><p>CNIC aur phone pehly enter kren. Match milny par existing record foran show ho jay ga.</p><form id="register"><div class="formgrid identity-first">${input('identity','CNIC / B-Form / Parent CNIC','text','',true)}${input('phone','Phone / Parent Phone','text','',true)}</div><div id="matchNotice" class="match-notice">Adult k lie CNIC aur phone unique hon gy. Child k lie parent details reuse ho sakti hain.</div><div class="formgrid">${input('name','Patient Name','text','',true)}<label>Patient Type<select name="is_minor"><option value="">Adult</option><option value="1">Child / Minor</option></select></label><label>Relation<select name="relation_type" required><option>S/O</option><option>W/O</option><option>D/O</option></select></label>${input('relation_name','Father / Husband Name','text','',true)}${input('age','Age','text','',true)}<label>Sex<select name="sex"><option>Male</option><option>Female</option><option>Other</option></select></label>${input('guardian_name','Parent / Guardian Name')}${input('address','Address (optional)')}</div><button>Register &amp; Print Token</button></form></div>` : '';
  $('#content').innerHTML = `<div class="registry-layout">${register}<div class="panel search-panel"><div class="section-kicker">PATIENT LOOKUP</div><h3>Find Existing Patient</h3><form id="find" class="inline"><input id="search" name="q" placeholder="CNIC, phone, name or registration number"><button>Search</button></form><div id="results">${patientRows(state.patients.slice(0,20))}</div></div></div>`;
  const results = $('#results');
  let searchVersion = 0;
  $('#find').onsubmit = async e => {
    e.preventDefault(); const version = ++searchVersion;
    try {
      const found = await api('state?q=' + encodeURIComponent(fd(e.target).q));
      if (!results.isConnected || version !== searchVersion) return;
      results.innerHTML = patientRows(found.patients); bindPatients();
    } catch (error) { toast(error.message); }
  };
  bindPatients();
  const ci = $('[name=identity]'), ph = $('[name=phone]'), notice = $('#matchNotice');
  mask(ci, 'cnic'); mask(ph, 'phone');
  let lookupVersion = 0, timer;
  [ci,ph].forEach(field => field?.addEventListener('input', () => {
    const version = ++lookupVersion;
    clearTimeout(timer);
    notice.textContent = 'Adult k lie CNIC aur phone unique hon gy. Child k lie parent details reuse ho sakti hain.';
    const query = field.value;
    if (query.replace(/\D/g, '').length !== (field === ci ? 13 : 11)) return;
    timer = setTimeout(async () => {
      try {
        const queries = [ci, ph].filter(el => el.value.replace(/\D/g,'').length === (el === ci ? 13 : 11)).map(el => el.value.replace(/\D/g, ''));
        const responses = await Promise.all(queries.map(q => api('state?q=' + encodeURIComponent(q))));
        if (!notice.isConnected || version !== lookupVersion) return;
        const matches = [...new Map(responses.flatMap(r => r.patients).map(p => [p.id,p])).values()];
        const match = matches[0];
        if (!match) { notice.textContent = 'No existing record found for this CNIC / phone.'; return; }
        notice.innerHTML = '<b>Existing record found:</b>' + matches.map((person,index) => `<div class="matched-patient">${esc(person.name)} &middot; ${esc(person.reg_no)}<br><strong>Last echo: ${person.last_echo ? fmtDate(person.last_echo) : 'No completed echo'}</strong> <button type="button" class="light" ${index === 0 ? 'id="openMatch"' : ''} data-match="${person.id}">Open Record / Token</button></div>`).join('');
        notice.querySelectorAll('[data-match]').forEach(button => button.onclick = () => openPatient(+button.dataset.match));
      } catch (error) { if (notice.isConnected && version === lookupVersion) toast(error.message); }
    }, 450);
  }));
  if ($('#register')) $('#register').onsubmit = async e => {
    e.preventDefault(); const data = fd(e.target); data.is_minor = !!data.is_minor;
    try {
      const button = e.target.querySelector('button'); button.disabled = true;
      let result;
      try { result = await api('patients', {...data, issue_token: true}); } finally { button.disabled = false; }
      await refresh(); await openPatient(result.id);
      visit = history.find(v => v.id === result.visit.id);
      toast('Patient registered and token issued: ' + result.reg_no); await printTokens([visit]);
    } catch (error) { toast(error.message); }
  };
}
function bindPatients() { $$('[data-patient]').forEach(b => b.onclick = () => openPatient(+b.dataset.patient)); }
async function openPatient(id) {
  try {
    const person = await api('patient', {id});
    const encounters = await api('history', {id});
    patient = person; history = encounters; page = 'record'; render();
  } catch (error) { toast(error.message); }
}
