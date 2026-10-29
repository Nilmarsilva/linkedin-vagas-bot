# -*- coding: utf-8 -*-
"""
Busca de vagas no LinkedIn com sessao persistente.

Uso:
    python vagas_linkedin.py login    -> abre o navegador pra voce logar uma vez
    python vagas_linkedin.py buscar   -> roda as pesquisas e gera vagas.csv/json

A sessao fica salva em ./li_profile (nao precisa logar de novo).
O script so LE resultados de busca - nao clica em "candidatar-se".
"""
import csv
import json
import random
import re
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = Path(__file__).parent
PROFILE_DIR = BASE / "li_profile_chrome"
SAIDA = BASE.parent / "painel"
SAIDA.mkdir(exist_ok=True)
CSV_OUT = SAIDA / "vagas.csv"
JSON_OUT = SAIDA / "vagas.json"

# (descricao, keywords, location, filtros extra da URL do LinkedIn)
# f_E: 1=estagio, 2=junior | f_WT: 1=presencial, 2=remoto, 3=hibrido | f_TPR=r604800 (ultima semana)
BUSCAS = [
    ("Estagio dev - remoto", "estagio desenvolvimento de software", "Brasil",
     "f_E=1&f_WT=2&f_TPR=r604800"),
    ("Estagio dev - BH", "estagio desenvolvimento", "Belo Horizonte, Minas Gerais, Brasil",
     "f_E=1&f_TPR=r604800"),
    ("Estagio TI - remoto", "estagio tecnologia da informacao", "Brasil",
     "f_E=1&f_WT=2&f_TPR=r604800"),
    ("Dev junior - remoto", "desenvolvedor junior", "Brasil",
     "f_E=2&f_WT=2&f_TPR=r604800"),
    ("Dev junior - BH", "desenvolvedor junior", "Belo Horizonte, Minas Gerais, Brasil",
     "f_E=2&f_TPR=r604800"),
    ("Back-end junior - remoto", "desenvolvedor back-end junior", "Brasil",
     "f_E=2&f_WT=2&f_TPR=r604800"),
    ("C# junior - remoto", "desenvolvedor C# junior", "Brasil",
     "f_E=2&f_WT=2&f_TPR=r604800"),
    ("Python junior - remoto", "desenvolvedor Python junior", "Brasil",
     "f_E=2&f_WT=2&f_TPR=r604800"),
]

PAUSA = lambda: time.sleep(random.uniform(1.8, 3.5))  # ritmo humano


def login():
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            str(PROFILE_DIR), channel="chrome", headless=False,
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto("https://www.linkedin.com/login")
        print("\n>>> Faca o login no LinkedIn na janela que abriu.")
        print(">>> Aguardando voce chegar no feed (timeout de 5 min)...\n")
        for _ in range(150):
            url = page.url
            if "/feed" in url or "/in/" in url or "/mynetwork" in url or "/jobs" in url:
                break
            try:
                page.wait_for_timeout(2000)
            except Exception:
                break
        ctx.close()
    print("Sessao salva em:", PROFILE_DIR)


def parse_card(txt):
    linhas = [l.strip() for l in txt.split("\n") if l.strip() and l.strip() != "•"]
    if linhas and linhas[0].startswith("Selecionada,"):
        linhas.pop(0)
    titulo = linhas[0] if linhas else ""
    if len(linhas) > 1 and linhas[1] == titulo:
        linhas.pop(0)
    return {
        "titulo": titulo.replace("(vaga verificada)", "").strip(),
        "empresa": linhas[1] if len(linhas) > 1 else "",
        "local": linhas[2] if len(linhas) > 2 else "",
    }


