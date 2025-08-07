# -*- coding: utf-8 -*-
import os
import tkinter as tk
from tkinter import filedialog
import pandas as pd

# =================================================================================
# ÁREA DE CONFIGURAÇÃO DO USUÁRIO
# =================================================================================

# Coloque 'S' para as colunas que deseja manter no arquivo de saída, 'N' para remover.
CONFIGURACAO_COLUNAS = {
    "RM": "N", "SUBORDINACAO": "N", "TIPO": "N", "CMDO_MIL_AREA": "N",
    "CODOM": "N", "SIGLA_OM": "N", "CAT": "N", "PG_PGTO": "N",
    "DESCRICAO_PG": "N", "PREC_CP": "S", "CPF": "S", "BANCO": "S",
    "BANCO_ATUAL": "S", "IDENTIDADE": "N", "NOME": "S", "CALCULO": "S",
    "SITUACAO_COD": "N", "IND": "N", "ALTERACAO_CAD": "N", "DT_LIMITE": "N",
    "CLASS_PENSAO": "N", "TIPO_PENSAO": "N", "VALOR_BRUTO": "N",
    "VALOR_DESCONTOS": "N", "VALOR_LIQUIDO": "N", "DUPLICADO": "N",
    "DESCRICAO_DUP": "N", "SISTEMA": "N", "CORRIDA": "N", "MES": "N", "ANO": "N"
}

# Defina os filtros a serem aplicados.
CONFIGURACAO_FILTROS = [
    ("BANCO", "==", "001"),
    ("PG_PGTO", "!=", "28"),
]

# =================================================================================
# FIM DA ÁREA DE CONFIGURAÇÃO
# =================================================================================

def selecionar_arquivo_excel():
    """Abre uma janela de diálogo para o usuário selecionar um arquivo Excel."""
    root = tk.Tk()
    root.withdraw()
    caminho_arquivo = filedialog.askopenfilename(
        title="Selecione o arquivo Excel da folha de pagamento",
        filetypes=[("Arquivos Excel", "*.xlsx *.xls"), ("Todos os arquivos", "*.*")]
    )
    if not caminho_arquivo:
        print("Nenhum arquivo selecionado. O programa será encerrado.")
        return None
    print(f"Arquivo selecionado: {caminho_arquivo}")
    return caminho_arquivo

def processar_planilha_excel():
    """
    Carrega um arquivo Excel, aplica filtros e seleciona colunas conforme 
    configurado pelo usuário, e salva o resultado em um arquivo de preparo.
    """
    caminho_arquivo = selecionar_arquivo_excel()
    if not caminho_arquivo:
        return False

    try:
        print("Lendo o arquivo Excel... (isso pode levar alguns segundos)")
        df = pd.read_excel(caminho_arquivo, dtype=str)
        print(f"Arquivo lido com sucesso. Total de {len(df)} linhas encontradas.")

        for coluna, operador, valor in CONFIGURACAO_FILTROS:
            if coluna not in df.columns:
                print(f"Aviso: A coluna de filtro '{coluna}' não existe na planilha. Filtro ignorado.")
                continue
            df[coluna] = df[coluna].str.strip()
            print(f"Aplicando filtro: {coluna} {operador} {valor}")
            if operador == '==':
                df = df[df[coluna] == valor]
            elif operador == '!=':
                df = df[df[coluna] != valor]

        print(f"Após filtros, restaram {len(df)} linhas.")

        colunas_para_manter = [coluna for coluna, status in CONFIGURACAO_COLUNAS.items() if status == 'S']
        colunas_para_manter = [col for col in colunas_para_manter if col in df.columns]
        
        df = df[colunas_para_manter]
        print(f"Colunas selecionadas: {', '.join(colunas_para_manter)}")

        if 'CPF' in df.columns:
            df['CPF'] = df['CPF'].str.replace(r'[.\-]', '', regex=True).str.strip()

        df.to_csv('preparo_excel_bco.txt', sep=';', index=False, header=True)
        print(f"Arquivo 'preparo_excel_bco.txt' gerado com sucesso com {len(df)} linhas e {len(df.columns)} colunas.")
        return True

    except FileNotFoundError:
        print(f"Erro: O arquivo selecionado não foi encontrado em '{caminho_arquivo}'")
        return False
    except Exception as e:
        print(f"Ocorreu um erro inesperado ao processar o arquivo Excel: {e}")
        return False

