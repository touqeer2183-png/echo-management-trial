function flowControls() {
  return `<div class="flow-controls">${['AR','MR','TR','PR'].map(name => `<div class="flow-control"><strong>${name}</strong><button type="button" class="light" data-flow="${name}" data-step="-1" aria-label="Decrease ${name}">&minus;</button><output id="flow-${name}">&mdash;</output><button type="button" data-flow="${name}" data-step="1" aria-label="Increase ${name}">+</button></div>`).join('')}</div>`;
}
function flowGrade(name) {
  const match = $('#color').value.match(new RegExp('\\b' + name + '\\s*(?:(\\d+)\\s*\\+|(\\+{1,}))', 'i'));
  return match ? (match[1] ? Number(match[1]) : match[2].length) : 0;
}
function updateFlowLabels() {
  ['AR','MR','TR','PR'].forEach(name => { const grade = flowGrade(name); $('#flow-' + name).textContent = grade ? '+'.repeat(Math.min(grade, 20)) : '—'; });
}
function bindFlow() {
  updateFlowLabels();
  $('#color').addEventListener('input', updateFlowLabels);
  $$('[data-flow]').forEach(button => button.onclick = () => {
    const name = button.dataset.flow;
    const grade = Math.max(0, Math.min(20, flowGrade(name) + Number(button.dataset.step)));
    const pattern = new RegExp('\\b' + name + '\\s*(?:\\d+\\s*\\+|\\++)', 'i');
    let text = $('#color').value;
    if (pattern.test(text)) text = text.replace(pattern, grade ? name + ' ' + '+'.repeat(grade) : '');
    else if (grade) text = [text.trim(), name + ' ' + '+'.repeat(grade)].filter(Boolean).join(', ');
    $('#color').value = text.replace(/,\s*,/g, ',').replace(/^\s*,\s*|,\s*$/g, '').trim();
    updateFlowLabels();
  });
}
