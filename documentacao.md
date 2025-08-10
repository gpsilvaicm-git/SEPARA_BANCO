# Documentação do Script `Bloqueia_Banco.py`

## 1. Objetivo do Script

O script `Bloqueia_Banco.py` foi desenvolvido para automatizar o processo de cruzamento de dados entre os arquivos de pagamento fornecidos por diferentes bancos e o arquivo da folha de pagamento geral.

Seu principal objetivo é identificar inconsistências, tais como:
- Pessoas que constam nos arquivos dos bancos mas não estão na folha de pagamento.
- Pessoas que estão na folha de pagamento mas não aparecem nos arquivos dos bancos para um determinado mês/período.

A ferramenta gera relatórios detalhados que auxiliam na análise e regularização de pendências financeiras e cadastrais.

## 2. Como Funciona o Código

O script opera em três passos principais, executados sequencialmente:

### Passo 1: Processamento dos Arquivos de Banco
- O script varre os diretórios pré-configurados (`SIAPPES` e `SIPPES`).
- Ele lê todos os arquivos de texto (`.txt`) contidos nesses diretórios.
- Para cada arquivo, ele extrai o código do banco, o CPF e o nome do beneficiário.
- Ele consolida os dados, removendo CPFs duplicados para cada banco.
- Ao final, gera arquivos de preparo no formato `preparo_lista_banco_XXX.txt`, onde `XXX` é o código do banco (ex: 001, 033). Esses arquivos contêm uma lista limpa com NOME e CPF.

### Passo 2: Preparação do Arquivo da Folha de Pagamento (Excel)
- O script solicita que o usuário selecione o arquivo da folha de pagamento em formato Excel (`.xlsx` ou `.xls`).
- Com base no código de cada banco identificado no Passo 1, o script filtra as linhas correspondentes a esse banco no arquivo Excel.
- Aplica filtros adicionais que podem ser configurados na seção "ÁREA DE CONFIGURAÇÃO DO USUÁRIO" do script (por exemplo, `PG_PGTO != 28`).
- Gera arquivos de preparo no formato `preparo_excel_bco_XXX.txt` com os dados da folha já filtrados e formatados para cada banco.

### Passo 3: Análise de Cruzamento e Geração de Relatórios
- Para cada banco, o script compara o arquivo de preparo do banco (`preparo_lista_banco_XXX.txt`) com o arquivo de preparo da folha (`preparo_excel_bco_XXX.txt`).
- Ele identifica quais CPFs estão em um arquivo mas não no outro.
- Com base nessa análise, gera os seguintes relatórios de saída:
  - `BANCO_ENCONTRADOS_NA_FOLHA_XXX.txt`: CPFs do banco que também estão na folha.
  - `BANCO_NAO_ENCONTRADOS_NA_FOLHA_XXX.txt`: CPFs do banco que **não** foram localizados na folha (possíveis pagamentos indevidos).
  - `FOLHA_ENCONTRADOS_NO_BANCO_XXX.txt`: CPFs da folha que também estão no arquivo do banco.
  - `FOLHA_NAO_ENCONTRADOS_NO_BANCO_XXX.txt`: CPFs da folha que **não** foram encontrados no arquivo do banco (possíveis pagamentos não realizados).

## 3. Arquivos de Entrada

Para que o script funcione corretamente, os seguintes arquivos e estruturas de diretório são necessários:

- **Diretórios de Bancos**:
  - `SIAPPES/JUNHO/`
  - `SIPPES/JUNHO/`
  - Dentro desses diretórios devem estar os arquivos de texto (`.txt`) fornecidos pelos bancos. O formato desses arquivos deve ser o esperado pelo script (layout de posição fixa).

- **Arquivo da Folha de Pagamento**:
  - Um arquivo no formato Excel (`.xlsx` ou `.xls`) contendo os dados da folha de pagamento.
  - Este arquivo será solicitado ao usuário no momento da execução.
  - Ele deve conter, no mínimo, as colunas `CPF` e `BANCO` para que o cruzamento funcione.

## 4. Relatórios Gerados

Após a execução, o script gera os seguintes arquivos na pasta principal:

- **Arquivos de Preparo (intermediários)**:
  - `preparo_lista_banco_XXX.txt`: Lista de CPFs e Nomes por banco.
  - `preparo_excel_bco_XXX.txt`: Dados da folha de pagamento filtrados por banco.

- **Relatórios de Análise (finais)**:
  - `BANCO_ENCONTRADOS_NA_FOLHA_XXX.txt`
  - `BANCO_NAO_ENCONTRADOS_NA_FOLHA_XXX.txt`
  - `FOLHA_ENCONTRADOS_NO_BANCO_XXX.txt`
  - `FOLHA_NAO_ENCONTRADOS_NO_BANCO_XXX.txt`

- **Relatório Geral Consolidado**:
  - `RELATÓRIO_GERAL.txt`: Um arquivo de log completo que contém todas as informações exibidas no terminal durante a execução, incluindo as estatísticas consolidadas de todos os bancos processados. É o principal arquivo para se ter uma visão geral do resultado.

## 5. Como Executar

1. Certifique-se de que os diretórios `SIAPPES/JUNHO` e `SIPPES/JUNHO` existem e contêm os arquivos de banco.
2. Execute o script `Bloqueia_Banco.py`.
3. Uma janela de diálogo será aberta. Selecione o arquivo Excel da folha de pagamento.
4. Aguarde o processamento. As informações serão exibidas no terminal.
5. Ao final, verifique os arquivos de relatório gerados na pasta do projeto.
