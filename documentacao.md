# Documentação Operacional - Separação Banco x Folha

Esta documentação descreve o fluxo atual do projeto, os arquivos de entrada/saída e o mapeamento das posições usadas nos layouts texto (mainframe).

---

## 1) Visão geral do processo

O script principal `analise_separa_banco_folha.py` executa o fluxo abaixo:

1. Lê recursivamente arquivos de banco nas pastas `SIAPPES/` e `SIPPES/`.
2. Monta lista única de CPFs por banco (`preparo_lista_banco_XXX.txt`), com controle de duplicidades.
3. Lê o Excel da folha (guia `DETALHAMENTO_COMPARATIVO_MES_AT`), aplica filtros configurados e gera `preparo_excel_bco_XXX.txt`.
4. Cruza banco x folha e gera arquivos de encontrados/não encontrados para cada banco.
5. Lê `SMOP400-A3-2026.txt`, identifica CPFs com inconsistência bancária (TIPO 2 com conta `2222222222222`) e gera `Inconsistencia_Bancaria_XXX.txt` com base em `FOLHA_NAO_ENCONTRADOS_NO_BANCO_XXX`.
6. Consolida tudo no `RELATÓRIO_GERAL.txt`.

---

## 2) Pré-requisito do Excel de folha

Antes de executar o script, a planilha de folha precisa conter os dados de banco atual por CPF (ex.: colunas `BANCO` e `BANCO_ATUAL` preenchidas por PROCV/SEERRO ou método equivalente).

Pontos importantes:
- A guia lida pelo script é fixa: `DETALHAMENTO_COMPARATIVO_MES_AT`.
- O CPF é normalizado para 11 dígitos (`zfill(11)`), removendo pontuação.
- Os filtros de exclusão são definidos em `CONFIGURACAO_FILTROS` no topo do script.

---

## 3) Mapeamento de variáveis e posições (layouts texto)

> Referência de indexação:
> - Mainframe: intervalos mostrados no padrão humano (1-based, fim exclusivo no documento legado).
> - Python: `linha[inicio:fim]` em base 0 (fim exclusivo).

### 3.1) Arquivos de banco (`SIAPPES/*`, `SIPPES/*`)

No passo de leitura, o script processa as linhas em pares (`linha_banco_a` e `linha_banco_b`):

- `banco_id`: `linha_banco_a[0:3]`
- `nome_banco`: `linha_banco_a[43:73].strip()`
- `cpf_banco`: `linha_banco_b[21:33].strip().zfill(11)`

Esses campos alimentam:
- `preparo_lista_banco_XXX.txt` (`NOME;CPF`)
- Detecção de duplicados por banco e entre sistemas.

### 3.2) Arquivo SMOP (`SMOP400-A3-2026.txt`) - foco da inconsistência

Somente linhas de **TIPO 2** são usadas para inconsistência bancária.

Campos usados:
- `tipo`: Python `linha[0:1]` -> deve ser `'2'`
- `cpf`: Mainframe `[25:36]` -> Python `linha[24:35]`
- `conta`: Mainframe `[49:62]` -> Python `linha[48:61]`

Regra aplicada:
- Se `tipo == '2'` **e** `conta == "2222222222222"`, então o CPF entra no conjunto de inconsistência.
- CPF é normalizado com `strip().zfill(11)`.

### 3.3) Planilha Excel (folha)

Campos relevantes no fluxo:
- `CPF`: chave principal de cruzamento.
- `BANCO_ATUAL`: usado para separar os registros por banco (padronizado para 3 dígitos).
- Campos adicionais saem conforme `CONFIGURACAO_COLUNAS`.

---

## 4) Regras de negócio atuais

### 4.1) Filtros da folha (antes do cruzamento)

Os filtros atuais excluem registros de:
- `PG == 28`
- `PG == 14`
- `PG == 11` com condição adicional `SISTEMA == SIPPES`

