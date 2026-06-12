# Códigos JUCESC (Santa Catarina) — REGIN v4.x

Validados em produção (Urubici, Cachoeira, Sul da Ilha, Rosa Spot).

## Estado Civil (`ddlSocioEstadoCivil`)

| Código | Texto |
|---|---|
| 492 | SOLTEIRO |
| 493 | CASADO |
| 494 | DESQUITADO |
| 495 | SEPARADO JUDICIALMENTE |
| 496 | VIÚVO |
| 6574 | DIVORCIADO |
| 6863 | SOLTEIRO EM UNIÃO ESTÁVEL |
| 6864 | DIVORCIADO EM UNIÃO ESTÁVEL |
| 6865 | VIÚVO EM UNIÃO ESTÁVEL |

⚠ **Crítico**: "União Estável" no JUCESC é `6863` (não `7111` como no JUCEB). Esse erro é causa frequente do alerta "campos em vermelho" sem destaque visual.

## Regime de Bens (`ddlSocioRegime`) — aparece após escolher CASADO ou União Estável

| Código | Texto |
|---|---|
| 991 | COMUNHÃO PARCIAL DE BENS |
| 992 | COMUNHÃO UNIVERSAL DE BENS |
| 993 | PARTICIPAÇÃO FINAL NOS AQUESTOS |
| 994 | SEPARAÇÃO DE BENS |

## Tipo de Documento (`ddlTipoIdentidade`)

| Código | Texto | Quando usar |
|---|---|---|
| 2076 | CARTEIRA DE IDENTIDADE | RG normal (SSP) — default mais comum |
| 6562 | CARTEIRA DE IDENTIDADE PROFISSIONAL | CRM, CRC, OAB, CREA, CRO etc. |
| 517 | CARTEIRA DE TRABALHO E PREVIDENCIA SOCIAL | CTPS |
| 516 | CARTEIRA NACIONAL DE HABILITAÇÃO | CNH (órgão DETRAN) |
| 514 | CERTIFICADO DE RESERVISTA | raro |
| 6634 | PASSAPORTE | estrangeiros |
| 6573 | REGISTRO NACIONAL DE ESTRANGEIRO | RNE |
| 7038 | REGISTRO NACIONAL MIGRATÓRIO | RNM |
| 7117 | DOCUMENTO PROVISÓRIO DE REGISTRO NACIONAL MIGRATÓRIO | raro |

**Regra prática para deduzir tipo a partir do órgão expedidor já preenchido:**
- `SSP` ou `IFP` ou `IGP` ou `II` ou similar → `2076`
- `DETRAN` → `516`
- `CRM`, `CRC`, `OAB`, `CREA`, `CRO`, `CRO`, `CFA`, `CFM` etc. → `6562`
- `PF` ou `DPF` ou `CGPI` → `6573` ou `7038` para estrangeiros

## Qualificação do Sócio (`ddlSocioQualificacao`)

| Código | Texto |
|---|---|
| 22 | SÓCIO PESSOA FÍSICA RESIDENTE NO BRASIL |
| 38 | SÓCIO PESSOA FÍSICA RESID. OU DOMICILIADO NO EXTERIOR |
| 29 | SÓCIO PESSOA FÍSICA INCAPAZ OU RELATIVAMENTE INCAPAZ |
| 30 | SÓCIO OU ACIONISTA PESSOA FÍSICA MENOR (ASSISTIDO/REPRESENTADO) |
| 48 | SÓCIO PESSOA JURÍDICA RESIDENTE NO BRASIL |
| 8 | ADMINISTRADOR |
| 52 | SÓCIO COM CAPITAL |

Normalmente o sistema já vem com 22 ou 48 pré-selecionado. Não mexer salvo necessidade explícita.

## Tipo Logradouro (`cbSocioTipoLogradouro`)

| Código | Texto |
|---|---|
| 79 | AVENIDA |
| 126 | ESTRADA |
| 158 | LOTEAMENTO |
| 174 | PASSEIO |
| 190 | PRAÇA |
| 208 | RUA |
| 213 | SERVIDÃO |
| 225 | TRAVESSA |

## Tipo Assistido / Representado (representante) (`ddlSocioRepresentanteTipoAssistidoRepresentado`)

| Código | Texto | Quando usar |
|---|---|---|
| 301 | PAI/REPRESENTANTE | menor representado pelo pai |
| 302 | MAE/REPRESENTANTE | menor representado pela mãe |
| 303 | CURADOR/REPRESENTANTE | tutela |
| 304 | REPRESENTANTE | **default para PJ** representada por sócio-administrador |
| 305 | PAI/ASSISTENTE | menor relativamente incapaz |
| 306 | MAE/ASSISTENTE | menor relativamente incapaz |
| 307 | CURADOR/ASSISTENTE | |
| 308 | TUTOR | |
| 309 | PROCURADOR | |
| 312 | INVENTARIANTE | |

Para representante de PJ comum, use sempre `304`.

## Nacionalidade (`ddlSocioNacionalidade`)

Valores comuns:
- 154 = BRASILEIRA
- 177 = SUL-COREANA
- 7 = ARGENTINA
- 8 = ARMÊNIA
- 153 = BOLIVIANA
- 178 = NORTE-COREANA

Lista completa tem ~240 entradas; raramente precisa mudar do default 154.
