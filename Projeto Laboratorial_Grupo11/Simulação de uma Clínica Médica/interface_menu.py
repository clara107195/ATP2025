import FreeSimpleGUI as sg
from funcoes import *
import os
import unicodedata
import re
import interface_simulacao


escuro='#2196f3'
claro='#c3e3fd'




layout = [
    [sg.Text('Sistema de Gestão Clínica', background_color=claro, text_color=escuro,
             font=('Helvetica', 21, 'bold'), justification='center', expand_x=True)],

    
    [sg.Text(background_color=claro, size=(1,2))],

    
    [sg.Text('', background_color=claro, size=(8,1)), sg.Button('Simulação Clínica', button_color=(claro, escuro), size=(33, 4), font=('Helvetica', 13), key='-SIMULACAO-'), sg.Text('', background_color=claro, size=(10,2))],
    [sg.Text('', background_color=claro, size=(8,1)), sg.Button('Alterar Dados', button_color=(claro, escuro), size=(33, 4), font=('Helvetica', 13), key='-ALTERAR-'), sg.Text('', background_color=claro, size=(10,2))],
    [sg.Text('', background_color=claro, size=(8,1)), sg.Button('Importar Dados', button_color=(claro, escuro), size=(33, 4), font=('Helvetica', 13), key='-IMPORTAR-'), sg.Text('', background_color=claro, size=(10,2))],
    
    [sg.Text(background_color=claro, size=(0,0))],

    
    [sg.Text('', background_color=claro, size=(6,1)), sg.Button('Sair', size=(12, 1), font=('Helvetica', 11), key='-SAIR-', button_color=('white', 'red'), pad=(0,20)), sg.Text('', background_color=claro, size=(10,1))]
]


def popup_sim_nao(message, title=None, background_color=None, text_color=None):
   
    bg = background_color if background_color is not None else claro
    txt = text_color if text_color is not None else escuro
    btn_layout = [[sg.Text(message, background_color=bg, text_color=txt)], [sg.Text('', background_color=bg, size=(3,1)), sg.Button('Sim', button_color=(claro, escuro)), sg.Text('', background_color=bg, size=(1,1)), sg.Button('Não', button_color=(claro, escuro)), sg.Text('', background_color=bg, size=(3,1))]]
    win = sg.Window(title or '', btn_layout, modal=True, background_color=bg)
    event, values = win.read()
    win.close()
    if event is None:
        return 'Não'
    return event



def popup_ok(message, title=None, background_color=None, button_color=None, text_color=None):
    
    bg = background_color if background_color is not None else claro
    txt = text_color if text_color is not None else escuro
    btn_col = button_color if button_color is not None else (claro, escuro)
    layout = [[sg.Text(message, background_color=bg, text_color=txt, pad=(10,10))], [ sg.Button('OK', button_color=btn_col), sg.Text('', background_color=bg, size=(6,1))]]
    w = sg.Window(title or '', layout, modal=True, background_color=bg)
    e, v = w.read()
    w.close()
    return e





def importar_dados():
    caminho_medicos = sg.popup_get_file(
        'Escolha o ficheiro de médicos',
        file_types=(('JSON Files', '*.json'),),
        initial_folder='.',
        save_as=False, background_color=claro, text_color=escuro, button_color=(claro, escuro)
    )

    if not caminho_medicos:
        return
    
    dados_medicos = carregar_dados(caminho_medicos)
    if not validar_estrutura_medicos(dados_medicos):
        popup_ok('Ficheiro selecionado não corresponde ao modelo de médicos!', 
                title='Erro', background_color=claro, button_color=(claro, escuro), text_color=escuro)
        return

    caminho_pacientes = sg.popup_get_file(
        'Escolha o ficheiro de pacientes',
        file_types=(('JSON Files', '*.json'),),
        initial_folder='.',
        save_as=False, background_color=claro, text_color=escuro, button_color=(claro, escuro)
    )

    if not caminho_pacientes:
        return

    dados_pacientes = carregar_dados(caminho_pacientes)
    if not validar_estrutura_pacientes(dados_pacientes):
        popup_ok('Ficheiro selecionado não corresponde ao modelo de pacientes!', 
                title='Erro', background_color=claro, button_color=(claro, escuro), text_color=escuro)
        return

    
    salvar_dados('medicos.json', dados_medicos)
    salvar_dados('pacientes.json', dados_pacientes)
    
    
    marcar_dados_como_importados()

    popup_ok('Dados importados com sucesso!', title='Sucesso', 
            background_color=claro, button_color=(claro, escuro), text_color=escuro)
    

