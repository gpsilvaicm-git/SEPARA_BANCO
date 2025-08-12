
import pandas as pd
import glob

def analisar_arquivos_nao_encontrados():
    """
    Lê os arquivos FOLHA_NAO_ENCONTRADOS_NO_BANCO_XXX, conta as ocorrências de cada 
    PG_PGTO, PREC_CP e CALCULO, e exibe os resultados em quadros separados.
    """
    padrao_arquivo = 'FOLHA_NAO_ENCONTRADOS_NO_BANCO_*.txt'
    arquivos = glob.glob(padrao_arquivo)

    if not arquivos:
        print(f"Nenhum arquivo encontrado com o padrão '{padrao_arquivo}'")
        return

    colunas = ['PG_PGTO', 'PREC_CP', 'CPF', 'BANCO', 'BANCO_ATUAL', 'NOME', 'CALCULO', 'SISTEMA']
    lista_dfs = []

    for arquivo in arquivos:
        try:
            # Ler o CSV sem cabeçalho, com nomes de coluna e todas as colunas como string
            df = pd.read_csv(arquivo, sep=';', header=None, names=colunas, dtype=str)
            
            # Remove a linha do cabeçalho se ela foi lida como dados
            if not df.empty and df.iloc[0]['PG_PGTO'] == 'PG_PGTO':
                df = df.iloc[1:]
            
            lista_dfs.append(df)

        except Exception as e:
            print(f"Erro ao processar o arquivo {arquivo}: {e}")

    if not lista_dfs:
        print("Nenhum dado foi processado com sucesso.")
        return

    # Concatena todos os dataframes em um só
    df_completo = pd.concat(lista_dfs, ignore_index=True)

    # Cria a coluna 'PREC' com os 2 primeiros dígitos de 'PREC_CP'
    if 'PREC_CP' in df_completo.columns:
        df_completo['PREC'] = df_completo['PREC_CP'].str[:2]

    # Função para imprimir os quadros de resultados
    def imprimir_quadro(titulo, series_contagem):
        print(f"\n--- {titulo} ---")
        if not series_contagem.empty:
            # O `value_counts` já ordena por padrão
            for item, contagem in series_contagem.items():
                print(f"{series_contagem.name}: {item} | Ocorrências: {contagem}")
        else:
            print("Nenhum dado encontrado.")
        print("--------------------" + "-" * len(titulo) + "\n")

    # Gera e imprime os resultados para cada coluna
    imprimir_quadro("Resultados da Análise por PG_PGTO", df_completo['PG_PGTO'].value_counts())
    if 'PREC' in df_completo.columns:
        imprimir_quadro("Resultados da Análise por PREC", df_completo['PREC'].value_counts())
    imprimir_quadro("Resultados da Análise por CALCULO", df_completo['CALCULO'].value_counts())


if __name__ == "__main__":
    analisar_arquivos_nao_encontrados()
