const measurementGroups = {dimensions: '2D Dimensions', dimensions_lv: 'LV Dimensions', doppler: 'Doppler Parameters'};
function measurementTables(report) {
  if (report.measurement_tables) {
    const tables = JSON.parse(JSON.stringify(report.measurement_tables));
    if (!tables.dimensions_lv) {
      const lvNames = new Set(dimensions_lv.map(row => row[0]));
      tables.dimensions_lv = {columns: [...tables.dimensions.columns], rows: tables.dimensions.rows.filter(row => lvNames.has(row[0]))};
      tables.dimensions.rows = tables.dimensions.rows.filter(row => !lvNames.has(row[0]));
    }
    tables.dimensions.columns[2] = 'Normal';
    return tables;
  }
  const tables = Object.fromEntries(Object.entries({dimensions, dimensions_lv, doppler}).map(([group, rows]) => [group, {
    columns: ['Parameter', 'Result', group === 'dimensions' ? 'Normal' : 'Reference'],
    rows: rows.map(([name, reference]) => [name, report.values?.[name] || '', reference])
  }]));
  // Retain measurements from older value-only reports, including renamed parameters.
  const known = new Set(Object.values(tables).flatMap(table => table.rows.map(row => row[0])));
  for (const [name, value] of Object.entries(report.values || {})) {
    if (!known.has(name)) tables.dimensions.rows.push([name, value, '']);
  }
  return tables;
}
function renderMeasurements() {
  draft.measurement_tables = measurementTables(draft);
  if (visit.status !== 'final') {
    const references = new Map(dimensions);
    draft.measurement_tables.dimensions.rows.forEach(row => {
      if (!row[2]?.trim() && references.get(row[0])) row[2] = references.get(row[0]);
    });
  }
  $('#measurementGroups').innerHTML = Object.entries(measurementGroups).map(([group, title]) => {
    const table = draft.measurement_tables[group];
    return `<section class="measurement-card" data-group="${group}"><div class="measurement-heading"><div><small>MANUAL MEASUREMENTS</small><h3>${title}</h3></div><button type="button" class="light mini" data-new-parameter="${group}">+ Parameter</button></div><div class="table"><table><thead><tr>${table.columns.map((name, col) => `<th>${col < 3 ? esc(name) : `<input data-heading="${col}" value="${esc(name)}" aria-label="Column name">`} ${col >= 3 ? `<button type="button" class="mini remove" data-remove-column="${col}" aria-label="Remove column">&times;</button>` : ''}</th>`).join('')}<th><button type="button" class="light mini" data-new-column="${group}" title="Add a column">+ Column</button></th></tr></thead><tbody>${table.rows.map((row, index) => `<tr data-parameter-row="${index}">${table.columns.map((_, col) => `<td>${col === 2 ? `<span class="measurement-reference" data-cell="2">${esc(row[col] || '')}</span>` : `<input data-cell="${col}" ${col === 1 ? `data-measure="${esc(row[0])}"` : ''} value="${esc(row[col] || '')}" aria-label="${esc(row[0])} ${esc(table.columns[col])}" placeholder="${col === 1 ? 'Value' : ''}">`}</td>`).join('')}<td class="parameter-tools"><button type="button" class="mini light" data-insert-parameter="${index}" title="Add parameter below">+</button><button type="button" class="mini remove" data-remove-parameter="${index}" title="Remove parameter">&times;</button><button type="button" class="mini light" data-move-parameter="${index}" title="Move parameter up" ${index === 0 ? 'disabled' : ''}>&uarr;</button></td></tr>`).join('')}</tbody></table></div></section>`;
  }).join('');
  $('#measurementGroups').onkeydown = event => {
    if (event.key !== 'Tab' || event.ctrlKey || event.altKey || event.metaKey || !event.target.matches('input[data-cell]')) return;
    const cells = [...document.querySelectorAll(`#measurementGroups input[data-cell="${event.target.dataset.cell}"]`)].filter(input => !input.matches(':disabled'));
    const next = cells[cells.indexOf(event.target) + (event.shiftKey ? -1 : 1)]
      || (event.shiftKey ? $('#doctor') : $('#addrow'));
    if (next && !next.matches(':disabled')) {
      event.preventDefault();
      next.focus();
    }
  };
  $$('[data-group]').forEach(section => {
    const group = section.dataset.group;
    const update = fn => { capture(); fn(draft.measurement_tables[group]); renderMeasurements(); };
    section.querySelector('[data-new-parameter]').onclick = () => update(t => t.rows.push(t.columns.map(() => '')));
    section.querySelector('[data-new-column]').onclick = () => update(t => { t.columns.push('Notes'); t.rows.forEach(r => r.push('')); });
    section.querySelectorAll('[data-insert-parameter]').forEach(b => b.onclick = () => update(t => t.rows.splice(+b.dataset.insertParameter + 1, 0, t.columns.map(() => ''))));
    section.querySelectorAll('[data-remove-parameter]').forEach(b => b.onclick = () => update(t => t.rows.splice(+b.dataset.removeParameter, 1)));
    section.querySelectorAll('[data-move-parameter]').forEach(b => b.onclick = () => update(t => { const i = +b.dataset.moveParameter; [t.rows[i - 1], t.rows[i]] = [t.rows[i], t.rows[i - 1]]; }));
    section.querySelectorAll('[data-remove-column]').forEach(b => b.onclick = () => update(t => { const i = +b.dataset.removeColumn; t.columns.splice(i, 1); t.rows.forEach(r => r.splice(i, 1)); }));
  });
}
function captureMeasurements() {
  draft.values = {};
  $$('[data-group]').forEach(section => {
    const table = draft.measurement_tables[section.dataset.group];
    section.querySelectorAll('[data-heading]').forEach(input => table.columns[+input.dataset.heading] = input.value);
    table.rows = [...section.querySelectorAll('[data-parameter-row]')].map(row => [...row.querySelectorAll('[data-cell]')].map(cell => cell.matches('input') ? cell.value.trim() : cell.textContent));
    table.rows.forEach(row => { if (row[0]) draft.values[row[0]] = row[1] || ''; });
  });
}
