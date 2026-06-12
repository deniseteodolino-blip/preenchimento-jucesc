#!/usr/bin/env python3
"""
Parseia uma minuta Seazone (PDF) e produz JSON estruturado com todos os sócios.

Uso:
    python parse_minuta.py <minuta.pdf> [<output.json>]

Saída JSON tem objetos com:
- num: posição na minuta
- tipo: 'PF' ou 'PJ'
- nome
- cpf (PF) ou cnpj (PJ)
- nire (PJ)
- nacionalidade, estado_civil_raw, profissao
- rg, orgao_expedidor, uf_orgao
- ec_jucesc, regime_jucesc (códigos JUCESC já mapeados)
- ec_juceb, regime_juceb (códigos JUCEB já mapeados)
- ddd, telefone, email
- cep, endereco_full
- sexo (heurística por nome — revise sempre)
"""
import re
import json
import sys
import os
import subprocess
import tempfile

EC_JUCESC = {
    'solteiro':           '492',
    'casado':             '493',
    'desquitado':         '494',
    'separado':           '495',
    'viuvo':              '496',
    'divorciado':         '6574',
    'solteiro_uniao':     '6863',
    'divorciado_uniao':   '6864',
    'viuvo_uniao':        '6865',
}

EC_JUCEB = {
    'solteiro':           '492',
    'casado':             '493',
    'desquitado':         '494',
    'separado':           '495',
    'viuvo':              '496',
    'divorciado':         '6574',
    'solteiro_uniao':     '7111',
    'divorciado_uniao':   '7129',
    'viuvo_uniao':        '7130',
}

REGIME_CODE = {
    'parcial':       '991',
    'universal':     '992',
    'aquestos':      '993',
    'separacao':     '994',
}

FEMALE_HINTS = (
    'ANA', 'PAULA', 'MARIA', 'POLIANA', 'VIVIANE', 'MELANIA', 'KATIA',
    'MONICA', 'CRISTINA', 'PATRICIA', 'VALNEIDE', 'NILZA', 'GRASIELA',
    'DENISE', 'FABIANA', 'MARCELA', 'GENECI', 'JULIA', 'JÚLIA',
    'PATRYCIA', 'CAROLINE', 'CAROLINA', 'CARINA', 'DANIELE',
    'DANIELLY', 'MARJORIE', 'MARCIA', 'MEIRE', 'SARA', 'IARA',
    'JAQUELINE', 'JEANINE', 'JULIANE', 'LARISSA', 'BARBARA',
    'BRUNA', 'BIANCA', 'HELOISA', 'HILDA', 'JAQUELINE', 'JULIANA',
    'TATIANA', 'VERONICA', 'GIULIANA', 'SILVANA', 'TALITA',
    'CHRISTINA', 'SOPHIA', 'MARIELLA', 'DANIELA', 'ELIZE',
    'ELISA', 'LUCY', 'ANNA', 'POLIANA', 'POLINA', 'MILA',
    'LAURA', 'CLAUDIA', 'CLÁUDIA', 'MAJDOLEIN', 'LETICIA', 'LETÍCIA',
    'LUA', 'NICOLE',
)


def deaccent(s):
    import unicodedata
    return ''.join(c for c in unicodedata.normalize('NFD', s) if not unicodedata.combining(c)).lower()


def extract_text(pdf_path):
    """Usa pdftotext -layout. Cai para pdfplumber se não disponível."""
    try:
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp:
            txt_path = tmp.name
        subprocess.run(['pdftotext', '-layout', pdf_path, txt_path], check=True)
        with open(txt_path, 'r', encoding='utf-8') as f:
            text = f.read()
        os.unlink(txt_path)
        return text
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback: pdfplumber
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            return '\n'.join(p.extract_text() or '' for p in pdf.pages)