Os excluídos são registrados em arquivos `FILTRO_EXCLUIDO_DA_FOLHA_*.txt`.

Regra especial do filtro `PG 11 / SIPPES`:
- O arquivo `FILTRO_EXCLUIDO_DA_FOLHA_PG_11.txt` considera apenas CPFs que **não** existem em nenhum `preparo_lista_banco_XXX.txt`.
- Esses CPFs **não** são removidos de `df_analise` e, portanto, não alteram os arquivos:
  - `FOLHA_ENCONTRADOS_NO_BANCO_XXX.txt`
  - `FOLHA_NAO_ENCONTRADOS_NO_BANCO_XXX.txt`
- Objetivo: o filtro vira um relatório de apoio, sem distorcer os resultados oficiais de cruzamento com banco.

### 4.2) Cruzamento principal

Para cada banco `XXX`:
- `FOLHA_ENCONTRADOS_NO_BANCO_XXX.txt`: CPF da folha presente na base do banco.
- `FOLHA_NAO_ENCONTRADOS_NO_BANCO_XXX.txt`: CPF da folha ausente na base do banco.

### 4.3) Inconsistência bancária (nova regra)

Base de comparação da inconsistência:
- Parte de `FOLHA_NAO_ENCONTRADOS_NO_BANCO_XXX` (lista em memória no fluxo).

Critério:
- CPF presente no conjunto de CPFs inconsistentes extraído do SMOP TIPO 2 (conta `2222222222222`).

Saída:
- `Inconsistencia_Bancaria_XXX.txt` (mesmo cabeçalho/formato da folha).

Observação importante:
- O arquivo `FOLHA_NAO_ENCONTRADOS_NO_BANCO_XXX.txt` permanece completo (sem remoção física de linhas).
- A subtração é aplicada somente no relatório consolidado.

---

## 5) Arquivos de saída gerados

Para cada banco `XXX`:
- `preparo_lista_banco_XXX.txt`
- `preparo_excel_bco_XXX.txt`
- `DUPLICADOS_BANCO_XXX.txt` (quando houver)
- `DUPLICADOS_INTERSISTEMAS_BANCO_XXX.txt` (quando houver)
- `BANCO_ENCONTRADOS_NA_FOLHA_XXX.txt`
- `BANCO_NAO_ENCONTRADOS_NA_FOLHA_XXX.txt`
- `FOLHA_ENCONTRADOS_NO_BANCO_XXX.txt`
- `FOLHA_NAO_ENCONTRADOS_NO_BANCO_XXX.txt`
- `Inconsistencia_Bancaria_XXX.txt`

Consolidado:
- `RELATÓRIO_GERAL.txt`

---

## 6) Itens do RELATÓRIO_GERAL

No bloco da FOLHA, o relatório apresenta:
- `Total ENCONTRADOS nos arquivos de banco`
- `CPFs da Folha em inconsistencia Bancaria`
- `Total NÃO ENCONTRADOS nos arquivos de banco` (valor ajustado = bruto - inconsistência)
- `Total NÃO ENCONTRADOS bruto (antes da subtração)` (valor original para auditoria)

---

## 7) Como executar

1. Organize os arquivos texto dos bancos nas pastas `SIAPPES/` e `SIPPES/`.
2. Garanta que `SMOP400-A3-2026.txt` esteja na raiz do projeto.
3. Execute:

```bash
python analise_separa_banco_folha.py
```

4. Selecione o arquivo Excel quando a janela abrir.
5. Ao final, valide os arquivos `Inconsistencia_Bancaria_XXX.txt` e `RELATÓRIO_GERAL.txt`.

---

## 8) Script auxiliar de diagnóstico

O script `analisar_nao_encontrados.py` permanece útil para análise estatística dos arquivos `FOLHA_NAO_ENCONTRADOS_NO_BANCO_*.txt`, ajudando a identificar padrões de divergência.
