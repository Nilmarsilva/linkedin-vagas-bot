# -*- coding: utf-8 -*-
"""Utilitario: mapeia campos e opcoes de um formulario de candidatura.
Uso: python mapear_form.py <url_da_vaga>
Gera campos.json e opcoes.json na pasta atual."""
import json
import os
import sys
import time
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")
URL = sys.argv[1] if len(sys.argv) > 1 else sys.exit("uso: python mapear_form.py <url>")
# sessao persistente do navegador (mesmo perfil do bot)
PERFIL = os.path.join(os.path.dirname(__file__), "..", "bot", "li_profile_chrome")

DUMP = """() => {
    const out = [];
    const lbl = el => {
        if (el.id) { const l = document.querySelector('label[for="'+el.id+'"]'); if (l) return l.innerText.trim(); }
        const l = el.closest('label'); if (l) return l.innerText.trim();
        let p = el.parentElement;
        for (let i = 0; i < 4 && p; i++) {
            const q = p.querySelector('label,legend,[class*=label],[class*=question]');
            if (q && q.innerText.trim()) return q.innerText.trim().slice(0,200);
            p = p.parentElement;
        }
        return el.getAttribute('aria-label') || el.placeholder || el.name || '';
    };
    document.querySelectorAll('input,select,textarea,[role=combobox]').forEach(el => {
        const t = el.type || el.getAttribute('role') || el.tagName;
        if (t === 'hidden' || t === 'submit' || t === 'button') return;
        out.push({tag: el.tagName, tipo: t, nome: el.name || '', label: lbl(el).slice(0,200),
                  opcoes: el.tagName === 'SELECT' ? [...el.options].map(o => o.text.trim()).filter(Boolean) : undefined});
    });
    document.querySelectorAll('input[type=checkbox],input[type=radio]').forEach(el => {
        const l = el.closest('label');
        out.push({tag: 'CHECK', tipo: el.type, nome: el.name || '', label: (l ? l.innerText : '').trim().slice(0,200)});
    });
    return out;
}"""

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        PERFIL, channel="chrome", headless=False, viewport={"width": 1280, "height": 900})
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto(URL, timeout=40000)
    time.sleep(5)
    btn = page.locator("button:has-text('Aplicar'), a:has-text('Aplicar'), button:has-text('Candidatar')").first
    if btn.count():
        try:
            btn.click(timeout=5000)
        except Exception:
            btn.dispatch_event("click")
        time.sleep(4)

    campos = []
    for _ in range(20):
        for c in page.evaluate(DUMP):
            if c not in campos:
                campos.append(c)
        ok = page.evaluate("""() => {
            const m = document.querySelector('[role=dialog],.MuiModal-root') || document.documentElement;
            let el = m;
            m.querySelectorAll('*').forEach(e => {
                if (e.scrollHeight > e.clientHeight + 50 && e.clientHeight > 200)
                    if (e.scrollHeight > el.scrollHeight) el = e;
            });
            const a = el.scrollTop; el.scrollTop += 500; return el.scrollTop > a;
        }""")
        if not ok:
            break
        time.sleep(0.4)
    open("campos.json", "w", encoding="utf-8").write(json.dumps(campos, ensure_ascii=False, indent=1))
    print(len(campos), "campos -> campos.json")

    # opcoes dos comboboxes
    combos, resultado = page.locator('[role="combobox"]'), []
    for i in range(combos.count()):
        cb = combos.nth(i)
        try:
            lbl = cb.evaluate("""el => { let p = el.parentElement;
                for (let i = 0; i < 5 && p; i++) {
                    const q = p.querySelector('label,[class*=label],[class*=question]');
                    if (q && q.innerText.trim()) return q.innerText.trim(); p = p.parentElement; }
                return el.innerText.trim().slice(0,100); }""")
            cb.scroll_into_view_if_needed(timeout=3000)
            cb.click(timeout=4000)
            time.sleep(1.0)
            op = cb.evaluate("""el => {
                const id = el.getAttribute('aria-controls') || el.getAttribute('aria-owns');
                let lb = id ? document.getElementById(id) : document.querySelector('[role=listbox],.MuiPopover-root ul,.MuiMenu-root ul');
                return lb ? [...lb.querySelectorAll('[role=option],li')].map(o => o.innerText.trim()).filter(Boolean).slice(0,80) : null; }""")
            resultado.append({"label": lbl[:150], "opcoes": op})
            page.keyboard.press("Escape")
            time.sleep(0.5)
        except Exception:
            page.keyboard.press("Escape")
    open("opcoes.json", "w", encoding="utf-8").write(json.dumps(resultado, ensure_ascii=False, indent=1))
    print(len(resultado), "comboboxes -> opcoes.json")
    ctx.close()
