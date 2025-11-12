



#exercício 21 fosforos jogador em primeiro lugar
##menu
import random
##modo 1- começa o jogador
def modo1():
    fosforos=21
    while fosforos>1:
        jog=int(input(f"Há {fosforos} Quantos fósforos queres tirar?(1,2,3 ou 4)"))
        while (jog<1 or jog>4) or jog>fosforos:
            jog=int(input("Entrada inválida. Escolha um valor entre 1 e 4."))
        fosforos=fosforos-jog
        comp=5-jog
        fosforos-=comp
        print(f"O computador retirou {comp} fósforos.")  
    print("Perdeste. É a tua vez e sobra 1 fósforo.")

##modo 2- computador começa
def modo2():
    fosf=21
    while fosf>0:
        comp=(fosf-1) % 5
        if comp == 0 or comp > fosf:
            comp=random.randint(1, min(4,fosf))
        fosf-=comp
        print(f"O computador retirou {comp} fósforos.")
        
        if fosf==1:
            print("Sobrou apenas 1  fósforo. O computador ganhou!")
            return
        

        jog=int(input(f"Agora é a tua vez,há {fosf} fósforos. Quantos fósforos queres tirar?"))
        while jog<1 or jog>4 or jog>fosf:
            jog=int(input("Entrada inválida. Escolhe um valor entre 1 e 4."))

        fosf= fosf-jog
        if fosf==1:
            print("Sobrou 1 fósforo. Ganhaste!!")
            return


##Jogo   ------------------------------------------------------------------------------------------
modo=input("Escolha um modo de jogo:\n1-Jogador começa\n2-Computador começa\n3-Sair do Jogo\n-Escolha:")
while modo != "3":
    if modo=="1":
        modo1()
    elif modo=="2":
        modo2()
    else:
        print("Opção inválida. Escolha 1,2 ou 3.")  
    modo=input("Escolha um modo de jogo:\n1-Jogador começa\n2-Computador começa\n3-Sair do Jogo\n-Escolha:")
print("Obrigado. Até á próxima!")