def adicionar_medico():
    dados = carregar_dados('medicos.json')
    
    
    if not isinstance(dados, dict):
        dados = {'medicos': []}
    if 'medicos' not in dados:
        dados['medicos'] = []
    
    medicos = dados['medicos']  
    
    
    if medicos:
        ultimo_id = max([int(m.get('id', 'm0').replace('m', '')) for m in medicos if m.get('id', '').startswith('m')])
        novo_id = f"m{ultimo_id + 1}"
    else:
        novo_id = "m1"
    
    layout_add = [
        [sg.Text('Adicionar Novo Médico', font=('Helvetica', 14, 'bold'), background_color=claro, text_color=escuro)],
        [sg.Text(f'ID: {novo_id}', font=('Helvetica', 10), background_color=claro, text_color=escuro)],
        [sg.Text('Nome:', background_color=claro, text_color=escuro), 
         sg.Combo(['Dr.', 'Dra.'], default_value='Dr.', key='-TRATAMENTO-', size=(6, 1), readonly=True),
         sg.Input(key='-NOME-', size=(23, 1))],
        [sg.Text('Especialidade:', background_color=claro, text_color=escuro), 
         sg.Input(key='-ESPECIALIDADE-', size=(30, 1))],
        [sg.Button('Guardar', key='-GUARDAR-', button_color=(claro, escuro)), 
         sg.Button('Cancelar', key='-CANCELAR-', button_color=(claro, escuro))]
    ]
    
    window = sg.Window('Adicionar Médico', layout_add, modal=True, background_color=claro)
    
    while True:
        event, values = window.read()
        
        if event in (sg.WIN_CLOSED, '-CANCELAR-'):
            window.close()
            return
        
        if event == '-GUARDAR-':
            if not values['-NOME-'].strip() or not values['-ESPECIALIDADE-'].strip():
                popup_ok('Por favor, preencha todos os campos necessários!', 
                        title='Erro', background_color=claro, text_color=escuro)
            else:
                
                nome_completo = f"{values['-TRATAMENTO-']} {values['-NOME-'].strip()}"
                
                
                novo_medico = {
                    "id": novo_id,
                    "nome": nome_completo,
                    "ocupado": False,
                    "doente_corrente": None,
                    "especialidade": values['-ESPECIALIDADE-'].strip(),
                    "total_tempo_ocupado": 0.0,
                    "inicio_ultima_consulta": 0.0
                }
                
               
                dados['medicos'].append(novo_medico)
                
                
                salvar_dados('medicos.json', dados)
                
                popup_ok('Médico adicionado com sucesso!', 
                        title='Médico Adicionado', background_color=claro, text_color=escuro)
                window.close()
                return


def adicionar_paciente():
    dados = carregar_dados('pacientes.json')
    
    
    if not isinstance(dados, dict):
        dados = {'pacientes': []}
    if 'pacientes' not in dados:
        dados['pacientes'] = []
    
    pacientes = dados['pacientes']  
    
    
    if pacientes:
        ultimo_id = max([int(p.get('id', 'd0').replace('d', '')) for p in pacientes if p.get('id', '').startswith('d')])
        novo_id = f"d{ultimo_id + 1}"
    else:
        novo_id = "d1"
    
    layout_add = [
        [sg.Text('Adicionar Novo Paciente', font=('Helvetica', 14, 'bold'), 
                background_color=claro, text_color=escuro)],
        [sg.Text(f'ID: {novo_id}', font=('Helvetica', 10), 
                background_color=claro, text_color=escuro)],
        [sg.Text('Nome:', background_color=claro, text_color=escuro), 
         sg.Input(key='-NOME-', size=(30, 1))],
        [sg.Text('Idade:', background_color=claro, text_color=escuro), 
         sg.Input(key='-IDADE-', size=(30, 1))],
        [sg.Text('Sexo:', background_color=claro, text_color=escuro), 
         sg.Combo(['masculino', 'feminino', 'outro'], key='-SEXO-', readonly=True)],
        [sg.Text('Doença:', background_color=claro, text_color=escuro), 
         sg.Input(key='-DOENCA-', size=(30, 1))],
        [sg.Text('Prioridade:', background_color=claro, text_color=escuro), 
         sg.Combo(['Baixa','Normal', 'Alta', 'Emergência'], key='-PRIORIDADE-', readonly=True)],
        [sg.Text('Atributos:', font=('Helvetica', 10, 'bold'), 
                background_color=claro, text_color=escuro)],
        [sg.Checkbox('Fumador', key='-FUMADOR-', background_color=claro, text_color=escuro)],
        [sg.Checkbox('Consome Álcool', key='-ALCOOL-', background_color=claro, text_color=escuro)],
        [sg.Text('Atividade Física:', background_color=claro, text_color=escuro), 
         sg.Combo(['baixa', 'moderada', 'alta'], key='-ATIVIDADE-', readonly=True)],
        [sg.Checkbox('Doença Crónica', key='-CRONICO-', background_color=claro, text_color=escuro)],
        [sg.Button('Guardar', key='-GUARDAR-', button_color=(claro, escuro)), 
         sg.Button('Cancelar', key='-CANCELAR-', button_color=(claro, escuro))]
    ]
    
    window = sg.Window('Adicionar Paciente', layout_add, modal=True, background_color=claro)
    
    while True:
        event, values = window.read()
        
        if event in (sg.WIN_CLOSED, '-CANCELAR-'):
            window.close()
            return
        
        if event == '-GUARDAR-':
           
            if not values['-NOME-'].strip():
                popup_ok('Por favor, preencha o nome!', title='Erro', 
                        background_color=claro, text_color=escuro)
            elif not values['-IDADE-'].strip():
                popup_ok('Por favor, preencha a idade!', title='Erro', 
                        background_color=claro, text_color=escuro)
            elif not values['-IDADE-'].isdigit():
                popup_ok('Idade deve ser um número!', title='Erro', 
                        background_color=claro, text_color=escuro)
            elif not values['-SEXO-']:
                popup_ok('Por favor, selecione o sexo!', title='Erro', 
                        background_color=claro, text_color=escuro)
            elif not values['-DOENCA-'].strip():
                popup_ok('Por favor, preencha a doença!', title='Erro', 
                        background_color=claro, text_color=escuro)
            elif not values['-PRIORIDADE-']:
                popup_ok('Por favor, selecione a prioridade!', title='Erro', 
                        background_color=claro, text_color=escuro)
            elif not values['-ATIVIDADE-']:
                popup_ok('Por favor, selecione a atividade física!', title='Erro', 
                        background_color=claro, text_color=escuro)
            else:
               
                novo_paciente = {
                    "id": novo_id,
                    "nome": values['-NOME-'].strip(),
                    "idade": int(values['-IDADE-']),
                    "sexo": values['-SEXO-'],
                    "doenca": values['-DOENCA-'].strip(),
                    "prioridade": values['-PRIORIDADE-'],
                    "atributos": {
                        "fumador": values['-FUMADOR-'],
                        "consome_alcool": values['-ALCOOL-'],
                        "atividade_fisica": values['-ATIVIDADE-'],
                        "cronico": values['-CRONICO-']
                    }
                }
                
                dados['pacientes'].append(novo_paciente)
                
                
                salvar_dados('pacientes.json', dados)
                
                popup_ok('Paciente adicionado com sucesso!', title='Sucesso', 
                        background_color=claro, text_color=escuro)
                window.close()
                return







