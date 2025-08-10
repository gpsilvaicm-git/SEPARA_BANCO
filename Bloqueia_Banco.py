# -*- coding: utf-8 -*-
import os
import tkinter as tk
from tkinter import filedialog
import pandas as pd
from collections import defaultdict

# Suprime o aviso SettingWithCopyWarning do pandas
pd.options.mode.chained_assignment = None

# Buffer para armazenar todas as mensagens de log
log_buffer = []

def log_print(message=""):
    """Imprime a mensagem no console e a adiciona ao buffer de log."""
    print(message)
    log_buffer.append(str(message))

# =================================================================================
# ÁREA DE CONFIGURAÇÃO DO USUÁRIO
# =================================================================================

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

CONFIGURACAO_FILTROS = [
    ("PG_PGTO", "!=", "28"),
]

"""Análise de cada linha:
("BANCO_ATUAL", "==", "001")
Coluna: BANCO_ATUAL
Operador: == (igual a)
Valor: "001" (o valor que estamos procurando)
("CAT", "==", "PENSIONISTA")
Coluna: CAT
Operador: == (igual a)
Valor: "PENSIONISTA"
("PG_PGTO", "in", ["CEL", "TC", "MAJ"])
Coluna: PG_PGTO
Operador: in (está contido em...)
Valor: ["CEL", "TC", "MAJ"] (uma lista de valores aceitáveis)


Outros Operadores Úteis que Você Pode Usar
Operador	O que faz	Exemplo de Uso
==	Exatamente igual a	("SITUACAO_COD", "==", "ATIVO")
!=	Diferente de	("BANCO", "!=", "104")
in	Está em uma lista de valores	("CAT", "in", ["CIVIL", "MILITAR"])
not in	Não está em uma lista de valores	("SISTEMA", "not in", ["TESTE", "LEGADO"])
>	Maior que (para números)	("VALOR_LIQUIDO", ">", 5000)
<	Menor que (para números)	("ANO", "<", 2023)
str.contains	Contém um pedaço de texto	("NOME", "str.contains", "SILVA")
Basta editar a lista CONFIGURACAO_FILTROS no topo do script com as regras que você precisar antes de executar.
"""


# =================================================================================
# FIM DA ÁREA DE CONFIGURAÇÃO
# =================================================================================

def passo1_identificar_e_processar_bancos():
    log_print(f"\n{'='*50}\nPASSO 1: PROCESSANDO ARQUIVOS DE BANCO\n{'='*50}")
    diretorios_base = ['SIAPPES/JUNHO', 'SIPPES/JUNHO']
    dados_por_banco = defaultdict(lambda: {'registros': {}, 'total_lido': 0})
    bancos_encontrados = set()

    for diretorio in diretorios_base:
        if not os.path.isdir(diretorio):
            log_print(f"Aviso: Diretório '{diretorio}' não encontrado. Pulando.")
            continue
        for nome_arquivo in os.listdir(diretorio):
            caminho_arquivo = os.path.join(diretorio, nome_arquivo)
            if not os.path.isfile(caminho_arquivo):
                continue
            
            try:
                with open(caminho_arquivo, 'r', encoding='utf-8', errors='ignore') as arq_banco:
                    banco_linhas = arq_banco.readlines()
                
                linhas_relevantes = banco_linhas[2:-2] if len(banco_linhas) > 4 else banco_linhas

                for i in range(0, len(linhas_relevantes), 2):
                    if i + 1 < len(linhas_relevantes):
                        linha_banco_a = linhas_relevantes[i]
                        linha_banco_b = linhas_relevantes[i+1]

                        if len(linha_banco_a) > 73 and len(linha_banco_b) > 33:
                            banco_id = linha_banco_a[:3]
                            nome_banco = linha_banco_a[43:73].strip()
                            cpf_banco = linha_banco_b[21:33].strip()
                            
                            if nome_banco and cpf_banco and banco_id.isdigit():
                                bancos_encontrados.add(banco_id)
                                dados_por_banco[banco_id]['total_lido'] += 1
                                if cpf_banco not in dados_por_banco[banco_id]['registros']:
                                    dados_por_banco[banco_id]['registros'][cpf_banco] = nome_banco
            except Exception as e:
                log_print(f"Erro ao processar '{caminho_arquivo}': {e}")
    
    if not bancos_encontrados:
        log_print("Nenhum banco encontrado nos arquivos. Verifique os diretórios e arquivos.")
        return None

    log_print("\n--- Relatório de Processamento dos Bancos ---")
    for banco_id, dados in dados_por_banco.items():
        nome_arquivo_saida = f'preparo_lista_banco_{banco_id}.txt'
        with open(nome_arquivo_saida, 'w', encoding='utf-8') as arq_preparo:
            arq_preparo.write("NOME;CPF\n")
            for cpf, nome in sorted(dados['registros'].items()):
                arq_preparo.write(f"{nome};{cpf}\n")
        
        total_unicos = len(dados['registros'])
        total_lido = dados['total_lido']
        duplicatas = total_lido - total_unicos
        log_print(f"Banco {banco_id}:")
        log_print(f"  - Registros lidos: {total_lido}")
        log_print(f"  - Registros únicos: {total_unicos}")
        log_print(f"  - Duplicatas eliminadas: {duplicatas}")
        log_print(f"  - Arquivo gerado: {nome_arquivo_saida}")

    return sorted(list(bancos_encontrados))