def find_socios_block(text):
    """Encontra o bloco de sócios entre 'ingressantes:' e 'Resolvem alterar'."""
    text = re.sub(r'Clicksign[^\n]*\n', '', text)
    text = re.sub(r'Página \d+ de \d+\n?', '', text)
    m = re.search(r'sócios? ingressantes?:?(.*?)(?:Resolvem alterar|RESOLVEM ALTERAR|I - DO DESDOBRAMENTO|2\.1[\s\S]{0,50}retira)', text, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1)
    # Fallback: tudo a partir do primeiro (1) ou 1.
    m = re.search(r'(\n\s*\(?1[\)\.][​\s ]+[A-ZÀ-Ú6][\s\S]+)', text)
    return m.group(1) if m else text


def split_entries(block):
    """Divide o bloco em entries por '(N)' ou 'N.'.

    Lida com:
    - (1) NOME
    - 1. NOME
    - 1.​ NOME (com zero-width-space típico Clicksign)
    """
    parts = re.split(r'\n\s*(?:\((\d+)\)|(\d+)\.)[​\s ]+', block)
    entries = []
    # parts[0] = preamble; depois alterna (num1, num2, content)
    for i in range(1, len(parts) - 2, 3):
        num = parts[i] or parts[i+1]
        content = parts[i+2].strip()
        content = re.sub(r'\s+', ' ', content)
        entries.append({'num': int(num), 'raw': content})
    return entries


def find_cpf(raw):
    for pat in [
        r'CPF\s*n[º°.]?\s*([\d./\-]{11,15})',
        r'CPF\s*sob\s*o?\s*n[º°.]?\s*([\d./\-]{11,15})',
        r'CPF/MF\s*sob\s*n?[º°.]?\s*([\d./\-]{11,15})',
    ]:
        m = re.search(pat, raw, re.IGNORECASE)
        if m:
            return re.sub(r'\D', '', m.group(1))
    return None


def find_cnpj(raw):
    for pat in [
        r'CNPJ\s*n[º°.]?\s*([\d./\-]{14,20})',
        r'CNPJ\s*sob\s*o?\s*n[º°.]?\s*([\d./\-]{14,20})',
        r'CNPJ\s*sob\s*o\s*no\s*([\d./\-]{14,20})',
    ]:
        m = re.search(pat, raw, re.IGNORECASE)
        if m:
            return re.sub(r'\D', '', m.group(1))
    return None


def parse_rg_orgao(raw):
    """Extrai RG, órgão expedidor e UF a partir de padrões variados Seazone."""
    patterns = [
        # "Carteira de Identidade nº 1234567 SSP/SC"
        r'(?:Carteira de Identidade|Cédula de Identidade|carteira de identidade|cédula de identidade|RG)\s*(?:RG)?\s*n[º°.]?\s*([\w\d.\-]+)[\s,]+(?:Órgão Expedidor\s+)?([A-Z]{2,6})\s*/\s*([A-Z]{2})',
        # "Carteira de Identidade nº 1234567 SSP SC"
        r'(?:Carteira de Identidade|Cédula de Identidade|carteira de identidade|cédula de identidade|RG)\s*n[º°.]?\s*([\w\d.\-]+)\s+([A-Z]{2,6})\s+([A-Z]{2})',
        # "carteira nacional de habilitação nº 01234567 expedida pelo DETRAN/SC"
        r'(?:carteira nacional de habilitação)\s*n[º°.]?\s*([\w\d.\-]+)\s+expedida pelo\s+([A-Z]{3,7})\s*/?\s*([A-Z]{2})',
        # "Órgão Expedidor SSP/SC" separado
    ]
    for pat in patterns:
        m = re.search(pat, raw, re.IGNORECASE)
        if m:
            return m.group(1).strip(' ,.'), m.group(2).strip(), m.group(3).strip()
    # Fallback: Órgão Expedidor X UF separado de RG
    rg_m = re.search(r'(?:Carteira de Identidade|Cédula de Identidade|carteira de identidade|cédula de identidade|RG|carteira nacional de habilitação)\s*(?:RG)?\s*n[º°.]?\s*([\w\d.\-]+)', raw, re.IGNORECASE)
    org_m = re.search(r'Órgão Expedidor\s+([A-Z]{2,6})\s*/?\s*([A-Z]{2})?', raw, re.IGNORECASE)
    expedida_m = re.search(r'expedida pel[oa]\s+([A-Z]{2,7})\s*/?\s*([A-Z]{2})?', raw, re.IGNORECASE)
    rg = rg_m.group(1).strip(' ,.') if rg_m else None
    if org_m:
        return rg, org_m.group(1), org_m.group(2) or 'SC'
    if expedida_m:
        return rg, expedida_m.group(1), expedida_m.group(2) or 'SC'
    return rg, 'SSP', 'SC'


