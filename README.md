# Programação concorrente

Este projeto lê uma lista de identificadores, consulta uma API simulada para cada
item e grava as respostas em um log. O processo pai executa o programa com uma e
quatro threads para comparar os tempos em listas de 10, 100 e 500 IDs. A
implementação usa apenas a biblioteca padrão do Python.

## Como executar

É necessário Python 3.9 ou superior. Abra um terminal na pasta do projeto e rode:

```console
python trabalho.py
```

No Windows, também é possível usar `py trabalho.py`. O programa gera as listas
de entrada, executa os seis casos em sequência, mostra a tabela comparativa no
terminal e grava os logs em `resultados/`. Uma nova execução substitui os logs
com os mesmos nomes; os tempos do relatório correspondem à rodada registrada
na entrega.

Para usar outra lista e escolher o número de threads da comparação:

```console
python trabalho.py --entrada entradas/pequena/lista_ids.txt 8
```

A lista deve conter um ID inteiro e único por linha. Linhas vazias são
ignoradas.

## Arquivos

- `trabalho.py`: cria os processos e as threads, simula a consulta e coordena as
  medições.
- `apoio.py`: lê os IDs, confere os logs e imprime a tabela de resultados.
- `gerar_listas.py`: gera as listas de 10, 100 e 500 IDs.
- `entradas/`: listas utilizadas na comparação.
- `resultados/`: logs das seis execuções apresentadas no relatório.
- `relatorio.pdf`: metodologia, resultados e análise de desempenho.

## Funcionamento

O processo pai (P0) inicia o filho (P1) com `subprocess.Popen`, aguarda sua saída
com `wait` e registra o tempo total. P1 recebe o número de threads, lê a lista,
cria as trabalhadoras com `threading.Thread` e aguarda todas com `join`.

Um semáforo protege a retirada dos IDs da lista e outro protege cada gravação
no log. A consulta simulada ocorre fora dessas regiões críticas, para que as
threads possam esperar ao mesmo tempo. A resposta JSON contém os campos `id`,
`status` e `valor`, e cada linha do log registra data, thread, ID e resposta.

P1 mede o intervalo entre o início da leitura e o fechamento do log. Depois de
cada execução, P0 confere o código de saída e compara o log com a lista de
entrada. A conferência verifica a quantidade de linhas, os IDs e o formato das
respostas. Um log incompleto é tratado como falha mesmo se P1 terminar com
código zero.
