# preenchimento-jucesc-juceb

Skill do Claude (Cowork) para automatizar o preenchimento de QSA (Página 5),
Distribuição de Quotas (Página 6) e Representantes de PJs nos sistemas REGIN
da **JUCESC** (Santa Catarina) e **JUCEB** (Bahia) a partir de minutas de
alteração contratual.

## O que faz

- Parseia minutas Seazone em PDF (`scripts/parse_minuta.py`)
- Extrai a tabela de capital social agregada por CPF (`scripts/extract_capital.py`)
- Gera planilha XLSX de referência com códigos JUCESC/JUCEB já mapeados (`scripts/generate_reference_xlsx.py`)
- Orienta o Claude através do workflow de postbacks ASP.NET dos sistemas REGIN
  (com waits adequados, tratamento de bugs conhecidos como "campos em vermelho
  sem destaque", e fallback para reload da página)

## Quando aciona

A skill é acionada automaticamente sempre que o usuário:

- Anexa uma minuta de "alteração contratual" de uma "SPE LTDA" Seazone
- Pede preenchimento de requerimento nos URLs `regin.jucesc.sc.gov.br` ou
  `regin.juceb.ba.gov.br`
- Solicita "revisar todos os sócios", "preencher o capital de cada sócio" ou
  "preencher o representante" de uma sócia PJ

## Estrutura

```
preenchimento-jucesc-juceb/
├── SKILL.md                       Visão geral + roteiro principal
├── references/
│   ├── codigos-jucesc.md          Estado Civil, Regime, Tipo Doc (SC)
│   ├── codigos-juceb.md           Mesmos campos para BA (diferenças críticas)
│   ├── workflow-pagina5.md        QSA — PF Novo, PF Atual, PJ
│   ├── workflow-pagina6.md        Distribuição de quotas
│   └── workflow-representante.md  Sub-form de representante de PJ
└── scripts/
    ├── parse_minuta.py
    ├── extract_capital.py
    └── generate_reference_xlsx.py
```

## Instalação como skill no Cowork

1. Empacote a pasta: `python -m scripts.package_skill preenchimento-jucesc-juceb`
   (a partir do diretório do `skill-creator`)
2. Abra o `.skill` resultante no Cowork — o app oferece "Save skill"

Ou clone este repositório dentro de `~/.claude/skills/` (ou no diretório de skills
do seu setup Cowork) — a skill aparece na lista de `available_skills` automaticamente.

## Dependências dos scripts

- `pdftotext` (poppler-utils) — usado pelo `parse_minuta.py` e `extract_capital.py`
- Python 3.10+
- `openpyxl` — usado pelo `generate_reference_xlsx.py`

Instalação típica:

```bash
sudo apt install poppler-utils
pip install openpyxl
```

## Diferenças críticas JUCESC × JUCEB

Os códigos para "União Estável" diferem entre os dois sistemas:

| Estado Civil | JUCESC | JUCEB |
|---|---|---|
| Solteiro em União Estável | 6863 | 7111 |
| Divorciado em União Estável | 6864 | 7129 |
| Viúvo em União Estável | 6865 | 7130 |

Confundir os dois causa o erro "Para passar a próxima etapa é necessário
preencher os campos em vermelho" sem destaque visual de qual campo. Veja
`references/codigos-jucesc.md` e `references/codigos-juceb.md`.

## Status

Validado em produção nos seguintes requerimentos Seazone:

- ✅ URUBICI SPOT SPE LTDA (JUCESC) — 58 sócios
- ✅ IMBASSAÍ SPOT SPE LTDA (JUCEB) — 43 sócios + Capital
- ✅ SUL DA ILHA SPOT SPE LTDA (JUCESC) — 55 sócios
- ✅ ROSA SPOT (JUCESC) — 8 novos + 23 revisões
- ✅ CACHOEIRA SPOT (JUCESC) — parse validado

## Licença

Uso interno Seazone.
