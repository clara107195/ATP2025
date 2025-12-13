#Cria uma aplicação phyton que permita ao utilizador usar todas as funcionalidades pedidas na ficha P6.


#Os seguintes comentários definem um modelo para guardar os registos de temperatura e precipitação aao longo de vários dias, materializando na variável tabMeteo1:

# TabMeteo = [(Data,TempMin,TempMax,Precipitacao)]
    # Data = (Int,Int,Int)
    # TempMin = Float
    # TempMax = Float
    # Precipitacao = Float

tabMeteo1 = [((2022,1,20), 2, 16, 0),((2022,1,21), 1, 13, 0.2), ((2022,1,22), 7, 17, 0.01)]

#Funções:

def medias(tabMeteo):
    res = []
    for dia in tabMeteo:
        mediatemp=(dia[1]+dia[2])/2
        res.append((dia[0],mediatemp))
    return res

def guardaTabMeteo(t, fnome):
    f=open(fnome, "w")
    for data,tmin,tmax,precip in t:
        linha=f"{data[0]}::{data[1]}::{data[2]}::{tmin}::{tmax}::{precip}\n"
        f.write(linha)
    f.close()
    return



def carregaTabMeteo(fnome):
    res = []
    f=open(fnome)
    for linha in f:
        if linha!="":
            campos= linha.split('::')
            data=(int(campos[0]),int(campos[1]),int(campos[2]))
            res.append((data,float(campos[3]),float(campos[4]),float(campos[5])))
    f.close()
    return res



def minMin(tabMeteo):
    minima=tabMeteo[0][1]
    for data,tmin,tmax,precip in tabMeteo[1:]:
        if tmin<minima:
            minima=tmin
    return minima

def amplTerm(tabMeteo):
    res = []
    for data,tmin,tmax,_ in tabMeteo:
        res.append((data,tmax-tmin))
    return res

def maxChuva(tabMeteo):
    max_prec=tabMeteo[0][3]
    max_data=tabMeteo[0][0]
    for data,_,_,precip in tabMeteo[1:]:
        if max_prec<precip:
            max_prec=precip
            max_data=data
    return (max_data, max_prec)

def diasChuvosos(tabMeteo, p):
    res = []
    for data, _, _, precip in tabMeteo:
        if precip > p:
            res.append((data, precip))
    return res

def maxPeriodoCalor(tabMeteo, p):
    consecutivos=0
    contador=0
    for *_, precip in tabMeteo:
        if precip<p:
            contador=contador+1
        else:
            if contador > consecutivos:
                consecutivos = contador
            contador = 0
 # Verifica se o maior período ocorre no final da sequência
    if contador > consecutivos:
        consecutivos = contador
    
    return consecutivos





def menu():
    print("""
    1. Calcular a temperatura média de cada dia
    2. Guardar tabela metereológica
    3. Carregar tabela metereológica
    4. Temperatura mínima mais baixa registada na tabela
    5. Calcula a amplitude térmica
    6. O dia em que aprecipitação teve valor máximo
    7. Tabela metereológica e limite p e devolve os dias em que a precipitação foi superior a p
    8.Retorna o maior número consecutivo de dias com precipitação abaixo de p
    0. Sair da aplicação
          """)

    opcao=int(input("Qual opção deseja selecionar?"))
    return opcao

op=menu()
while op!=0:
    if op ==1:
        medias(tabMeteo1)
        print(medias(tabMeteo1))
    elif op==2:
        guardaTabMeteo(tabMeteo1, "meteorologia.txt")
    elif op==3:
        tabMeteo2 = carregaTabMeteo("meteorologia.txt")
        print(tabMeteo2)
    elif op==4:
        print(minMin(tabMeteo1))
    elif op==5:
        print(amplTerm(tabMeteo1))
    elif op==6:
        print(maxChuva(tabMeteo1))
    elif op==7:
        print(diasChuvosos(tabMeteo1, 0.1))
    elif op==8:
        print(maxPeriodoCalor(tabMeteo1, 0.1))
    op=menu()
print("Obrigado e até á próxima.")  