def passo2_preparar_excel_por_banco(df_original, banco_id):
    log_print(f"\n--- Preparando Excel para o Banco {banco_id} ---")
    
    if 'BANCO' not in df_original.columns:
        log_print("!! ERRO CRÍTICO: A coluna 'BANCO' não foi encontrada na planilha. !!")
        return False
        
    df = df_original.copy()
    
    df['BANCO_PADRONIZADO'] = df['BANCO'].astype(str).str.strip().str.zfill(3)
    df_banco = df[df['BANCO_PADRONIZADO'] == banco_id]
    
    log_print(f"Encontradas {len(df_banco)} linhas no Excel para o banco {banco_id} (antes dos filtros gerais).")
    
    for coluna, operador, valor in CONFIGURACAO_FILTROS:
        if coluna not in df_banco.columns:
            log_print(f"  - AVISO: A coluna de filtro '{coluna}' não existe. Filtro ignorado.")
            continue
        
        linhas_antes = len(df_banco)
        df_banco.loc[:, coluna] = df_banco[coluna].astype(str).str.strip()
        
        if operador == '==':
            df_banco = df_banco[df_banco[coluna] == valor]
        elif operador == '!=':
            df_banco = df_banco[df_banco[coluna] != valor]
        
        log_print(f"  - Filtro '{coluna} {operador} {valor}': {linhas_antes} -> {len(df_banco)} linhas")

    colunas_para_manter = [col for col, status in CONFIGURACAO_COLUNAS.items() if status == 'S']
    colunas_existentes = [c for c in colunas_para_manter if c in df_banco.columns]
    
    df_final = df_banco[colunas_existentes].copy()

    if 'CPF' in df_final.columns:
        df_final.loc[:, 'CPF'] = df_final['CPF'].astype(str).str.replace(r'[.\-]', '', regex=True).str.strip()

    nome_arquivo_saida = f'preparo_excel_bco_{banco_id}.txt'
    df_final.to_csv(nome_arquivo_saida, sep=';', index=False, header=True)
    log_print(f"Arquivo '{nome_arquivo_saida}' gerado com {len(df_final)} linhas.")
    
    return True

def passo3_analisar_cruzamento(banco_id):
    

    arquivo_banco = f'preparo_lista_banco_{banco_id}.txt'
    arquivo_folha = f'preparo_excel_bco_{banco_id}.txt'
    
    try:
        if os.path.exists(arquivo_folha) and os.path.getsize(arquivo_folha) > 5:
            with open(arquivo_folha, 'r', encoding='utf-8') as f:
                header_folha = next(f).strip().split(';')
                try:
                    idx_cpf_folha = header_folha.index('CPF')
                    linhas_folha = [line.strip() for line in f if ';' in line.strip()]
                    cpfs_folha = {line.split(';')[idx_cpf_folha] for line in linhas_folha}
                except ValueError:
                    log_print(f"Aviso: Coluna 'CPF' não encontrada no cabeçalho de '{arquivo_folha}'.")
                    cpfs_folha, linhas_folha, header_folha, idx_cpf_folha = set(), [], [], -1
        else:
             cpfs_folha, linhas_folha, header_folha, idx_cpf_folha = set(), [], [], -1

        with open(arquivo_banco, 'r', encoding='utf-8') as f:
            header_banco = next(f).strip().split(';')
            idx_cpf_banco = header_banco.index('CPF')
            linhas_banco = [line.strip() for line in f if ';' in line.strip()]
            cpfs_banco = {line.split(';')[idx_cpf_banco] for line in linhas_banco}

    except FileNotFoundError as e:
        log_print(f"Erro: Arquivo de preparo não encontrado: {e.filename}. Pulando análise.")
        return None
    except (ValueError, IndexError) as e:
        log_print(f"Erro ao ler arquivo de preparo para o banco {banco_id}: {e}.")
        return None

    banco_encontrados_list = [line for line in linhas_banco if line.split(';')[idx_cpf_banco] in cpfs_folha]
    banco_nao_encontrados_list = [line for line in linhas_banco if line.split(';')[idx_cpf_banco] not in cpfs_folha]

    if idx_cpf_folha != -1:
        folha_encontrados_list = [line for line in linhas_folha if line.split(';')[idx_cpf_folha] in cpfs_banco]
        folha_nao_encontrados_list = [line for line in linhas_folha if line.split(';')[idx_cpf_folha] not in cpfs_banco]
    else:
        folha_encontrados_list, folha_nao_encontrados_list = [], []
    
    header_banco_str = ";".join(header_banco) + "\n"
    header_folha_str = ";".join(header_folha) + "\n" if header_folha else ""
    
    with open(f'BANCO_ENCONTRADOS_NA_FOLHA_{banco_id}.txt', 'w', encoding='utf-8') as f:
        f.write(header_banco_str)
        f.write('\n'.join(banco_encontrados_list))
    with open(f'BANCO_NAO_ENCONTRADOS_NA_FOLHA_{banco_id}.txt', 'w', encoding='utf-8') as f:
        f.write(header_banco_str)
        f.write('\n'.join(banco_nao_encontrados_list))
    with open(f'FOLHA_ENCONTRADOS_NO_BANCO_{banco_id}.txt', 'w', encoding='utf-8') as f:
        f.write(header_folha_str)
        f.write('\n'.join(folha_encontrados_list))
    with open(f'FOLHA_NAO_ENCONTRADOS_NO_BANCO_{banco_id}.txt', 'w', encoding='utf-8') as f:
        f.write(header_folha_str)
        f.write('\n'.join(folha_nao_encontrados_list))

    stats = {
        "banco_total": len(linhas_banco),
        "banco_encontrados": len(banco_encontrados_list),
        "folha_total": len(linhas_folha),
        "folha_encontrados": len(folha_encontrados_list),
    }
    
    log_print(f"\n--- Análise de Cruzamento - Banco {banco_id} ---")
    log_print(f"  - Total de CPFs no arquivo do Banco: {stats['banco_total']}")
    log_print(f"  - CPFs do Banco ENCONTRADOS na Folha: {stats['banco_encontrados']}")
    log_print(f"  - CPFs no Banco que não foram encontrados na Folha: {stats['banco_total'] - stats['banco_encontrados']}")
    log_print(f"  - Total de CPFs no arquivo da Folha: {stats['folha_total']}")
    log_print(f"  - CPFs da Folha ENCONTRADOS no Banco: {stats['folha_encontrados']}")
    log_print(f"  - CPFs da Folha que não foram encontrados no Banco: {stats['folha_total'] - stats['folha_encontrados']}")
    log_print(f"  - Arquivos de resultado gerados com sufixo '_{banco_id}.txt'")

    return stats

