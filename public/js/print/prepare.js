let printBusy = false;
async function preparedPrint(kind) {
  if (printBusy) { toast('Print preparation is already in progress'); return; }
  printBusy = true;
  try {
    await Promise.all([...$('#print').querySelectorAll('img')].map(async img => {
      try { await img.decode(); } catch (_) { throw new Error('Print logo or stamp could not load. Please retry printing.'); }
      if (!img.naturalWidth) throw new Error('Print image is unavailable. Please retry printing.');
    }));
    if (document.fonts?.ready) await document.fonts.ready;
    document.body.classList.add(kind);
    await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
    window.print();
  } catch (error) { toast(error.message); }
  finally { document.body.classList.remove(kind); printBusy = false; }
}
