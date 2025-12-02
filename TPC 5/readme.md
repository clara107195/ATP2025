# Resumo TPC5
## 19/10/2025

# Autora: Clara Carvalho A107195

O objetivo deste trabalho foi desenvolver uma aplicação para gestão de alunos. A aplicação permite criar uma turma (uma lista de alunos), inserir novos alunos, consultar alunos pelo seu ID, listar toda a turma, e ainda guardar e carregar turmas através de ficheiro. Cada aluno é representado por um tuplo contendo: nome, ID e uma lista com três notas (TPC, Projeto e Teste).

# Defenir o menu
Comecei por definir o menu principal, que orienta o utilizador nas várias opções disponíveis. Cada opção foi associada a um número, como nos trabalhos anteriores, facilitando a navegação.

# Defenir as funções
Como referido nos  trabalhos anteriores enquanto ia defenindo as funções ia ao ciclo while criado abaixo do menu ajustar as opções de forma ao programa rolar da melhor forma.~
* Função criar turma e inserir aluno na turma:
Foi criada uma função para inicializar uma turma vazia.
Na inserção de alunos, o programa pede ao utilizador o nome, ID e as notas. As notas são validadas através de um ciclo while para garantir que ficam entre 0 e 20.
Cada aluno é guardado num tuplo:
(nome, id, [nota_tpc, nota_proj, nota_teste])
Este tuplo é depois adicionado à turma com append().

* Função listar turma e função consultar aluno:
A função listar turma utiliza um ciclo for para percorrer a lista de alunos e imprimir cada um.
Na função consultar aluno, é pedido o ID e o programa percorre a turma à procura de um aluno cujo ID corresponda à posição 1 do tuplo.
Se o aluno existir, é mostrado; caso contrário, é devolvida uma mensagem de erro.
Em ambos os casos, foi incluída a opção de o utilizador repetir a operação.

* Função guardar turma e carregar turma:
Para guardar a turma num ficheiro, foi criada inicialmente uma função que converte um aluno (tuplo) numa linha de texto formatada.
Depois, a função guardar turma abre um ficheiro em modo de escrita e grava nele todos os alunos da lista, linha a linha.

Na função carregar turma, o utilizador indica o nome do ficheiro. O programa lê cada linha, separa os dados e reconstrói os tuplos correspondentes aos alunos.
Foram incluídos tratamentos de erro para ficheiros inexistentes ou mal formatados.



# Detalhes adicionais
Quando uma operação termina (como inserir ou consultar alunos), o programa pergunta se o utilizador pretende continuar nessa mesma opção.
Caso o utilizador tente aceder a uma opção que exige uma turma antes de esta existir, aparece a mensagem: “Ainda não existem turmas.”
A opção 0 encerra o programa com a mensagem “Obrigado e até à próxima.”
No final, foi ainda criada uma turma de exemplo com cinco alunos e guardada num ficheiro.