def processar_arquivo_banco():
    """
    Lê múltiplos arquivos de banco, extrai nome e CPF, e consolida em um arquivo intermediário.
    """
    diretorios_base = ['SIAPPES/JUNHO', 'SIPPES/JUNHO']
    registros_unicos = {}
    registros_por_arquivo = {}

    for diretorio in diretorios_base:
        if not os.path.isdir(diretorio):
            continue
        for nome_arquivo in os.listdir(diretorio):
            caminho_arquivo = os.path.join(diretorio, nome_arquivo)
            if not os.path.isfile(caminho_arquivo):
                continue
            
            registros_neste_arquivo = 0
            try:
                with open(caminho_arquivo, 'r', encoding='utf-8') as arq_banco:
                    banco_linhas = arq_banco.readlines()
                    if len(banco_linhas) > 4:
                        linhas_relevantes = banco_linhas[2:-2]
                    else:
                        linhas_relevantes = banco_linhas
                    for i in range(0, len(linhas_relevantes), 2):
                        if i + 1 < len(linhas_relevantes):
                            linha_banco_a = linhas_relevantes[i]
                            linha_banco_b = linhas_relevantes[i+1]
                            if len(linha_banco_a) > 73 and len(linha_banco_b) > 33:
                                nome_banco = linha_banco_a[43:73].strip()
                                cpf_banco = linha_banco_b[21:33].strip()
                                if nome_banco and cpf_banco:
                                    if cpf_banco not in registros_unicos:
                                        registros_unicos[cpf_banco] = nome_banco
                                    registros_neste_arquivo += 1
                chave_relatorio = os.path.join(os.path.basename(diretorio), nome_arquivo)
                registros_por_arquivo[chave_relatorio] = registros_neste_arquivo
            except Exception as e:
                print(f"Erro ao processar '{caminho_arquivo}': {e}")
    
    with open('preparo_lista_banco.txt', 'w', encoding='utf-8') as arq_preparo:
        for cpf in sorted(registros_unicos.keys()):
            nome = registros_unicos[cpf]
            arq_preparo.write(f"{nome};{cpf}\n")
            
    total_antes_deduplicacao = sum(count for count in registros_por_arquivo.values() if isinstance(count, int))
    total_apos_deduplicacao = len(registros_unicos)

    print("\n--- Relatório de Processamento dos Bancos ---")
    for nome, contagem in registros_por_arquivo.items():
        print(f"Arquivo '{nome}': {contagem} registros processados.")
    print("-----------------------------------------------")
    print(f"Total de registros lidos: {total_antes_deduplicacao}")
    print(f"Total de registros únicos consolidados: {total_apos_deduplicacao}")
    print(f"Duplicatas eliminadas: {total_antes_deduplicacao - total_apos_deduplicacao}")
    return True

def analisar_banco_vs_folha():
    try:
        with open('preparo_excel_bco.txt', 'r', encoding='utf-8') as arq_folha:
            next(arq_folha)
            cpfs_folha = {linha.split(';')[0].strip() for linha in arq_folha if linha.strip()}
        banco_encontrados_na_folha, banco_nao_encontrados_na_folha = [], []
        with open('preparo_lista_banco.txt', 'r', encoding='utf-8') as arq_banco:
            for linha in arq_banco:
                linha = linha.strip()
                if linha:
                    try:
                        cpf_banco = linha.split(';')[1].strip()
                        if cpf_banco in cpfs_folha:
                            banco_encontrados_na_folha.append(linha)
                        else:
                            banco_nao_encontrados_na_folha.append(linha)
                    except IndexError:
                        print(f"Aviso: Linha mal formada em 'preparo_lista_banco.txt' ignorada: {linha}")
        with open('BANCO_ENCONTRADOS_NA_FOLHA.txt', 'w', encoding='utf-8') as arq:
            arq.write('\n'.join(banco_encontrados_na_folha))
        with open('BANCO_NAO_ENCONTRADOS_NA_FOLHA.txt', 'w', encoding='utf-8') as arq:
            arq.write('\n'.join(banco_nao_encontrados_na_folha))
        print(f"\n--- Análise: BANCO vs FOLHA ---")
        print(f"CPFs do banco que ESTÃO na folha: {len(banco_encontrados_na_folha)}")
        print(f"CPFs do banco que NÃO estão na folha: {len(banco_nao_encontrados_na_folha)}")
        return len(banco_encontrados_na_folha), len(banco_nao_encontrados_na_folha)
    except FileNotFoundError as e:
        print(f"Erro: Arquivo não encontrado - {e.filename}")
        return 0, 0
    except Exception as e:
        print(f"Ocorreu um erro inesperado na análise banco vs folha: {e}")
        return 0, 0