def coletar_vagas(page, limite=15):
    # a lista de vagas = a div rolavel com mais filhos
    page.evaluate("""() => {
        let lista = null;
        document.querySelectorAll('div').forEach(el => {
            if (el.scrollHeight > el.clientHeight + 300 && el.children.length > 10)
                if (!lista || el.children.length > lista.children.length) lista = el;
        });
        if (lista) lista.setAttribute('data-vagas-lista', '1');
    }""")
    container = page.locator("div[data-vagas-lista]")
    if not container.count():
        # pagina pode demorar mais pra renderizar: tenta de novo
        time.sleep(4)
        page.evaluate("""() => {
            let lista = null;
            document.querySelectorAll('div').forEach(el => {
                if (el.scrollHeight > el.clientHeight + 300 && el.children.length > 10)
                    if (!lista || el.children.length > lista.children.length) lista = el;
            });
            if (lista) lista.setAttribute('data-vagas-lista', '1');
        }""")
        container = page.locator("div[data-vagas-lista]")
        if not container.count():
            return []
    # rola a lista pra renderizar cards virtualizados
    for _ in range(3):
        page.evaluate("""() => { const l = document.querySelector('div[data-vagas-lista]');
                                if (l) l.scrollTop += l.clientHeight; }""")
        time.sleep(0.8)
    page.evaluate("""() => { const l = document.querySelector('div[data-vagas-lista]');
                            if (l) l.scrollTop = 0; }""")
    time.sleep(0.6)
    cards = container.locator(":scope > div[data-display-contents]")
    n = min(cards.count(), limite)
    itens = cards.evaluate_all("""els => els.slice(0, %d).map(c => {
        const k = c.querySelector('[componentkey^="job-card-component-ref-"]');
        return {key: k ? k.getAttribute('componentkey') : '', txt: c.innerText};
    })""" % n)
    out = []
    for it in itens:
        m = re.search(r"job-card-component-ref-(\d+)", it["key"])
        info = parse_card(it["txt"])
        if not info["titulo"]:
            continue
        jid = m.group(1) if m else ""
        info["id"] = jid or info["titulo"] + "|" + info["empresa"]
        info["link"] = f"https://www.linkedin.com/jobs/view/{jid}" if jid else ""
        out.append(info)
    return out


def rodar_buscas(page):
    todas, vistos = [], set()
    # checa se a sessao ainda vale
    page.goto("https://www.linkedin.com/feed/")
    PAUSA()
    if "login" in page.url or "authwall" in page.url:
        sys.exit("Sem sessao ativa no LinkedIn nesse navegador.")

    for desc, kw, loc, extra in BUSCAS:
        url = ("https://www.linkedin.com/jobs/search/?"
               f"keywords={kw.replace(' ', '%20')}"
               f"&location={loc.replace(' ', '%20').replace(',', '%2C')}"
               f"&{extra}")
        print(f"[{desc}]")
        try:
            page.goto(url, timeout=30000)
        except Exception:
            print("  timeout, pulando")
            continue
        time.sleep(4)

        cards = coletar_vagas(page)
        novos = 0
        for c in cards:
            if c["id"] in vistos:
                continue
            vistos.add(c["id"])
            c["busca"] = desc
            todas.append(c)
            novos += 1
        print(f"  {len(cards)} lidos, {novos} novos")
        PAUSA()

    JSON_OUT.write_text(json.dumps(todas, ensure_ascii=False, indent=2), encoding="utf-8")
    with open(CSV_OUT, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["titulo", "empresa", "local", "busca", "link"],
                           extrasaction="ignore")
        w.writeheader()
        w.writerows(todas)
    print(f"\n{len(todas)} vagas unicas -> {CSV_OUT.name} / {JSON_OUT.name}")


def buscar():
    if not PROFILE_DIR.exists():
        sys.exit("Rode primeiro: python vagas_linkedin.py login")
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            str(PROFILE_DIR), channel="chrome", headless=False,
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        rodar_buscas(page)
        ctx.close()


def buscar_cdp(porta=9222):
    """Conecta num Chrome ja aberto com --remote-debugging-port=<porta>."""
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://localhost:{porta}")
        ctx = browser.contexts[0]
        page = ctx.new_page()
        rodar_buscas(page)
        page.close()
        # nao fecha o browser: ele e do usuario


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "login":
        login()
    elif cmd == "buscar":
        buscar()
    elif cmd == "cdp":
        buscar_cdp()
    else:
        print(__doc__)
