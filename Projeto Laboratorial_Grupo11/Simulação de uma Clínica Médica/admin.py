import json
import os
import FreeSimpleGUI as sg
from funcoes import DIRETORIO_BASE
from funcoes import CAMINHO_ADMIN
escuro = '#2196f3'
claro = '#c3e3fd'




def verificar_ficheiro_admin():
    """Verifica se o ficheiro existe e tenta encontrá-lo"""
    
    
    if os.path.exists(CAMINHO_ADMIN):
        return CAMINHO_ADMIN
    
    
    if os.path.exists(DIRETORIO_BASE):
        ficheiros = os.listdir(DIRETORIO_BASE)
        ficheiros_json = [f for f in ficheiros if f.endswith('.json') and 'admin' in f.lower()]
        
        if ficheiros_json:
            mensagem = (
                f"Ficheiro 'usersadmin.json' não encontrado!\n\n"
                f"Ficheiros JSON com 'admin' encontrados:\n"
                + "\n".join(f"  • {f}" for f in ficheiros_json) +
                f"\n\nPor favor, renomeie um deles para 'usersadmin.json'"
            )
            sg.popup_error(mensagem, title="Ficheiro não encontrado")
            return None
    
    sg.popup_error(
        f"Ficheiro de administrador não encontrado em:\n{CAMINHO_ADMIN}\n\n"
        f"Por favor, verifique se o ficheiro existe!",
        title="Erro",
        background_color=claro,
        text_color='red'
    )
    return None


def login_admin(email, password):
    """Valida as credenciais do administrador"""
    
    
    caminho = verificar_ficheiro_admin()
    if not caminho:
        return False
    
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            creds = json.load(f)
    except json.JSONDecodeError:
        sg.popup_error(
            "Ficheiro de administrador corrompido!",
            title="Erro"
        )
        return False
    except Exception as e:
        sg.popup_error(
            f"Erro ao ler ficheiro:\n{str(e)}",
            title="Erro"
        )
        return False
    
    
    if isinstance(creds, list):
        for user in creds:
            if user.get("email") == email and user.get("password") == password:
                return True
    elif isinstance(creds, dict):
        if creds.get("email") == email and creds.get("password") == password:
            return True
    else:
        sg.popup_error("Formato de ficheiro inválido!", title="Erro")
        return False
    
    return False


def login():
    """Interface de login do administrador"""
    sg.theme('TemaClinica')
    
    layout = [
        [sg.Text("Sistema de Gestão de Clínica", 
                font=("Helvetica", 20), 
                justification="center", 
                expand_x=True,
                background_color=claro,
                text_color=escuro)],
        [sg.Text("", background_color=claro)],
        [sg.Text("Email:", size=(12,1), background_color=claro, text_color=escuro), 
         sg.Input(key="-EMAIL-", size=(30,1))],
        [sg.Text("Palavra-passe:", size=(12,1), background_color=claro, text_color=escuro), 
         sg.Input(key="-PASSWORD-", password_char="*", size=(30,1))],
        [sg.Text("", background_color=claro)],
        [sg.Button("Entrar", size=(12,1), button_color=('white',escuro)), 
         sg.Button("Sair", size=(12,1), button_color=('white',escuro))],
        [sg.Text("", key="-OUTPUT-", text_color='red', justification='center', 
                expand_x=True, background_color=claro)]
    ]
    
    window = sg.Window(
        "Autenticação Administrativa", 
        layout, 
        modal=True, 
        element_justification='center',
        background_color=claro
    )
    
    resultado = False
    continuar_login = True
    
    while continuar_login:
        event, values = window.read()
        
        if event == sg.WINDOW_CLOSED or event == "Sair":
            continuar_login = False
            resultado = False
        
        elif event == "Entrar":
            email = values["-EMAIL-"].strip()
            password = values["-PASSWORD-"]
            
            if not email or not password:
                window["-OUTPUT-"].update("Preencha todos os campos!")
                continue
            
            if login_admin(email, password):
                resultado = True
                continuar_login = False
            else:
                window["-OUTPUT-"].update("Credenciais inválidas!")
    
    window.close()
    return resultado