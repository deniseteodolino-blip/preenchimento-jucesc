# Códigos JUCEB (Bahia) — REGIN v4.23.x

Validados em produção (Imbassaí SPOT). **Diferem do JUCESC em vários códigos críticos.**

## Estado Civil (`ddlSocioEstadoCivil`) — JUCEB

| Código | Texto |
|---|---|
| 492 | SOLTEIRO |
| 493 | CASADO |
| 494 | DESQUITADO |
| 495 | SEPARADO |
| 496 | VIÚVO |
| 6574 | DIVORCIADO |
| 7111 | SOLTEIRO EM UNIÃO ESTÁVEL |
| 7129 | DIVORCIADO EM UNIÃO ESTÁVEL |
| 7130 | VIÚVO EM UNIÃO ESTÁVEL |

⚠ **Crítico**: "União Estável" no JUCEB é `7111`/`7129`/`7130`. Trocar com os códigos JUCESC (`6863`/`6864`/`6865`) causa o GRAVAR a falhar silenciosamente com "campos em vermelho" sem indicação visual.

## Regime de Bens (`ddlSocioRegime`) — igual ao JUCESC

| Código | Texto |
|---|---|
| 991 | COMUNHÃO PARCIAL DE BENS |
| 992 | COMUNHÃO UNIVERSAL DE BENS |
| 993 | PARTICIPAÇÃO FINAL NOS AQUESTOS |
| 994 | SEPARAÇÃO DE BENS |

## Tipo de Documento (`ddlTipoIdentidade`) — igual ao JUCESC

| Código | Texto |
|---|---|
| 2076 | CARTEIRA DE IDENTIDADE |
| 6562 | CARTEIRA DE IDENTIDADE PROFISSIONAL |
| 517 | CARTEIRA DE TRABALHO E PREVIDENCIA SOCIAL |
| 516 | CARTEIRA NACIONAL DE HABILITAÇÃO |
| 514 | CERTIFICADO DE RESERVISTA |
| 6634 | PASSAPORTE |
| 6573 | REGISTRO NACIONAL DE ESTRANGEIRO |
| 7038 | REGISTRO NACIONAL MIGRATÓRIO |
| 7117 | DOCUMENTO PROVISÓRIO DE RNM |

## Órgão Expedidor (`cbSocioOrgaoExpedidor`) — diferença importante

JUCEB e JUCESC têm **dicionários completamente diferentes** de órgãos expedidores (centenas de entradas cada). Não confie em valores hard-coded entre os dois — sempre busque por contains:

```javascript
const org = document.getElementById('ctl00_ContentPlaceHolder_cbSocioOrgaoExpedidor');
const candidatos = Array.from(org.options).filter(o => 
    o.text.startsWith('SSP - ') || o.value === 'SSP'
);
```

**Valores garantidos no JUCEB**:
- `SSP` → SECRETARIA DE SEGURANÇA PÚBLICA
- `DPF` → DEPARTAMENTO DE POLÍCIA FEDERAL
- `DETRAN` → DETRAN (variantes específicas por UF existem mas DETRAN puro funciona)

## Qualificação (`ddlSocioQualificacao`) — igual ao JUCESC

| Código | Texto |
|---|---|
| 22 | SÓCIO PESSOA FÍSICA RESIDENTE NO BRASIL |
| 38 | SÓCIO PESSOA FÍSICA RESID. OU DOMICILIADO NO EXTERIOR |
| 48 | SÓCIO PESSOA JURÍDICA RESIDENTE NO BRASIL |

## Particularidades do JUCEB

1. **A primeira renderização do formulário pode esconder os campos `txtSocioDataNascimento`, `ddlSocioEstadoCivil`, `rdbSocioSexoM/F`, `rdbAnalfabetoN`** se a sessão estiver "stale" após múltiplos postbacks. Solução: `navigate()` para a mesma URL e reabra o sócio. Após o reload limpo, os campos voltam.

2. **Endereço do representante**: o botão `BUSCAR CEP` do painel Representante **NÃO** dispara auto-fill no JUCEB (diferente do JUCESC). Os bairros mostram "NÃO ENCONTRADO" mesmo com CEP válido. Para representantes de PJ no JUCEB, recomenda-se deixar o endereço para preenchimento manual.

3. **Foreigners (RNE)**: O JUCEB exige Nacionalidade compatível com o RNE/RNM. Setar `ddlSocioNacionalidade` para o país de origem antes de definir TipoIdentidade=6573. Se persistir erro, mude qualificação para 38 (PF residente no exterior).
