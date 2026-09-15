function appHeader() {
  const titles = {
    dashboard: user.role === 'operator' ? 'Pending Echo Queue' : user.role === 'admin' ? 'System Administration' : user.role === 'doctor' ? 'Doctor Performance' : 'Today Overview',
    patients: 'Patient Registry', totalPatients: 'Total Registered Patients',
    queue: user.role === 'operator' ? 'In Progress' : 'Issued Tokens / Reprint',
    drafts: 'Draft Reports', historyPage: 'Completed Reports', performance: 'My Performance',
    operatorPerformance: 'Operator Performance', analytics: 'Performance Analytics',
    settings: 'Administration', record: 'Patient Record', editor: 'Echo Findings'
  };
  return `<header><div><small>AFZAL HEART CENTRE &middot; SIALKOT</small><h2>${titles[page] || 'Echo Management'}</h2></div><div class="account"><span>${esc(user.name)} <small>${esc(user.role)}</small></span><button id="logout" class="ghost">Sign out</button></div></header>`;
}
