# Resumo TPC2
## 24/09/2025

## Autora: Clara Carvalho A107195
Para este trabalho  foi-nos pedido para realizar um jogo. No jogo existem 21 fósforos e entre os dois jogadores (computador e jogador) iam retirando entre 1 a 4 fósforos  sendo o objeto não poder ficar com o último pois perdia. O segredo do jogo é retirar n+1 palitos no fim de cada jogada ( computador+jogador) sendo n o número máximo de fósforos que poderiam ser retirados.  No primeiro modo de jogo deveria ser o jogador a começar, sendo o computador o segundo jogador teria a  vantagem de retirar os palitos restantes para  fazer 5 ( neste caso). Assim nesse modo de jogo o computador é obrigado a ganhar sempre. No segundo modo de jogo deveria ser o computador a começar tendo por isso o jogador essa vantagem, porém caso o jogador se engana-se nos cálculos e retira-se o número de palitos errado seria obrigado o computador a acertar estas e a passar para lugar de vencedor.
# Iniciação do jogo
Para iniciar o jogo foi necessário colocar um comando de import random para que gere um número aleatório entre 1,2 3 e 4.
De seguida decidi chamar como "modo1" ao modo de jogo em que o jogador é o primeiro a retirar fósforos e como "modo2" o modo de jogo em que o computador é o primeiro a retirar fósforos. ( para ambas foi necessário criar uma função para que quando um jogador selecionar esse modo de jogo apenas coloque modo1 ou modo2 para que comece a percorrer o código do respetivo modo de jogo.)
# Modo de jogo 1
Para este modo de jogo decidi fazer um ciclo (while) para de forma a que o computador ganhe sempre. Assim incialmente defeni que eram 21 fósforos e que sempre que um jogador seleciona-se algo diferente de 1,2,3 ou 4 palitos para retirar, irá  aparecer  uma mensagem de como é inválido.
Durante o ciclo coloquei a perguntar ao jogador o número de fósforos que deseja retirar e o número de fósforos que irá restar, sendo estes depois do computador jogar, sempre que o computador jogar, -5 que o valor anterior. Desta forma também decidi colocar uma mensagemm com o código print de quantos fósforos irá retirar o computador.
Por fim decidi colocar uma mensagem com esse mesmo código, porém fora do ciclo para quando restar apenas 1 palito, referindo que o jogador perdeu.

# Modo de jogo 2
Para este modo de jogo decidi aplicar o mesmo raciocínio usado para o modo anterior porém em vez do ciclo ocorrer enquanto o número de fósforos for maior 1 irá ocorrer enquanto for maior que zero.
De seguida decidi colocar o computador a fazer grupos de 5 fósforos junto com o jogador porém a sobrar 1 fósforo pois assim poderá ganhar.Assim enquanto este grupo for maior que o número de fósforos decidi colocar o computador a gerar um número aleatório  entre 1 e 4 dependendo do número de fósforos ainda existentes, com o comando random.randint. Coloquei igualmente uma mensagem a avisar quantos fósforos é que o computador retirou.
Coloquei também que, no caso do jogador se enganar nos cálculos e apenas sobrar 1 fósforo avisar o jogador que o computador foi o vencedor.
Por fim coloquei igualmente que caso sofre 1 fósforo e seja a vez do computador jogar, aparecer uma mensagem a avisar o jogador que venceu.

# Menu
Coloquei por fim uma espécie de menu que irá fazer uma pequena introdução ao jogo e para que o jogador selecione o modo de jogo que está interessado. 
Assim caso selcione o número 1 coloquei a iniciar o modo 1, caso selecione o 2 a iniciar o modo 2 e caso coloque um número 3 como referido na pequena introdução o jogo não inicie e despede-se do jogador. 
Utilizei a ferramenta do \n na introdução para que realize uma mudança de linha para explicar por tópicos os modos de jogo possíveis por uma questão de ser mais fácil para o jogador.