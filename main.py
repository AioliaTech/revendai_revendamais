def filtrar_veiculos(vehicles, filtros, valormax=None):
    campos_com_fuzzy = ["modelo"]
    campos_exatos = ["titulo"]
    vehicles_filtrados = vehicles.copy()

    for chave, valor in filtros.items():
        if not valor:
            continue
        termo_busca = normalizar(valor)
        termos = termo_busca.split()
        resultados = []

        for v in vehicles_filtrados:
            match = False
            for campo in campos_com_fuzzy + campos_exatos:
                conteudo = v.get(campo, "")
                if not conteudo:
                    continue
                texto = normalizar(str(conteudo))

                for termo in termos:
                    if campo in campos_exatos:
                        if termo in texto or texto in termo:
                            match = True
                            break
                    elif campo in campos_com_fuzzy:
                        if termo in texto or texto in termo:
                            match = True
                            break
                        score_ratio = fuzz.ratio(texto, termo)
                        score_token = fuzz.token_set_ratio(texto, termo)
                        score_partial = fuzz.partial_ratio(texto, termo)
                        if score_ratio >= 70 or score_token >= 70 or score_partial >= 70:
                            match = True
                            break
                if match:
                    break

            if match:
                resultados.append(v)
        vehicles_filtrados = resultados

    if valormax:
        try:
            teto = float(valormax)
            maximo = teto * 1.3
            vehicles_filtrados = [
                v for v in vehicles_filtrados
                if "preco" in v and converter_preco(v["preco"]) is not None and converter_preco(v["preco"]) <= maximo
            ]
        except:
            return []

    vehicles_filtrados.sort(
        key=lambda v: converter_preco(v["preco"]) if "preco" in v else float('inf'),
        reverse=True
    )
    return vehicles_filtrados
