#TPC3
#menu 
from random import randrange
def menu():
    print(" Bem-vindo!\n(1)Criar Lista\n(2)Ler Lista\n(3)Soma\n(4)Média\n(5)Maior\n(6)Menor\n(7)estaOrdenada por ordem crescente\n(8)estaOrdenada por ordem decrescente \n (9) Procura um elemento \n (0)Sair")

def criarlista():
    lista=[]
    for i in range(5):
        n=randrange(1,101)
        lista.append(n)
    return lista


def lerlista():
    lista=[]
    for i in range(5):
        n=int(input(f"Introduza o {i+1} número para a lista."))
        lista.append(n)
    return lista

def somalista(lista):
    soma=0
    for i in lista:
        soma=soma+i
    return soma

def medialista(lista):
    for i in lista:
        media= somalista(lista)/len(lista)
    return media

def estaOrdenadacrescente(lista):
    estaOrdenadacrescente= "Sim"
    i=0
    while estaOrdenadacrescente and i < len(lista)-1:
        if lista[i]>lista[i+1]:
            estaOrdenadacrescente= "Não"
        i+=1
    return estaOrdenadacrescente

def estaOrdenadadecrescente(lista):
    estaOrdenadadecrescente="Sim"
    i=0
    while estaOrdenadadecrescente and i < len(lista)-1:
        if lista[i]<lista[i+1]:
            estaOrdenadadecrescente="Não"
        i+=1
    return estaOrdenadadecrescente

def procurarelemento(lista,n):
    for i in range(len(lista)):
        if n==lista[i]:
            return i
    return -1
    


lista=[]
menu()
resp=int(input("Indique a opção que pretende:"))

while resp!=0:
    if resp==1:
        lista=criarlista()
        print(lista)
    elif resp==2:
        lista=lerlista()
        print(lista)
    elif resp==3:
        if not lista: #significa que a lista está vazia
            print("Lista vazia.")
        else:
            soma=somalista(lista)
            print(soma)
    elif resp==4:
        if not lista:
            print("Lista vazia.")
        else:
            media=medialista(lista)
            print(media)
    elif resp==5:
        if not lista:
            print("Lista vazia.")
        else:
            print(f"O maior valor é {max(lista)}") #podemos usar também a vígula para separação em vez de o f
    elif resp==6:
        if not lista:
            print("Lista vazia.")
        else:
            print("O menor valor é", min(lista)) #outra forma de colocar o valor
    elif resp==7:
        if not lista:
            print("Lista vazia.")
        else:
            estaOrdenadacrescente=estaOrdenadacrescente(lista)
            print(estaOrdenadacrescente)
    elif resp==8:
        if not lista:
            print("Lista vazia.")
        else:
            estaOrdenadadecrescente=estaOrdenadadecrescente(lista)
            print(estaOrdenadadecrescente)
    elif resp==9:
        if not lista:
            print("Lista vazia.")
        else:
            n=int(input("Introduza o número da lista."))
            p=procurarelemento(lista,n)
            if p ==-1:
                print(f"O número {n} não foi encontrado na lista.")
            else:
                print(f"O número {n} encontra-se na posição {p}.")
    else: 
        print("Opção inválida.")

    menu()
    resp=int(input("Indique a opção que pretende:"))

print(f"A lista final é {lista}. \n Obrigada e até á próxima.")








    