# Resumo TPC7
## 11/11/2025

# Autora: Clara Carvalho A 107195

## Realização de um Teste de Aferição

Neste trabalho, foi solicitado que realizássemos um conjunto de exercícios com diferentes tipos de abordagens, organizados por categorias para treinarmos o uso de estruturas, funções e manipulação de dados. Abaixo descrevo o que foi realizado e as escolhas feitas para cada questão.


### TPC1:
* a)Foi criada uma lista de elementos que não são comuns entre duas listas (`lista1` e `lista2`). A lista final (`ncomuns`) foi construída utilizando uma compreensão de listas(com o ciclo for) com uma expressão condicional que verifica se um número está em apenas uma das listas.

* b)A segunda questão extrai palavras de um texto dado que possuem mais de 3 caracteres. Utilizou-se a função `split` para separar o texto em palavras e uma compreensão de listas para filtrar as que atendem à condição de tamanho.

* c) Criou-se uma lista com pares de índice e elementos de uma lista fornecida. Para esta combinei índices gerados pelo `range` e elementos da lista.


### TPC2:
* a)Implementou-se a função `strCount`, que conta quantas vezes uma substring aparece numa string. Assim, usei uma abordagem iterativa, onde percorro a string e comparo substrings em cada posição.

* b)Para calcular o produto dos três menores números de uma lista, usei  a função `sorted` para ordenar a lista, e os três primeiros elementos foram multiplicados.

* c)Desenvolvi uma  função `reduxInt`, que reduz um número até que reste apenas um dígito, somando seus dígitos iterativamente.

* d) A função `myIndexOf` encontra a primeira ocorrência de uma substring dentro de uma string. Usou-se um loop para comparar as fatias da string principal com a substring.


### TPC3:
* a)Criou-se a função `quantosPost` para retornar o número de posts numa rede social representada por uma lista.

* b)A função `postsAutor` filtra os posts de um autor específico. Utilizou-se um loop para verificar o autor de cada post e adicionar os correspondentes a uma nova lista.

* c)A função `autores` gera uma lista com todos os autores de posts presentes na rede social, verificando a existência da chave `autor`.

* d)Para inserir um novo post, a função `insPost` cria um dicionário com as informações fornecidas e adiciona-o à lista de posts.

* e)A função `remPost` remove um post da lista, filtrando os que têm um ID diferente do especificado.

* f)Para contabilizar os posts por autor, utilizei a função `postsPorAutor` que utiliza um dicionário que armazena os contadores associados a cada autor.

* g)A função `comentadoPor` retorna os posts comentados por um autor específico. Foram utilizados loops para percorrer os comentários de cada post.


### Conclusão:
O TPC7, sendo ele um teste de aferição ajudou na compreensão de listas, manipulação de strings, operações sobre números e estruturas mais complexas como dicionários e listas de dicionários. Foi importante aplicar abordagens diferentes.