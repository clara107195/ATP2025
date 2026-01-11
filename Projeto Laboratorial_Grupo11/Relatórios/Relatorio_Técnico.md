# Projeto: Simulação de Clínica Médica
**UC:** Algoritmos e Técnicas de Programação
**Instituição:** Universidade do Minho - Escola de Engenharia
**Data:** Novembro 2025 a Janeiro 2026
## Realizado por: Andreia Beatriz Barroso Ferreira a107234; Bianca de Araújo Pereira a107193; Clara Sofia Salazar Carvalho a107195


---
## 1. Introdução

Este projeto foi desenvolvido no âmbito da unidade curricular de **Algoritmos e Técnicas de Programação** do 2º ano da **Licenciatura em Engenharia Biomédica** na Universidade do Minho. O objetivo principal é a construção de uma aplicação que simula o fluxo de atendimento de doentes numa clínica médica através de um modelo de simulação de eventos discretos.

A simulação assenta em processos para modelar o comportamento real de uma unidade de saúde:
* **Chegadas:** Os doentes chegam à clínica de forma aleatória, seguindo uma distribuição de Poisson.
* **Atendimento:** O tempo de consulta é variável e segue distribuições estatísticas como a Exponencial, Normal ou Uniforme, dependendo da configuração escolhida.
* **Gestão de Recursos:** O sistema gere a ocupação de um número fixo de médicos e a formação de filas de espera sempre que a procura excede a capacidade de atendimento imediato.

Mais do que um exercício académico, este trabalho é apresentado como um **projeto de engenharia** que exige a análise de dados estatísticos e a investigação de como a variação de parâmetros (como a taxa de chegada ou o número de médicos) influencia a eficiência do sistema e o tempo de espera dos doentes. No final, a aplicação produz indicadores de desempenho e gráficos detalhados que permitem validar as hipóteses testadas durante a simulação.


## 2. Arquitetura e Implementação

A arquitetura do sistema baseia-se num modelo de Simulação de Eventos Discretos (SED), onde o estado da clínica evolui apenas em pontos específicos no tempo, coincidindo com a ocorrência de eventos.

### Estruturas de Dados e Organização
Para garantir a eficiência e a ordem cronológica da simulação, o código utiliza duas estruturas principais:
* **Fila de Eventos (Event Queue):** Uma lista organizada por tempo que armazena todas as ocorrências futuras. Esta fila gere o fluxo de "Chegadas" (entrada de novos doentes) e "Saídas" (momento em que o médico termina a consulta).
* **Fila de Espera (Waiting Queue):** Uma estrutura que armazena os doentes que chegaram à clínica mas não encontraram médicos disponíveis, aguardando o próximo profissional livre para serem atendidos.

### Lógica de Funcionamento
O motor da simulação processa o ciclo de vida de cada doente através dos seguintes passos:
1. **Geração de Chegadas:** Assim que um doente entra no sistema, o próximo evento de chegada é imediatamente calculado e agendado, garantindo um fluxo contínuo de entrada.
2. **Alocação de Médicos:** O sistema verifica constantemente a disponibilidade da equipa médica. Se um médico estiver livre, o atendimento inicia-se de imediato conforme a especialidade; caso contrário, o doente é colocado na fila de espera.
3. **Processamento de Consultas:** Ao iniciar uma consulta, o tempo de duração é gerado aleatoriamente com base na distribuição escolhida. Um evento de "Saída" é então adicionado à fila de eventos com o tempo exato do fim da consulta.
4. **Libertação e Reatribuição:** Quando ocorre um evento de "Saída", o médico é libertado. O sistema verifica então a fila de espera: se houver doentes a aguardar, o médico inicia imediatamente uma nova consulta com o primeiro doente da fila, mas existe também a possibilidade de entrar em pausa durante 15 a 20 minutos.

### Entidades Médicas
Os médicos são modelados como objetos com estados binários (Ocupado/Livre). O sistema monitoriza individualmente cada profissional para registar o seu tempo total de ocupação, permitindo calcular a taxa de eficiência da equipa no final da simulação.

## 3. Modelagem 

A eficácia desta simulação depende da representação fiel da imprevisibilidade do mundo real através de modelos matemáticos de probabilidade.

### Modelagem de Chegadas
As chegadas dos doentes à clínica não ocorrem em intervalos fixos, mas sim de forma aleatória e independente. Para simular este comportamento, utilizou-se a **Distribuição de Poisson** com o parâmetro `lambda_rate` (λ), que define a taxa média de doentes por hora. No código, isto traduz-se no cálculo do intervalo de tempo entre chegadas sucessivas, permitindo que a clínica enfrente períodos de grande afluência ou momentos de maior tranquilidade.

