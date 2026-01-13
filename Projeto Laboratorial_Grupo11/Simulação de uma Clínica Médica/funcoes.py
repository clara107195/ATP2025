import json
import os
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Dict, Any, Optional
import datetime
import re
import unicodedata
from datetime import datetime
import random



PRIORIDADE_MAP = {
    "emergência": 0,
    "alta": 1,
    "média": 2,
    "normal": 2,
    "baixa": 3
}

TIME_SLOTS = ["08:00-09:00","09:00-10:00","10:00-11:00","11:00-12:00",
              "14:00-15:00","15:00-16:00","16:00-17:00"]


# --- AJUSTE DINÂMICO DE CAMINHOS ---

DIRETORIO_BASE = os.path.dirname(os.path.abspath(__file__))

CAMINHO_MEDICOS = os.path.join(DIRETORIO_BASE, 'medicos.json')
CAMINHO_PACIENTES = os.path.join(DIRETORIO_BASE, 'pacientes.json')
CAMINHO_ADMIN = os.path.join(DIRETORIO_BASE, 'usersadmin.json')
CAMINHO_FLAG_IMPORTACAO = os.path.join(DIRETORIO_BASE, '.dados_importados')



# ============================================================================
# FUNÇÕES ALTERAR DADOS
# ============================================================================



