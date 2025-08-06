# Abrir os arquivos
Arqlista = open("ArqLista.txt", "r")
Arqbanco = open("ArqBanco.txt", "r")
resultado_banco = open("Resultado.txt", "w")

# Ler as linhas dos arquivos
lista_linhas = Arqlista.readlines()
banco_linhas = Arqbanco.readlines()

# Iterar sobre as linhas de ArqLista
for linha_lista in lista_linhas:
    # Supondo que o CPF está nas primeiras 11 posições
    cpf_lista = int(linha_lista[0:11])
    # Supondo que o valor está após o ponto e vírgula
    valor_lista = linha_lista[12:]

    # Iterar sobre as linhas de ArquiBanco em pares
    for linha_banco_a, linha_banco_b in zip(banco_linhas[2::2], banco_linhas[3::2]):

        valor_banco = int(linha_banco_a[120:135])
        cpf_banco = linha_banco_b[21:33]
        if cpf_banco == 12146965703:
            print(f"{cpf_banco}  {cpf_lista}")
        # Comparar CPF e valor
        # if cpf_lista == cpf_banco and valor_lista == valor_banco:
        #   resultado_banco.write(f'{cpf_lista};{valor_lista}\n')

        # print(f"cpf_lista: {cpf_lista} cpf_banco: {cpf_banco}")
        # print(f"valor_lista: {valor_lista} valor_banco: {valor_banco}")
        # print(f"linha_banco_a: {linha_banco_a}")
        # print(f"linha_banco_b: {linha_banco_b}")
        # print("                                                   ")
        # print("###################################################")
        # print("###################################################")


# Fechar os arquivos
Arqlista.close()
Arqbanco.close()
resultado_banco.close()
# print(f"cpf da lista {cpf_lista}")
# print(f"valor da lista {valor_lista}")
# print(f"cpf do banco {cpf_banco}")
# print(f"valor do banco {valor_banco}")
