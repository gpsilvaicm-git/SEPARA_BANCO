# -*- coding: utf-8 -*-
import os

def processar_arquivo_banco():
    """
    Lê múltiplos arquivos de banco de diretórios especificados, 
    extrai nome e CPF, e consolida em um arquivo intermediário sem duplicatas.
    """
    diretorios_base = ['SIAPPES/JUNHO', 'SIPPES/JUNHO']
    
    registros_por_arquivo = {}
    # Usar dicionário para eliminar duplicatas baseado apenas no CPF
    # Chave = CPF, Valor = nome formatado (mantém o primeiro encontrado)
    registros_unicos = {}

    try:
        for diretorio in diretorios_base:
            if not os.path.isdir(diretorio):
                print(f"Aviso: Diretório '{diretorio}' não encontrado. Pulando...")
                continue

            for nome_arquivo in os.listdir(diretorio):
                caminho_arquivo = os.path.join(diretorio, nome_arquivo)
                
                # Pular subdiretórios, se houver
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

                                # Validação mínima do comprimento da linha para evitar IndexError
                                if len(linha_banco_a) > 73 and len(linha_banco_b) > 33:
                                    nome_banco = linha_banco_a[43:73].strip()
                                    cpf_banco = linha_banco_b[21:33].strip()

                                    if nome_banco and cpf_banco:
                                        # Adicionar apenas se o CPF ainda não existir (mantém o primeiro nome encontrado)
                                        if cpf_banco not in registros_unicos:
                                            registros_unicos[cpf_banco] = nome_banco
                                        registros_neste_arquivo += 1
                    
                    chave_relatorio = os.path.join(os.path.basename(diretorio), nome_arquivo)
                    registros_por_arquivo[chave_relatorio] = registros_neste_arquivo

                except (IOError, UnicodeDecodeError) as e:
                    chave_relatorio = os.path.join(os.path.basename(diretorio), nome_arquivo)
                    print(f"Aviso: Não foi possível processar o arquivo '{caminho_arquivo}'. Pode não ser um arquivo de texto ou ter uma codificação inesperada. Erro: {e}")
                    registros_por_arquivo[chave_relatorio] = f"Erro de leitura"
                except Exception as e:
                    chave_relatorio = os.path.join(os.path.basename(diretorio), nome_arquivo)
                    print(f"Erro inesperado ao processar o arquivo '{caminho_arquivo}': {e}")
                    registros_por_arquivo[chave_relatorio] = f"Erro ({e})"

        # Agora escrever os registros únicos no arquivo final
        with open('preparo_lista_banco.txt', 'w', encoding='utf-8') as arq_preparo:
            for cpf in sorted(registros_unicos.keys()):  # sorted por CPF para ordem consistente
                nome = registros_unicos[cpf]
                arq_preparo.write(f"{nome};{cpf}\n")

        total_antes_deduplicacao = sum(count for count in registros_por_arquivo.values() if isinstance(count, int))
        total_apos_deduplicacao = len(registros_unicos)

        print("\n--- Relatório de Processamento dos Bancos ---")
        for nome, contagem in registros_por_arquivo.items():
            print(f"Arquivo '{nome}': {contagem} registros processados.")
        print("-----------------------------------------------")
        print(f"Total de registros lidos: {total_antes_deduplicacao}")
        print(f"Total de registros únicos consolidados em 'preparo_lista_banco.txt': {total_apos_deduplicacao}")
        print(f"Duplicatas eliminadas: {total_antes_deduplicacao - total_apos_deduplicacao}")
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

def analisar_banco_vs_folha():
    """
    Analisa CPFs do banco que estão ou não na folha de pagamento.
    """
    try:
        # Carregar CPFs da folha em um set
        with open('preparo_excel_bco.txt', 'r', encoding='utf-8') as arq_folha:
            cpfs_folha = {linha.split(';')[0].strip() for linha in arq_folha if linha.strip()}

        # Analisar arquivo do banco
        banco_encontrados_na_folha = []
        banco_nao_encontrados_na_folha = []
        
        with open('preparo_lista_banco.txt', 'r', encoding='utf-8') as arq_banco:
            for linha in arq_banco:
                linha = linha.strip()
                if linha:
                    cpf_banco = linha.split(';')[1].strip()
                    
                    if cpf_banco in cpfs_folha:
                        banco_encontrados_na_folha.append(linha)
                    else:
                        banco_nao_encontrados_na_folha.append(linha)

        # Escrever os resultados
        with open('BANCO_ENCONTRADOS_NA_FOLHA.txt', 'w', encoding='utf-8') as arq:
            for linha in banco_encontrados_na_folha:
                arq.write(f"{linha}\n")

        with open('BANCO_NAO_ENCONTRADOS_NA_FOLHA.txt', 'w', encoding='utf-8') as arq:
            for linha in banco_nao_encontrados_na_folha:
                arq.write(f"{linha}\n")

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
    """
    Analisa CPFs da folha que estão ou não no arquivo do banco.
    """
    try:
        # Carregar CPFs do banco em um set
        with open('preparo_lista_banco.txt', 'r', encoding='utf-8') as arq_banco:
            cpfs_banco = {linha.split(';')[1].strip() for linha in arq_banco if linha.strip()}

        # Analisar arquivo da folha
        folha_encontrados_no_banco = []
        folha_nao_encontrados_no_banco = []
        
        with open('preparo_excel_bco.txt', 'r', encoding='utf-8') as arq_folha:
            for linha in arq_folha:
                linha = linha.strip()
                if linha:
                    cpf_folha = linha.split(';')[0].strip()
                    
                    if cpf_folha in cpfs_banco:
                        folha_encontrados_no_banco.append(linha)
                    else:
                        folha_nao_encontrados_no_banco.append(linha)

        # Escrever os resultados
        with open('FOLHA_ENCONTRADOS_NO_BANCO.txt', 'w', encoding='utf-8') as arq:
            for linha in folha_encontrados_no_banco:
                arq.write(f"{linha}\n")

        with open('FOLHA_NAO_ENCONTRADOS_NO_BANCO.txt', 'w', encoding='utf-8') as arq:
            for linha in folha_nao_encontrados_no_banco:
                arq.write(f"{linha}\n")

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
    """
    Executa análise bidirecional completa entre banco e folha.
    """
    print(f"\n{'='*50}")
    print(f"ANÁLISE BIDIRECIONAL COMPLETA")
    print(f"{'='*50}")
    
    # Análise 1: Banco vs Folha
    banco_na_folha, banco_nao_na_folha = analisar_banco_vs_folha()
    
    # Análise 2: Folha vs Banco  
    folha_no_banco, folha_nao_no_banco = analisar_folha_vs_banco()
    
    # Resumo final
    print(f"\n{'='*50}")
    print(f"RESUMO FINAL")
    print(f"{'='*50}")
    print(f"Intersecção (CPFs em ambos): {banco_na_folha} CPFs")
    print(f"\nArquivos gerados:")
    print(f"  - BANCO_ENCONTRADOS_NA_FOLHA.txt")
    print(f"  - BANCO_NAO_ENCONTRADOS_NA_FOLHA.txt")
    print(f"  - FOLHA_ENCONTRADOS_NO_BANCO.txt")
    print(f"  - FOLHA_NAO_ENCONTRADOS_NO_BANCO.txt")

if __name__ == "__main__":
    if processar_arquivo_banco():
        if filtrar_folha_por_banco():
            comparar_listas()

# --- CÓDIGO ANTIGO COMENTADO ---
# ...