def carregar_dados(arquivo):
    
    if 'medicos' in arquivo:
        caminho = CAMINHO_MEDICOS
    else:
        caminho = CAMINHO_PACIENTES
    
    if os.path.exists(caminho):
        with open(caminho, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        return {"medicos": []} if "medicos" in arquivo else {"pacientes": []}


def salvar_dados(arquivo, dados):
    
    if 'medicos' in arquivo:
        caminho = CAMINHO_MEDICOS
    else:
        caminho = CAMINHO_PACIENTES
    
    
    with open(caminho, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)
    

def criar_medico(id_medico, nome, especialidade, disponivel):
    
    novo_medico = {
        "id": id_medico,
        "nome": nome,
        "ocupado": not disponivel,
        "doente_corrente": None,
        "especialidade": especialidade,
        "total_tempo_ocupado": 0.0,
        "inicio_ultima_consulta": 0.0
    }
    return novo_medico

def atualizar_medico(medico, nome, especialidade, disponivel):
    
    medico['nome'] = nome
    medico['especialidade'] = especialidade
    medico['ocupado'] = not disponivel
    return medico

def criar_paciente(id_paciente, nome, idade, sexo, doenca, prioridade, fumador, alcool, atividade, cronico):
    
    novo_paciente = {
        "id": id_paciente,
        "nome": nome,
        "idade": idade,
        "sexo": sexo,
        "doenca": doenca,
        "prioridade": prioridade,
        "atributos": {
            "fumador": fumador,
            "consome_alcool": alcool,
            "atividade_fisica": atividade,
            "cronico": cronico
        }
    }
    return novo_paciente

def atualizar_paciente(paciente, nome, idade, sexo, doenca, prioridade, fumador, alcool, atividade, cronico):
    
    paciente['nome'] = nome.strip()
    paciente['idade'] = idade
    paciente['sexo'] = sexo
    paciente['doenca'] = doenca.strip()
    paciente['prioridade'] = prioridade
    paciente['atributos']['fumador'] = fumador
    paciente['atributos']['consome_alcool'] = alcool
    paciente['atributos']['atividade_fisica'] = atividade
    paciente['atributos']['cronico'] = cronico
    return paciente

def adicionar_medico_dados(novo_medico, arquivo='medicos.json'):
   
    dados = carregar_dados(arquivo)
    if not isinstance(dados, dict):
        dados = {'medicos': []}
    if 'medicos' not in dados or not isinstance(dados['medicos'], list):
        dados['medicos'] = []
    dados['medicos'].append(novo_medico)
    salvar_dados(arquivo, dados)

def adicionar_paciente_dados(novo_paciente, arquivo='pacientes.json'):
  
    dados = carregar_dados(arquivo)
    if not isinstance(dados, dict):
        dados = {'pacientes': []}
    if 'pacientes' not in dados or not isinstance(dados['pacientes'], list):
        dados['pacientes'] = []
    dados['pacientes'].append(novo_paciente)
    salvar_dados(arquivo, dados)



def procurar_medico_dados(chave):
    dados = carregar_dados('medicos.json')
    medicos = dados.get('medicos', [])

    chave = chave.lower()
    encontrados = []

    for medico in medicos:
        if str(medico.get('id')) == chave:
            return medico, dados

        nome = medico.get('nome', '').lower().replace('dr.', '').replace('dra.', '')

        if chave in nome:
            encontrados.append(medico)

    if len(encontrados) == 1:
        return encontrados[0], dados

    if len(encontrados) > 1:
        return encontrados, dados

    return None, dados





def procurar_paciente_dados(chave, arquivo='pacientes.json'):
    

    dados = carregar_dados(arquivo)
    pacientes = dados.get('pacientes') if isinstance(dados, dict) else []
    if not isinstance(pacientes, list):
        pacientes = []

    def normalizar(s):
        if not isinstance(s, str):
            return ''

        s = s.lower()
        s = unicodedata.normalize('NFKD', s)
        s = ''.join(c for c in s if not unicodedata.combining(c))
        s = re.sub(r'[^a-z\s]', '', s)
        s = re.sub(r'\s+', ' ', s).strip()
        return s

    chave_str = str(chave).strip()
    chave_norm = normalizar(chave)

    encontrados = []

    for paciente in pacientes:
        
        if str(paciente.get('id')) == chave_str:
            return paciente, dados

        
        nome_norm = normalizar(paciente.get('nome', ''))
        if chave_norm and chave_norm in nome_norm:
            encontrados.append(paciente)

    if len(encontrados) == 1:
        return encontrados[0], dados

    if len(encontrados) > 1:
        return encontrados, dados

    return None, dados



def remover_medico_dados(chave, arquivo='medicos.json'):
    

    dados = carregar_dados(arquivo)
    medicos = dados.get('medicos') if isinstance(dados, dict) else []
    if not isinstance(medicos, list):
        medicos = []

    def normalizar(s):
        if not isinstance(s, str):
            return ''

        s = s.lower()
        s = re.sub(r'\bdr\.?\b|\bdra\.?\b', '', s)
        s = unicodedata.normalize('NFKD', s)
        s = ''.join(c for c in s if not unicodedata.combining(c))
        s = re.sub(r'[^a-z\s]', '', s)
        s = re.sub(r'\s+', ' ', s).strip()
        return s

    chave_str = str(chave).strip()
    chave_norm = normalizar(chave)

    encontrados = []

    for medico in medicos:
        
        if str(medico.get('id')) == chave_str:
            dados['medicos'] = [m for m in medicos if m.get('id') != medico.get('id')]
            salvar_dados(arquivo, dados)
            return True

        
        nome_norm = normalizar(medico.get('nome', ''))
        if chave_norm and chave_norm in nome_norm:
            encontrados.append(medico)

   
    if len(encontrados) > 1:
        return encontrados

    
    if len(encontrados) == 1:
        medico = encontrados[0]
        dados['medicos'] = [m for m in medicos if m.get('id') != medico.get('id')]
        salvar_dados(arquivo, dados)
        return True

    return False


def remover_paciente_dados(chave, arquivo='pacientes.json'):

    dados = carregar_dados(arquivo)
    pacientes = dados.get('pacientes') if isinstance(dados, dict) else []
    if not isinstance(pacientes, list):
        pacientes = []

    def normalizar(s):
        if not isinstance(s, str):
            return ''

        s = s.lower()
        s = unicodedata.normalize('NFKD', s)
        s = ''.join(c for c in s if not unicodedata.combining(c))
        s = re.sub(r'[^a-z\s]', '', s)
        s = re.sub(r'\s+', ' ', s).strip()
        return s

    chave_str = str(chave).strip()
    chave_norm = normalizar(chave)

    encontrados = []

    for paciente in pacientes:
        
        if str(paciente.get('id')) == chave_str:
            dados['pacientes'] = [p for p in pacientes if p.get('id') != paciente.get('id')]
            salvar_dados(arquivo, dados)
            return True

        
        nome_norm = normalizar(paciente.get('nome', ''))
        if chave_norm and chave_norm in nome_norm:
            encontrados.append(paciente)

   
    if len(encontrados) > 1:
        return encontrados

    
    if len(encontrados) == 1:
        paciente = encontrados[0]
        dados['pacientes'] = [p for p in pacientes if p.get('id') != paciente.get('id')]
        salvar_dados(arquivo, dados)
        return True

    return False


def validar_campos_medico(id_medico, nome, especialidade):
    
    if not id_medico or not nome or not especialidade:
        return False
    return True

def validar_campos_paciente(id_paciente, nome, idade, sexo, doenca, prioridade, atividade):
    
    if not all([id_paciente, nome, idade, sexo, doenca, prioridade, atividade]):
        return False
    return True


def validar_idade(idade_str):
    
    if idade_str.isdigit():
        idade = int(idade_str)
        if idade > 0 and idade < 150:
            return idade, True
    return None, False




def validar_estrutura_medicos(dados):
    if not isinstance(dados, dict):
        return False
    medicos = dados.get('medicos')
    if not isinstance(medicos, list):
        return False
    for m in medicos:
        if not isinstance(m, dict):
            return False
        if 'id' not in m or 'nome' not in m or 'especialidade' not in m:
            return False
        
        if not isinstance(m.get('id'), (str, int)):
            return False
        if not isinstance(m.get('nome'), str) or not isinstance(m.get('especialidade'), str):
            return False
    return True


def validar_estrutura_pacientes(dados):
    if not isinstance(dados, dict):
        return False
    pacientes = dados.get('pacientes')
    if not isinstance(pacientes, list):
        return False
    for p in pacientes:
        if not isinstance(p, dict):
            return False
        required = ['id', 'nome', 'idade', 'sexo', 'doenca', 'prioridade', 'atributos']
        for k in required:
            if k not in p:
                return False
        if not isinstance(p.get('id'), (str, int)):
            return False
        if not isinstance(p.get('nome'), str):
            return False
        
        if not isinstance(p.get('idade'), int):
            return False
        if not isinstance(p.get('sexo'), str) or not isinstance(p.get('doenca'), str) or not isinstance(p.get('prioridade'), str):
            return False
        atr = p.get('atributos')
        if not isinstance(atr, dict):
            return False
       
        if 'fumador' not in atr or 'consome_alcool' not in atr or 'atividade_fisica' not in atr or 'cronico' not in atr:
            return False
    return True



def marcar_dados_como_importados():
    
    with open(CAMINHO_FLAG_IMPORTACAO, 'w') as f:
        f.write('importado')


def limpar_flag_importacao():
    
    if os.path.exists(CAMINHO_FLAG_IMPORTACAO):
        os.remove(CAMINHO_FLAG_IMPORTACAO)


def verificar_dados_importados():
    
    
    if not os.path.exists(CAMINHO_FLAG_IMPORTACAO):
        return False, False
    
    
    if not os.path.exists(CAMINHO_MEDICOS) or not os.path.exists(CAMINHO_PACIENTES):
        return False, False
    
    
    dados_medicos = carregar_dados('medicos.json')
    dados_pacientes = carregar_dados('pacientes.json')
    
    
    tem_medicos = False
    if isinstance(dados_medicos, dict) and 'medicos' in dados_medicos:
        medicos_lista = dados_medicos['medicos']
        if isinstance(medicos_lista, list) and len(medicos_lista) > 0:
            tem_medicos = True
    
    
    tem_pacientes = False
    if isinstance(dados_pacientes, dict) and 'pacientes' in dados_pacientes:
        pacientes_lista = dados_pacientes['pacientes']
        if isinstance(pacientes_lista, list) and len(pacientes_lista) > 0:
            tem_pacientes = True
    
    return tem_medicos, tem_pacientes


# ============================================================================
# FUNÇÕES SIMULAÇÃO
# ============================================================================

def enqueue(q, item):
    
    return q + [item]

def dequeue(q):
    
    if not q:
        return None, []
    return q[0], q[1:]

def queue_empty(q):
    
    return len(q) == 0

def queue_peek(q):
    
    if queue_empty(q):
        return None
    return q[0]






# ============================================================================
# FUNÇÕES PARA MANIPULAR A FILA DE ESPERA (usando as funções acima)
# ============================================================================

def adicionar_a_fila(fila, paciente):
    
    return enqueue(fila, paciente)

def remover_da_fila(fila):
    
    if queue_empty(fila):
        return None, fila
    return dequeue(fila)

def obter_proximo_paciente_fila(fila):
    
    return queue_peek(fila)

def tamanho_fila(fila):
   
    return len(fila)


def carregar_mapeamento_doencas():
    
    if os.path.exists(CAMINHO_MEDICOS):
        try:
            with open(CAMINHO_MEDICOS, "r", encoding="utf-8") as f:
                dados = json.load(f)
                
                mapeamento = dados.get("mapeamento_doencas", {})
                
                if mapeamento:
                    mapeamento_expandido = {}
                    for doenca, especialidade in mapeamento.items():
                        mapeamento_expandido[doenca.lower()] = especialidade
                        
                        
                        if doenca.endswith('s'):
                            mapeamento_expandido[doenca.lower()[:-1]] = especialidade
                        else:
                            mapeamento_expandido[doenca.lower() + 's'] = especialidade
                    return mapeamento_expandido
        except:
            pass

   
    return {
        'febre': 'Clínica Geral', 'gripe': 'Clínica Geral', 'dor': 'Clínica Geral',
        'lombar': 'Ortopedia', 'fratura': 'Ortopedia',
        'cardíaco': 'Cardiologia', 'coração': 'Cardiologia',
        'pulmonar': 'Pneumologia', 'asma': 'Pneumologia',
        'pele': 'Dermatologia', 'acne': 'Dermatologia'
    }

def carregar_pacientes_simula():
    
    if not os.path.exists(CAMINHO_PACIENTES):
        return []

    try:
        with open(CAMINHO_PACIENTES, "r", encoding="utf-8") as f:
            dados = json.load(f)
            
            pessoas = dados.get("pacientes", []) if isinstance(dados, dict) else dados
            
            if not pessoas: return []

            pessoas_validas = []
            mapa_prioridades = {
                "emergência": "URGENTE", "emergencia": "URGENTE",
                "alta": "ALTA", "normal": "NORMAL", "baixa": "BAIXA"
            }
            
            mapeamento_doencas = carregar_mapeamento_doencas()
            
            i = 0
            while i < len(pessoas):
                p = pessoas[i]
                if isinstance(p, dict):
                    
                    prioridade_raw = str(p.get("prioridade", "NORMAL")).lower()
                    p["prioridade"] = mapa_prioridades.get(prioridade_raw, "NORMAL")
                    p["doenca"] = p.get("doenca", "Consulta de rotina")
                    p["consulta_marcada"] = p.get("consulta_marcada", False)
                    
                    doenca_lower = p["doenca"].lower()
                    especialidade = "Clínica Geral"
                    
                    if doenca_lower in mapeamento_doencas:
                        especialidade = mapeamento_doencas[doenca_lower]
                    else:
                        palavras = doenca_lower.split()
                        j = 0
                        encontrado = False
                        while j < len(palavras) and not encontrado:
                            if palavras[j] in mapeamento_doencas:
                                especialidade = mapeamento_doencas[palavras[j]]
                                encontrado = True
                            j = j + 1
                    
                    p["especialidade_necessaria"] = especialidade
                    pessoas_validas.append(p)
                i = i + 1
            return pessoas_validas
    except Exception as e:
        print(f"Erro crítico nos pacientes: {e}")
        return []

def carregar_medicos_simula():
    
    if os.path.exists(CAMINHO_MEDICOS):
        try:
            with open(CAMINHO_MEDICOS, "r", encoding="utf-8") as f:
                dados = json.load(f)
                medicos = dados.get("medicos", []) if isinstance(dados, dict) else dados
                
                for m in medicos:
                    if "especialidade" not in m:
                        m["especialidade"] = "Clínica Geral"
                return medicos
        except Exception as e:
            print(f"Erro ao ler médicos: {e}")
            return []
    return []




def ordenar_fila_por_prioridade(fila, prioridades):
    if not fila:
        return fila
    lista_fila = []
    while not queue_empty(fila):
        paciente, fila = remover_da_fila(fila)
        lista_fila.append(paciente)
    lista_fila.sort(key=lambda p: prioridades.get(p.get("prioridade", "NORMAL"), 3))
    fila_ordenada = []
    for paciente in lista_fila:
        fila_ordenada = adicionar_a_fila(fila_ordenada, paciente)
    return fila_ordenada


def gera_tempo_consulta(tempo_medio, dist):
    if dist == "exponential":
        tempo = np.random.exponential(scale=tempo_medio)
    elif dist == "normal":
        tempo = np.random.normal(tempo_medio, 5)
    elif dist == "uniform":
        tempo = np.random.uniform(tempo_medio * 0.5, tempo_medio * 1.5)
    else:
        tempo = tempo_medio
    
    tempo = max(tempo_medio * 0.3, min(tempo, tempo_medio * 2.0))
    return tempo





def salvar_arquivo(conteudo, nome_arquivo):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_base = nome_arquivo.rsplit('.', 1)[0]
    extensao = nome_arquivo.rsplit('.', 1)[1] if '.' in nome_arquivo else 'txt'
    nome_completo = f"{nome_base}_{timestamp}.{extensao}"
    
    with open(nome_completo, "w", encoding="utf-8") as f:
        f.write(conteudo)
    return nome_completo









