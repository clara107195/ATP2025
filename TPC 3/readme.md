# Resumo TPC3
## 1/10/2025

## Autora: Clara Carvalho A107195
Para este trabalho foi-nos solicitado desenvolver uma aplicação que trabalhasse com listas, permitindo realizar várias operações sobre elas: gerar uma lista aleatória, permitir ao utilizador criar a sua própria lista, calcular a soma e a média dos elementos, identificar o valor máximo e mínimo e, ainda, procurar a posição de um número indicado pelo utilizador, caso este exista na lista.

# Menu inicial e primeira função
Comecei por criar um menu que apresenta ao utilizador todas as opções disponíveis. Antes disso importei a função randrange do módulo random, uma vez que seria necessária para gerar números aleatórios.

A primeira função criada foi criarlista, correspondente à opção 1 do menu. Esta função gera automaticamente uma lista de cinco valores aleatórios entre 1 e 100. Inicializei uma lista vazia e utilizei um ciclo for com range(5) para garantir exatamente cinco valores (como o range vai até n-1). Em cada iteração, gerei um número aleatório com randrange(1, 101) e adicionei-o à lista com append. Por fim, retornei a lista completa.

# Estrutura principal- Ciclo while
Para garantir o funcionamento contínuo da aplicação, utilizei um ciclo while. Sempre que concluía uma função, descia até à secção de execução do programa para testar o seu funcionamento.

Comecei por definir a lista como vazia no início, de forma a garantir que não ficavam valores de execuções anteriores. Em seguida apresentei o menu e pedi ao utilizador que inserisse a opção desejada. O ciclo while ficou ativo enquanto a opção fosse diferente de 0 (que representa a saída).

Dentro do ciclo utilizei várias condições if para tratar cada opção válida (1 a 9). Caso o utilizador inserisse uma opção inválida, o programa mostrava uma mensagem de erro. Para a primeira opção, por exemplo, a lista passava a ser o retorno da função criarlista e era imediatamente apresentada ao utilizador.

# Segunda função
Para a segunda opção desenvolvi a função lerlista, que permite ao utilizador criar manualmente os cinco elementos da lista. Tal como antes, iniciei a lista vazia, utilizei um ciclo for com range(5) e pedi ao utilizador que inserisse um valor por iteração. Usei i+1 para indicar corretamente qual o número que estava a ser pedido (evitando começar pelo 0). Cada valor inserido era adicionado à lista com append e no final a lista era devolvida. No while, tratei esta opção da mesma forma que a anterior.

# Função de somar e da média
Para somar os elementos criei uma função simples: iniciei a variável soma com zero e percorri a lista, acrescentando cada elemento. Devolvi o total no final. No ciclo principal coloquei uma verificação para impedir o cálculo caso a lista estivesse vazia — exibindo a mensagem "Lista Vazia".

A função da média foi construída com base na função da soma: dividi o total obtido pelo número de elementos usando len(lista).

# Máximo e mínimo
Para o máximo e o mínimo da lista não criei função pois não achei necessário uma vez que usei o comando max e o comando min. Assim apenas fui ao ciclo while e coloquei um print que irá dizer automaticamente qual será o valor máximo ou mínimo da atual lista.

# Ordem crescente e ordem decrescente
Para obter o valor máximo e mínimo não considerei necessário criar funções, pois os comandos max() e min() resolvem diretamente o problema. Assim, no while, para estas opções apenas devolvi o valor adequado com um print.

# Procurar elemento
Para estas operações criei duas funções semelhantes, variando apenas o tipo de comparação.

* Ordem Crescente
A função verifica se todos os elementos estão organizados do menor para o maior. Assumi inicialmente que a lista estaria ordenada, e utilizei um ciclo while para percorrer os índices. Se algum elemento fosse maior do que o próximo (lista[i] > lista[i+1]), significava que a lista não estava ordenada, e devolvi "não". Caso contrário, devolvia "sim".

* Ordem Decrescente
A lógica foi idêntica, apenas alterando o operador para < de forma a detetar se algum elemento era menor do que o seguinte.

Ambas as funções foram integradas no ciclo principal à semelhança das anteriores.

# Procura de elemento
Para a última função criei um algoritmo que percorre a lista em busca de um número indicado pelo utilizador. Se o valor coincidisse com lista[i], devolvia o índice correspondente. Caso percorresse toda a lista sem encontrar o número, retornava -1.

No while, pedi ao utilizador o número a procurar e apresentei o resultado. Se o valor retornado fosse -1, era mostrada uma mensagem a indicar que o número não se encontrava na lista; caso contrário, era apresentada a posição correta.


# Finalização
Já fora do ciclo while — isto é, quando o utilizador escolhia a opção 0 — apresentei uma mensagem final a indicar a lista atual e uma despedida.