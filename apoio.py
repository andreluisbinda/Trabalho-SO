from datetime import datetime
import json
import math


def ler_ids(caminho):
    ids = []
    with caminho.open(encoding="utf-8-sig") as arquivo:
        for numero, linha in enumerate(arquivo, 1):
            if linha.strip():
                try:
                    ids.append(int(linha.strip()))
                except ValueError as erro:
                    raise ValueError(f"ID inválido na linha {numero}") from erro
    if len(ids) != len(set(ids)):
        raise ValueError("A lista contém IDs repetidos. Use um inteiro único por linha.")
    return ids


def conferir_log(caminho, ids):
    if not caminho.exists():
        return 0, "enriquecimento incompleto: log ausente"
    linhas = caminho.read_text(encoding="utf-8").splitlines()
    if len(linhas) != len(ids):
        return len(linhas), "enriquecimento incompleto"
    encontrados = []
    try:
        for linha in linhas:

            data, thread, identificador, resposta = linha.split(",", 3)
            datetime.strptime(data.strip(), "%Y-%m-%d %H:%M:%S")
            if not thread.strip().startswith("Thread-"):
                raise ValueError("Nome de thread inválido")
            identificador = int(identificador)
            dados = json.loads(resposta)
            if (not isinstance(dados, dict) or set(dados) != {"id", "status", "valor"}
                    or type(dados["id"]) is not int or dados["id"] != identificador
                    or dados["status"] != "ok" or type(dados["valor"]) not in (int, float)
                    or not math.isfinite(dados["valor"])):
                raise ValueError("JSON fora do formato esperado")
            encontrados.append(identificador)
    except (ValueError, TypeError, KeyError) as erro:
        return len(linhas), f"log inválido: {erro}"
    if sorted(encontrados) != sorted(ids):
        return len(linhas), "enriquecimento incompleto: IDs ausentes ou duplicados"
    return len(linhas), "completo"


def imprimir_tabela(resultados):
    tabela = ["| Lista | IDs | Threads | P1 (s) | Total P0 (s) | Linhas | Status |",
              "|---|---:|---:|---:|---:|---:|---|"]
    for r in resultados:
        tempo = "n/d" if r["tempo_p1"] is None else f'{r["tempo_p1"]:.4f}'
        tabela.append(f'| {r["lista"]} | {r["ids"]} | {r["threads"]} | {tempo} | '
                      f'{r["tempo_total"]:.4f} | {r["linhas"]} | {r["status"]} |')
    print("\n" + "\n".join(tabela))