def _normalize_text(s):
    if not isinstance(s, str):
        return ''

    s = s.strip().lower()

    
    s = re.sub(r'\bdr\.?\b|\bdra\.?\b', '', s)

    
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))

    
    s = re.sub(r'[^a-z\s]', '', s)

    
    s = re.sub(r'\s+', ' ', s).strip()

    return s



def listar_medicos():
    tem_medicos, _ = verificar_dados_importados()
    if not tem_medicos:
        popup_ok('Não há médicos registados!', title='Aviso', background_color=claro, text_color=escuro)
        return

    dados = carregar_dados('medicos.json')
    medicos = dados.get('medicos', [])

    headings = ['ID', 'Nome', 'Especialidade', 'Estado']

    def build_med_rows(filter_name=''):
        rows = []
        nf = _normalize_text(filter_name)
        i = 0
        while i < len(medicos):
            m = medicos[i]
            nome = m.get('nome', '')
            if nf and nf not in _normalize_text(nome):
                i = i + 1
                continue
            ocupado = m.get('ocupado', False)
            status = 'Ocupado' if ocupado else 'Disponível'
            doente = m.get('doente_corrente', '')
            if ocupado and doente:
                status = status + f' (atendendo {doente})'
            rows.append([m.get('id', ''), nome, m.get('especialidade', ''), status])
            i = i + 1
        return rows

    def calcular_estatisticas():
        total = len(medicos)
        disponiveis = 0
        ocupados = 0
        j = 0
        while j < len(medicos):
            if not medicos[j].get('ocupado', False):
                disponiveis = disponiveis + 1
            else:
                ocupados = ocupados + 1
            j = j + 1
        return f"Total: {total}  |  Disponíveis: {disponiveis}  |  Ocupados: {ocupados}"

    left_col = sg.Column([
        [sg.Input('', key='-SEARCH-MED-', size=(25,1), tooltip='Pesquisar por nome'),
         sg.Button('Pesquisar', key='-SEARCH-MED-BTN-', button_color=(claro, escuro)),
         sg.Button('Limpar', key='-CLEAR-MED-', button_color=(claro, escuro))],
        [sg.Table(
            values=build_med_rows(), headings=headings, auto_size_columns=False,
            col_widths=[8,25,20,25], justification='left', num_rows=15,
            key='-TABLE-MEDICOS-', enable_events=True, row_height=28,
            background_color='white', header_background_color=claro,
            text_color=escuro, header_text_color=escuro
        )]
    ], background_color='white', pad=(6,6))

    right_col = sg.Column([
        [sg.Text('Detalhes', font=('Helvetica', 12, 'bold'), background_color='white', text_color=escuro)],
        [sg.Multiline('', size=(50,13), key='-DETALHES-', disabled=True, autoscroll=False,
                      background_color='white', text_color=escuro, font=('Courier', 10))],
        [sg.Button('Editar', key='-EDITAR-MED-', button_color=(claro, escuro), size=(12,1), visible=False),
         sg.Button('Remover', key='-REMOVER-MED-', button_color=(claro, escuro), size=(12,1), visible=False)],
        [sg.Text(calcular_estatisticas(), key='-ESTAT-', background_color='white', text_color=escuro, pad=(0,10))]
    ], background_color='white', pad=(6,6))

    layout = [
        [sg.Text('Lista de Médicos', font=('Helvetica', 16, 'bold'), background_color=claro, text_color=escuro, pad=(10,10))],
        [sg.Column([[left_col, sg.VerticalSeparator(), right_col]], background_color=claro, pad=(0,0))],
        [sg.Push(background_color=claro),
         sg.Button('Fechar', button_color=(claro, escuro), size=(12,1), font=('Helvetica', 10), key='-FECHAR-MED-', pad=(10,10)),
         sg.Push(background_color=claro)]
    ]

    w = sg.Window('Médicos', layout, modal=True, background_color=claro, size=(1150, 680), element_justification='left', finalize=True)
    
    medico_selecionado = None

    while True:
        event, values = w.read()
        if event in (sg.WIN_CLOSED, '-FECHAR-MED-'):
            w.close()
            return

        if event == '-SEARCH-MED-BTN-':
            q = values.get('-SEARCH-MED-', '')
            w['-TABLE-MEDICOS-'].update(values=build_med_rows(q))
            w['-DETALHES-'].update('')
            w['-EDITAR-MED-'].update(visible=False)
            w['-REMOVER-MED-'].update(visible=False)
            w['-ESTAT-'].update(calcular_estatisticas())
            medico_selecionado = None

        if event == '-CLEAR-MED-':
            w['-SEARCH-MED-'].update('')
            w['-TABLE-MEDICOS-'].update(values=build_med_rows(''))
            w['-DETALHES-'].update('')
            w['-EDITAR-MED-'].update(visible=False)
            w['-REMOVER-MED-'].update(visible=False)
            w['-ESTAT-'].update(calcular_estatisticas())
            medico_selecionado = None

        if event == '-TABLE-MEDICOS-':
            sel = values.get('-TABLE-MEDICOS-')
            if sel:
                idx = sel[0]
                filter_q = values.get('-SEARCH-MED-', '')
                filtered = build_med_rows(filter_q)
                if idx < len(filtered):
                    row = filtered[idx]
                    med_id = row[0]
                    
                    # Procurar médico sem next/generator (loop while)
                    m = None
                    k = 0
                    while k < len(medicos):
                        if str(medicos[k].get('id','')) == str(med_id):
                            m = medicos[k]
                        k = k + 1
                    
                    if m:
                        medico_selecionado = m
                        linhas = [
                            f"ID: {m.get('id','')}",
                            f"Nome: {m.get('nome','')}",
                            f"Especialidade: {m.get('especialidade','')}",
                            f"Estado: {'Ocupado' if m.get('ocupado',False) else 'Disponível'}",
                            f"Doente corrente: {m.get('doente_corrente','N/A')}",
                            
                        ]
                        w['-DETALHES-'].update('\n'.join(linhas))
                        w['-EDITAR-MED-'].update(visible=True)
                        w['-REMOVER-MED-'].update(visible=True)
                        w['-ESTAT-'].update(calcular_estatisticas())

        if event == '-EDITAR-MED-' and medico_selecionado:
          
            nome_completo = medico_selecionado['nome']
            tratamento = 'Dr.'
            nome_sem_tratamento = nome_completo
            
            
            if nome_completo.startswith('Dr. '):
                tratamento = 'Dr.'
                nome_sem_tratamento = nome_completo[4:]  
            elif nome_completo.startswith('Dra. '):
                tratamento = 'Dra.'
                nome_sem_tratamento = nome_completo[5:]  
            
            layout_edit = [
                [sg.Text('Editar Médico', font=('Helvetica', 14, 'bold'), background_color=claro, text_color=escuro)],
                [sg.Text(f'ID: {medico_selecionado["id"]}', font=('Helvetica', 10), background_color=claro, text_color=escuro)],
                [sg.Text('Nome:', background_color=claro, text_color=escuro), 
                sg.Combo(['Dr.', 'Dra.'], default_value=tratamento, key='-TRATAMENTO-', size=(6, 1), readonly=True),
                sg.Input(default_text=nome_sem_tratamento, key='-NOME-', size=(23, 1))],
                [sg.Text('Especialidade:', background_color=claro, text_color=escuro), 
                sg.Input(default_text=medico_selecionado['especialidade'], key='-ESPECIALIDADE-', size=(30, 1))],
                [sg.Text('Disponível:', background_color=claro, text_color=escuro), 
                sg.Text('Sim' if not medico_selecionado.get('ocupado', False) else 'Não', key='-DISPONIVEL-', background_color=claro, text_color=escuro)],
                [sg.Button('Salvar Alterações', key='-SALVAR-', button_color=(claro, escuro)), 
                sg.Button('Cancelar', key='-CANCELAR-', button_color=(claro, escuro))]
            ]
            
            window_edit = sg.Window('Editar Médico', layout_edit, modal=True, background_color=claro)
            
            editando = True
            while editando:
                event_edit, values_edit = window_edit.read()
                
                if event_edit in (sg.WIN_CLOSED, '-CANCELAR-'):
                    window_edit.close()
                    editando = False
                
                if event_edit == '-SALVAR-':
                    if not values_edit['-NOME-'].strip() or not values_edit['-ESPECIALIDADE-'].strip():
                        popup_ok('Por favor, preencha todos os campos!', title='Erro', 
                                background_color=claro, text_color=escuro)
                    else:
                        
                        nome_completo_editado = f"{values_edit['-TRATAMENTO-']} {values_edit['-NOME-'].strip()}"
                        
                        
                        disponivel = not medico_selecionado.get('ocupado', False)
                        atualizar_medico(medico_selecionado, nome_completo_editado, 
                                    values_edit['-ESPECIALIDADE-'], disponivel)
                        salvar_dados('medicos.json', dados)
                        popup_ok('Médico editado com sucesso!', title='Sucesso', 
                                background_color=claro, text_color=escuro)
                        window_edit.close()
                        editando = False
                        
                        
                        dados = carregar_dados('medicos.json')
                        medicos = dados.get('medicos', [])
                        
                        
                        filtro_atual = values.get('-SEARCH-MED-', '')
                        w['-TABLE-MEDICOS-'].update(values=build_med_rows(filtro_atual))
                        w['-DETALHES-'].update('')
                        w['-EDITAR-MED-'].update(visible=False)
                        w['-REMOVER-MED-'].update(visible=False)
                        w['-ESTAT-'].update(calcular_estatisticas())
                        medico_selecionado = None

        if event == '-REMOVER-MED-' and medico_selecionado:
            confirma = popup_sim_nao(
                f'Tem certeza que deseja remover {medico_selecionado["nome"]}?',
                title='Confirmar Remoção', background_color=claro, text_color=escuro
            )
            
            if confirma == 'Sim':
                if remover_medico_dados(medico_selecionado['id']):
                    popup_ok('Médico removido com sucesso!', title='Sucesso', 
                            background_color=claro, text_color=escuro)
                    
                   
                    dados = carregar_dados('medicos.json')
                    medicos = dados.get('medicos', [])
                    
                    
                    filtro_atual = values.get('-SEARCH-MED-', '')
                    w['-TABLE-MEDICOS-'].update(values=build_med_rows(filtro_atual))
                    w['-DETALHES-'].update('')
                    w['-EDITAR-MED-'].update(visible=False)
                    w['-REMOVER-MED-'].update(visible=False)
                    w['-ESTAT-'].update(calcular_estatisticas())
                    medico_selecionado = None
