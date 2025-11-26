# Resumo TPC4
## 8/10/2025

## Autora: Clara Carvalho A107195 — Resumo do Trabalho
O objetivo deste trabalho foi desenvolver um programa para gerir um cinema, permitindo criar e remover salas, listar as existentes, vender bilhetes e consultar os lugares disponíveis.

# 1.Menu
Comecei por definir um menu com opções numeradas, à semelhança dos trabalhos anteriores, para orientar o utilizador nas operações que pode realizar.

# 2. Defenir as funções
Antes do menu, criei as funções necessárias e iniciei o cinema como uma lista vazia.

Opção 1 – Criar sala:
Pedi ao utilizador o número de lugares e o filme em exibição. Cada sala foi guardada numa lista composta por lugares totais, bilhetes vendidos (inicialmente 0) e nome do filme (usando capitalize para uniformizar).

Opção 2 – Remover sala:
Usei o índice da sala indicado pelo utilizador e o método pop para a remover.

Opção 3 – Listar salas:
Utilizei um ciclo for para apresentar cada sala separadamente.

Opção 4 – Consultar todas as salas:
Mostrei diretamente a lista completa do cinema.

Opção 5 – Verificar lugares disponíveis:
Pedi o nome do filme, procurei a sala correspondente e calculei os lugares ainda disponíveis:
lugares totais – bilhetes vendidos.

Opção 6 – Vender bilhetes:
Procurei a sala pelo nome do filme e acrescentei o número de bilhetes vendidos, verificando primeiro se existiam lugares suficientes.


# 3. As opções
Em cada opção verifiquei se o cinema não estava vazio.
Repeti o uso de capitalize para evitar erros na pesquisa de filmes.
Na venda de bilhetes, informei o utilizador quando o número pedido era superior aos lugares disponíveis.
Para opções inválidas, apresentei a mensagem correspondente.
Na opção 0, o programa termina com “Obrigado e até à próxima”.