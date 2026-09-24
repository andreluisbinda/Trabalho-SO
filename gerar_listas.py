from pathlib import Path


TAMANHOS = [("pequena", 10), ("media", 100), ("grande", 500)]


def gerar_listas(pasta):
    casos = []
    for nome, tamanho in TAMANHOS:
        caminho = pasta / nome / "lista_ids.txt"
        caminho.parent.mkdir(parents=True, exist_ok=True)
        with caminho.open("w", encoding="utf-8") as arquivo:
            for identificador in range(100, 100 + tamanho):
                arquivo.write(f"{identificador}\n")
        casos.append((nome, caminho))
    return casos


if __name__ == "__main__":
    gerar_listas(Path(__file__).resolve().parent / "entradas")
    print("Listas geradas na pasta entradas.")