def parse_ec_regime(raw):
    """Detecta estado civil e regime."""
    ec_m = re.search(
        r',\s*(Solteir[oa]\(a\)|Solteir[oa]\s*em\s*Uni[ãa]o\s*Est[áa]vel|Casad[oa]\(a\)[^,]*|casado pelo regime[^,]*|casada pelo regime[^,]*|casado em regime[^,]*|casada em regime[^,]*|Divorciad[oa]\(a\)|Divorciad[oa]|Viúv[oa]\(a\)|Viúv[oa]|União Estável[^,]*|nascid[oa])',
        raw, re.IGNORECASE
    )
    if not ec_m:
        return 'desconhecido', None, None, None
    ec_text = ec_m.group(1).lower()
    if 'nascid' in ec_text:  # match falso
        return 'desconhecido', None, None, None
    # Categorizar
    if 'união' in ec_text or 'uniao' in ec_text or 'estável' in ec_text or 'estavel' in ec_text:
        if 'divorciad' in ec_text:
            key_ec = 'divorciado_uniao'
        elif 'viúv' in ec_text or 'viuv' in ec_text:
            key_ec = 'viuvo_uniao'
        else:
            key_ec = 'solteiro_uniao'
    elif 'casad' in ec_text:
        key_ec = 'casado'
    elif 'solteir' in ec_text:
        key_ec = 'solteiro'
    elif 'divorciad' in ec_text:
        key_ec = 'divorciado'
    elif 'viúv' in ec_text or 'viuv' in ec_text:
        key_ec = 'viuvo'
    elif 'separa' in ec_text:
        key_ec = 'separado'
    else:
        key_ec = 'desconhecido'

    # Regime (somente se casado ou união)
    key_reg = None
    if key_ec in ('casado', 'solteiro_uniao', 'divorciado_uniao', 'viuvo_uniao'):
        if 'universal' in ec_text or 'universal' in raw.lower()[:300]:
            key_reg = 'universal'
        elif 'separa' in ec_text or 'separação' in raw.lower()[:500] or 'separacao' in raw.lower()[:500]:
            key_reg = 'separacao'
        elif 'aquestos' in raw.lower()[:500]:
            key_reg = 'aquestos'
        else:
            key_reg = 'parcial'

    return key_ec, key_reg, ec_text, EC_JUCESC.get(key_ec),


