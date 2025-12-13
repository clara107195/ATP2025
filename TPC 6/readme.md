# Resumo TPC6
## 27/10/2025

# Autora: Clara Carvalho A107195

## Resumo do Trabalho – Aplicação de Dados Meteorológicos

Neste trabalho foi desenvolvida uma aplicação em Python para o tratamento de dados meteorológicos relativos a um determinado ano. A aplicação resulta da junção dos vários exercícios realizados na aula (P6), sendo que cada função corresponde a uma alínea do exercício proposto. Para armazenar os dados foi fornecido um modelo inicial, guardado na variável tabMeteo1, que contém os registos diários de temperatura e precipitação.

### Estrutura dos Dados
Cada elemento da tabela meteorológica representa um dia e é constituído por:
- **Data**: tuplo no formato (ano, mês, dia)
- **Temperatura mínima**
- **Temperatura máxima**
- **Precipitação**

### Funcionalidades Desenvolvidas

- **Cálculo da temperatura média e gravação em ficheiro**  
  Foi criada uma função que percorre a tabela meteorológica, calcula a temperatura média diária a partir das temperaturas mínima e máxima e guarda os resultados num ficheiro de texto.

- **Carregamento da tabela e determinação da temperatura mínima mais baixa**  
  A aplicação permite carregar a tabela meteorológica a partir de um ficheiro e determinar a temperatura mínima mais baixa registada em todo o período.

- **Cálculo da amplitude térmica e identificação do dia com maior precipitação**  
  Implementou-se uma função para calcular a amplitude térmica diária (diferença entre a temperatura máxima e a mínima) e outra para identificar o dia em que a precipitação atingiu o valor mais elevado.

- **Análise da precipitação face a um limite p**  
  Foram desenvolvidas funções que:
  - Devolvem os dias em que a precipitação foi superior a um valor limite p;
  - Calculam o maior número de dias consecutivos com precipitação inferior a p.

### Menu da Aplicação
Todas as funcionalidades foram integradas num menu interactivo, permitindo ao utilizador seleccionar as operações pretendidas. Foi incluída a opção (0) para sair da aplicação, apresentando uma mensagem final de despedida e encerrando correctamente o programa.

Este trabalho permitiu consolidar conhecimentos sobre listas, ciclos, funções e manipulação de ficheiros, aplicados a um contexto prático de análise de dados meteorológicos.