### Modelagem do Tempo de Consulta
Ao contrário das chegadas, a duração de uma consulta médica depende de múltiplos fatores clínicos. Para oferecer versatilidade à simulação, foram implementados três modelos de distribuição distintos:
* **Exponencial:** Modela consultas onde a maioria é rápida, mas algumas podem prolongar-se significativamente. É a distribuição padrão para tempos de serviço em sistemas de filas de espera.
* **Normal (Gaussiana):** Ideal para cenários onde as consultas têm uma duração previsível em torno de uma média, com poucas variações extremas.
* **Uniforme:** Define um intervalo fixo (mínimo e máximo) onde qualquer duração tem a mesma probabilidade de ocorrer.

### Importância da Variabilidade
A aplicação permite testar o comportamento da clínica sob diferentes condições de pressão. Ao ajustar estes parâmetros, é possível observar fenómenos de engenharia como a formação de "gargalos" quando a taxa de chegada se aproxima da capacidade máxima de atendimento dos médicos, ou o impacto que a variabilidade do tempo de consulta tem no tamanho máximo da fila de espera.

## 4. Manual de Utilização (Interface SimpleGUI)

A aplicação disponibiliza uma interface gráfica intuitiva que permite ao utilizador configurar, executar e analisar a simulação de forma dinâmica, sem necessidade de intervir diretamente no código-fonte.

### Configuração da Simulação
Através do painel de controlo, o utilizador pode definir os parâmetros que moldam o cenário clínico:
* **Taxa de Chegada ($\lambda$):** Ajuste da frequência média com que novos doentes entram no sistema.
* **Recursos Médicos:** Definição do número de médicos disponíveis para atendimento imediato.
* **Distribuição de Consulta:** Seleção do modelo estatístico (Exponencial, Normal ou Uniforme) que ditará a variabilidade da duração das consultas.
* **Janela Temporal:** Definição do tempo total de funcionamento da clínica a ser simulado.

### Fluxo de Operação
O processo de utilização da ferramenta segue três etapas principais:
1. **Importação de Dados:** Antes de iniciar a simulação, o sistema permite carregar bases de dados de médicos e doentes (através de ficheiros JSON), personalizando as entidades envolvidas.
2. **Execução:** Ao ativar a simulação, a interface exibe em tempo real o estado da fila de espera e a ocupação dos médicos, permitindo observar a dinâmica de eventos discretos em curso.
3. **Consulta de Resultados:** Após o encerramento do tempo de simulação, o utilizador tem acesso imediato aos indicadores estatísticos e pode acionar a geração de gráficos para uma análise visual aprofundada.

### Visualização e Diagnóstico
A interface integra botões específicos para a renderização de gráficos através da biblioteca `matplotlib`. Estas visualizações permitem diagnosticar rapidamente períodos de sobrecarga na clínica, tempos excessivos de espera e a eficiência da equipa médica perante os parâmetros configurados.


## 5. Resultados e Indicadores de Desempenho

O sistema de simulação foi desenhado para recolher métricas precisas que permitem avaliar a eficiência operacional da clínica. Ao final de cada execução, são processados os seguintes indicadores:

### Métricas de Tempo
* **Tempo Médio de Espera (TME):** Representa o tempo médio que cada doente passou na fila antes de ser chamado por um médico. Este é o principal indicador de satisfação do utente.
* **Tempo Médio de Consulta:** Cálculo da duração real das consultas processadas, servindo para validar se a distribuição aplicada está alinhada com os parâmetros configurados.

### Métricas de Fluxo e Ocupação
* **Taxa de Ocupação Médica:** Calculada através da soma dos tempos de consulta de cada médico em relação ao tempo total da simulação. Uma ocupação próxima dos 100% indica um sistema sob stress, enquanto valores muito baixos sugerem excesso de recursos.
* **Tamanho da Fila:** Registo do número médio e máximo de doentes em espera. Este dado é vital para o planeamento do espaço físico da sala de espera.
* **Volume de Atendimento:** Contagem total de doentes que completaram o ciclo de atendimento, permitindo verificar a produtividade da clínica no período estipulado.

### Exportação de Dados
Todos os resultados estatísticos podem ser salvos em ficheiros de log ou visualizados diretamente no painel de estatísticas da interface. Estes dados servem de base para a análise comparativa entre diferentes cenários de simulação, permitindo identificar, por exemplo, o ponto de rutura da clínica face ao aumento da taxa de chegada de doentes.