# Documentação dos Scripts de Análise de Folha de Pagamento

Este documento detalha o funcionamento e o modo de uso dos scripts Python desenvolvidos para analisar, comparar e validar os dados da folha de pagamento contra os arquivos de retorno dos bancos.

---
## 0. Preparo do arquivo excell

Receber da FOPAG (Farias) os arquivos 1->FINAL_SAAFOPAG_FOLHA_PGTO_G3_2025.xlsx e 2->MIGRACAO_ENTRE_BANCOS_G3_2025.xlsx (G3 é exemplo - mescorrida). Abrir os 2 arquivos e na planilha 1 criar as colunas BANCO e BANCO_ATUAL depois da coluna CPF.  Realizar um PROCV : =SEERRO(PROCV($K2;[MIGRACAO_ENTRE_BANCOS_H3_2025.xlsx]DETALHAMENTO_COMPARATIVO_MES_AT!$E$2:$L$418007;7;0);"") na coluna BANCO e BANCO_ATUAL para trazer os dados de banco da planilha 2. Copiar e salvar somente valores destas duas colunas criadas. Pronto, o arquivo está preparado para script abaixo.

## 1. `analise_separa_banco_folha.py`

Este é o script principal do processo. Sua função é ler múltiplos arquivos de banco, consolidar os CPFs, compará-los com uma planilha Excel da folha de pagamento e gerar relatórios detalhados sobre as correspondências e divergências.

### Funcionalidades Principais

-   **Leitura Recursiva de Arquivos:** Percorre toda a estrutura de subdiretórios dentro das pastas `SIAPPES/` e `SIPPES/`, permitindo uma organização flexível dos arquivos de entrada (ex: por ano, por mês).
-   **Identificação e Separação por Banco:** Agrupa automaticamente todos os registros pelo código do banco (os 3 primeiros dígitos de cada registro).
-   **Detecção Avançada de Duplicatas:**
    -   **Geral:** Identifica e reporta CPFs que aparecem mais de uma vez dentro do conjunto de arquivos de um mesmo banco.
    -   **Inter-sistemas:** Identifica e reporta CPFs que existem simultaneamente nos sistemas `SIAPPES` e `SIPPES` para o mesmo banco, apontando possíveis inconsistências de cadastro.
-   **Seleção Interativa do Arquivo Excel:** Abre uma janela para que o usuário selecione o arquivo da folha de pagamento (`.xlsx` ou `.xls`) a ser usado na comparação.
-   **Filtragem e Seleção Configurável:** Permite que o usuário defina facilmente quais colunas do Excel devem ser salvas e quais filtros devem ser aplicados antes da comparação, através das variáveis `CONFIGURACAO_COLUNAS` e `CONFIGURACAO_FILTROS` no topo do script.
-   **Geração de Relatórios Completos:** Cria um conjunto de arquivos de saída para cada banco, detalhando cada etapa do cruzamento de dados.

### Arquivos Gerados

Para cada banco processado (identificado por `XXX`), o script gera os seguintes arquivos:

-   `preparo_lista_banco_XXX.txt`: Contém a lista final de CPFs **únicos** extraídos dos arquivos de texto daquele banco, servindo como base para a comparação.
-   `preparo_excel_bco_XXX.txt`: Contém as linhas da planilha Excel que correspondem àquele banco e que passaram pelos filtros definidos.
-   `DUPLICADOS_BANCO_XXX.txt`: Lista os CPFs que foram encontrados mais de uma vez nos arquivos de origem daquele banco.
-   `DUPLICADOS_INTERSISTEMAS_BANCO_XXX.txt`: Lista os CPFs que foram encontrados tanto em arquivos do sistema `SIAPPES` quanto do `SIPPES`.
-   `BANCO_ENCONTRADOS_NA_FOLHA_XXX.txt`: Registros do banco que **foram encontrados** na folha de pagamento.
-   `BANCO_NAO_ENCONTRADOS_NA_FOLHA_XXX.txt`: Registros do banco que **NÃO foram encontrados** na folha de pagamento.
-   `FOLHA_ENCONTRADOS_NO_BANCO_XXX.txt`: Registros da folha de pagamento que **foram encontrados** nos arquivos do banco.
-   `FOLHA_NAO_ENCONTRADOS_NO_BANCO_XXX.txt`: Registros da folha de pagamento que **NÃO foram encontrados** nos arquivos do banco. Este arquivo é o principal insumo para o script `analisar_nao_encontrados.py`.
-   `RELATÓRIO_GERAL.txt`: Um arquivo de log completo que espelha toda a saída do terminal, registrando cada etapa da execução, os totais e o resumo final consolidado.

### Como Usar

1.  **Organize os Arquivos:** Coloque os arquivos de texto dos bancos dentro das pastas `SIAPPES` ou `SIPPES`. Você pode criar subpastas (ex: `SIAPPES/2025/JUNHO/`) para melhor organização.
2.  **Configure (Opcional):** Edite as listas `CONFIGURACAO_COLUNAS` e `CONFIGURACAO_FILTROS` no topo do script para ajustar quais dados do Excel serão analisados.
3.  **Execute o Script:** Abra um terminal na pasta do projeto e execute o comando:
    ```bash
    python analise_separa_banco_folha.py
    ```
4.  **Selecione o Arquivo Excel:** Uma janela de diálogo aparecerá. Navegue e selecione o arquivo da folha de pagamento.
5.  **Analise os Resultados:** Após a conclusão, verifique a pasta do projeto para encontrar todos os arquivos de saída e o relatório geral.

---

## 2. `analisar_nao_encontrados.py`

Este é um script de diagnóstico, projetado para analisar os resultados do `analise_separa_banco_folha.py` e ajudar a entender por que certos registros da folha de pagamento não foram encontrados nos arquivos dos bancos.

### Objetivo

O script lê todos os arquivos `FOLHA_NAO_ENCONTRADOS_NO_BANCO_*.txt`, consolida os dados e apresenta um resumo estatístico, agrupando os registros por critérios específicos. Isso ajuda a identificar padrões, como por exemplo, se a maioria dos não encontrados pertence a um determinado Posto/Graduação (`PG_PGTO`) ou tipo de cálculo (`CALCULO`).

### Funcionalidades Principais

-   **Consolidação Automática:** Encontra e processa todos os arquivos de "não encontrados" gerados pelo script principal.
-   **Análise Estatística:** Utiliza a biblioteca `pandas` para contar as ocorrências de cada valor nas colunas `PG_PGTO`, `PREC` (os 2 primeiros dígitos de `PREC_CP`) e `CALCULO`.
-   **Apresentação Clara:** Exibe os resultados em quadros separados e ordenados no terminal, mostrando os itens mais frequentes primeiro.

### Como Usar

1.  **Execute o Script Principal:** Certifique-se de que o `analise_separa_banco_folha.py` já foi executado e que os arquivos `FOLHA_NAO_ENCONTRADOS_NO_BANCO_*.txt` existem na pasta.
2.  **Execute o Script de Análise:** No terminal, execute o comando:
    ```bash
    python analisar_nao_encontrados.py
    ```
3.  **Interprete a Saída:** Observe os quadros de resumo no terminal para identificar os principais motivos de divergência entre a folha e os arquivos dos bancos.