def parse_entry(entry):
    raw = entry['raw']
    num = entry['num']
    out = {'num': num, 'raw': raw}

    is_pj = 'pessoa jurídica' in raw.lower()
    if is_pj:
        out['tipo'] = 'PJ'
        nm = re.match(r'^(.+?),\s*pessoa jurídica', raw)
        out['nome'] = re.sub(r'\s+', ' ', nm.group(1)).strip() if nm else None
        out['cnpj'] = find_cnpj(raw)
        nire = re.search(r'NIRE\s*(?:n[º°.]?\s*)?([\d]+)', raw)
        out['nire'] = nire.group(1) if nire else None
        # Representante
        rep_m = re.search(r'representad[ao]\[?a?\]?\s*por\s+([^,]+),', raw, re.IGNORECASE)
        if rep_m:
            out['representante_nome'] = re.sub(r'\s+', ' ', rep_m.group(1)).strip()
            rep_cpf = re.search(r'representad[ao].*?CPF[\s/\w]*?n[º°.]?\s*([\d./\-]{11,15})', raw, re.IGNORECASE)
            if rep_cpf:
                out['representante_cpf'] = re.sub(r'\D', '', rep_cpf.group(1))
    else:
        out['tipo'] = 'PF'
        nm = re.match(r'^([^,]+),', raw)
        out['nome'] = re.sub(r'\s+', ' ', nm.group(1)).strip() if nm else None
        out['cpf'] = find_cpf(raw)
        # Nacionalidade
        nac_m = re.match(r'^[^,]+,\s*([^,]+),', raw)
        out['nacionalidade'] = nac_m.group(1).strip() if nac_m else None
        # Profissão (heurística — terceiro campo geralmente)
        parts = [p.strip() for p in raw.split(',')[:6]]
        prof_candidates = [p for p in parts[2:5] if p and not re.search(r'(solteir|casad|divorciad|viúv|união estável|nascid)', p, re.IGNORECASE) and not re.search(r'inscrit', p, re.IGNORECASE)]
        out['profissao'] = prof_candidates[0] if prof_candidates else None
        # RG / órgão
        rg, org, uf = parse_rg_orgao(raw)
        out['rg'] = rg
        out['orgao_expedidor'] = org
        out['uf_orgao'] = uf
        # Estado civil + regime
        ec_data = parse_ec_regime(raw)
        if len(ec_data) >= 3:
            key_ec, key_reg, ec_text = ec_data[:3]
            out['estado_civil_raw'] = ec_text
            out['ec_key'] = key_ec
            out['regime_key'] = key_reg
            out['ec_jucesc'] = EC_JUCESC.get(key_ec)
            out['ec_juceb'] = EC_JUCEB.get(key_ec)
            out['regime_jucesc'] = REGIME_CODE.get(key_reg) if key_reg else None
            out['regime_juceb'] = REGIME_CODE.get(key_reg) if key_reg else None
        # Telefone / email
        tel_m = re.search(r'telefone:?\s*\(?(\d{2})\)?[\s\-.]*([\d.\s\-]+?)(?:[,;]|\s+e\s+|\s+endere)', raw, re.IGNORECASE)
        if tel_m:
            out['ddd'] = tel_m.group(1)
            out['telefone'] = re.sub(r'\D', '', tel_m.group(2))[-9:]
        em_m = re.search(r'(?:eletrônico|e-?mail):?\s*([\w.+\-]+@[\w.\-]+)', raw, re.IGNORECASE)
        if em_m:
            out['email'] = em_m.group(1).strip(' .,;')
        cep_m = re.search(r'CEP[:\s]*([\d.\-]{8,10})', raw)
        if cep_m:
            out['cep'] = re.sub(r'\D', '', cep_m.group(1))
        # Sexo (heurística)
        if out['nome']:
            up = out['nome'].upper()
            out['sexo_heuristico'] = 'F' if any(up.startswith(h + ' ') or up == h for h in FEMALE_HINTS) else 'M'
        # Data nascimento (default Seazone)
        nasc_m = re.search(r'nascid[oa]\s+em\s+(\d{2}/\d{2}/\d{4})', raw, re.IGNORECASE)
        out['data_nascimento'] = nasc_m.group(1) if nasc_m else '09/08/1980'

    return out


def main():
    if len(sys.argv) < 2:
        print('Uso: python parse_minuta.py <minuta.pdf> [<output.json>]', file=sys.stderr)
        sys.exit(1)
    pdf = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else pdf.replace('.pdf', '.json')

    text = extract_text(pdf)
    block = find_socios_block(text)
    entries = split_entries(block)
    socios = [parse_entry(e) for e in entries]
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(socios, f, ensure_ascii=False, indent=2)
    print(f'Parseados {len(socios)} sócios → {out}')
    pf = sum(1 for s in socios if s.get('tipo') == 'PF')
    pj = sum(1 for s in socios if s.get('tipo') == 'PJ')
    print(f'  PF: {pf} | PJ: {pj}')
    # Sumário rápido
    for s in socios[:3]:
        print(f"  #{s['num']:2} {s.get('nome','')[:45]:45} {s.get('cpf') or s.get('cnpj','')}")


if __name__ == '__main__':
    main()