def listar_pacientes():
    _, tem_pacientes = verificar_dados_importados()
    if not tem_pacientes:
        popup_ok('Não há pacientes registados!', title='Aviso', background_color=claro, text_color=escuro)
        return

    dados = carregar_dados('pacientes.json')
    pacientes = dados.get('pacientes', [])

    headings = ['ID', 'Nome', 'Idade', 'Sexo', 'Prioridade', 'Doença']

    def prioridade_label(pr):
        np = _normalize_text(pr)
        if np in ('emergencia', 'emergência'):
            return 'Emergência'
        if np == 'alta':
            return 'Alta'
        return 'Normal'

    def build_pac_rows(filter_value='', filter_type='Nome'):
        rows = []
        nf = _normalize_text(filter_value)
        
        i = 0
        while i < len(pacientes):
            p = pacientes[i]
            match = True

            if nf:
                if filter_type == 'Nome':
                    match = nf in _normalize_text(p.get('nome', ''))
                elif filter_type == 'Prioridade':
                    prioridade = _normalize_text(p.get('prioridade', ''))
                    if nf in ('urgente', 'emergencia', 'emergência'):
                        match = prioridade in ('emergencia', 'emergência')
                    else:
                        match = nf == prioridade
                elif filter_type == 'Doença':
                    match = nf in _normalize_text(p.get('doenca', ''))

            if match:
                prioridade = prioridade_label(p.get('prioridade', 'normal'))
                rows.append([
                    p.get('id',''),
                    p.get('nome',''),
                    str(p.get('idade','')),
                    p.get('sexo','').capitalize(),
                    prioridade,
                    p.get('doenca','')
                ])
            i = i + 1
        return rows

    def calcular_estatisticas():
        total = len(pacientes)
        emergencia = 0
        alta = 0
        normal = 0
        
        j = 0
        while j < len(pacientes):
            prioridade = _normalize_text(pacientes[j].get('prioridade',''))
            if prioridade in ('emergencia', 'emergência'):
                emergencia = emergencia + 1
            elif prioridade == 'alta':
                alta = alta + 1
            else:
                normal = normal + 1
            j = j + 1
        
        return f"Total: {total}  |  Emergência: {emergencia}  |  Alta: {alta}  |  Normal: {normal}"

    left_col = sg.Column([
        [
            sg.Combo(
                ['Nome', 'Prioridade', 'Doença'],
                default_value='Nome',
                key='-SEARCH-TIPO-',
                readonly=True,
                size=(15,1)
            ),
            sg.Input('', key='-SEARCH-PAC-', size=(25,1)),
            sg.Button('Pesquisar', key='-SEARCH-PAC-BTN-', button_color=(claro, escuro)),
            sg.Button('Limpar', key='-CLEAR-PAC-', button_color=(claro, escuro))
        ],
        [sg.Table(
            values=build_pac_rows(), headings=headings, auto_size_columns=False,
            col_widths=[6,25,7,10,12,20], justification='left', num_rows=15,
            key='-TABLE-PACIENTES-', enable_events=True, row_height=28,
            background_color='white', header_background_color=claro,
            text_color=escuro, header_text_color=escuro
        )]
    ], background_color='white', pad=(6,6))

    right_col = sg.Column([
        [sg.Text('Detalhes', font=('Helvetica', 12, 'bold'), background_color='white', text_color=escuro)],
        [sg.Multiline('', size=(55,13), key='-DETALHES-PAC-', disabled=True, autoscroll=False,
                      background_color='white', text_color=escuro, font=('Courier', 10))],
        [sg.Button('Editar', key='-EDITAR-PAC-', button_color=(claro, escuro), size=(12,1), visible=False),
         sg.Button('Remover', key='-REMOVER-PAC-', button_color=(claro, escuro), size=(12,1), visible=False)],
        [sg.Text(calcular_estatisticas(), key='-ESTAT-PAC-', background_color='white', text_color=escuro, pad=(0,10), size=(55,2))]
    ], background_color='white', pad=(6,6))

    layout = [
        [sg.Text('Lista de Pacientes', font=('Helvetica', 16, 'bold'), background_color=claro, text_color=escuro, pad=(10,10))],
        [sg.Column([[left_col, sg.VerticalSeparator(), right_col]], background_color=claro, pad=(0,0))],
        [sg.Push(background_color=claro),
         sg.Button('Fechar', button_color=(claro, escuro), size=(12,1), font=('Helvetica', 10), key='-FECHAR-PAC-', pad=(10,10)),
         sg.Push(background_color=claro)]
    ]

    w = sg.Window('Pacientes', layout, modal=True, background_color=claro, size=(1150, 680), element_justification='left', finalize=True)
    
    paciente_selecionado = None

    while True:
        event, values = w.read()
        if event in (sg.WIN_CLOSED, '-FECHAR-PAC-'):
            w.close()
            return

        if event == '-SEARCH-PAC-BTN-':
            q = values.get('-SEARCH-PAC-', '')
            tipo = values.get('-SEARCH-TIPO-', 'Nome')

            w['-TABLE-PACIENTES-'].update(
                values=build_pac_rows(q, tipo)
            )

            w['-DETALHES-PAC-'].update('')
            w['-EDITAR-PAC-'].update(visible=False)
            w['-REMOVER-PAC-'].update(visible=False)
            w['-ESTAT-PAC-'].update(calcular_estatisticas())
            paciente_selecionado = None

        if event == '-CLEAR-PAC-':
            w['-SEARCH-PAC-'].update('')
            w['-SEARCH-TIPO-'].update('Nome')

            w['-TABLE-PACIENTES-'].update(
                values=build_pac_rows('', 'Nome')
            )

            w['-DETALHES-PAC-'].update('')
            w['-EDITAR-PAC-'].update(visible=False)
            w['-REMOVER-PAC-'].update(visible=False)
            w['-ESTAT-PAC-'].update(calcular_estatisticas())
            paciente_selecionado = None

        if event == '-TABLE-PACIENTES-':
            sel = values.get('-TABLE-PACIENTES-')
            if sel:
                idx = sel[0]
                filter_q = values.get('-SEARCH-PAC-', '')
                filter_type = values.get('-SEARCH-TIPO-', 'Nome')

                filtered = build_pac_rows(filter_q, filter_type)

                if idx < len(filtered):
                    row = filtered[idx]
                    pac_id = row[0]
                    
                    # Procurar paciente sem next/generator (loop while)
                    p = None
                    k = 0
                    while k < len(pacientes):
                        if str(pacientes[k].get('id','')) == str(pac_id):
                            p = pacientes[k]
                        k = k + 1
                    
                    if p:
                        paciente_selecionado = p
                        atributos = p.get('atributos', {})
                        atr_list = []
                        if atributos.get('fumador'):
                            atr_list.append('Fumador')
                        if atributos.get('consome_alcool'):
                            atr_list.append('Consome Álcool')
                        if atributos.get('cronico'):
                            atr_list.append('Doença Crónica')
                        atr_list.append(f"Ativ. Física: {atributos.get('atividade_fisica','N/A').capitalize()}")
                        linhas = [
                            f"ID: {p.get('id','')}",
                            f"Nome: {p.get('nome','')}",
                            f"Idade: {p.get('idade','')}",
                            f"Sexo: {p.get('sexo','')}",
                            f"Prioridade: {p.get('prioridade','')}",
                            f"Doença: {p.get('doenca','')}",
                            "",
                            "Atributos:",
                            ", ".join(atr_list)
                        ]
                        w['-DETALHES-PAC-'].update('\n'.join(linhas))
                        w['-EDITAR-PAC-'].update(visible=True)
                        w['-REMOVER-PAC-'].update(visible=True)
                        w['-ESTAT-PAC-'].update(calcular_estatisticas())

        if event == '-EDITAR-PAC-' and paciente_selecionado:
            
            layout_edit = [
                [sg.Text('Editar Paciente', font=('Helvetica', 14, 'bold'), background_color=claro, text_color=escuro)],
                [sg.Text(f'ID: {paciente_selecionado["id"]}', font=('Helvetica', 10), background_color=claro, text_color=escuro)],
                [sg.Text('Nome:', background_color=claro, text_color=escuro), 
                 sg.Input(default_text=paciente_selecionado['nome'], key='-NOME-', size=(30, 1))],
                [sg.Text('Idade:', background_color=claro, text_color=escuro), 
                 sg.Input(default_text=str(paciente_selecionado['idade']), key='-IDADE-', size=(30, 1))],
                [sg.Text('Sexo:', background_color=claro, text_color=escuro), 
                 sg.Combo(['masculino', 'feminino', 'outro'], default_value=paciente_selecionado['sexo'], 
                         key='-SEXO-', readonly=True)],
                [sg.Text('Doença:', background_color=claro, text_color=escuro), 
                 sg.Input(default_text=paciente_selecionado['doenca'], key='-DOENCA-', size=(30, 1))],
                [sg.Text('Prioridade:', background_color=claro, text_color=escuro), 
                 sg.Combo(['Baixa','Normal', 'Alta', 'Urgente'], default_value=paciente_selecionado['prioridade'], 
                         key='-PRIORIDADE-', readonly=True)],
                [sg.Text('Atributos:', font=('Helvetica', 10, 'bold'), background_color=claro, text_color=escuro)],
                [sg.Checkbox('Fumador', default=paciente_selecionado['atributos']['fumador'], 
                            key='-FUMADOR-', background_color=claro, text_color=escuro)],
                [sg.Checkbox('Consome Álcool', default=paciente_selecionado['atributos']['consome_alcool'], 
                            key='-ALCOOL-', background_color=claro, text_color=escuro)],
                [sg.Text('Atividade Física:', background_color=claro, text_color=escuro), 
                 sg.Combo(['baixa', 'moderada', 'alta'], 
                         default_value=paciente_selecionado['atributos']['atividade_fisica'], 
                         key='-ATIVIDADE-', readonly=True)],
                [sg.Checkbox('Doença Crónica', default=paciente_selecionado['atributos']['cronico'], 
                            key='-CRONICO-', background_color=claro, text_color=escuro)],
                [sg.Button('Salvar Alterações', key='-SALVAR-', button_color=(claro, escuro)), 
                 sg.Button('Cancelar', key='-CANCELAR-', button_color=(claro, escuro))]
            ]
            
            window_edit = sg.Window('Editar Paciente', layout_edit, modal=True, background_color=claro)
            
            editando = True
            while editando:
                event_edit, values_edit = window_edit.read()
                
                if event_edit in (sg.WIN_CLOSED, '-CANCELAR-'):
                    window_edit.close()
                    editando = False
                
                if event_edit == '-SALVAR-':
                    idade, valido = validar_idade(values_edit['-IDADE-'])
                    if not valido:
                        popup_ok('Idade deve ser um número!', title='Erro', 
                                background_color=claro, text_color=escuro)
                    
                    elif not values_edit['-NOME-'].strip():
                        popup_ok('Por favor, preencha o nome!', title='Erro', 
                                background_color=claro, text_color=escuro)
                    
                    else:
                        atualizar_paciente(
                            paciente_selecionado, values_edit['-NOME-'], idade, values_edit['-SEXO-'],
                            values_edit['-DOENCA-'], values_edit['-PRIORIDADE-'], values_edit['-FUMADOR-'],
                            values_edit['-ALCOOL-'], values_edit['-ATIVIDADE-'], values_edit['-CRONICO-']
                        )
                        salvar_dados('pacientes.json', dados)
                        popup_ok('Paciente editado com sucesso!', title='Sucesso', 
                                background_color=claro, text_color=escuro)
                        window_edit.close()
                        editando = False
                        
                        dados = carregar_dados('pacientes.json')
                        pacientes = dados.get('pacientes', [])
                        
                        filtro_atual = values.get('-SEARCH-PAC-', '')
                        w['-TABLE-PACIENTES-'].update(values=build_pac_rows(filtro_atual))
                        w['-DETALHES-PAC-'].update('')
                        w['-EDITAR-PAC-'].update(visible=False)
                        w['-REMOVER-PAC-'].update(visible=False)
                        w['-ESTAT-PAC-'].update(calcular_estatisticas())
                        paciente_selecionado = None

        if event == '-REMOVER-PAC-' and paciente_selecionado:
            confirma = popup_sim_nao(
                f'Tem certeza que deseja remover {paciente_selecionado["nome"]}?',
                title='Confirmar Remoção', background_color=claro, text_color=escuro
            )
            
            if confirma == 'Sim':
                if remover_paciente_dados(paciente_selecionado['id']):
                    popup_ok('Paciente removido com sucesso!', title='Sucesso', 
                            background_color=claro, text_color=escuro)
                    
                    dados = carregar_dados('pacientes.json')
                    pacientes = dados.get('pacientes', [])
                    
                    filtro_atual = values.get('-SEARCH-PAC-', '')
                    w['-TABLE-PACIENTES-'].update(values=build_pac_rows(filtro_atual))
                    w['-DETALHES-PAC-'].update('')
                    w['-EDITAR-PAC-'].update(visible=False)
                    w['-REMOVER-PAC-'].update(visible=False)
                    w['-ESTAT-PAC-'].update(calcular_estatisticas())
                    paciente_selecionado = None



