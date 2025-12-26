#TPC7
#Realização de um teste de aferição


#tpc1:
##a)
lista1 = [1, 2, 3, 4, 5]
lista2 = [4, 5, 6, 7, 8]  
ncomuns = [n for n in lista1 + lista2 if (n in lista1) != (n in lista2)]
print(ncomuns)

##b)
texto = """Vivia há já não poucos anos algures num concelho do Ribatejo 
    um pequeno lavrador e negociante de gado chamado Manuel Peres Vigário"""
lista = [palavra for palavra in texto.split(" ") if len(palavra)>3]
print(lista)

##c)
lista = ['anaconda', 'burro', 'cavalo', 'macaco']
listaRes = [(i+1, lista[i]) for i in range(len(lista))]
print(listaRes)



#tpc2:
##a)
def strCount(s, subs):
    cont = 0
    i = 0
    while i <= len(s) - len(subs):
        if s[i:i+len(subs)] == subs:
            cont += 1
            i += len(subs)
        else: 
            i += 1
    return cont

##b)
def produtoM3(lista):
    listao = sorted(lista)
    return listao[0]*listao[1]*listao[2]

print(produtoM3([12,3,7,10,12,8,9]))

##c)
# Input: 38
# Output: 2
# Explicação: 3 + 8 = 11, 1 + 1 = 2.

# Input: 777
# Output: 3
# Explicação: 7 + 7 + 7 = 21, 2 + 1 = 3.

def reduxInt(n):
    while n >= 10:
        soma = 0
        for digito in str(n):
            soma += int(digito)
        n = soma
    return n

##d)
def myIndexOf(s1, s2):
    i = 0
    res = -1
    while i <= len(s1) - len(s2):
        if s1[i:i+len(s2)] == s2:
            res = i
            i += 1
        else:
            i += 1
    return res



#tpc3
##a)
def quantosPost(redeSocial):
    return len(redeSocial)

##b)
def postsAutor(redeSocial, autor):#segunda chave
    lista = []
    for post in redeSocial:
        if autor == post["autor"]:
            lista.append(post)
    return lista

##c)
def autores(redeSocial): #terceira chave
    lista=[]
    for post in redeSocial:
        if "autor" in post:
            lista.append(post["autor"])
    return  lista

##d)
def insPost(redeSocial, conteudo, autor, dataCriacao, comentarios):
    id = f"p{len(redeSocial)+1}"
    post = {"id" : id, "conteudo" : conteudo, "autor" : autor, 'dataCriacao': dataCriacao, 'comentarios': comentarios}
    return redeSocial.append(post)

##e)
def remPost(redeSocial, id):
    redeSocial = [post for post in redeSocial if post["id"] != id]
    return redeSocial

##f)
def postsPorAutor(redeSocial):
    distrib = {}
    for post in redeSocial:
        autor = post.get("autor")
        if autor in distrib:
            distrib[autor] += 1
        else:
            distrib[autor] = 1
    return distrib

##g)
def comentadoPor(redeSocial, autor):
    lista = []
    for post in redeSocial:
        if "comentarios" in post:
            for comentario in post["comentarios"]:
                if comentario.get("autor") == autor:
                    lista.append(post)
    return lista






#tpc3:
# A rede social
# A informação sobre uma rede social está numa lista de dicionários.
# Cada dicionário corresponde a um post e tem: (id, conteúdo, autor, datacriação e comentarios)
# Os comentários é uma lista de dicionários com chaves{comentário autor}