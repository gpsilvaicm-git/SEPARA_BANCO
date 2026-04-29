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

NOME_DA_GUIA_EXCEL = "DETALHAMENTO_COMPARATIVO_MES_AT"
ARQUIVO_SMOP = "SMOP400-A3-2026.txt"
CONTA_INCONSISTENTE = "2222222222222"

# Tipos de arquivo que NÃO entram na base principal de registros únicos/duplicados.
# CPFs desses tipos são apenas mapeados para excluir do relatório de "não encontrados".
TIPOS_FORA_DA_BASE_PRINCIPAL = {"EFVAR", "PJNOR", "PJPEC"}

CONFIGURACAO_COLUNAS = {
    "SISTEMA": "S", "CAT": "N", "CODOM": "N", "SIGLA_OM": "N", "CPF": "S",
    "PREC_CP": "S", "PG": "S", "DESCRIÇÃO_PG": "N", "NOME": "S", "TIPO_FOLHA": "N",
    "BANCO_ATUAL": "S", "DESCRIÇÃO_ATUAL": "S", "AGENCIA_ATUAL": "N", "SOMA_VALOR": "N",
    "SISTEMA_ANTERIOR": "N", "CAT_ANTERIOR": "N", "TIPO_FOLHA_ANTERIOR": "N",
    "BANCO_ANTERIOR": "N", "DESCRIÇÃO_ANTERIOR": "N", "AGENCIA_ANTERIOR": "N",
    "INDICATIVO": "N"
}