def selecionar_arquivo_excel():
    root = tk.Tk()
    root.withdraw()
    caminho_arquivo = filedialog.askopenfilename(
        title="Selecione o arquivo Excel da folha de pagamento",
        filetypes=[("Arquivos Excel", "*.xlsx *.xls"), ("Todos os arquivos", "*.*")]
    )
    if not caminho_arquivo:
        log_print("Nenhum arquivo selecionado. O programa será encerrado.")
        return None
    log_print(f"\nArquivo da folha selecionado: {caminho_arquivo}")
    return caminho_arquivo

def main():
    bancos_a_processar = passo1_identificar_e_processar_bancos()
    if not bancos_a_processar:
        return

    caminho_excel = selecionar_arquivo_excel()
    if not caminho_excel:
        return

    try:
        log_print("Lendo o arquivo Excel... (isso pode levar alguns segundos)")
        df_excel_main = pd.read_excel(caminho_excel, dtype=str)
        log_print(f"Arquivo lido com sucesso. Total de {len(df_excel_main)} linhas encontradas.")
    except Exception as e:
        log_print(f"Ocorreu um erro fatal ao ler o arquivo Excel: {e}")
        return

    totais_gerais = defaultdict(int)

    for banco_id in bancos_a_processar:
        passo2_ok = passo2_preparar_excel_por_banco(df_excel_main, banco_id)
        if not passo2_ok:
            continue 
        
        stats_banco = passo3_analisar_cruzamento(banco_id)
        
        if stats_banco:
            for key, value in stats_banco.items():
                totais_gerais[key] += value

    banco_nao_encontrados_total = totais_gerais['banco_total'] - totais_gerais['banco_encontrados']
    folha_nao_encontrados_total = totais_gerais['folha_total'] - totais_gerais['folha_encontrados']
    
    # Monta o relatório final como uma string
    relatorio_final_str = f"""
{'='*60}
RELATÓRIO FINAL CONSOLIDADO (TODOS OS BANCOS)
{'='*60}
Total de CPFs de TODOS os bancos processados: {totais_gerais['banco_total']}
  - Total ENCONTRADOS na folha: {totais_gerais['banco_encontrados']}
  - Total NÃO ENCONTRADOS na folha: {banco_nao_encontrados_total}
Total de CPFs da FOLHA (todos os bancos): {totais_gerais['folha_total']}
  - Total ENCONTRADOS nos arquivos de banco: {totais_gerais['folha_encontrados']}
  - Total NÃO ENCONTRADOS nos arquivos de banco: {folha_nao_encontrados_total}
Processo concluído."""

    print(relatorio_final_str)  # Imprime no console
    log_buffer.append(relatorio_final_str) # Adiciona ao buffer para o arquivo
    
    # Grava o log no arquivo
    with open("RELATÓRIO_GERAL.txt", "w", encoding='utf-8') as f:
        f.write("\n".join(log_buffer))
    
    print(f"\nO relatório completo desta execução também foi salvo em 'RELATÓRIO_GERAL.txt'")


if __name__ == "__main__":
    main()
