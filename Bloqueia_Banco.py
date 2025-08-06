# -*- coding: utf-8 -*-
import os

def processar_arquivo_banco():
    """
    Lê múltiplos arquivos de banco, extrai nome e CPF, e consolida em um arquivo intermediário.
    """
    arquivos_banco = [
        'bco001_febra.txt',
        'bco001_febra_pec.txt',
        'febraban_bco001_ev.txt',
        'febraban_pj_001.txt'
    ]
    diretorio_base = 'SIAPPES/JUNHO'
    
    registros_por_arquivo = {}
    total_registros_consolidados = 0

    try:
        with open('preparo_lista_banco.txt', 'w', encoding='utf-8') as arq_preparo:
            for nome_arquivo in arquivos_banco:
                caminho_arquivo = os.path.join(diretorio_base, nome_arquivo)
                registros_neste_arquivo = 0
                
                try:
                    with open(caminho_arquivo, 'r', encoding='latin-1') as arq_banco:
                        banco_linhas = arq_banco.readlines()
                        # Alguns arquivos podem ser pequenos e não ter cabeçalho/rodapé
                        if len(banco_linhas) > 4:
                            linhas_relevantes = banco_linhas[2:-2]
                        else:
                            linhas_relevantes = banco_linhas

                        for i in range(0, len(linhas_relevantes), 2):
                            if i + 1 < len(linhas_relevantes):
                                linha_banco_a = linhas_relevantes[i]
                                linha_banco_b = linhas_relevantes[i+1]

                                nome_banco = linha_banco_a[43:73].strip()
                                cpf_banco = linha_banco_b[21:33].strip()

                                nome_banco_formatado = nome_banco.ljust(30)
                                if nome_banco and cpf_banco:
                                    arq_preparo.write(f"{nome_banco_formatado},{cpf_banco}\n")
                                    registros_neste_arquivo += 1
                    
                    registros_por_arquivo[nome_arquivo] = registros_neste_arquivo
                    total_registros_consolidados += registros_neste_arquivo

                except FileNotFoundError:
                    print(f"Aviso: O arquivo '{caminho_arquivo}' não foi encontrado e será ignorado.")
                    registros_por_arquivo[nome_arquivo] = "Não encontrado"
                except Exception as e:
                    print(f"Erro ao processar o arquivo '{caminho_arquivo}': {e}")
                    registros_por_arquivo[nome_arquivo] = f"Erro ({e})"

        print("--- Relatório de Processamento dos Bancos ---")
        for nome, contagem in registros_por_arquivo.items():
            print(f"Arquivo '{nome}': {contagem} registros processados.")
        print("-----------------------------------------------")
        print(f"Total de registros consolidados em 'preparo_lista_banco.txt': {total_registros_consolidados}")
        return True

    except Exception as e:
        print(f"Ocorreu um erro geral ao processar os arquivos de banco: {e}")
        return False

def filtrar_folha_por_banco():
    """
    Filtra o arquivo da folha de pagamento para manter apenas os registros do banco '001'.
    """
    linhas_lidas_folha = 0
    linhas_filtradas = 0
    try:
        with open('FINAL_SAAFOPAG_FOLHA_PGTO_F3_2025.CSV', 'r', encoding='utf-8') as arq_folha, \
             open('preparo_excel_bco.txt', 'w', encoding='utf-8') as arq_filtrado:

            for linha in arq_folha:
                linhas_lidas_folha += 1
                try:
                    partes = linha.strip().split(';')
                    if len(partes) > 1 and partes[1].strip() == "001":
                        arq_filtrado.write(linha)
                        linhas_filtradas += 1
                except IndexError:
                    print(f"Aviso: Linha mal formada na folha de pagamento será ignorada: {linha.strip()}")
        
        print("\n--- Relatório de Filtragem da Folha ---")
        print(f"Arquivo 'FINAL_SAAFOPAG_FOLHA_PGTO_F3_2025.CSV' lido: {linhas_lidas_folha} linhas.")
        print(f"Arquivo 'preparo_excel_bco.txt' gerado com {linhas_filtradas} registros do banco '001'.")
        return True

    except FileNotFoundError:
        print("Erro: O arquivo 'FINAL_SAAFOPAG_FOLHA_PGTO_F3_2025.CSV' não foi encontrado.")
        return False
    except Exception as e:
        print(f"Ocorreu um erro inesperado durante a filtragem da folha: {e}")
        return False

def comparar_listas():
    """
    Compara o arquivo do banco com a folha de pagamento filtrada.
    """
    try:
        with open('preparo_excel_bco.txt', 'r', encoding='utf-8') as arq_folha_filtrada:
            conteudo_folha = arq_folha_filtrada.readlines()
            linhas_folha_filtrada = len(conteudo_folha)
            cpfs_folha = {linha.split(';')[0].strip() for linha in conteudo_folha}

        total_encontrados = 0
        total_nao_encontrados = 0
        linhas_preparo = 0
        with open('preparo_lista_banco.txt', 'r', encoding='utf-8') as arq_preparo, \
             open('LISTA_ENCONTRADOS.txt', 'w', encoding='utf-8') as arq_encontrados, \
             open('LISTA_NAO_ENCONTRADOS.txt', 'w', encoding='utf-8') as arq_nao_encontrados:

            for linha_preparo in arq_preparo:
                linhas_preparo += 1
                try:
                    cpf_preparo = linha_preparo.strip().split(',')[1]

                    if cpf_preparo in cpfs_folha:
                        arq_encontrados.write(linha_preparo)
                        total_encontrados += 1
                    else:
                        arq_nao_encontrados.write(linha_preparo)
                        total_nao_encontrados += 1
                except IndexError:
                    print(f"Aviso: Linha mal formada no 'preparo_lista_banco.txt' será ignorada: {linha_preparo.strip()}")

        print("\n--- Relatório Final de Comparação ---")
        print(f"Arquivo 'preparo_excel_bco.txt' lido: {linhas_folha_filtrada} linhas.")
        print(f"Arquivo 'preparo_lista_banco.txt' lido: {linhas_preparo} linhas.")
        print(f"Total de registros encontrados: {total_encontrados}")
        print(f"Total de registros não encontrados: {total_nao_encontrados}")

    except FileNotFoundError as e:
        print(f"Erro: Arquivo não encontrado - {e.filename}")
    except Exception as e:
        print(f"Ocorreu um erro inesperado durante a comparação: {e}")

if __name__ == "__main__":
    if processar_arquivo_banco():
        if filtrar_folha_por_banco():
            comparar_listas()

# --- CÓDIGO ANTIGO COMENTADO ---
# ...