def selecionar_medico_lista(lista_medicos):
    layout = [
        [sg.Text('Selecione o médico correto:')],
        [sg.Listbox(
            values=[f'ID: {m["id"]} | {m["nome"]} | {m["especialidade"]}' for m in lista_medicos],
            size=(50, 6),
            key='-LISTA-'
        )],
        [sg.Button('Selecionar'), sg.Button('Cancelar')]
    ]

    window = sg.Window('Selecionar Médico', layout, modal=True)
    event, values = window.read()
    window.close()

    if event == 'Selecionar' and values['-LISTA-']:
        selecionado = values['-LISTA-'][0]
        id_medico = selecionado.split('|')[0].replace('ID:', '').strip()
        return next((m for m in lista_medicos if str(m['id']) == id_medico), None)

    return None


def selecionar_paciente_lista(lista_pacientes):
    layout = [
        [sg.Text('Selecione o paciente correto:')],
        [sg.Listbox(
            values=[f'ID: {p["id"]} | {p["nome"]} | {p["doenca"]}' for p in lista_pacientes],
            size=(50, 6),
            key='-LISTA-'
        )],
        [sg.Button('Selecionar'), sg.Button('Cancelar')]
    ]

    window = sg.Window('Selecionar Paciente', layout, modal=True)
    event, values = window.read()
    window.close()

    if event == 'Selecionar' and values['-LISTA-']:
        selecionado = values['-LISTA-'][0]
        id_paciente = selecionado.split('|')[0].replace('ID:', '').strip()
        return next((p for p in lista_pacientes if str(p['id']) == id_paciente), None)

    return None