def analisar_folha_vs_banco():
    try:
        with open('preparo_lista_banco.txt', 'r', encoding='utf-8') as arq_banco:
            cpfs_banco = {linha.split(';')[1].strip() for linha in arq_banco if linha.strip()}
        folha_encontrados_no_banco, folha_nao_encontrados_no_banco = [], []
        with open('preparo_excel_bco.txt', 'r', encoding='utf-8') as arq_folha:
            next(arq_folha)
            for linha in arq_folha:
                linha = linha.strip()
                if linha:
                    try:
                        cpf_folha = linha.split(';')[0].strip()
                        if cpf_folha in cpfs_banco:
                            folha_encontrados_no_banco.append(linha)
                        else:
                            folha_nao_encontrados_no_banco.append(linha)
                    except IndexError:
                        print(f"Aviso: Linha mal formada em 'preparo_excel_bco.txt' ignorada: {linha}")
        with open('FOLHA_ENCONTRADOS_NO_BANCO.txt', 'w', encoding='utf-8') as arq:
            arq.write('\n'.join(folha_encontrados_no_banco))
        with open('FOLHA_NAO_ENCONTRADOS_NO_BANCO.txt', 'w', encoding='utf-8') as arq:
            arq.write('\n'.join(folha_nao_encontrados_no_banco))
        print(f"\n--- Análise: FOLHA vs BANCO ---")
        print(f"CPFs da folha que ESTÃO no banco: {len(folha_encontrados_no_banco)}")
        print(f"CPFs da folha que NÃO estão no banco: {len(folha_nao_encontrados_no_banco)}")
        return len(folha_encontrados_no_banco), len(folha_nao_encontrados_no_banco)
    except FileNotFoundError as e:
        print(f"Erro: Arquivo não encontrado - {e.filename}")
        return 0, 0
    except Exception as e:
        print(f"Ocorreu um erro inesperado na análise folha vs banco: {e}")
        return 0, 0

def comparar_listas():
    print(f"\n{'='*50}\nANÁLISE BIDIRECIONAL COMPLETA\n{'='*50}")
    
    banco_na_folha, banco_nao_na_folha = analisar_banco_vs_folha()
    folha_no_banco, folha_nao_no_banco = analisar_folha_vs_banco()
    
    print(f"\n{'='*50}\nRESUMO FINAL\n{'='*50}")
    print(f"Intersecção (CPFs em ambos): {banco_na_folha} CPFs")
    print(f"Só no banco (não na folha): {banco_nao_na_folha} CPFs")
    print(f"Só na folha (não no banco): {folha_nao_no_banco} CPFs")
    print(f"\nArquivos gerados:")
    print("  - BANCO_ENCONTRADOS_NA_FOLHA.txt")
    print("  - BANCO_NAO_ENCONTRADOS_NA_FOLHA.txt")
    print("  - FOLHA_ENCONTRADOS_NO_BANCO.txt")
    print("  - FOLHA_NAO_ENCONTRADOS_NO_BANCO.txt")

if __name__ == "__main__":
    if processar_arquivo_banco():
        if processar_planilha_excel():
            comparar_listas()