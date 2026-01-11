import FreeSimpleGUI as sg
from admin import login
from interface_menu import abrir_menu
from funcoes import limpar_flag_importacao

escuro = '#2196f3'
claro = '#c3e3fd'



sg.theme_add_new('TemaClinica', {
    'BACKGROUND': claro, 'TEXT': 'black', 'INPUT': 'white', 'TEXT_INPUT': 'black',
    'SCROLL': escuro, 'BUTTON': ('white', escuro), 'PROGRESS': (escuro, claro),
    'BORDER': 1, 'SLIDER_DEPTH': 0, 'PROGRESS_DEPTH': 0,
})
sg.theme('TemaClinica')


def main():
    limpar_flag_importacao()

    autenticado = login()

    if autenticado:
        abrir_menu()
    else:
        sg.popup(
            'Acesso não autorizado.\nPrograma encerrado.',
            title='Erro de Autenticação'
        )


if __name__ == '__main__':
    main()