def alterar_dados():
    tem_medicos, tem_pacientes = verificar_dados_importados()
    
    if not tem_medicos and not tem_pacientes:
        sg.popup('Não há dados na base. Importe médicos ou pacientes antes de alterar.', 
                title='Aviso', background_color=claro, text_color=escuro)
        return
    
    
    coluna_medicos = [
        [sg.Text('Gestão de Médicos', font=('Helvetica', 13, 'bold'), 
                justification='center', background_color=claro, text_color=escuro, 
                expand_x=True, pad=(0,10))],
        [sg.Button('Adicionar Médico', size=(24, 3), key='-ADD-MEDICO-', 
                  button_color=(claro, escuro), pad=(0,5), font=('Helvetica', 12))],
        [sg.Button('Listar Médicos', size=(24, 3), key='-LIST-MEDICOS-', 
                  button_color=(claro, escuro), pad=(0,5), font=('Helvetica', 12))]
    ]
    
    coluna_pacientes = [
        [sg.Text('Gestão de Pacientes', font=('Helvetica', 13, 'bold'), 
                justification='center', background_color=claro, text_color=escuro, 
                expand_x=True, pad=(0,10))],
        [sg.Button('Adicionar Paciente', size=(24, 3), key='-ADD-PACIENTE-', 
                  button_color=(claro, escuro), pad=(0,5), font=('Helvetica', 12))],
        [sg.Button('Listar Pacientes', size=(24, 3), key='-LIST-PACIENTES-', 
                  button_color=(claro, escuro), pad=(0,5), font=('Helvetica', 12))]
    ]
    
    layout = [
        [sg.Text('Alteração de Dados', font=('Helvetica', 17, 'bold'), 
                justification='center', expand_x=True, background_color=claro, 
                text_color=escuro, pad=(0,15))],
        [sg.Column(coluna_medicos, element_justification='center', 
                  vertical_alignment='top', background_color=claro, expand_x=True,expand_y=True), 
         sg.VerticalSeparator(pad=(20,0)),
         sg.Column(coluna_pacientes, element_justification='center', 
                  vertical_alignment='top', background_color=claro, expand_x=True,expand_y=True)],
        [sg.VStretch(background_color=claro)],
        [sg.Push(background_color=claro),
         
         sg.Button('Voltar ao Menu', size=(18, 1), key='-VOLTAR-', 
                  button_color=(claro, escuro), pad=(0,15), font=('Helvetica', 10)),
         sg.Push(background_color=claro)]
    ]
    
    window = sg.Window('Alteração de Dados', layout, size=(800, 400), 
                      element_justification='center', background_color=claro, finalize=True)
    
    while True:
        event, values = window.read()
        
        if event in (sg.WIN_CLOSED, '-VOLTAR-'):
            window.close()
            return
        
        if event == '-ADD-MEDICO-':
            adicionar_medico()
        
        elif event == '-ADD-PACIENTE-':
            adicionar_paciente()
        
        elif event == '-LIST-MEDICOS-':
            listar_medicos()

        elif event == '-LIST-PACIENTES-':
            listar_pacientes()
        





