function printHead(){return `<div class="print-head"><img src="/assets/logo-left.png" alt="Afzal Heart Centre logo"><div><h1>GOVERNMENT ALLAMA IQBAL MEMORIAL<br>TEACHING HOSPITAL SIALKOT</h1><p>(Affiliated with Khawaja Muhammad Safdar Medical College, Sialkot)</p><h2>AFZAL HEART CENTRE</h2><h3>TRANSTHORACIC ECHOCARDIOGRAPHY</h3></div><img src="/assets/logo-right.png" alt="Medical college logo"></div>`}
function meta(visit){let saved=JSON.parse(visit.report||'{}'),person=saved.patient||patient;let prev=history.filter(x=>x.status==='final'&&x.id!==visit.id&&x.finalized<=visit.created).sort((a,b)=>(b.finalized||'').localeCompare(a.finalized||''))[0];return `<div class="print-meta"><div><b>Patient Name:</b> ${esc(person.name)}</div><div><b>${esc(person.relation_type)}:</b> ${esc(person.relation_name)}</div><div><b>Age / Sex:</b> ${esc(person.age)} / ${esc(person.sex)}</div><div><b>Registration No:</b> ${esc(person.reg_no)}</div><div><b>Echo Date:</b> ${fmtDate(visit.finalized||visit.created)}</div><div><b>Previous Echo Date:</b> ${fmtDate(saved.previous_echo!==undefined?saved.previous_echo:prev?.finalized)}</div></div>`}
function reportMeasurementTable(table, title, group) {
  // Parameter labels and reference units alone are not entered measurements.
  const rows = group === 'doppler'
    ? table.rows.filter(row => row.some((value, index) => index !== 0 && index !== 2 && String(value ?? '').trim()))
    : table.rows;
  if (group === 'doppler' && !rows.length) return '';
  return `<table class="echo-table"><thead><tr><th colspan="${table.columns.length}">${title}</th></tr><tr>${table.columns.map(name => `<th>${esc(name)}</th>`).join('')}</tr></thead><tbody>${rows.map(row => `<tr>${table.columns.map((_,i) => `<td>${esc(row[i] || '')}</td>`).join('')}</tr>`).join('') || `<tr><td colspan="${table.columns.length}">&mdash;</td></tr>`}</tbody></table>`;
}
function reportMarkup(visit) {
  const r = JSON.parse(visit.report), tables = measurementTables(r);
  const doctor = r.doctor || {};
  const custom = (r.rows || []).filter(row => row.some(value => String(value).trim()));
  const bullets = text => String(text || '').split('\n').filter(line => line.trim()).map(line => `<li>${esc(line.replace(/^[-•]\s*/,''))}</li>`).join('');
  const stamp = /^data:image\/(png|jpeg);base64,[A-Za-z0-9+/=]+$/.test(doctor.stamp_image || '') ? `<img class="doctor-stamp" src="${esc(doctor.stamp_image)}" alt="Doctor stamp">` : '';
  return `<article class="report-page">${printHead()}${meta(visit)}<div class="report-tables">${Object.entries(measurementGroups).map(([group,title]) => reportMeasurementTable(tables[group],title,group)).join('')}</div>${custom.length ? `<table class="echo-table custom-print"><thead><tr>${(r.columns || []).map(c => `<th>${esc(c)}</th>`).join('')}</tr></thead><tbody>${custom.map(row => `<tr>${row.map(cell => `<td>${esc(cell)}</td>`).join('')}</tr>`).join('')}</tbody></table>` : ''}${r.color?.trim() ? `<p class="print-color"><b>Color Flow Mapping:</b> ${esc(r.color)}</p>` : ''}${(r.lines || []).filter(Boolean).map(line => `<p class="additional-print-line">${esc(line)}</p>`).join('')}<h3>REPORT:</h3><ul>${bullets(r.findings)}</ul><h3>CONCLUSION:</h3><div class="conclusion">${esc(r.conclusion)}</div><div class="report-signoff"><div class="signature">${stamp}<b>${esc(doctor.name)}</b><br>${esc(doctor.qualification)}<br>${esc(doctor.registration)}</div><div class="created-by">Created by: ${esc(visit.operator || visit.creator)}${visit.report_revision ? ` &middot; Corrected revision ${visit.report_revision}` : ''}</div><footer>Note: This report is not valid for the court.</footer><div class="print-company-credit">Powered by MediTech</div></div></article>`;
}
async function printReport() {
  if (printBusy) return;
  $('#print').innerHTML = reportMarkup(visit);
  await preparedPrint('printing-report');
}

function previewReport(reportVisit) {
  if (!reportVisit || reportVisit.status !== 'final' || !reportVisit.report) return;
  const dialog = document.createElement('dialog');
  dialog.className = 'report-preview';
  dialog.setAttribute('aria-label', 'Echo report preview');
  dialog.innerHTML = `<div class="preview-toolbar"><b>Echo Report &middot; ${fmtDate(reportVisit.finalized)}</b><button type="button">Close Preview</button></div><div class="preview-paper">${reportMarkup(reportVisit)}</div>`;
  dialog.querySelector('button').onclick = () => dialog.close();
  dialog.onclose = () => dialog.remove();
  document.body.appendChild(dialog);
  dialog.showModal();
}