CONFIGURACAO_FILTROS = [
    ("PG", "!=", "28"),
    ("PG", "!=", "14"),
    ("PG", "!=", "11", "SISTEMA", "==", "SIPPES")
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

def carregar_cpfs_inconsistencia_bancaria():
    caminho_smop = selecionar_arquivo_smop()
    if not caminho_smop:
        log_print("  - AVISO: Nenhum arquivo SMOP selecionado. Nenhuma inconsistência será considerada.")
        return set()
    log_print(f"\n--- Carregando CPFs com inconsistência bancária de '{caminho_smop}' ---")

    cpfs_inconsistentes = set()
    total_linhas_tipo2 = 0

    try:
        with open(caminho_smop, 'r', encoding='utf-8', errors='ignore') as arquivo_smop:
            for linha in arquivo_smop:
                if linha[0:1] != '2':
                    continue

                total_linhas_tipo2 += 1
                conta = linha[48:61].strip()
                if conta != CONTA_INCONSISTENTE:
                    continue

                cpf = linha[24:35].strip().zfill(11)
                if cpf:
                    cpfs_inconsistentes.add(cpf)
    except Exception as e:
        log_print(f"  - ERRO ao processar o arquivo '{caminho_smop}': {e}")
        return set()

    log_print(f"  - Total de linhas TIPO 2 lidas: {total_linhas_tipo2}")
    log_print(f"  - Total de CPFs em inconsistência bancária: {len(cpfs_inconsistentes)}")
    return cpfs_inconsistentes


def extrair_tipo_arquivo_linha_a(linha_banco_a):
    """Extrai o tipo do arquivo no segmento A (posição humana 74:78)."""
    return linha_banco_a[73:78].strip().upper()


def extrair_cpf_da_linha(linha, idx_cpf):
    partes = linha.split(';')
    if idx_cpf < 0 or idx_cpf >= len(partes):
        return ""
    return partes[idx_cpf].strip().zfill(11)

def passo1_identificar_e_processar_bancos():
    log_print(f"\n{'='*50}\nPASSO 1: PROCESSANDO ARQUIVOS DE BANCO\n{'='*50}")
    diretorios_base = ['SIAPPES', 'SIPPES']
    dados_por_banco = defaultdict(lambda: {
        'registros': {}, 
        'duplicatas': {}, 
        'duplicatas_intersistemas': {},
        'arquivos_info': defaultdict(int),
        'arquivos_efvar_info': defaultdict(int),
        'tipos_registros': defaultdict(int),
        'cpfs_efvar': set()
    })
    bancos_encontrados = set()

    for diretorio in diretorios_base:
        if not os.path.isdir(diretorio):
            log_print(f"Aviso: Diretório '{diretorio}' não encontrado. Pulando.")
            continue
        
        sistema_atual = os.path.basename(diretorio)

        # os.walk para percorrer subdiretórios
        for root, _, files in os.walk(diretorio):
            for nome_arquivo in files:
                caminho_arquivo = os.path.join(root, nome_arquivo)
                
                try:
                    with open(caminho_arquivo, 'r', encoding='utf-8', errors='ignore') as arq_banco:
                        banco_linhas = arq_banco.readlines()
                    
                    linhas_relevantes = banco_linhas[2:-2] if len(banco_linhas) > 4 else banco_linhas

                    for i in range(0, len(linhas_relevantes), 2):
                        if i + 1 < len(linhas_relevantes):
                            linha_banco_a = linhas_relevantes[i]
                            linha_banco_b = linhas_relevantes[i+1]

                            if len(linha_banco_a) > 77 and len(linha_banco_b) > 33:
                                banco_id = linha_banco_a[:3]
                                nome_banco = linha_banco_a[43:73].strip()
                                cpf_banco = linha_banco_b[21:33].strip().zfill(11)
                                tipo_arquivo = extrair_tipo_arquivo_linha_a(linha_banco_a) or "DESCONHECIDO"
                                
                                if nome_banco and cpf_banco and banco_id.isdigit():
                                    bancos_encontrados.add(banco_id)
                                    dados_por_banco[banco_id]['tipos_registros'][tipo_arquivo] += 1

                                    if tipo_arquivo in TIPOS_FORA_DA_BASE_PRINCIPAL:
                                        dados_por_banco[banco_id]['arquivos_efvar_info'][caminho_arquivo] += 1
                                        dados_por_banco[banco_id]['cpfs_efvar'].add(cpf_banco)
                                        continue

                                    dados_por_banco[banco_id]['arquivos_info'][caminho_arquivo] += 1
                                    
                                    registro_existente = dados_por_banco[banco_id]['registros'].get(cpf_banco)

                                    if registro_existente:
                                        # É uma duplicata. Adiciona à lista geral de duplicados.
                                        dados_por_banco[banco_id]['duplicatas'][cpf_banco] = registro_existente['nome']
                                        
                                        # Verifica se é uma duplicata inter-sistemas.
                                        if registro_existente['sistema'] != sistema_atual:
                                            dados_por_banco[banco_id]['duplicatas_intersistemas'][cpf_banco] = registro_existente['nome']
                                    else:
                                        # Primeira vez que vemos este CPF, armazena com seu sistema de origem.
                                        dados_por_banco[banco_id]['registros'][cpf_banco] = {'nome': nome_banco, 'sistema': sistema_atual}
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
            # O dicionário 'registros' agora guarda outro dicionário {'nome': ..., 'sistema': ...}
            for cpf, registro in sorted(dados['registros'].items()):
                # Escrevemos apenas o nome e o CPF, como era o layout original
                arq_preparo.write(f"{registro['nome']};{cpf}\n")
        
        # Cálculos consolidados
        total_lido = sum(dados['arquivos_info'].values())
        total_unicos = len(dados['registros'])
        duplicatas_eliminadas = total_lido - total_unicos

        log_print(f"Banco {banco_id}:")
        log_print(f"  - Total de arquivos processados: {len(dados['arquivos_info'])}")
        for arquivo, qtd in sorted(dados['arquivos_info'].items()):
            # Usar os.path.basename para um nome de arquivo mais limpo
            log_print(f"    - Arquivo '{os.path.basename(arquivo)}': {qtd} registros lidos")
        if dados['arquivos_efvar_info']:
            log_print(f"  - Arquivos EFVAR lidos (fora da base principal): {len(dados['arquivos_efvar_info'])}")
            log_print(f"    - CPFs únicos mapeados em EFVAR: {len(dados['cpfs_efvar'])}")
            for arquivo, qtd in sorted(dados['arquivos_efvar_info'].items()):
                log_print(f"    - Arquivo EFVAR '{os.path.basename(arquivo)}': {qtd} registros lidos")
        if dados['tipos_registros']:
            resumo_tipos = ", ".join(
                f"{tipo}: {qtd}" for tipo, qtd in sorted(dados['tipos_registros'].items())
            )
            log_print(f"  - Registros por tipo identificados: {resumo_tipos}")

        log_print(f"  - Resumo Consolidado:")
        log_print(f"    - Total de registros lidos: {total_lido}")
        log_print(f"    - Registros únicos: {total_unicos}")
        log_print(f"    - Duplicatas eliminadas: {duplicatas_eliminadas}")
        log_print(f"    - Arquivo de únicos gerado: {nome_arquivo_saida}")

        # Gera o arquivo de duplicatas GERAL se houver alguma
        if dados['duplicatas']:
            nome_arquivo_duplicatas = f'DUPLICADOS_BANCO_{banco_id}.txt'
            duplicatas_ordenadas = sorted(dados['duplicatas'].items())
            with open(nome_arquivo_duplicatas, 'w', encoding='utf-8') as arq_duplicatas:
                arq_duplicatas.write("NOME;CPF\n")
                for cpf, nome in duplicatas_ordenadas:
                    arq_duplicatas.write(f"{nome};{cpf}\n")
            log_print(f"    - Arquivo de duplicatas (GERAL) gerado: {nome_arquivo_duplicatas} ({len(duplicatas_ordenadas)} CPFs duplicados)")

        # Gera o arquivo de duplicatas INTER-SISTEMAS se houver alguma
        if dados['duplicatas_intersistemas']:
            nome_arquivo_inter = f'DUPLICADOS_INTERSISTEMAS_BANCO_{banco_id}.txt'
            intersistemas_ordenados = sorted(dados['duplicatas_intersistemas'].items())
            with open(nome_arquivo_inter, 'w', encoding='utf-8') as arq_inter:
                arq_inter.write("NOME;CPF\n")
                for cpf, nome in intersistemas_ordenados:
                    arq_inter.write(f"{nome};{cpf}\n")
            log_print(f"    - Arquivo de duplicatas (INTER-SISTEMAS) gerado: {nome_arquivo_inter} ({len(intersistemas_ordenados)} CPFs)")


    cpfs_efvar_por_banco = {
        banco_id: dados['cpfs_efvar'] for banco_id, dados in dados_por_banco.items()
    }
    return sorted(list(bancos_encontrados)), cpfs_efvar_por_banco

def carregar_cpfs_todos_bancos(bancos_a_processar):
    cpfs_bancos = set()

    for banco_id in bancos_a_processar:
        arquivo_banco = f'preparo_lista_banco_{banco_id}.txt'
        if not os.path.exists(arquivo_banco):
            continue

        try:
            with open(arquivo_banco, 'r', encoding='utf-8') as f:
                header = next(f).strip().split(';')
                if 'CPF' not in header:
                    continue
                idx_cpf = header.index('CPF')

                for line in f:
                    line = line.strip()
                    if ';' not in line:
                        continue
                    partes = line.split(';')
                    if idx_cpf >= len(partes):
                        continue
                    cpf = partes[idx_cpf].strip().zfill(11)
                    if cpf:
                        cpfs_bancos.add(cpf)
        except Exception as e:
            log_print(f"Aviso: Não foi possível ler '{arquivo_banco}' para mapear CPFs de banco: {e}")

    log_print(f"Total de CPFs únicos mapeados em todos os bancos: {len(cpfs_bancos)}")
    return cpfs_bancos

def passo2_preparar_excel_por_banco(df_original, banco_id):
    log_print(f"\n--- Preparando Excel para o Banco {banco_id} ---")
    
    if 'BANCO_ATUAL' not in df_original.columns:
        log_print("!! ERRO CRÍTICO: A coluna 'BANCO_ATUAL' não foi encontrada na planilha. !!")
        return False
        
    df = df_original.copy()
    
    df['BANCO_PADRONIZADO'] = df['BANCO_ATUAL'].astype(str).str.strip().str.zfill(3)
    df_banco = df[df['BANCO_PADRONIZADO'] == banco_id]
    
    log_print(f"Encontradas {len(df_banco)} linhas no Excel para o banco {banco_id}.")

    colunas_para_manter = [col for col, status in CONFIGURACAO_COLUNAS.items() if status == 'S']
    colunas_existentes = [c for c in colunas_para_manter if c in df_banco.columns]
    
    df_final = df_banco[colunas_existentes].copy()

    if 'CPF' in df_final.columns:
        df_final.loc[:, 'CPF'] = df_final['CPF'].astype(str).str.replace(r'[.\-]', '', regex=True).str.strip().str.zfill(11)

    nome_arquivo_saida = f'preparo_excel_bco_{banco_id}.txt'
    df_final.to_csv(nome_arquivo_saida, sep=';', index=False, header=True)
    log_print(f"Arquivo '{nome_arquivo_saida}' gerado com {len(df_final)} linhas.")
    
    return True

def passo3_analisar_cruzamento(
    banco_id,
    cpfs_excluidos,
    cpfs_inconsistentes_bancarios,
    cpfs_efvar_banco
):
    

    arquivo_banco = f'preparo_lista_banco_{banco_id}.txt'
    arquivo_folha = f'preparo_excel_bco_{banco_id}.txt'
    
    try:
        if os.path.exists(arquivo_folha) and os.path.getsize(arquivo_folha) > 5:
            with open(arquivo_folha, 'r', encoding='utf-8') as f:
                header_folha = next(f).strip().split(';')
                try:
                    idx_cpf_folha = header_folha.index('CPF')
                    linhas_folha = [line.strip() for line in f if ';' in line.strip()]
                    cpfs_folha = {extrair_cpf_da_linha(line, idx_cpf_folha) for line in linhas_folha}
                except ValueError:
                    log_print(f"Aviso: Coluna 'CPF' não encontrada no cabeçalho de '{arquivo_folha}'.")
                    cpfs_folha, linhas_folha, header_folha, idx_cpf_folha = set(), [], [], -1
        else:
             cpfs_folha, linhas_folha, header_folha, idx_cpf_folha = set(), [], [], -1

        with open(arquivo_banco, 'r', encoding='utf-8') as f:
            header_banco = next(f).strip().split(';')
            idx_cpf_banco = header_banco.index('CPF')
            linhas_banco = [line.strip() for line in f if ';' in line.strip()]
            cpfs_banco = {extrair_cpf_da_linha(line, idx_cpf_banco) for line in linhas_banco}

    except FileNotFoundError as e:
        log_print(f"Erro: Arquivo de preparo não encontrado: {e.filename}. Pulando análise.")
        return None
    except (ValueError, IndexError) as e:
        log_print(f"Erro ao ler arquivo de preparo para o banco {banco_id}: {e}.")
        return None

    banco_encontrados_list = [line for line in linhas_banco if extrair_cpf_da_linha(line, idx_cpf_banco) in cpfs_folha]
    
    banco_nao_encontrados_bruto_list = [
        line for line in linhas_banco
        if extrair_cpf_da_linha(line, idx_cpf_banco) not in cpfs_folha
    ]

    # CPFs presentes em EFVAR não entram nos "não encontrados" do lado banco.
    banco_nao_encontrados_bruto_sem_efvar_list = [
        line for line in banco_nao_encontrados_bruto_list
        if extrair_cpf_da_linha(line, idx_cpf_banco) not in cpfs_efvar_banco
    ]

    banco_nao_encontrados_list = [
        line for line in banco_nao_encontrados_bruto_sem_efvar_list
        if extrair_cpf_da_linha(line, idx_cpf_banco) not in cpfs_excluidos
    ]

    if idx_cpf_folha != -1:
        folha_encontrados_list = [line for line in linhas_folha if extrair_cpf_da_linha(line, idx_cpf_folha) in cpfs_banco]
        folha_nao_encontrados_list = [line for line in linhas_folha if extrair_cpf_da_linha(line, idx_cpf_folha) not in cpfs_banco]
        folha_inconsistencia_bancaria_list = [
            line for line in folha_nao_encontrados_list
            if extrair_cpf_da_linha(line, idx_cpf_folha) in cpfs_inconsistentes_bancarios
        ]
    else:
        folha_encontrados_list, folha_nao_encontrados_list, folha_inconsistencia_bancaria_list = [], [], []

    folha_encontrados_efvar_list = [
        line for line in folha_nao_encontrados_list
        if extrair_cpf_da_linha(line, idx_cpf_folha) in cpfs_efvar_banco
    ] if idx_cpf_folha != -1 else []
    
    header_banco_str = ";".join(header_banco) + "\n"
    header_folha_str = ";".join(header_folha) + "\n" if header_folha else ""
    
    with open(f'BANCO_ENCONTRADOS_NA_FOLHA_{banco_id}.txt', 'w', encoding='utf-8') as f:
        f.write(header_banco_str)
        f.write('\n'.join(banco_encontrados_list))
    with open(f'BANCO_NAO_ENCONTRADOS_NA_FOLHA_{banco_id}.txt', 'w', encoding='utf-8') as f:
        f.write(header_banco_str)
        f.write('\n'.join(banco_nao_encontrados_list))
    with open(f'BANCO_NAO_ENCONTRADOS_NA_FOLHA_{banco_id}_BRUTO.txt', 'w', encoding='utf-8') as f:
        f.write(header_banco_str)
        f.write('\n'.join(banco_nao_encontrados_bruto_sem_efvar_list))
    with open(f'FOLHA_ENCONTRADOS_NO_BANCO_{banco_id}.txt', 'w', encoding='utf-8') as f:
        f.write(header_folha_str)
        f.write('\n'.join(folha_encontrados_list))
    with open(f'FOLHA_NAO_ENCONTRADOS_NO_BANCO_{banco_id}.txt', 'w', encoding='utf-8') as f:
        f.write(header_folha_str)
        f.write('\n'.join(folha_nao_encontrados_list))
    with open(f'Inconsistencia_Bancaria_{banco_id}.txt', 'w', encoding='utf-8') as f:
        f.write(header_folha_str)
        f.write('\n'.join(folha_inconsistencia_bancaria_list))

    cpfs_inconsistencia = {extrair_cpf_da_linha(line, idx_cpf_folha) for line in folha_inconsistencia_bancaria_list}
    cpfs_efvar = {extrair_cpf_da_linha(line, idx_cpf_folha) for line in folha_encontrados_efvar_list}
    cpfs_abatidos = cpfs_inconsistencia.union(cpfs_efvar)
    folha_nao_encontrados_pos_abatimento_list = [
        line for line in folha_nao_encontrados_list
        if extrair_cpf_da_linha(line, idx_cpf_folha) not in cpfs_abatidos
    ]
    folha_nao_encontrados_ajustado = len(folha_nao_encontrados_pos_abatimento_list)

    stats = {
        "banco_total": len(linhas_banco),
        "banco_encontrados": len(banco_encontrados_list),
        "banco_nao_encontrados_bruto": len(banco_nao_encontrados_bruto_sem_efvar_list),
        "banco_nao_encontrados": len(banco_nao_encontrados_list),
        "folha_total": len(linhas_folha),
        "folha_encontrados": len(folha_encontrados_list),
        "folha_nao_encontrados": len(folha_nao_encontrados_list),
        "folha_inconsistencia_bancaria": len(folha_inconsistencia_bancaria_list),
        "folha_encontrados_efvar": len(folha_encontrados_efvar_list),
        "folha_nao_encontrados_ajustado": folha_nao_encontrados_ajustado,
        "header_folha": header_folha,
        "folha_encontrados_efvar_list": folha_encontrados_efvar_list,
        "folha_nao_encontrados_pos_abatimento_list": folha_nao_encontrados_pos_abatimento_list
    }
    
    log_print(f"\n--- Análise de Cruzamento - Banco {banco_id} ---")
    log_print(f"  - Total de CPFs no arquivo do Banco: {stats['banco_total']}")
    log_print(f"  - CPFs do Banco ENCONTRADOS na Folha: {stats['banco_encontrados']}")
    log_print(f"  - CPFs no Banco que não foram encontrados na Folha (BRUTO): {stats['banco_nao_encontrados_bruto']}")
    log_print(f"  - CPFs no Banco que não foram encontrados na Folha: {stats['banco_nao_encontrados']}")
    log_print(f"  - Total de CPFs no arquivo da Folha: {stats['folha_total']}")
    log_print(f"  - CPFs da Folha ENCONTRADOS no Banco: {stats['folha_encontrados']}")
    log_print(f"  - CPFs da Folha em inconsistencia Bancaria: {stats['folha_inconsistencia_bancaria']}")
    log_print(f"  - CPFs da Folha que estão no banco EFVAR: {stats['folha_encontrados_efvar']}")
    log_print(f"  - CPFs da Folha que não foram encontrados no Banco: {stats['folha_nao_encontrados_ajustado']}")
    log_print(f"  - Arquivos de resultado gerados com sufixo '_{banco_id}.txt'")

    return stats

def gerar_relatorios_excluidos(df_original, cpfs_todos_bancos):
    log_print(f"\n--- Gerando Relatórios de CPFs Excluídos pelos Filtros ---")
    df = df_original.copy()

    if 'CPF' not in df.columns:
        log_print("  - AVISO: Coluna 'CPF' não encontrada para gerar relatórios de exclusão.")
        return df, set()

    cpfs_excluidos_geral = set()
    indices_para_remover = []

    for filtro in CONFIGURACAO_FILTROS:
        if len(filtro) == 3:
            coluna, operador, valor = filtro
            coluna_condicional, operador_condicional, valor_condicional = None, None, None
        elif len(filtro) == 6:
            coluna, operador, valor, coluna_condicional, operador_condicional, valor_condicional = filtro
        else:
            log_print(f"  - AVISO: Filtro inválido '{filtro}'. Filtro ignorado.")
            continue

        if coluna not in df.columns:
            log_print(f"  - AVISO: A coluna de filtro '{coluna}' não existe na planilha. Filtro ignorado.")
            continue
        
        if operador == '!=':
            mascara_principal = df[coluna].astype(str).str.strip() == valor
            mascara_final = mascara_principal

            if coluna_condicional:
                if coluna_condicional not in df.columns:
                    log_print(f"  - AVISO: A coluna condicional '{coluna_condicional}' não existe na planilha. Filtro ignorado.")
                    continue
                if operador_condicional == '==':
                    mascara_condicional = df[coluna_condicional].astype(str).str.strip() == valor_condicional
                    mascara_final = mascara_principal & mascara_condicional
                else:
                    log_print(f"  - AVISO: Operador condicional '{operador_condicional}' não suportado. Filtro ignorado.")
                    continue

            filtro_pg11_sippes = (
                coluna == 'PG' and str(valor).strip() == '11' and
                coluna_condicional == 'SISTEMA' and operador_condicional == '==' and
                str(valor_condicional).strip().upper() == 'SIPPES'
            )
            remover_da_analise = True
            contabilizar_como_excluido = True

            if filtro_pg11_sippes:
                cpf_normalizado = df['CPF'].astype(str).str.replace(r'[.\-]', '', regex=True).str.strip().str.zfill(11)
                mascara_nao_esta_no_banco = ~cpf_normalizado.isin(cpfs_todos_bancos)
                mascara_final = mascara_final & mascara_nao_esta_no_banco
                remover_da_analise = False
                contabilizar_como_excluido = False
                log_print("  - Regra especial PG 11/SIPPES: relatório considera apenas CPFs que NÃO estão em nenhum arquivo de banco.")

            df_excluido_neste_filtro = df[mascara_final]

            if not df_excluido_neste_filtro.empty:
                nome_arquivo_saida = f'FILTRO_EXCLUIDO_DA_FOLHA_{coluna}_{valor}.txt'
                caminho_absoluto = os.path.abspath(nome_arquivo_saida)
                
                cpfs_deste_filtro = set(df_excluido_neste_filtro['CPF'].astype(str).str.replace(r'[.\\-]', '', regex=True).str.strip().str.zfill(11))
                if contabilizar_como_excluido:
                    cpfs_excluidos_geral.update(cpfs_deste_filtro)

                df_excluido_neste_filtro.to_csv(
                    nome_arquivo_saida, sep=';', index=False, header=True
                )
                log_print(f"  - Relatório de exclusão gerado: '{nome_arquivo_saida}' com {len(df_excluido_neste_filtro)} CPFs.")
                log_print(f"  - Arquivo salvo em: {caminho_absoluto}")
                
                if remover_da_analise:
                    indices_para_remover.extend(df_excluido_neste_filtro.index)

    df_analise = df.drop(index=list(set(indices_para_remover)))
    
    total_excluidos = len(list(set(indices_para_remover)))
    log_print(f"  - Total de CPFs únicos excluídos por filtros: {len(cpfs_excluidos_geral)}")
    log_print(f"  - Total de CPFs restantes para análise: {len(df_analise)}")

    return df_analise, cpfs_excluidos_geral

def _abrir_dialogo_selecao_arquivo(titulo, filetypes, initialfile=None):
    """Abre um filedialog forçando a janela a aparecer SOBRE as demais.
    Retorna o caminho selecionado ou string vazia se o usuário cancelar.
    """
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    root.lift()
    root.focus_force()
    root.update_idletasks()

    kwargs = {"title": titulo, "filetypes": filetypes, "parent": root}
    if initialfile:
        kwargs["initialfile"] = initialfile

    try:
        return filedialog.askopenfilename(**kwargs)
    finally:
        root.destroy()


def selecionar_arquivo_excel():
    log_print("\n>> AGUARDANDO: selecione o arquivo Excel da folha de pagamento na janela aberta...")
    caminho_arquivo = _abrir_dialogo_selecao_arquivo(
        titulo="Selecione o arquivo Excel da folha de pagamento",
        filetypes=[("Arquivos Excel", "*.xlsx *.xls"), ("Todos os arquivos", "*.*")]
    )
    if not caminho_arquivo:
        log_print("Nenhum arquivo selecionado. O programa será encerrado.")
        return None
    log_print(f"\nArquivo da folha selecionado: {caminho_arquivo}")
    return caminho_arquivo


def selecionar_arquivo_smop():
    log_print("\n>> AGUARDANDO: selecione o arquivo SMOP (inconsistência bancária) na janela aberta...")
    caminho_arquivo = _abrir_dialogo_selecao_arquivo(
        titulo="Selecione o arquivo SMOP",
        filetypes=[("Arquivos texto", "*.txt"), ("Todos os arquivos", "*.*")],
        initialfile=ARQUIVO_SMOP
    )
    if not caminho_arquivo:
        log_print("Nenhum arquivo SMOP selecionado. O processamento seguirá sem inconsistência bancária.")
        return None
    log_print(f"Arquivo SMOP selecionado: {caminho_arquivo}")
    return caminho_arquivo

def main():
    resultado_passo1 = passo1_identificar_e_processar_bancos()
    if not resultado_passo1:
        return
    bancos_a_processar, cpfs_efvar_por_banco = resultado_passo1
    if not bancos_a_processar:
        return

    caminho_excel = selecionar_arquivo_excel()
    if not caminho_excel:
        return

    try:
        log_print("Lendo o arquivo Excel... (isso pode levar alguns segundos)")
        log_print(f"Lendo a guia: '{NOME_DA_GUIA_EXCEL}'")
        df_excel_main = pd.read_excel(caminho_excel, sheet_name=NOME_DA_GUIA_EXCEL, dtype=str)
        log_print(f"Arquivo lido com sucesso. Total de {len(df_excel_main)} linhas encontradas.")
    except Exception as e:
        log_print(f"Ocorreu um erro fatal ao ler o arquivo Excel: {e}")
        return

    cpfs_todos_bancos = carregar_cpfs_todos_bancos(bancos_a_processar)
    df_para_analise, cpfs_excluidos = gerar_relatorios_excluidos(df_excel_main, cpfs_todos_bancos)
    cpfs_inconsistentes_bancarios = carregar_cpfs_inconsistencia_bancaria()

    totais_gerais = defaultdict(int)
    header_folha_geral = []
    folha_encontrados_efvar_geral = []
    folha_nao_encontrados_pos_abatimento_geral = []

    for banco_id in bancos_a_processar:
        passo2_ok = passo2_preparar_excel_por_banco(df_para_analise, banco_id)
        if not passo2_ok:
            continue 
        
        stats_banco = passo3_analisar_cruzamento(
            banco_id,
            cpfs_excluidos,
            cpfs_inconsistentes_bancarios,
            cpfs_efvar_por_banco.get(banco_id, set())
        )
        
        if stats_banco:
            for key, value in stats_banco.items():
                if key in {"header_folha", "folha_encontrados_efvar_list", "folha_nao_encontrados_pos_abatimento_list"}:
                    continue
                totais_gerais[key] += value

            if not header_folha_geral and stats_banco.get("header_folha"):
                header_folha_geral = stats_banco["header_folha"]

            for line in stats_banco.get("folha_encontrados_efvar_list", []):
                folha_encontrados_efvar_geral.append(f"{banco_id};{line}")
            for line in stats_banco.get("folha_nao_encontrados_pos_abatimento_list", []):
                folha_nao_encontrados_pos_abatimento_geral.append(f"{banco_id};{line}")

    if header_folha_geral:
        header_geral = "BANCO_REFERENCIA;" + ";".join(header_folha_geral) + "\n"

        with open("FOLHA_ENCONTRADOS_NO_BANCO_EFVAR_GERAL.txt", "w", encoding="utf-8") as f:
            f.write(header_geral)
            f.write("\n".join(folha_encontrados_efvar_geral))

        with open("FOLHA_NAO_ENCONTRADOS_GERAL_APOS_ABATIMENTOS.txt", "w", encoding="utf-8") as f:
            f.write(header_geral)
            f.write("\n".join(folha_nao_encontrados_pos_abatimento_geral))

    banco_nao_encontrados_total = totais_gerais['banco_nao_encontrados']
    folha_nao_encontrados_total = totais_gerais['folha_nao_encontrados']
    folha_inconsistencia_bancaria_total = totais_gerais['folha_inconsistencia_bancaria']
    folha_encontrados_efvar_total = totais_gerais['folha_encontrados_efvar']
    folha_nao_encontrados_ajustado_total = totais_gerais['folha_nao_encontrados_ajustado']
    
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
  - CPFs da Folha em inconsistencia Bancaria: {folha_inconsistencia_bancaria_total}
  - CPFs da Folha que estão no banco EFVAR: {folha_encontrados_efvar_total}
  - Total NÃO ENCONTRADOS nos arquivos de banco: {folha_nao_encontrados_ajustado_total}
  - Total NÃO ENCONTRADOS bruto (antes da subtração): {folha_nao_encontrados_total}
Processo concluído."""

    print(relatorio_final_str)  # Imprime no console
    log_buffer.append(relatorio_final_str) # Adiciona ao buffer para o arquivo
    
    # Grava o log no arquivo
    with open("RELATÓRIO_GERAL.txt", "w", encoding='utf-8') as f:
        f.write("\n".join(log_buffer))
    
    print(f"\nO relatório completo desta execução também foi salvo em 'RELATÓRIO_GERAL.txt'")


if __name__ == "__main__":
    main()