def abrir_menu():
    window = sg.Window('Menu Principal', layout, background_color=claro, size=(700, 500), element_justification='center')

    while True:
        event, values = window.read()

        
        if event == sg.WIN_CLOSED or event is None:
            limpar_flag_importacao()  
            window.close()
            return

        if event == '-SIMULACAO-':
            tem_medicos, tem_pacientes = verificar_dados_importados()
            
            if not tem_medicos or not tem_pacientes:
                popup_ok('Erro: Deves importar os dados de Médicos e Pacientes antes de iniciar a simulação!', 
                         title='Aviso', background_color=claro, text_color=escuro)
            else:
                window.hide()
                interface_simulacao.abrir_simulacao() 
                window.un_hide()

        
        elif event == '-ALTERAR-':
            tem_medicos, tem_pacientes = verificar_dados_importados()
            
            if not tem_medicos and not tem_pacientes:
                popup_ok('Não há dados na base. Importe médicos ou pacientes antes de alterar.', 
                        title='Aviso', background_color=claro, button_color=(claro, escuro), text_color=escuro)
                continue
            
            window.hide()
            alterar_dados()
            window.un_hide()

        
        elif event == '-IMPORTAR-':
            importar_dados()

        
        elif event == '-SAIR-':
            resposta = popup_sim_nao('Tem certeza que deseja sair?', text_color=escuro, title='Confirmar Saída')
            if resposta == 'Sim':
                limpar_flag_importacao()  # Limpa o flag antes de sair
                popup_ok('Obrigado por utilizar o Sistema de Gestão Clínica!\nAté breve!', 
                        title='Agradecimento', background_color=claro, button_color=(claro, escuro), text_color=escuro)
                window.close()
                return



