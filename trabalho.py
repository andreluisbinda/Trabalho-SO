import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime

from apoio import ler_ids, conferir_log, imprimir_tabela
from gerar_listas import gerar_listas


NUMBER_OF_THREADS = 4
TEMPO_API = 0.02
PASTA = Path(__file__).resolve().parent


lista_ids = []
proximo_id = 0
sem_ids = threading.Semaphore(1)
sem_log = threading.Semaphore(1)


def consultar_api(identificador):

    time.sleep(TEMPO_API)
    resposta = {
        "id": identificador,
        "status": "ok",
        "valor": round((identificador * 137 % 100000) / 100, 2)
    }
    return json.dumps(resposta, separators=(",", ":"))


def processar_ids(tid, arquivo_log, erros):
    global proximo_id
    print(f"[THREAD {tid}] Iniciada.", flush=True)
    try:
        while True:


            sem_ids.acquire()
            try:
                if proximo_id >= len(lista_ids):
                    break
                identificador = lista_ids[proximo_id]
                proximo_id += 1
            finally:

                sem_ids.release()


            resposta = consultar_api(identificador)


            sem_log.acquire()
            try:
                data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                arquivo_log.write(f"{data}, Thread-{tid}, {identificador}, {resposta}\n")
            finally:
                sem_log.release()

    except Exception as erro:


        erros[tid - 1] = str(erro)
    print(f"[THREAD {tid}] Finalizada.", flush=True)


def processo_filho(entrada, log, quantidade):
    global lista_ids, proximo_id
    if quantidade < 1:
        raise ValueError("P1 precisa de pelo menos uma thread.")
    print(f"[FILHO] PID: {os.getpid()} | Pai: {os.getppid()}", flush=True)
    inicio = time.perf_counter()
    lista_ids = ler_ids(entrada)
    proximo_id = 0
    erros = [None] * quantidade
    threads = []
    log.parent.mkdir(parents=True, exist_ok=True)

    with log.open("w", encoding="utf-8") as arquivo_log:
        try:

            for i in range(quantidade):
                print(f"[FILHO] Criando thread {i + 1}.", flush=True)
                thread = threading.Thread(target=processar_ids,
                                          args=(i + 1, arquivo_log, erros))
                thread.start()
                threads.append(thread)
        finally:

            for thread in threads:
                thread.join()


    tempo = time.perf_counter() - inicio
    log.with_suffix(".tempo.txt").write_text(str(tempo), encoding="utf-8")
    for erro in erros:
        if erro is not None:
            print(f"[FILHO] Erro na thread: {erro}", file=sys.stderr)
    if any(erro is not None for erro in erros):
        return 1
    print(f"[FILHO] Terminando. Tempo de P1: {tempo:.4f}s", flush=True)
    return 0


def status_saida(codigo):
    if codigo == 0:
        return "normal"
    if os.name == "posix" and codigo < 0:
        try:
            return f"sinal {signal.Signals(-codigo).name}"
        except ValueError:
            return f"sinal {-codigo}"
    return f"erro (código {codigo})"


def executar_teste(nome, entrada, quantidade, destino):
    ids = ler_ids(entrada)
    log = destino / f"{nome}_{quantidade}_threads.log"
    medicao = log.with_suffix(".tempo.txt")

    for arquivo in (log, medicao):
        if arquivo.exists():
            arquivo.unlink()


    comando = [sys.executable, str(Path(__file__).resolve()), "--child",
               str(entrada), str(log), str(quantidade)]
    inicio = time.perf_counter()
    filho = subprocess.Popen(comando)
    print(f"[PAI] PID: {os.getpid()} | Filho criado: {filho.pid}", flush=True)
    codigo = filho.wait()
    tempo_total = time.perf_counter() - inicio

    linhas, auditoria = conferir_log(log, ids)
    tempo_filho = None
    if medicao.exists():
        tempo_filho = float(medicao.read_text(encoding="utf-8"))
        medicao.unlink()
    status = status_saida(codigo) + "; " + auditoria
    if tempo_filho is None:
        status += "; tempo P1 indisponível"
    sucesso = codigo == 0 and auditoria == "completo" and tempo_filho is not None
    print(f"[PAI] Filho terminou: {status}\n", flush=True)
    return {"lista": nome, "ids": len(ids), "threads": quantidade,
            "tempo_p1": tempo_filho, "tempo_total": tempo_total,
            "linhas": linhas, "status": status, "sucesso": sucesso}


def processo_pai(entrada=None, quantidade=NUMBER_OF_THREADS):
    if quantidade < 2:
        raise ValueError("Escolha N > 1 para comparar com a execução de 1 thread.")
    destino = PASTA / "resultados"
    destino.mkdir(exist_ok=True)
    if entrada is None:
        casos = gerar_listas(PASTA / "entradas")
    else:
        casos = [("personalizada", entrada.resolve())]
    resultados = []

    for nome, caminho in casos:
        for n in (1, quantidade):
            resultados.append(executar_teste(nome, caminho, n, destino))
    imprimir_tabela(resultados)
    return 0 if all(r["sucesso"] for r in resultados) else 1


def main():

    try:
        if len(sys.argv) > 1 and sys.argv[1] == "--child":
            if len(sys.argv) != 5:
                raise ValueError("Uso interno: --child entrada log numero_threads")
            return processo_filho(Path(sys.argv[2]), Path(sys.argv[3]), int(sys.argv[4]))
        if len(sys.argv) == 1:
            return processo_pai()
        if len(sys.argv) == 4 and sys.argv[1] == "--entrada":
            return processo_pai(Path(sys.argv[2]), int(sys.argv[3]))
        raise ValueError("Use: python trabalho.py OU python trabalho.py --entrada lista_ids.txt 4")
    except Exception as erro:
        print(f"[ERRO] {erro}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
