"""One-time extraction from the user-supplied approved trial archive."""
from pathlib import Path
import datetime
import hashlib
import json
import re
import sqlite3
import zipfile

ROOT = Path(__file__).resolve().parents[1]
backup = ROOT / 'backups' / datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
backup.mkdir(parents=True)
files = [p for p in ROOT.rglob('*') if p.is_file() and not {'backups', '__pycache__', 'dist'}.intersection(p.relative_to(ROOT).parts)]
with zipfile.ZipFile(backup / 'project-before.zip', 'w', zipfile.ZIP_DEFLATED) as z:
    for p in files:
        z.write(p, p.relative_to(ROOT))
src = sqlite3.connect(f'file:{(ROOT / "data/echo.sqlite3").as_posix()}?mode=ro', uri=True)
dst = sqlite3.connect(backup / 'echo-consistent.sqlite3')
src.backup(dst)
counts = {t: src.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in ('users','patients','visits','doctors','settings','audit')}
src.close(); dst.close()
(backup / 'manifest.json').write_text(json.dumps({'counts': counts, 'sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}, indent=2))
archive = zipfile.ZipFile(Path.home() / 'Downloads/AFZAL_HEART_CENTRE_ECHO_SYSTEM_TRIAL_FINAL.zip')
prefix = 'afzal_echo_final/public/'
lines = archive.read(prefix+'app.js').decode('utf-8-sig').splitlines()
groups = {
    'utils/escape.js':[1], 'state.js':[2,13], 'utils/dates.js':[3],
    'screens/report-template.js':[4,5,6], 'api.js':[7], 'components/toast.js':[8],
    'components/forms.js':[9,10], 'app.js':[11,49], 'screens/auth.js':[12],
    'components/sidebar.js':[14], 'components/shell.js':[15], 'components/stats.js':[16],
    'screens/receptionist.js':[17], 'screens/patients.js':[18,21,24,25],
    'components/tables.js':[19,20], 'utils/masks.js':[22,23],
    'screens/patient-record.js':[26], 'screens/operator.js':[27,28,29],
    'screens/report-editor.js':[30,31,32,33,34], 'screens/doctor.js':[35,36],
    'screens/analytics.js':[37,38,39,40,41,42], 'screens/admin.js':[43],
    'utils/files.js':[44], 'print/report.js':[45,46,48], 'print/token.js':[47],
}
def write(rel, text):
    p=ROOT/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(text,encoding='utf-8')
for name, nums in groups.items():
    s='\n'.join(lines[i-1] for i in nums)+'\n'
    s=s.replace("patient=state.patients.find(p=>p.id===visit.patient_id)", "patient=await api('patient',{id:visit.patient_id})")
    s=s.replace("patient=state.patients.find(p=>p.id===v.patient_id)", "patient=await api('patient',{id:v.patient_id})")
    s=s.replace("patient=state.patients.find(p=>p.id===id)||patient", "patient=await api('patient',{id})")
    if name=='screens/operator.js':
        s=s.replace('state.active.filter(v=>v.report)', 'state.drafts').replace('visit=state.active.find(v=>v.id===+b.dataset.draft)', 'visit=state.drafts.find(v=>v.id===+b.dataset.draft)')
        s=s.replace('workTable(state.waiting,true)', 'workTable(operator?state.waiting:state.issued,true)').replace('let v=state.waiting.find(x=>x.id===+b.dataset.reprint)', 'let v=state.issued.find(x=>x.id===+b.dataset.reprint)')
    if name=='screens/report-editor.js':
        s=s.replace("visit.status==='in_progress'?", "visit.status!=='final'?").replace('In progress · locked to you', "In progress / draft · locked to you")
        # The print action must remain enabled outside the locked report fieldset.
        s=s.replace('<div class="panel final-actions">', '</fieldset><div class="panel final-actions">').replace('</div></fieldset></form>', '</div></form>')
        s=s.replace('draft.findings||DEFAULT_REPORT','draft.findings??DEFAULT_REPORT').replace('draft.conclusion||DEFAULT_CONCLUSION','draft.conclusion??DEFAULT_CONCLUSION')
    if name=='components/shell.js':
        s=s.replace('function render(){', 'function render(){page=allowedPage(page);')
        start=s.index(';({dashboard,patients,')
        s=s[:start]+';routeScreen()}\n'
    if name=='print/report.js':
        s=s.replace('function meta(){let prev=', "function meta(){let saved=JSON.parse(visit.report||'{}'),person=saved.patient||patient;let prev=")
        # Only the metadata function uses patient; use its immutable snapshot.
        s=s.replace('esc(patient.', 'esc(person.')
        s=s.replace("${prev?fmtDate(prev.finalized):'—'}", "${fmtDate(saved.previous_echo!==undefined?saved.previous_echo:prev?.finalized)}")
        s=s.replace('${r.doctor.stamp_image}', '${esc(r.doctor.stamp_image)}')
    write('public/js/'+name,s)
write('public/js/router.js', '''// Route access mirrors the server's permission boundary.
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
''')
write('public/js/app.js', '''// Application lifecycle. Screens and transport live in their own files.
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
''')
write('public/js/api.js', '''async function api(path, data) {
  const response = await fetch('/api/' + path, {
    method: data === undefined ? 'GET' : 'POST',
    headers: {'Content-Type': 'application/json'},
    body: data === undefined ? undefined : JSON.stringify(data)
  });
  const body = await response.json();
  if (!response.ok) {
    if (response.status === 401 && path !== 'login') window.dispatchEvent(new Event('session-expired'));
    const error = new Error(body.error || 'Request failed');
    error.status = response.status; throw error;
  }
  return body;
}
''')
# Preserve the exact stylesheet cascade with ordered CSS layers, while separating ownership.
css=archive.read(prefix+'style.css').decode('utf-8-sig')
rules=[]; start=0; depth=0
for i,ch in enumerate(css):
    if ch=='{': depth+=1
    elif ch=='}':
        depth-=1
        if depth==0: rules.append(css[start:i+1].strip()); start=i+1
categories={k:[] for k in ['base','layout','components','forms','role-screens','token-print','report-print']}
for rule in rules:
    selector=rule.split('{',1)[0]
    if 'ticket' in selector or 'token-' in selector: cat='token-print'
    elif any(t in selector for t in ['print','report-page','echo-table','signature','doctor-stamp','created-by','conclusion']): cat='report-print'
    elif selector.startswith('@media'): cat='layout'
    elif any(t in selector for t in ['.shell','aside','nav','.brand','header','main','.quick','.account']): cat='layout'
    elif any(t in selector for t in ['form','input','textarea','fieldset','label','.measure','.editor','.custom','.line']): cat='forms'
    elif any(t in selector for t in ['reception','register','admin','draft','queue','performance','auth','login']): cat='role-screens'
    elif any(t in selector for t in ['panel','stats','table','toast','badge','hero','visit','empty','actions','inline','two','section-kicker','live-dot']): cat='components'
    else: cat='base'
    categories[cat].append(rule)
for cat, body in categories.items(): write('public/css/'+cat+'.css','\n'.join(body)+'\n')
# Categories are disjoint except intentional responsive overrides, loaded last below.
order=['base','components','forms','role-screens','token-print','report-print','layout']
write('public/style.css','\n'.join('@import url("/css/'+n+'.css");' for n in order)+'\n')
scripts=[name for name in groups if name!='app.js']+['router.js','app.js']
html=archive.read(prefix+'index.html').decode('utf-8-sig')
html=html.replace('<script src="/app.js"></script>', '\n'.join('<script defer src="/js/'+name+'"></script>' for name in scripts))
write('public/index.html',html)
write('public/app.js','// Legacy URL retained. The application is loaded by public/index.html from /js/.\n')
for asset in ['hospital-bg.jpg','logo-left.png','logo-right.png']:
    p=ROOT/'public/assets'/asset; p.parent.mkdir(exist_ok=True); p.write_bytes(archive.read(prefix+asset))
print('Backup:',backup)
print('Baseline counts:',counts)
