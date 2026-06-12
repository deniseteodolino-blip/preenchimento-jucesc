#!/usr/bin/env python3
"""
Extrai a tabela de capital social de uma minuta Seazone e agrega por CPF/CNPJ.

A minuta tem uma tabela final no formato:

    Sócio       Total de quotas      Capital integralizado   Capital a integralizar   %

Cada sócio pode aparecer múltiplas vezes (subscrições separadas) — agregamos.

Uso:
    python extract_capital.py <minuta.pdf> <socios.json> [<output.json>]

Onde socios.json é a saída do parse_minuta.py (para mapear nome→CPF).
"""
import re
import json
import sys
import os
import subprocess
import tempfile
import unicodedata
from collections import defaultdict


def deaccent(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if not unicodedata.combining(c)).lower().strip()


def extract_text(pdf):
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp:
        txt = tmp.name
    subprocess.run(['pdftotext', '-layout', pdf, txt], check=True)
    with open(txt, 'r', encoding='utf-8') as f:
        text = f.read()
    os.unlink(txt)
    return text


def main():
    if len(sys.argv) < 3:
        print('Uso: python extract_capital.py <minuta.pdf> <socios.json> [<output.json>]', file=sys.stderr)
        sys.exit(1)
    pdf_path = sys.argv[1]
    socios_json = sys.argv[2]
    out_path = sys.argv[3] if len(sys.argv) > 3 else pdf_path.replace('.pdf', '_capital.json')

    socios = json.load(open(socios_json, encoding='utf-8'))
    # Index nome→ID
    name_to_id = {}
    for s in socios:
        n = deaccent(s.get('nome') or '')
        key = s.get('cpf') or s.get('cnpj')
        if key:
            name_to_id[n] = {'cpf': key, 'nome': s['nome'], 'tipo': s.get('tipo')}

    text = extract_text(pdf_path)
    text = re.sub(r'Clicksign[^\n]*\n', '', text)
    text = re.sub(r'Página \d+ de \d+\n?', '', text)

    # Procura o bloco da tabela
    m = re.search(r'(?:Total de\s+Capital\s+Capital a|Total\s+de\s+quotas\s+Capital)(.+?)Total\s+(?:R?\$?\s*)?[\d.,]+\s+(?:R\$\s*)?[\d.,]+\s+(?:R\$\s*)?[\d.,]+\s+100', text, re.DOTALL | re.IGNORECASE)
    if not m:
        # Fallback: busca por linhas que parecem da tabela
        m = re.search(r'(Sócio[\s\S]+?)\s+Total\s+', text, re.IGNORECASE)
    if not m:
        print('Tabela de capital não encontrada na minuta', file=sys.stderr)
        sys.exit(2)

    table_text = m.group(1)

    # Cada linha: NOME (multi-line) QUOTAS R$ INT R$ A_INT %
    row_pattern = re.compile(
        r'((?:[A-Z][\wÀ-ÿ\s\-\'.&]+?))\s+([\d.]+)\s+R\$\s*([\d.,]+)\s+R\$\s*([\d.,]+)\s+(\d+,\d+%?)',
        re.MULTILINE
    )

    rows = []
    for rm in row_pattern.finditer(table_text):
        nome = re.sub(r'\s+', ' ', rm.group(1)).strip()
        quotas = int(rm.group(2).replace('.', ''))
        int_cents = int(rm.group(3).replace('.', '').replace(',', ''))
        a_cents = int(rm.group(4).replace('.', '').replace(',', ''))
        rows.append({'nome': nome, 'quotas': quotas, 'int_cents': int_cents, 'a_int_cents': a_cents})

    print(f'Encontradas {len(rows)} linhas de capital')

    # Agrega por nome normalizado
    agg = defaultdict(lambda: {'quotas': 0, 'int_cents': 0, 'a_int_cents': 0, 'names': set()})
    for r in rows:
        k = deaccent(r['nome'])
        agg[k]['quotas'] += r['quotas']
        agg[k]['int_cents'] += r['int_cents']
        agg[k]['a_int_cents'] += r['a_int_cents']
        agg[k]['names'].add(r['nome'])

    # Match com CPFs do socios.json
    out = []
    unmatched = []
    for k, v in agg.items():
        info = name_to_id.get(k)
        if not info:
            # fuzzy: maior interseção de palavras
            best = None
            best_score = 0
            for nk, ninfo in name_to_id.items():
                common = sum(1 for w in k.split() if w in nk.split())
                if common > best_score and common >= 2:
                    best_score = common
                    best = ninfo
            info = best
        if info:
            out.append({
                'cpf': info['cpf'],
                'nome': info['nome'],
                'tipo': info['tipo'],
                'quotas': v['quotas'],
                'integralizado': f"{v['int_cents']/100:.2f}".replace('.', ','),
                'a_integralizar': f"{v['a_int_cents']/100:.2f}".replace('.', ','),
            })
        else:
            unmatched.append((k, list(v['names'])))

    # Totais
    tQ = sum(s['quotas'] for s in out)
    tI = sum(int(s['integralizado'].replace(',', '')) for s in out) / 100
    tA = sum(int(s['a_integralizar'].replace(',', '')) for s in out) / 100
    print(f'Totais: Quotas={tQ:,} | Integralizado=R$ {tI:,.2f} | A Integralizar=R$ {tA:,.2f}')
    print(f'Capital Social total: R$ {tI+tA:,.2f}')
    if unmatched:
        print(f'\n⚠ Não foi possível casar com CPF/CNPJ: {len(unmatched)}')
        for u in unmatched:
            print(f'  - {u[1][0]}')

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f'\n→ Salvo em {out_path}')


if __name__ == '__main__':
    main()
