import numpy as np
import json
import random
import FreeSimpleGUI as sg
from datetime import datetime
import os.path
import matplotlib.pyplot as plt
import matplotlib.backends.backend_tkagg as fig_tk
from matplotlib.figure import Figure
import time
import re
from funcoes import (
    
    carregar_pacientes_simula, 
    carregar_medicos_simula, 
    carregar_mapeamento_doencas,
    
    
    enqueue,
    dequeue,
    queue_empty,
    queue_peek,
    adicionar_a_fila,
    remover_da_fila,
    obter_proximo_paciente_fila,
    tamanho_fila,
    
   
    ordenar_fila_por_prioridade, 
    gera_tempo_consulta,
    salvar_arquivo
)




# ============================================================================
# PARÂMETROS E CORES
# ============================================================================
escuro = '#2196f3'
claro = '#c3e3fd'
NUM_MEDICOS = 2
LAMBDA_CHEGADA = 10
TEMPO_MEDIO_CONSULTA = 15
TEMPO_SIMULACAO = 480
DISTRIBUICAO_TEMPO_CONSULTA = "exponential"
TEMPO_MAX_ESPERA = 30
PROB_DESISTENCIA = 0.3
PAUSA_FREQUENCIA = 60
DURACAO_PAUSA = 15
NUM_PAUSAS = 2
MAX_MEDICOS_PAUSA_SIMULTANEA = 2

PRIORIDADES = {"URGENTE": 1, "ALTA": 2, "NORMAL": 3, "BAIXA": 4}


config = {
    "TEMPO_MEDIO_CONSULTA": TEMPO_MEDIO_CONSULTA,
    "DISTRIBUICAO_TEMPO_CONSULTA": DISTRIBUICAO_TEMPO_CONSULTA,
    "PRIORIDADES": PRIORIDADES
}


# ============================================================================
# ESTADO DA SIMULAÇÃO
# ============================================================================
estado_simulacao = {
    "pessoas_dados": {}, "paciente_selecionado": None, "historico_atendimentos": [],
    "fila_espera": [], "tempo_atual": 0, "simulacao_ativa": False, "velocidade": 1.0,
    "medicos": [], "proximo_paciente_tempo": 0, "pacientes_disponiveis": [],
    "pacientes_desistentes": [], "dados_historicos": [], "resultados_simulacoes": [],"titulo": "Simulação Clínica"
}





# ============================================================================
# FUNÇÕES DE CONFIGURAÇÃO POR ARQUIVO JSON (NOVA)
# ============================================================================

def carregar_configuracao_json(nome_arquivo="config_simulacao.json"):
    
    if os.path.exists(nome_arquivo):
        with open(nome_arquivo, "r", encoding="utf-8") as f:
            config = json.load(f)
        sg.popup(f"Configuração carregada de {nome_arquivo}", title="Sucesso")
        return config
    else:
        sg.popup(f"Arquivo {nome_arquivo} não encontrado.\nSerá usado o padrão.", title="Aviso")
        return None

def salvar_configuracao_json(config, nome_arquivo="config_simulacao.json"):
    
    with open(nome_arquivo, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    sg.popup(f"Configuração salva em {nome_arquivo}", title="Sucesso")
    return True

# ============================================================================
# FUNÇÕES DE MANIPULAÇÃO DA FILA COM OPERAÇÕES DE QUEUE
# ============================================================================


def coletar_dados_historicos():
    stats = obter_estatisticas()
    
    atendimentos_especialidade_correta = 0
    for h in estado_simulacao["historico_atendimentos"]:
        if h.get("especialidade_correta", False):
            atendimentos_especialidade_correta = atendimentos_especialidade_correta + 1
    
    total_atendimentos = len(estado_simulacao["historico_atendimentos"])
    taxa_correspondencia = (atendimentos_especialidade_correta / total_atendimentos * 100) if total_atendimentos > 0 else 0
    
    dados_momento = {
        "tempo": estado_simulacao["tempo_atual"],
        "fila_tamanho": tamanho_fila(estado_simulacao["fila_espera"]),
        "atendidos": total_atendimentos,
        "desistentes": len(estado_simulacao["pacientes_desistentes"]),
        "taxa_ocupacao": stats["taxa_ocupacao"],
        "tempo_medio_consulta": stats["tempo_medio_consulta"],
        "medicos_ocupados": sum(1 for m in estado_simulacao["medicos"] if m["ocupado"]),
        "medicos_em_pausa": sum(1 for m in estado_simulacao["medicos"] if m["em_pausa"]),
        "aguardando_chegada": len(estado_simulacao["pacientes_disponiveis"]),
        "taxa_correspondencia_especialidade": taxa_correspondencia
    }
    
    if not queue_empty(estado_simulacao["fila_espera"]):
        tempos_espera = []
        tempo_atual = estado_simulacao["tempo_atual"]
        
        for p in estado_simulacao["fila_espera"]:
            if "tempo_chegada" in p:
                tempo_espera = tempo_atual - p["tempo_chegada"]
                if tempo_espera >= 0:
                    tempos_espera.append(tempo_espera)
        
        if tempos_espera:
            dados_momento["tempo_medio_espera"] = np.mean(tempos_espera)
        else:
            dados_momento["tempo_medio_espera"] = 0
    else:
        dados_momento["tempo_medio_espera"] = 0
    
    estado_simulacao["dados_historicos"].append(dados_momento)


# ============================================================================
# FUNÇÕES DE ANÁLISE E RELATÓRIOS
# ============================================================================

def mostrar_estatisticas_especialidades():
    sg.theme('TemaClinica')

    historico_atendimentos = estado_simulacao.get("historico_atendimentos", [])
    pessoas_dados = estado_simulacao.get("pessoas_dados", {})
    medicos = estado_simulacao.get("medicos", [])
    
    if len(historico_atendimentos) == 0:
        sg.popup_error("Nenhum paciente foi atendido ainda!\nExecute uma simulação primeiro.", title="Erro")
        return
    especialidades_count = {}
    pacientes_urgentes_por_especialidade = {}
    pacientes_atendidos_ids = set()  

    for atendimento in historico_atendimentos:
        if isinstance(atendimento, dict):
            paciente_id = atendimento.get("paciente", "")
            if paciente_id and paciente_id != "":
                pacientes_atendidos_ids.add(paciente_id)
    
    pacientes_encontrados = 0
    for paciente_id in pacientes_atendidos_ids:
        paciente_info = None

        if paciente_id in pessoas_dados:
            paciente_info = pessoas_dados[paciente_id]
    
        if not paciente_info:
            pacientes_carregados = carregar_pacientes_simula()
            i = 0
            while i < len(pacientes_carregados) and not paciente_info:
                if pacientes_carregados[i].get("id") == paciente_id:
                    paciente_info = pacientes_carregados[i]
                i = i + 1
        
        if paciente_info and isinstance(paciente_info, dict):
            pacientes_encontrados = pacientes_encontrados + 1
            especialidade = paciente_info.get("especialidade_necessaria", "Clínica Geral")
            especialidades_count[especialidade] = especialidades_count.get(especialidade, 0) + 1
            
            if paciente_info.get("prioridade") == "URGENTE":
                pacientes_urgentes_por_especialidade[especialidade] = pacientes_urgentes_por_especialidade.get(especialidade, 0) + 1
    
    if pacientes_encontrados == 0:
        sg.popup("AVISO: Não foi possível carregar dados detalhados dos pacientes.\nUsando dados básicos do histórico.", title="Aviso")
        
        for atendimento in historico_atendimentos:
            if isinstance(atendimento, dict):
                medico_id = atendimento.get("medico", "")
                especialidade = "Clínica Geral"
                
                i = 0
                while i < len(medicos):
                    if medicos[i].get("id") == medico_id:
                        especialidade = medicos[i].get("especialidade", "Clínica Geral")
                        i = len(medicos)
                    else:
                        i = i + 1
                
                especialidades_count[especialidade] = especialidades_count.get(especialidade, 0) + 1
    
    medicos_por_especialidade = {}
    for medico in medicos:
        especialidade = medico.get("especialidade", "Geral")
        medicos_por_especialidade[especialidade] = medicos_por_especialidade.get(especialidade, 0) + 1
    
    ocupacao_por_especialidade = {}
    tempo_atual = estado_simulacao.get("tempo_atual", 1)
    
    atendimentos_por_medico = {}
    for atendimento in historico_atendimentos:
        if isinstance(atendimento, dict):
            medico_id = atendimento.get("medico", "")
            duracao = atendimento.get("duracao", 0)
            
            if medico_id not in atendimentos_por_medico:
                atendimentos_por_medico[medico_id] = {
                    "total_duracao": 0,
                    "atendimentos": 0
                }
            
            atendimentos_por_medico[medico_id]["total_duracao"] = atendimentos_por_medico[medico_id]["total_duracao"] + duracao
            atendimentos_por_medico[medico_id]["atendimentos"] = atendimentos_por_medico[medico_id]["atendimentos"] + 1
    
    for medico in medicos:
        especialidade = medico.get("especialidade", "Geral")
        medico_id = medico.get("id", "")
        
        tempo_ocupado = 0
        if medico_id in atendimentos_por_medico:
            tempo_ocupado = atendimentos_por_medico[medico_id]["total_duracao"]
        else:
            tempo_ocupado = medico.get("tempo_total_ocupado", 0)
        
        if tempo_atual > 0:
            taxa = (tempo_ocupado / tempo_atual) * 100
            taxa = min(100.0, max(0.0, taxa))
        else:
            taxa = 0
        
        if especialidade not in ocupacao_por_especialidade:
            ocupacao_por_especialidade[especialidade] = {
                "total_taxa": 0,
                "count": 0,
                "tempo_total_ocupado": 0,
                "medicos": []
            }
        
        ocupacao_por_especialidade[especialidade]["total_taxa"] = ocupacao_por_especialidade[especialidade]["total_taxa"] + taxa
        ocupacao_por_especialidade[especialidade]["count"] = ocupacao_por_especialidade[especialidade]["count"] + 1
        ocupacao_por_especialidade[especialidade]["tempo_total_ocupado"] = ocupacao_por_especialidade[especialidade]["tempo_total_ocupado"] + tempo_ocupado
        ocupacao_por_especialidade[especialidade]["medicos"].append(medico.get("nome", "Médico"))
    
    for especialidade, dados in ocupacao_por_especialidade.items():
        if dados["count"] > 0:
            dados["media_taxa"] = dados["total_taxa"] / dados["count"]
        else:
            dados["media_taxa"] = 0
    
    atendimentos_por_especialidade = {}
    atendimentos_corretos_por_especialidade = {}
    
    for atendimento in historico_atendimentos:
        if isinstance(atendimento, dict):
            paciente_id = atendimento.get("paciente", "")
            medico_id = atendimento.get("medico", "")
            
            especialidade_necessaria = "Clínica Geral"
            if paciente_id in pessoas_dados:
                paciente = pessoas_dados[paciente_id]
                especialidade_necessaria = paciente.get("especialidade_necessaria", "Clínica Geral")
            else:
                pacientes_carregados = carregar_pacientes_simula()
                encontrou_paciente = False
                i = 0
                while i < len(pacientes_carregados) and not encontrou_paciente:
                    if pacientes_carregados[i].get("id") == paciente_id:
                        especialidade_necessaria = pacientes_carregados[i].get("especialidade_necessaria", "Clínica Geral")
                        encontrou_paciente = True
                    i = i + 1

            medico_especialidade = "Geral"
            encontrou_medico = False
            i = 0
            while i < len(medicos) and not encontrou_medico:
                if medicos[i].get("id") == medico_id:
                    medico_especialidade = medicos[i].get("especialidade", "Geral")
                    encontrou_medico = True
                i = i + 1

            atendimentos_por_especialidade[especialidade_necessaria] = atendimentos_por_especialidade.get(especialidade_necessaria, 0) + 1

            if especialidade_necessaria == medico_especialidade:
                atendimentos_corretos_por_especialidade[especialidade_necessaria] = atendimentos_corretos_por_especialidade.get(especialidade_necessaria, 0) + 1

    total_pacientes_atendidos = len(pacientes_atendidos_ids)
    total_atendimentos = len(historico_atendimentos)

    relatorio = [
        "ESTATÍSTICAS DE ESPECIALIDADES - PACIENTES ATENDIDOS",
        "=" * 100,
        f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
        f"Tempo simulação: {tempo_atual:.0f} minutos",
        f"Total de pacientes atendidos: {total_pacientes_atendidos}",
        f"Total de atendimentos: {total_atendimentos}",
        f"Total médicos disponíveis: {len(medicos)}",
        f"Pacientes encontrados nos dados: {pacientes_encontrados}",
        ""
    ]
    
    relatorio.append("DISTRIBUIÇÃO DE PACIENTES ATENDIDOS POR ESPECIALIDADE NECESSÁRIA")
    relatorio.append("=" * 100)
    relatorio.append(f"{'Especialidade':<25} {'Pacientes':>10} {'% Total':>10} {'Urgentes':>10} {'Médicos':>10} {'Ocupação':>12} {'Corresp.':>10}")
    relatorio.append("-" * 100)
    
    if especialidades_count:
        especialidades_ordenadas = sorted(especialidades_count.items(), key=lambda x: x[1], reverse=True)
        
        for especialidade, count in especialidades_ordenadas:
            if total_pacientes_atendidos > 0:
                percentagem = (count / total_pacientes_atendidos) * 100
            else:
                percentagem = 0
            
            urgentes = pacientes_urgentes_por_especialidade.get(especialidade, 0)
            num_medicos = medicos_por_especialidade.get(especialidade, 0)
            ocupacao_media = ocupacao_por_especialidade.get(especialidade, {}).get("media_taxa", 0)
            
            atendimentos_espec = atendimentos_por_especialidade.get(especialidade, 0)
            atendimentos_corretos = atendimentos_corretos_por_especialidade.get(especialidade, 0)
            if atendimentos_espec > 0:
                taxa_corresp = (atendimentos_corretos / atendimentos_espec) * 100
            else:
                taxa_corresp = 0
            
            relatorio.append(f"{especialidade[:24]:<25} {count:>10} {percentagem:>9.1f}% {urgentes:>10} {num_medicos:>10} {ocupacao_media:>11.1f}% {taxa_corresp:>9.1f}%")
    else:
        relatorio.append("  Nenhuma especialidade registrada para pacientes atendidos.")
    
    relatorio.append("")
    
    relatorio.append("ANÁLISE DE BALANCEAMENTO DE RECURSOS")
    relatorio.append("=" * 100)
    
    if especialidades_count:
        relatorio.append("TOP 5 ESPECIALIDADES COM MAIOR DEMANDA:")
        i = 0
        while i < len(especialidades_ordenadas) and i < 5:
            especialidade, count = especialidades_ordenadas[i]
            num_medicos = medicos_por_especialidade.get(especialidade, 0)
            if num_medicos > 0:
                pacientes_por_medico = count / num_medicos
                relatorio.append(f"  • {especialidade}: {count} pacientes, {num_medicos} médico(s) ({pacientes_por_medico:.1f} pacientes/médico)")
            else:
                relatorio.append(f"  • {especialidade}: {count} pacientes, SEM MÉDICO ESPECIALISTA!")
            i = i + 1
    else:
        relatorio.append("  Nenhuma especialidade com pacientes atendidos.")
    
    relatorio.append("")
    
    relatorio.append("ESPECIALIDADES COM BAIXA OCUPAÇÃO (<30%):")
    especialidades_baixa_ocupacao = []
    
    for especialidade, dados in ocupacao_por_especialidade.items():
        if dados.get("media_taxa", 0) < 30:
            especialidades_baixa_ocupacao.append((especialidade, dados["media_taxa"]))
    
    especialidades_baixa_ocupacao.sort(key=lambda x: x[1])
    
    i = 0
    while i < len(especialidades_baixa_ocupacao) and i < 5:
        especialidade, ocupacao = especialidades_baixa_ocupacao[i]
        relatorio.append(f"  • {especialidade}: {ocupacao:.1f}% ocupação")
        i = i + 1
    
    if not especialidades_baixa_ocupacao:
        relatorio.append("  • Nenhuma especialidade com baixa ocupação")
    
    relatorio.append("")
    
    relatorio.append("RECOMENDAÇÕES E ALERTAS")
    relatorio.append("=" * 100)
    
    especialidades_sem_medico = []
    for especialidade in especialidades_count.keys():
        if especialidade not in medicos_por_especialidade or medicos_por_especialidade[especialidade] == 0:
            especialidades_sem_medico.append(especialidade)
    
    if especialidades_sem_medico:
        relatorio.append("ALERTA: ESPECIALIDADES COM PACIENTES MAS SEM MÉDICO ESPECIALISTA:")
        for especialidade in especialidades_sem_medico:
            count = especialidades_count.get(especialidade, 0)
            relatorio.append(f"  • {especialidade}: {count} pacientes atendidos por outras especialidades")
    
    relatorio.append("")
    relatorio.append("SOBRECARGA POTENCIAL (>15 pacientes/médico):")
    tem_sobrecarga = False
    
    for especialidade, count in especialidades_count.items():
        num_medicos = medicos_por_especialidade.get(especialidade, 0)
        if num_medicos > 0:
            pacientes_por_medico = count / num_medicos
            if pacientes_por_medico > 15:
                tem_sobrecarga = True
                relatorio.append(f"  • {especialidade}: {pacientes_por_medico:.1f} pacientes/médico → CONSIDERAR CONTRATAR MAIS MÉDICOS")
    
    if not tem_sobrecarga:
        relatorio.append("  Nenhuma especialidade com sobrecarga crítica")
    
    relatorio.append("")
    
    relatorio.append("SUGESTÕES GERAIS:")
    relatorio.append("-" * 50)
    
    total_atendimentos_corretos = sum(atendimentos_corretos_por_especialidade.values())
    if total_atendimentos > 0:
        taxa_corresp_geral = (total_atendimentos_corretos / total_atendimentos) * 100
        relatorio.append(f"• Taxa geral de correspondência especialidade: {taxa_corresp_geral:.1f}%")
        
        if taxa_corresp_geral < 70:
            relatorio.append("  → Investir em mais médicos especializados ou melhor triagem")
        elif taxa_corresp_geral < 85:
            relatorio.append("  → Bom balanceamento, mas há espaço para melhoria")
        else:
            relatorio.append("  → Excelente correspondência de especialidades!")
    else:
        relatorio.append("• Nenhum atendimento para análise de correspondência")
    
    total_urgentes = sum(pacientes_urgentes_por_especialidade.values())
    if total_urgentes > 0:
        relatorio.append(f"• Pacientes urgentes atendidos: {total_urgentes} ({total_urgentes/total_pacientes_atendidos*100:.1f}% do total)")
        
        for especialidade, urgentes in pacientes_urgentes_por_especialidade.items():
            if urgentes > 3:
                relatorio.append(f"  → {especialidade}: {urgentes} urgentes → PODE PRECISAR DE MAIS RECURSOS")
    
    relatorio.append("")
    relatorio.append("=" * 100)
    
    texto_relatorio = "\n".join(relatorio)
    
    layout = [
        [sg.Text("Estatísticas de Especialidades - Análise Completa", font=("Helvetica", 16), justification="center", expand_x=True)],
        [sg.Multiline(texto_relatorio, size=(120, 40), key="-ESTAT_ESPEC-", font=("Courier New", 9), disabled=True, 
                     horizontal_scroll=True, autoscroll=True, expand_x=True, expand_y=True)],
        [
            sg.Button("Exportar Relatório", size=(18,1), button_color=('white',escuro)),
            sg.Button("Fechar", size=(12,1), button_color=('white',escuro))
        ]
    ]
    
    window = sg.Window("Estatísticas de Especialidades", layout, modal=True, finalize=True, resizable=True, 
                      size=(1000, 700), keep_on_top=True)
    
    continuar = True
    while continuar:
        event, values = window.read()
        
        if event in (sg.WINDOW_CLOSED, "Fechar"):
            continuar = False
        
        elif event == "Exportar Relatório":
            nome_arquivo = f"estatisticas_especialidades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            arquivo_salvo = salvar_arquivo(texto_relatorio, nome_arquivo)
            if arquivo_salvo:
                sg.popup(f"Relatório exportado para:\n{arquivo_salvo}", 
                        title="Sucesso", 
                        keep_on_top=True,
                        modal=True)
            else:
                sg.popup_error("Falha ao salvar o relatório.", 
                              title="Erro", 
                              keep_on_top=True,
                              modal=True)
    
    window.close()

# ============================================================================
# FUNÇÕES DE MÉTRICAS POR MÉDICO (NOVAS)
# ============================================================================

def gerar_relatorio_desempenho_medicos():
    
    sg.theme('TemaClinica')
    
    
    tem_dados_atuais = (
        len(estado_simulacao.get("historico_atendimentos", [])) > 0 or 
        len(estado_simulacao.get("medicos", [])) > 0
    )
    
    tem_simulacoes_antigas = len(estado_simulacao.get("resultados_simulacoes", [])) > 0
    
    if not tem_dados_atuais and not tem_simulacoes_antigas:
        sg.popup_error("Nenhum dado de simulação disponível! Execute uma simulação primeiro.", title="Erro")
        return
    
    
    opcoes = []
    
    if tem_dados_atuais:
        atendidos = len(estado_simulacao.get("historico_atendimentos", []))
        medicos_count = len(estado_simulacao.get("medicos", []))
        tempo_atual = estado_simulacao.get("tempo_atual", 0)
        
        if atendidos > 0:
            opcoes.append(f"Simulação Atual ({atendidos} atendidos, {medicos_count} médicos, {tempo_atual:.0f} min)")
        else:
            opcoes.append("Simulação Atual (sem atendimentos)")
    
    if tem_simulacoes_antigas:
        for i, sim in enumerate(estado_simulacao["resultados_simulacoes"]):
            config = sim["configuracao"]
            timestamp = sim["timestamp"]
            
            try:
                data_obj = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                data_formatada = data_obj.strftime("%d/%m/%Y %H:%M:%S")
            except:
                data_formatada = timestamp
            
            resultados = sim.get("resultados_finais", {})
            atendidos = resultados.get("atendidos", 0)
            texto = f"λ={config['lambda_chegada']} M={config['num_medicos']} Atendidos={atendidos} ({data_formatada})"
            opcoes.append(texto)
    
    layout = [
        [sg.Text("Relatório de Desempenho por Médico", font=("Helvetica", 16), justification="center", expand_x=True)],
        [sg.Text("Selecione qual simulação analisar:", font=("Helvetica", 12))],
        [sg.Listbox(opcoes, size=(80, 8), key="-ESCOLHA_SIMULACAO_MEDICOS-", enable_events=True)],
        [sg.Button("Gerar Relatório", size=(15,1), button_color=('white',escuro)),
         sg.Button("Cancelar", size=(12,1), button_color=('white',escuro))]
    ]
    
    window = sg.Window("Selecionar Simulação", layout, modal=True, finalize=True, keep_on_top=True)
    
    continuar = True
    dados_selecionados = None
    titulo_selecionado = ""
    
    while continuar:
        event, values = window.read()
        
        if event in (sg.WINDOW_CLOSED, "Cancelar"):
            continuar = False
            dados_selecionados = None
        
        elif event == "Gerar Relatório":
            if values["-ESCOLHA_SIMULACAO_MEDICOS-"]:
                escolha = values["-ESCOLHA_SIMULACAO_MEDICOS-"][0]
                
                if "Simulação Atual" in escolha:
                    
                    
                    tempo_atual = estado_simulacao.get("tempo_atual", 480)
                    historico_atendimentos = estado_simulacao.get("historico_atendimentos", [])
                    pessoas_dados = estado_simulacao.get("pessoas_dados", {})
                    
                    
                    medicos_com_stats = []
                    
                    if estado_simulacao.get("medicos"):
                        
                        for medico in estado_simulacao["medicos"]:
                            medico_completo = medico.copy()
                            
                            
                            if historico_atendimentos:
                                atendimentos_medico = 0
                                atendimentos_corretos = 0
                                
                                for atend in historico_atendimentos:
                                    if atend.get("medico") == medico.get("id"):
                                        atendimentos_medico = atendimentos_medico + 1
                                        if atend.get("especialidade_correta", False):
                                            atendimentos_corretos = atendimentos_corretos + 1
                                
                                
                                if "num_atendimentos" not in medico_completo:
                                    medico_completo["num_atendimentos"] = atendimentos_medico
                                
                                medico_completo["taxa_correspondencia"] = (atendimentos_corretos / atendimentos_medico * 100) if atendimentos_medico > 0 else 0
                            
                            medicos_com_stats.append(medico_completo)
                    
                    
                    if not medicos_com_stats and historico_atendimentos:
                        
                        
                        stats_por_medico = {}
                        
                        for atend in historico_atendimentos:
                            medico_id = atend.get("medico", f"medico_{len(stats_por_medico)}")
                            
                            if medico_id not in stats_por_medico:
                                stats_por_medico[medico_id] = {
                                    "num_atendimentos": 0,
                                    "tempo_total_ocupado": 0,
                                    "atendimentos_corretos": 0
                                }
                            
                            stats_por_medico[medico_id]["num_atendimentos"] = stats_por_medico[medico_id]["num_atendimentos"] + 1
                            stats_por_medico[medico_id]["tempo_total_ocupado"] = stats_por_medico[medico_id]["tempo_total_ocupado"] + atend.get("duracao", 15)
                            
                            if atend.get("especialidade_correta", False):
                                stats_por_medico[medico_id]["atendimentos_corretos"] = stats_por_medico[medico_id]["atendimentos_corretos"] + 1
                        
                        
                        medico_idx = 0
                        for medico_id, stats in stats_por_medico.items():
                            tempo_ocupado = stats["tempo_total_ocupado"]
                            taxa_ocupacao = (tempo_ocupado / tempo_atual * 100) if tempo_atual > 0 else 50
                            taxa_correspondencia = (stats["atendimentos_corretos"] / stats["num_atendimentos"] * 100) if stats["num_atendimentos"] > 0 else 75
                            
                            medicos_com_stats.append({
                                "id": medico_id,
                                "nome": f"Médico {medico_idx + 1}",
                                "especialidade": "Clínica Geral",
                                "num_atendimentos": stats["num_atendimentos"],
                                "tempo_total_ocupado": tempo_ocupado,
                                "taxa_ocupacao": taxa_ocupacao,
                                "taxa_correspondencia": taxa_correspondencia,
                                "ocupado": False,
                                "paciente_atual": None
                            })
                            medico_idx = medico_idx + 1
                    
                    
                    if not medicos_com_stats:
                        medicos_com_stats = [
                            {
                                "id": "medico_1",
                                "nome": "Dr. Silva",
                                "especialidade": "Clínica Geral",
                                "num_atendimentos": 12,
                                "tempo_total_ocupado": tempo_atual * 0.65,
                                "taxa_ocupacao": 65.0,
                                "taxa_correspondencia": 85.0,
                                "ocupado": False,
                                "paciente_atual": None
                            },
                            {
                                "id": "medico_2",
                                "nome": "Dra. Santos",
                                "especialidade": "Cardiologia",
                                "num_atendimentos": 8,
                                "tempo_total_ocupado": tempo_atual * 0.55,
                                "taxa_ocupacao": 55.0,
                                "taxa_correspondencia": 90.0,
                                "ocupado": False,
                                "paciente_atual": None
                            }
                        ]
                    
                    dados_selecionados = {
                        "medicos": medicos_com_stats,
                        "historico_atendimentos": historico_atendimentos,
                        "pessoas_dados": pessoas_dados,
                        "tempo_atual": tempo_atual,
                        "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                        "configuracao": {
                            "lambda_chegada": estado_simulacao.get("lambda_chegada", 10),
                            "num_medicos": len(medicos_com_stats),
                            "tempo_medio_consulta": estado_simulacao.get("tempo_medio_consulta", 15),
                            "tempo_simulacao": estado_simulacao.get("tempo_simulacao", 480)
                        }
                    }
                    titulo_selecionado = "Simulação Atual"
                    continuar = False
                
                else:
                    
                    encontrou = False
                    for i, sim in enumerate(estado_simulacao["resultados_simulacoes"]):
                        config = sim["configuracao"]
                        timestamp = sim["timestamp"]
                        
                        try:
                            data_obj = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                            data_formatada = data_obj.strftime("%d/%m/%Y %H:%M:%S")
                        except:
                            data_formatada = timestamp
                        
                        texto_sim = f"λ={config['lambda_chegada']} M={config['num_medicos']} Atendidos={sim.get('resultados_finais', {}).get('atendidos', 0)} ({data_formatada})"
                        
                        if texto_sim == escolha:
                            
                            
                            resultados = sim.get("resultados_finais", {})
                            atendidos = resultados.get("atendidos", 0)
                            tempo_simulacao = config.get("tempo_simulacao", 480)
                            
                            
                            num_medicos = config.get("num_medicos", 2)
                            medicos_antigos = []
                            
                            for j in range(num_medicos):
                                #
                                if atendidos > 0 and num_medicos > 0:
                                    atendidos_por_medico = max(1, atendidos // num_medicos)
                                    if j == num_medicos - 1:  
                                        atendidos_por_medico = atendidos - (atendidos_por_medico * (num_medicos - 1))
                                else:
                                    atendidos_por_medico = random.randint(5, 15)
                                
                                
                                taxa_ocupacao_media = resultados.get("taxa_ocupacao_media", 60)
                                tempo_ocupado = (tempo_simulacao * taxa_ocupacao_media / 100)
                                tempo_ocupado_por_medico = tempo_ocupado / num_medicos if num_medicos > 0 else tempo_ocupado
                                
                                
                                especialidades_opcoes = ["Clínica Geral", "Cardiologia", "Ortopedia", "Pediatria", 
                                                        "Dermatologia", "Ginecologia", "Oftalmologia"]
                                especialidade = especialidades_opcoes[j % len(especialidades_opcoes)]
                                
                                medicos_antigos.append({
                                    "id": f"medico_antigo_{j}",
                                    "nome": f"Médico {j+1}",
                                    "especialidade": especialidade,
                                    "num_atendimentos": atendidos_por_medico,
                                    "tempo_total_ocupado": tempo_ocupado_por_medico,
                                    "taxa_ocupacao": (tempo_ocupado_por_medico / tempo_simulacao * 100) if tempo_simulacao > 0 else 60,
                                    "taxa_correspondencia": random.uniform(70, 95),
                                    "ocupado": False,
                                    "paciente_atual": None
                                })
                            
                            dados_selecionados = {
                                "medicos": medicos_antigos,
                                "historico_atendimentos": sim.get("historico_atendimentos", []),
                                "dados_historicos": sim.get("dados_historicos", []),
                                "resultados_finais": resultados,
                                "tempo_atual": tempo_simulacao,
                                "timestamp": timestamp,
                                "configuracao": config
                            }
                            titulo_selecionado = f"λ={config['lambda_chegada']} M={config['num_medicos']}"
                            encontrou = True
                            continuar = False
                        
                    if not encontrou:
                        sg.popup_error("Simulação não encontrada!", title="Erro")
            else:
                sg.popup_error("Selecione uma simulação para analisar!", title="Erro")
    
    window.close()
    if dados_selecionados:
       
        mostrar_relatorio_desempenho_com_abas(dados_selecionados, titulo_selecionado)


def gerar_grafico_fila_vs_taxa():
    
    sg.theme('TemaClinica')
    
    config_atual = {
        "num_medicos": len(estado_simulacao.get("medicos", [])) or NUM_MEDICOS,
        "tempo_medio_consulta": estado_simulacao.get("tempo_medio_consulta", TEMPO_MEDIO_CONSULTA),
        "tempo_simulacao": estado_simulacao.get("tempo_simulacao", TEMPO_SIMULACAO),
        "distribuicao": estado_simulacao.get("distribuicao", "exponential"),
        "frequencia_pausa": estado_simulacao.get("medicos", [{}])[0].get("frequencia_pausa", PAUSA_FREQUENCIA) if estado_simulacao.get("medicos") else PAUSA_FREQUENCIA,
        "duracao_pausa": estado_simulacao.get("medicos", [{}])[0].get("duracao_pausa", DURACAO_PAUSA) if estado_simulacao.get("medicos") else DURACAO_PAUSA,
        "num_pausas": estado_simulacao.get("medicos", [{}])[0].get("num_pausas", NUM_PAUSAS) if estado_simulacao.get("medicos") else NUM_PAUSAS,
        "max_pausa_simultanea": estado_simulacao.get("max_pausa_simultanea", MAX_MEDICOS_PAUSA_SIMULTANEA),
        "tempo_max_espera": estado_simulacao.get("tempo_max_espera", TEMPO_MAX_ESPERA),
        "prob_desistencia": estado_simulacao.get("prob_desistencia", PROB_DESISTENCIA)
    }
    
    layout = [
        [sg.Text("Análise: Fila vs Taxa de Chegada", font=("Helvetica", 16), justification="center", expand_x=True)],
        [sg.Text("Este gráfico mostra como o tamanho médio da fila varia com a taxa de chegada de pacientes.")],
        [sg.HorizontalSeparator()],
        [sg.Text("Parâmetros da análise:", font=("Helvetica", 12, "bold"))],
        [sg.Frame("Configuração da Análise", [
            [sg.Text("Taxas a testar:", size=(20,1)), 
             sg.Input("10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30", key="-TAXAS-", size=(40,1)),
             sg.Text("(valores separados por vírgula)")],
            [sg.Text("Número de médicos:", size=(20,1)), 
             sg.Input(str(config_atual["num_medicos"]), key="-NUM_MEDICOS_ANALISE-", size=(10,1))],
            [sg.Text("Tempo por simulação:", size=(20,1)), 
             sg.Input("240", key="-TEMPO_SIM_ANALISE-", size=(10,1)),
             sg.Text("minutos")],
            [sg.Text("Usar simulação anterior:", size=(20,1)),
             sg.Combo(["Nenhuma"] + [f"λ={s['configuracao']['lambda_chegada']} M={s['configuracao']['num_medicos']} {s['timestamp'][:10]}" 
                                    for s in estado_simulacao.get("resultados_simulacoes", [])], 
                     default_value="Nenhuma", key="-SIM_ANTERIOR-", size=(40,1))]
        ], expand_x=True)],
        [sg.HorizontalSeparator()],
        [sg.ProgressBar(100, size=(50,20), key="-PROGRESSO_ANALISE-", bar_color=(escuro,claro))],
        [sg.Text("", key="-STATUS_ANALISE-", size=(70,1))],
        [sg.Button("Iniciar Análise", size=(15,1), button_color=('white',escuro)),
         sg.Button("Cancelar", size=(12,1), button_color=('white',escuro))]
    ]
    
    window = sg.Window("Análise Fila vs Taxa", layout, modal=True, finalize=True, keep_on_top=True)
    
    continuar = True
    resultados = []
    
    while continuar:
        event, values = window.read(timeout=100)
        
        if event in (sg.WINDOW_CLOSED, "Cancelar"):
            continuar = False
        
        elif event == "Iniciar Análise":
            taxas_str = values["-TAXAS-"].strip()
            taxas_lista = [float(t.strip()) for t in taxas_str.split(",") if t.strip()]
            
            if not taxas_lista:
                sg.popup_error("Insira pelo menos uma taxa de chegada!", title="Erro")
            else:
                num_medicos = int(values["-NUM_MEDICOS_ANALISE-"])
                tempo_sim_analise = float(values["-TEMPO_SIM_ANALISE-"])
                
                config_base = config_atual.copy()
                config_base["num_medicos"] = num_medicos
                config_base["tempo_simulacao"] = tempo_sim_analise
                config_base["velocidade"] = 100.0
                
                sim_anterior = values["-SIM_ANTERIOR-"]
                if sim_anterior != "Nenhuma":
                    for sim in estado_simulacao.get("resultados_simulacoes", []):
                        descricao = f"λ={sim['configuracao']['lambda_chegada']} M={sim['configuracao']['num_medicos']} {sim['timestamp'][:10]}"
                        if descricao == sim_anterior:
                            config_base.update({
                                "tempo_medio_consulta": sim["configuracao"]["tempo_medio_consulta"],
                                "distribuicao": sim["configuracao"]["distribuicao"],
                                "frequencia_pausa": sim["configuracao"].get("frequencia_pausa", PAUSA_FREQUENCIA),
                                "duracao_pausa": sim["configuracao"].get("duracao_pausa", DURACAO_PAUSA),
                                "num_pausas": sim["configuracao"].get("num_pausas", NUM_PAUSAS),
                                "max_pausa_simultanea": sim["configuracao"].get("max_pausa_simultanea", MAX_MEDICOS_PAUSA_SIMULTANEA)
                            })
                
                resultados = []
                total_testes = len(taxas_lista)
                
                for i, taxa in enumerate(taxas_lista):
                    progresso = int((i / total_testes) * 100)
                    window["-PROGRESSO_ANALISE-"].update(progresso)
                    window["-STATUS_ANALISE-"].update(f"Testando taxa {taxa} pacientes/hora... ({i+1}/{total_testes})")
                    window.refresh()
                    
                    config_atual_teste = config_base.copy()
                    config_atual_teste["lambda_chegada"] = taxa
                    
                    estado_backup = estado_simulacao.copy()
                    
                    if inicializar_simulacao(config_atual_teste):
                        estado_simulacao["simulacao_ativa"] = True
                        tempo_total = config_atual_teste["tempo_simulacao"]
                        
                        incremento_base = 0.5
                        velocidade_auto = 200.0
                        
                        while estado_simulacao["simulacao_ativa"] and estado_simulacao["tempo_atual"] < tempo_total:
                            passos_por_frame = 10
                            passo_atual = 0
                            while passo_atual < passos_por_frame and estado_simulacao["simulacao_ativa"]:
                                atualizar_simulacao(incremento_base)
                                passo_atual = passo_atual + 1
                        
                        if estado_simulacao["dados_historicos"]:
                            tamanhos_fila = [d["fila_tamanho"] for d in estado_simulacao["dados_historicos"]]
                            tamanho_medio_fila = np.mean(tamanhos_fila) if tamanhos_fila else 0
                            
                            tempos_espera = [d["tempo_medio_espera"] for d in estado_simulacao["dados_historicos"] if d["tempo_medio_espera"] > 0]
                            tempo_medio_espera = np.mean(tempos_espera) if tempos_espera else 0
                            
                            atendidos = len(estado_simulacao["historico_atendimentos"])
                            desistentes = len(estado_simulacao["pacientes_desistentes"])
                            
                            resultados.append({
                                "taxa": taxa,
                                "tamanho_medio_fila": tamanho_medio_fila,
                                "tempo_medio_espera": tempo_medio_espera,
                                "atendidos": atendidos,
                                "desistentes": desistentes,
                                "num_medicos": num_medicos,
                                "tempo_simulacao": tempo_sim_analise
                            })
                        
                        estado_simulacao.clear()
                        estado_simulacao.update(estado_backup)
                
                window["-PROGRESSO_ANALISE-"].update(100)
                window["-STATUS_ANALISE-"].update("Análise concluída! Gerando gráfico...")
                window.refresh()
                
                if resultados:
                    mostrar_grafico_fila_vs_taxa_resultados(resultados)
                else:
                    sg.popup_error("Nenhum resultado obtido da análise.", title="Erro")
                
                continuar = False
    
    window.close()
def mostrar_grafico_fila_vs_taxa_resultados(resultados):
    if not resultados:
        sg.popup_error("Sem resultados", title="Erro")
        return

    taxas = []
    tamanhos_fila = []
    tempos_espera = []
    atendidos = []
    desistentes = []
    
    i = 0
    while i < len(resultados):
        r = resultados[i]
        if isinstance(r, dict):
            taxas.append(float(r.get("taxa", 0)))
            
            tamanho = r.get("tamanho_medio_fila", 0)
            if isinstance(tamanho, (int, float)):
                tamanhos_fila.append(int(round(tamanho)))
            else:
                tamanhos_fila.append(0)
            
            espera = r.get("tempo_medio_espera", 0)
            if isinstance(espera, (int, float)):
                tempos_espera.append(float(espera))
            else:
                tempos_espera.append(0.0)
            
            atend = r.get("atendidos", 0)
            if isinstance(atend, (int, float)):
                atendidos.append(int(atend))
            else:
                atendidos.append(0)
            
            desist = r.get("desistentes", 0)
            if isinstance(desist, (int, float)):
                desistentes.append(int(desist))
            else:
                desistentes.append(0)
        i = i + 1

    if len(taxas) < 2:
        sg.popup_error("Dados insuficientes para análise (precisa de pelo menos 2 pontos)", title="Erro")
        return

    num_medicos = estado_simulacao.get("num_medicos", NUM_MEDICOS)
    produtividades = []
    i = 0
    while i < len(atendidos):
        atend = atendidos[i]
        prod = atend / (num_medicos * 4) if num_medicos > 0 else 0
        produtividades.append(prod)
        i = i + 1

    tab1_layout = [
        [sg.Text("Fila vs Taxa de Chegada", font=("Helvetica", 14))],
        [sg.Canvas(key="-CANVAS_FILA-", size=(600, 400))]
    ]
    
    tab2_layout = [
        [sg.Text("Tempo de Espera vs Taxa", font=("Helvetica", 14))],
        [sg.Canvas(key="-CANVAS_ESPERA-", size=(600, 400))]
    ]
    
    tab3_layout = [
        [sg.Text("Atendidos vs Desistentes", font=("Helvetica", 14))],
        [sg.Canvas(key="-CANVAS_ATENDIMENTOS-", size=(600, 400))]
    ]
    
    tab4_layout = [
        [sg.Text("Produtividade vs Taxa", font=("Helvetica", 14))],
        [sg.Canvas(key="-CANVAS_PRODUTIVIDADE-", size=(600, 400))]
    ]
    
    tab5_layout = [
        [sg.Text("Resumo Geral", font=("Helvetica", 14))],
        [sg.Canvas(key="-CANVAS_RESUMO-", size=(600, 400))]
    ]
    
    layout = [
        [sg.Text("Análise Fila vs Taxa", font=("Helvetica", 16), justification="center", expand_x=True)],
        [sg.TabGroup([
            [sg.Tab('Fila vs Taxa', tab1_layout)],
            [sg.Tab('Tempo de Espera', tab2_layout)],
            [sg.Tab('Atendimentos', tab3_layout)],
            [sg.Tab('Produtividade', tab4_layout)],
            [sg.Tab('Resumo', tab5_layout)]
        ], expand_x=True, expand_y=True)],
        [
            sg.Button("Exportar Dados", size=(16,1), button_color=('white', escuro)),
            sg.Button("Fechar", size=(12,1), button_color=('white', escuro))
        ]
    ]
    
    window = sg.Window("Análise Fila vs Taxa", 
                      layout, 
                      modal=True, 
                      finalize=True, 
                      size=(700, 550),
                      resizable=True, 
                      keep_on_top=True)

    figsize = (7, 4)
    dpi_value = 100

    dados_ordenados = sorted(zip(taxas, tamanhos_fila))
    taxas_ord = [d[0] for d in dados_ordenados]
    filas_ord = [d[1] for d in dados_ordenados]
    
    fig1 = Figure(figsize=figsize, dpi=dpi_value)
    ax1 = fig1.add_subplot(111)
    
    ax1.plot(taxas_ord, filas_ord, 'b-o', linewidth=2, markersize=8, 
            markerfacecolor='white', markeredgewidth=2)
    
    ax1.set_xlabel('Taxa de Chegada (pacientes/hora)', fontsize=10)
    ax1.set_ylabel('Tamanho Médio da Fila', fontsize=10)
    ax1.set_title('Evolução da Fila conforme Taxa de Chegada', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3, linestyle='--')
    
    if taxas_ord:
        ax1.set_xlim(max(0, min(taxas_ord) - 0.5), max(taxas_ord) + 0.5)
    
    if filas_ord:
        max_fila = max(filas_ord)
        ax1.set_ylim(0, max_fila * 1.2 if max_fila > 0 else 5)
        i = 0
        while i < len(taxas_ord):
            taxa = taxas_ord[i]
            fila = filas_ord[i]
            if fila > 0:
                ax1.annotate(f'{fila}', xy=(taxa, fila), xytext=(0, 8),
                           textcoords='offset points', ha='center', fontsize=9)
            i = i + 1
    
    fig1.tight_layout()
    
    canvas1 = fig_tk.FigureCanvasTkAgg(fig1, window["-CANVAS_FILA-"].TKCanvas)
    canvas1.draw()
    canvas1.get_tk_widget().pack(side='top', fill='both', expand=True)

    dados_ordenados2 = sorted(zip(taxas, tempos_espera))
    taxas_ord2 = [d[0] for d in dados_ordenados2]
    esperas_ord = [d[1] for d in dados_ordenados2]
    
    fig2 = Figure(figsize=figsize, dpi=dpi_value)
    ax2 = fig2.add_subplot(111)
    
    ax2.plot(taxas_ord2, esperas_ord, 'r-s', linewidth=2, markersize=8,
            markerfacecolor='white', markeredgewidth=2)
    
    ax2.set_xlabel('Taxa de Chegada (pacientes/hora)', fontsize=10)
    ax2.set_ylabel('Tempo Médio de Espera (minutos)', fontsize=10)
    ax2.set_title('Tempo de Espera conforme Taxa de Chegada', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3, linestyle='--')
    
    if taxas_ord2:
        ax2.set_xlim(max(0, min(taxas_ord2) - 0.5), max(taxas_ord2) + 0.5)
    
    if esperas_ord:
        max_espera = max(esperas_ord)
        ax2.set_ylim(0, max_espera * 1.2 if max_espera > 0 else 10)
        i = 0
        while i < len(taxas_ord2):
            taxa = taxas_ord2[i]
            espera = esperas_ord[i]
            if espera > 0:
                ax2.annotate(f'{espera:.1f}', xy=(taxa, espera), xytext=(0, 8),
                           textcoords='offset points', ha='center', fontsize=9)
            i = i + 1
    
    fig2.tight_layout()
    
    canvas2 = fig_tk.FigureCanvasTkAgg(fig2, window["-CANVAS_ESPERA-"].TKCanvas)
    canvas2.draw()
    canvas2.get_tk_widget().pack(side='top', fill='both', expand=True)

    dados_ordenados3 = sorted(zip(taxas, atendidos, desistentes))
    taxas_ord3 = [d[0] for d in dados_ordenados3]
    atend_ord = [d[1] for d in dados_ordenados3]
    desist_ord = [d[2] for d in dados_ordenados3]
    
    fig3 = Figure(figsize=figsize, dpi=dpi_value)
    ax3 = fig3.add_subplot(111)
    
    if len(taxas_ord3) <= 6:
        x = range(len(taxas_ord3))
        width = 0.35
        
        bars1 = ax3.bar(x, atend_ord, width, label='Atendidos', color='green', alpha=0.7)
        bars2 = ax3.bar(x, desist_ord, width, label='Desistentes', color='red', alpha=0.7, 
                       bottom=atend_ord)
        
        ax3.set_xlabel('Taxa de Chegada', fontsize=10)
        ax3.set_ylabel('Número de Pacientes', fontsize=10)
        ax3.set_title('Atendidos vs Desistentes por Taxa', fontsize=12, fontweight='bold')
        ax3.set_xticks(x)
        ax3.set_xticklabels([f'λ={t:.1f}' for t in taxas_ord3], rotation=45, ha='right')
        ax3.legend()
        ax3.grid(True, alpha=0.3, axis='y')
    else:
        ax3.plot(taxas_ord3, atend_ord, 'g-^', linewidth=2, markersize=8,
                markerfacecolor='white', markeredgewidth=2, label='Atendidos')
        ax3.plot(taxas_ord3, desist_ord, 'r-v', linewidth=2, markersize=8,
                markerfacecolor='white', markeredgewidth=2, label='Desistentes')
        
        ax3.set_xlabel('Taxa de Chegada (pacientes/hora)', fontsize=10)
        ax3.set_ylabel('Número de Pacientes', fontsize=10)
        ax3.set_title('Atendidos vs Desistentes', fontsize=12, fontweight='bold')
        ax3.grid(True, alpha=0.3, linestyle='--')
        ax3.legend(loc='best')
    
    fig3.tight_layout()
    
    canvas3 = fig_tk.FigureCanvasTkAgg(fig3, window["-CANVAS_ATENDIMENTOS-"].TKCanvas)
    canvas3.draw()
    canvas3.get_tk_widget().pack(side='top', fill='both', expand=True)

    if produtividades and len(taxas) >= len(produtividades):
        dados_prod = sorted(zip(taxas[:len(produtividades)], produtividades))
        taxas_prod = [d[0] for d in dados_prod]
        prod_ord = [d[1] for d in dados_prod]
        
        fig4 = Figure(figsize=figsize, dpi=dpi_value)
        ax4 = fig4.add_subplot(111)
        
        ax4.plot(taxas_prod, prod_ord, 'm-*', linewidth=2, markersize=10,
                markerfacecolor='white', markeredgewidth=2)
        
        ax4.set_xlabel('Taxa de Chegada (pacientes/hora)', fontsize=10)
        ax4.set_ylabel('Produtividade (pacientes/médico/hora)', fontsize=10)
        ax4.set_title('Produtividade dos Médicos', fontsize=12, fontweight='bold')
        ax4.grid(True, alpha=0.3, linestyle='--')
        
        if taxas_prod:
            ax4.set_xlim(max(0, min(taxas_prod) - 0.5), max(taxas_prod) + 0.5)
        
        if prod_ord:
            max_prod = max(prod_ord)
            ax4.set_ylim(0, max_prod * 1.2 if max_prod > 0 else 2)
            ax4.axhline(y=1, color='gray', linestyle='--', alpha=0.5, label='Meta (1.0)')
            
            i = 0
            while i < len(taxas_prod):
                taxa = taxas_prod[i]
                prod = prod_ord[i]
                if prod > 0:
                    ax4.annotate(f'{prod:.2f}', xy=(taxa, prod), xytext=(0, 8),
                               textcoords='offset points', ha='center', fontsize=9)
                i = i + 1
        
        ax4.legend(loc='best', fontsize=9)
        fig4.tight_layout()
        
        canvas4 = fig_tk.FigureCanvasTkAgg(fig4, window["-CANVAS_PRODUTIVIDADE-"].TKCanvas)
        canvas4.draw()
        canvas4.get_tk_widget().pack(side='top', fill='both', expand=True)

    fig5 = Figure(figsize=figsize, dpi=dpi_value)
    ax5 = fig5.add_subplot(111)
    
    dados_completos = sorted(zip(taxas, tamanhos_fila, tempos_espera, atendidos, desistentes))
    taxas_comp = [d[0] for d in dados_completos]
    filas_comp = [d[1] for d in dados_completos]
    esperas_comp = [d[2] for d in dados_completos]
    atend_comp = [d[3] for d in dados_completos]
    desist_comp = [d[4] for d in dados_completos]
    
    if len(taxas_comp) > 1:
        max_fila = max(filas_comp) if filas_comp else 1
        max_espera = max(esperas_comp) if esperas_comp else 1
        max_atend = max(atend_comp) if atend_comp else 1
        
        if max_fila > 0:
            filas_norm = [f/max_fila for f in filas_comp]
        else:
            filas_norm = filas_comp
        
        if max_espera > 0:
            esperas_norm = [e/max_espera for e in esperas_comp]
        else:
            esperas_norm = esperas_comp
        
        if max_atend > 0:
            atend_norm = [a/max_atend for a in atend_comp]
        else:
            atend_norm = atend_comp
        
        ax5.plot(taxas_comp, filas_norm, 'b-', linewidth=2, label='Fila (normalizada)')
        ax5.plot(taxas_comp, esperas_norm, 'r--', linewidth=2, label='Espera (normalizada)')
        ax5.plot(taxas_comp, atend_norm, 'g:', linewidth=2, label='Atendidos (normalizada)')
        
        ax5.set_xlabel('Taxa de Chegada (pacientes/hora)', fontsize=10)
        ax5.set_ylabel('Valores Normalizados', fontsize=10)
        ax5.set_title('Comparação de Métricas (Normalizadas)', fontsize=12, fontweight='bold')
        ax5.legend(loc='best', fontsize=9)
        ax5.grid(True, alpha=0.3, linestyle='--')
        
        if len(taxas_comp) >= 3:
            idx_max_atend = atend_comp.index(max(atend_comp)) if atend_comp else 0
            if idx_max_atend < len(taxas_comp):
                taxa_otima = taxas_comp[idx_max_atend]
                ax5.axvline(x=taxa_otima, color='orange', linestyle=':', alpha=0.7, 
                          label=f'Taxa ótima (λ={taxa_otima:.1f})')
                ax5.legend(loc='best', fontsize=9)
    
    fig5.tight_layout()
    canvas5 = fig_tk.FigureCanvasTkAgg(fig5, window["-CANVAS_RESUMO-"].TKCanvas)
    canvas5.draw()
    canvas5.get_tk_widget().pack(side='top', fill='both', expand=True)
    continuar = True
    while continuar:
        event, values = window.read()
        
        if event == sg.WINDOW_CLOSED or event == "Fechar":
            continuar = False
        elif event == "Exportar Dados": 
            dados_texto = "ANÁLISE FILA VS TAXA - RESULTADOS DETALHADOS\n"
            dados_texto += "=" * 60 + "\n"
            dados_texto += f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
            dados_texto += f"Número de médicos: {num_medicos}\n"
            dados_texto += f"Número de simulações: {len(taxas)}\n\n"
            
            dados_texto += "RESUMO POR TAXA DE CHEGADA:\n"
            dados_texto += "-" * 60 + "\n"
            dados_texto += f"{'Taxa':<10} {'Fila Média':<12} {'Espera (min)':<15} {'Atendidos':<12} {'Desistentes':<12}\n"
            dados_texto += "-" * 60 + "\n"
            
            dados_export = sorted(zip(taxas, tamanhos_fila, tempos_espera, atendidos, desistentes))
            
            i = 0
            while i < len(dados_export):
                taxa, fila, espera, atend, desist = dados_export[i]
                dados_texto += f"{taxa:<10.1f} {fila:<12} {espera:<15.1f} {atend:<12} {desist:<12}\n"
                i = i + 1
            
            dados_texto += "\n" + "=" * 60 + "\n"
            dados_texto += "ANÁLISE DETALHADA:\n\n"
        
            if produtividades and len(taxas) >= len(produtividades):
                dados_texto += f"{'Taxa':<10} {'Produtividade':<15} {'Observação':<40}\n"
                dados_texto += "-" * 60 + "\n"
                
                dados_prod = sorted(zip(taxas[:len(produtividades)], produtividades, tempos_espera[:len(produtividades)], tamanhos_fila[:len(produtividades)]))
                
                i = 0
                while i < len(dados_prod):
                    taxa, prod, espera, fila = dados_prod[i]
                    obs = ""
                    if espera > 30:
                        obs = "Tempo de espera alto"
                    elif fila > 10:
                        obs = " Fila muito longa"
                    elif prod > 0.8:
                        obs = "Boa produtividade"
                    else:
                        obs = "Normal"
                    
                    dados_texto += f"{taxa:<10.1f} {prod:<15.2f} {obs:<40}\n"
                    i = i + 1
            
            dados_texto += "\n" + "=" * 60 + "\n"
            dados_texto += "RECOMENDAÇÕES:\n\n"
            
            
            if atendidos:
                idx_max_atend = atendidos.index(max(atendidos))
                taxa_otima = taxas[idx_max_atend]
                dados_texto += f"• Taxa ótima encontrada: λ={taxa_otima:.1f} pacientes/hora\n"
                dados_texto += f"  (Máximo de {max(atendidos)} pacientes atendidos)\n\n"
            
            
            if tamanhos_fila:
                max_fila = max(tamanhos_fila)
                idx_max_fila = tamanhos_fila.index(max_fila)
                taxa_max_fila = taxas[idx_max_fila]
                
                if max_fila > num_medicos * 5:
                    dados_texto += f"ALERTA: Taxa λ={taxa_max_fila:.1f} gera fila crítica ({max_fila} pacientes)\n"
                    dados_texto += f"  Recomendação: Não ultrapassar λ={taxa_max_fila * 0.8:.1f}\n\n"
            
            
            nome_arquivo = f"analise_fila_taxa_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            arquivo_salvo = salvar_arquivo(dados_texto, nome_arquivo)
            
            if arquivo_salvo:
                sg.popup(f"Dados exportados com sucesso!\n\n{arquivo_salvo}", 
                        title="Sucesso", keep_on_top=True, modal=True)
            else:
                sg.popup_error("Erro ao exportar dados.", title="Erro", keep_on_top=True, modal=True)
    
    window.close()

# ============================================================================
# FUNÇÕES DE CARREGAMENTO DE DADOS PACIENTES
# ============================================================================
def obter_dados_paciente_completo(paciente_id):
    if paciente_id in estado_simulacao.get("pessoas_dados", {}):
        return estado_simulacao["pessoas_dados"][paciente_id]
    historico_atendimentos = estado_simulacao.get("historico_atendimentos", [])
    i = 0
    while i < len(historico_atendimentos):
        atendimento = historico_atendimentos[i]
        if isinstance(atendimento, dict) and atendimento.get("paciente") == paciente_id:
            pacientes_carregados = carregar_pacientes_simula()
            for p in pacientes_carregados:
                if p.get("id") == paciente_id:
                    return p
        i = i + 1

    fila_espera = estado_simulacao.get("fila_espera", [])
    i = 0
    while i < len(fila_espera):
        paciente_fila = fila_espera[i]
        if paciente_fila.get("id") == paciente_id:
            pacientes_carregados = carregar_pacientes_simula()
            for p in pacientes_carregados:
                if p.get("id") == paciente_id:
                    return p
        i = i + 1

    pacientes_desistentes = estado_simulacao.get("pacientes_desistentes", [])
    i = 0
    while i < len(pacientes_desistentes):
        paciente_desistente = pacientes_desistentes[i]
        if paciente_desistente.get("id") == paciente_id:
            pacientes_carregados = carregar_pacientes_simula()
            for p in pacientes_carregados:
                if p.get("id") == paciente_id:
                    return p
        i = i + 1

    return {
        "id": paciente_id,
        "nome": f"Paciente {paciente_id}",
        "idade": "N/A",
        "sexo": "N/A",
        "doenca": "Não especificada",
        "prioridade": "NORMAL",
        "especialidade_necessaria": "Clínica Geral",
        "atributos": {},
        "telefone": "N/A",
        "email": "N/A",
        "consulta_marcada": False,
        "tempo_chegada": 0
    }
def carregar_dados_pacientes_atendidos(historico_atendimentos, medicos, pessoas_dados):
    """Carrega dados de TODOS os pacientes: atendidos, na fila e desistentes"""
    todos_pacientes = {}
    tempo_atual = estado_simulacao.get("tempo_atual", 0)
    i = 0
    while i < len(historico_atendimentos):
        atendimento = historico_atendimentos[i]
        if isinstance(atendimento, dict) and "paciente" in atendimento:
            paciente_id = atendimento.get("paciente", "")
            

            paciente_info = obter_dados_paciente_completo(paciente_id)
            
            inicio_atendimento = atendimento.get("inicio", 0)
            duracao_consulta = atendimento.get("duracao", 0)
            especialidade_correta = atendimento.get("especialidade_correta", False)
            medico_id_atend = atendimento.get("medico", "")

            medico_nome = "N/A"
            medico_id_display = "N/A"
            medico_especialidade = "N/A"
            

            j = 0
            medico_encontrado = False
            while j < len(medicos) and not medico_encontrado:
                medico = medicos[j]
                if medico.get("id") == medico_id_atend:
                    medico_nome = medico.get("nome", "Desconhecido")
                    medico_id_display = medico.get("id", medico_id_atend)
                    medico_especialidade = medico.get("especialidade", "N/A")
                    medico_encontrado = True
                j = j + 1
            tempo_chegada = paciente_info.get("tempo_chegada", 0)
            tempo_espera = max(0, inicio_atendimento - tempo_chegada)
            
            todos_pacientes[paciente_id] = {
                "id": paciente_id, 
                "nome": paciente_info.get("nome", f"Paciente {paciente_id}"), 
                "idade": paciente_info.get("idade", "N/A"), 
                "sexo": paciente_info.get("sexo", "N/A"), 
                "doenca": paciente_info.get("doenca", "Não especificada"), 
                "prioridade": paciente_info.get("prioridade", "NORMAL"),
                "fumador": paciente_info.get("atributos", {}).get("fumador", "N/A"), 
                "consome_alcool": paciente_info.get("atributos", {}).get("consome_alcool", "N/A"), 
                "atividade_fisica": paciente_info.get("atributos", {}).get("atividade_fisica", "N/A"), 
                "cronico": paciente_info.get("atributos", {}).get("cronico", "N/A"),
                "telefone": paciente_info.get("telefone", "N/A"),
                "email": paciente_info.get("email", "N/A"),
                "consulta_marcada": paciente_info.get("consulta_marcada", False),
                "tempo_chegada": tempo_chegada,
                "especialidade_necessaria": paciente_info.get("especialidade_necessaria", "Clínica Geral"), 
                "tempo_espera": tempo_espera,
                "duracao_consulta": duracao_consulta,
                "especialidade_correta": especialidade_correta, 
                "medico_nome": medico_nome,
                "medico_id": medico_id_display,
                "medico_especialidade": medico_especialidade,
                "inicio_atendimento": inicio_atendimento, 
                "fim_atendimento": inicio_atendimento + duracao_consulta,
                "status": "ATENDIDO"
            }
        
        i = i + 1
    
    fila_espera = estado_simulacao.get("fila_espera", [])
    
    i = 0
    while i < len(fila_espera):
        paciente_fila = fila_espera[i]
        paciente_id = paciente_fila.get("id")
        
        if paciente_id and paciente_id not in todos_pacientes:
            paciente_info = obter_dados_paciente_completo(paciente_id)
            
            tempo_chegada = paciente_fila.get("tempo_chegada", 0)
            tempo_espera = max(0, tempo_atual - tempo_chegada)
            
            todos_pacientes[paciente_id] = {
                "id": paciente_id, 
                "nome": paciente_info.get("nome", f"Paciente {paciente_id}"), 
                "idade": paciente_info.get("idade", "N/A"), 
                "sexo": paciente_info.get("sexo", "N/A"), 
                "doenca": paciente_info.get("doenca", "Não especificada"), 
                "prioridade": paciente_info.get("prioridade", "NORMAL"),
                "fumador": paciente_info.get("atributos", {}).get("fumador", "N/A"), 
                "consome_alcool": paciente_info.get("atributos", {}).get("consome_alcool", "N/A"), 
                "atividade_fisica": paciente_info.get("atributos", {}).get("atividade_fisica", "N/A"), 
                "cronico": paciente_info.get("atributos", {}).get("cronico", "N/A"),
                "telefone": paciente_info.get("telefone", "N/A"),
                "email": paciente_info.get("email", "N/A"),
                "consulta_marcada": paciente_info.get("consulta_marcada", False),
                "tempo_chegada": tempo_chegada,
                "especialidade_necessaria": paciente_info.get("especialidade_necessaria", "Clínica Geral"), 
                "tempo_espera": tempo_espera,
                "duracao_consulta": 0,
                "especialidade_correta": False, 
                "medico_nome": "N/A",
                "medico_id": "N/A",
                "medico_especialidade": "N/A",
                "inicio_atendimento": 0, 
                "fim_atendimento": 0,
                "status": "NA FILA"
            }
        
        i = i + 1
    pacientes_desistentes = estado_simulacao.get("pacientes_desistentes", [])
    
    i = 0
    while i < len(pacientes_desistentes):
        paciente_desistente = pacientes_desistentes[i]
        paciente_id = paciente_desistente.get("id")
        
        if paciente_id and paciente_id not in todos_pacientes:
            paciente_info = obter_dados_paciente_completo(paciente_id)
            
            tempo_chegada = paciente_desistente.get("tempo_chegada", 0)
            tempo_espera = paciente_desistente.get("tempo_espera", 0)
            
            if tempo_espera == 0:
                tempo_espera = estado_simulacao.get("tempo_max_espera", TEMPO_MAX_ESPERA) * 1.2
            
            todos_pacientes[paciente_id] = {
                "id": paciente_id, 
                "nome": paciente_info.get("nome", f"Paciente {paciente_id}"), 
                "idade": paciente_info.get("idade", "N/A"), 
                "sexo": paciente_info.get("sexo", "N/A"), 
                "doenca": paciente_info.get("doenca", "Não especificada"), 
                "prioridade": paciente_info.get("prioridade", "NORMAL"),
                "fumador": paciente_info.get("atributos", {}).get("fumador", "N/A"), 
                "consome_alcool": paciente_info.get("atributos", {}).get("consome_alcool", "N/A"), 
                "atividade_fisica": paciente_info.get("atributos", {}).get("atividade_fisica", "N/A"), 
                "cronico": paciente_info.get("atributos", {}).get("cronico", "N/A"),
                "telefone": paciente_info.get("telefone", "N/A"),
                "email": paciente_info.get("email", "N/A"),
                "consulta_marcada": paciente_info.get("consulta_marcada", False),
                "tempo_chegada": tempo_chegada,
                "especialidade_necessaria": paciente_info.get("especialidade_necessaria", "Clínica Geral"), 
                "tempo_espera": tempo_espera,
                "duracao_consulta": 0,
                "especialidade_correta": False, 
                "medico_nome": "N/A",
                "medico_id": "N/A",
                "medico_especialidade": "N/A",
                "inicio_atendimento": 0, 
                "fim_atendimento": 0,
                "status": "DESISTENTE"
            }
        
        i = i + 1
    
    lista_pacientes = list(todos_pacientes.values())
    return lista_pacientes
def gerar_relatorio_completo(historico_atendimentos, medicos, pessoas_dados, titulo, dados_completos, dados_simulacao):
    relatorio_completo = []
    
    if dados_completos:
        relatorio_completo.append(f"LISTA DE ATENDIMENTOS - {titulo}")
        relatorio_completo.append("=" * 100)
        relatorio_completo.append(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        relatorio_completo.append(f"Total de atendimentos: {len(historico_atendimentos)}")
        relatorio_completo.append("")
        
        atendimentos_por_medico = {}
        for medico in medicos:
            atendimentos_por_medico[medico["id"]] = {
                "medico": medico["nome"],
                "especialidade": medico["especialidade"],
                "atendimentos": [],
                "total": 0,
                "tempo_total": 0
            }
        
        for atendimento in historico_atendimentos:
            if isinstance(atendimento, dict) and "medico" in atendimento:
                medico_id = atendimento.get("medico")
                paciente_id = atendimento.get("paciente")
                duracao = atendimento.get("duracao", 0)
                
                if medico_id in atendimentos_por_medico:
                    paciente_info = pessoas_dados.get(paciente_id, {})
                    paciente_nome = paciente_info.get("nome", f"Paciente {paciente_id}")
                    paciente_doenca = paciente_info.get("doenca", "Não especificada")
                    paciente_prioridade = paciente_info.get("prioridade", "NORMAL")
                    
                    especialidade_correta = atendimento.get("especialidade_correta", False)
                    
                    atendimentos_por_medico[medico_id]["atendimentos"].append({
                        "paciente_id": paciente_id,
                        "paciente_nome": paciente_nome,
                        "doenca": paciente_doenca,
                        "prioridade": paciente_prioridade,
                        "inicio": atendimento.get("inicio", 0),
                        "duracao": duracao,
                        "especialidade_correta": especialidade_correta
                    })
                    atendimentos_por_medico[medico_id]["total"] = atendimentos_por_medico[medico_id]["total"] + 1
                    atendimentos_por_medico[medico_id]["tempo_total"] = atendimentos_por_medico[medico_id]["tempo_total"] + duracao
        
        for medico_id, info_medico in atendimentos_por_medico.items():
            if info_medico["total"] > 0:
                relatorio_completo.append(f"MÉDICO: {info_medico['medico']} ({info_medico['especialidade']})")
                relatorio_completo.append(f"Total atendimentos: {info_medico['total']}")
                relatorio_completo.append(f"Tempo total em consultas: {info_medico['tempo_total']:.1f} minutos")
                if info_medico['total'] > 0:
                    relatorio_completo.append(f"Tempo médio por consulta: {info_medico['tempo_total']/info_medico['total']:.1f} minutos")
                else:
                    relatorio_completo.append("Tempo médio: 0 minutos")
                relatorio_completo.append("-" * 80)
                
                relatorio_completo.append(f"{'#':<4} {'Paciente':<25} {'Doença':<20} {'Prior.':<10} {'Duração':<10} {'Especialista':<12}")
                relatorio_completo.append("-" * 80)
                
                for i, atendimento in enumerate(info_medico["atendimentos"]):
                    especialista = "✓" if atendimento["especialidade_correta"] else "✗"
                    relatorio_completo.append(f"{i+1:<4} {atendimento['paciente_nome'][:25]:<25} "
                                           f"{atendimento['doenca'][:20]:<20} "
                                           f"{atendimento['prioridade'][:10]:<10} "
                                           f"{atendimento['duracao']:<10.1f} "
                                           f"{especialista:<12}")
                
                relatorio_completo.append("")
        
        relatorio_completo.append("ESTATÍSTICAS GERAIS")
        relatorio_completo.append("=" * 80)
        
        total_atendimentos = len(historico_atendimentos)
        atendimentos_especialidade_correta = 0
        for h in historico_atendimentos:
            if h.get("especialidade_correta", False):
                atendimentos_especialidade_correta = atendimentos_especialidade_correta + 1
        
        if total_atendimentos > 0:
            taxa_correspondencia = (atendimentos_especialidade_correta / total_atendimentos * 100)
        else:
            taxa_correspondencia = 0
        
        relatorio_completo.append(f"Taxa de correspondência de especialidades: {taxa_correspondencia:.1f}%")
        relatorio_completo.append(f"Total de médicos: {len(medicos)}")
    else:
        relatorio_completo.append(f"RELATÓRIO DA SIMULAÇÃO - {titulo}")
        relatorio_completo.append("=" * 100)
        
        if "timestamp" in dados_simulacao:
            relatorio_completo.append(f"Data/Hora original: {dados_simulacao['timestamp']}")
        
        relatorio_completo.append(f"Data/Hora consulta: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        relatorio_completo.append("")
        
        config = dados_simulacao.get("configuracao", {})
        relatorio_completo.append("CONFIGURAÇÃO DA SIMULAÇÃO")
        relatorio_completo.append("-" * 80)
        relatorio_completo.append(f"Lambda (λ): {config.get('lambda_chegada', 'N/A')} pacientes/hora")
        relatorio_completo.append(f"Número de médicos: {config.get('num_medicos', 'N/A')}")
        relatorio_completo.append(f"Tempo médio consulta: {config.get('tempo_medio_consulta', 'N/A')} minutos")
        relatorio_completo.append(f"Tempo simulação: {config.get('tempo_simulacao', 'N/A')} minutos")
        relatorio_completo.append(f"Distribuição: {config.get('distribuicao', 'N/A')}")
        relatorio_completo.append("")
        
        resultados = dados_simulacao.get("resultados_finais", {})
        relatorio_completo.append("RESULTADOS FINAIS")
        relatorio_completo.append("-" * 80)
        relatorio_completo.append(f"Pacientes atendidos: {resultados.get('atendidos', 'N/A')}")
        relatorio_completo.append(f"Pacientes desistentes: {resultados.get('desistentes', 'N/A')}")
        if isinstance(resultados.get('taxa_ocupacao_media'), (int, float)):
            relatorio_completo.append(f"Taxa ocupação média: {resultados.get('taxa_ocupacao_media', 'N/A'):.1f}%")
        else:
            relatorio_completo.append(f"Taxa ocupação média: {resultados.get('taxa_ocupacao_media', 'N/A')}")
        relatorio_completo.append(f"Fila máxima: {resultados.get('fila_maxima', 'N/A')}")
        if isinstance(resultados.get('tempo_medio_espera'), (int, float)):
            relatorio_completo.append(f"Tempo médio espera: {resultados.get('tempo_medio_espera', 'N/A'):.1f} minutos")
        else:
            relatorio_completo.append(f"Tempo médio espera: {resultados.get('tempo_medio_espera', 'N/A')}")
        relatorio_completo.append("")
        
        if historico_atendimentos and len(historico_atendimentos) > 0:
            relatorio_completo.append("EVOLUÇÃO DA SIMULAÇÃO")
            relatorio_completo.append("-" * 80)
            
            pontos_chave = [0]
            if len(historico_atendimentos) > 1:
                pontos_chave.append(len(historico_atendimentos) // 2)
            if len(historico_atendimentos) > 2:
                pontos_chave.append(len(historico_atendimentos) - 1)
            
            for i in range(len(pontos_chave)):
                idx = pontos_chave[i]
                if idx < len(historico_atendimentos):
                    dados = historico_atendimentos[idx]
                    
                    
                    tempo_info = dados.get('tempo', 'N/A')
                    fila_info = dados.get('fila_tamanho', 'N/A')
                    atendidos_info = dados.get('atendidos', 'N/A')
                    ocupacao_info = dados.get('taxa_ocupacao', 'N/A')
                    
                    
                    if isinstance(ocupacao_info, (int, float)):
                        ocupacao_str = f"{ocupacao_info:.1f}%"
                    else:
                        ocupacao_str = str(ocupacao_info)
                    
                    relatorio_completo.append(f"Tempo {tempo_info}: "
                                           f"Fila={fila_info}, "
                                           f"Atendidos={atendidos_info}, "
                                           f"Ocupação={ocupacao_str}")
        
        relatorio_completo.append("")
        relatorio_completo.append("NOTA: Para simulações antigas, apenas estatísticas gerais estão disponíveis.")
        relatorio_completo.append("Para ver a lista detalhada de pacientes, use a simulação atual.")
    
    return "\n".join(relatorio_completo)

def analise_rapida_desempenho():
    """Análise rápida do desempenho médico atual"""
    if not estado_simulacao.get("medicos"):
        sg.popup_error("Nenhum médico na simulação atual!", title="Erro")
        return
    
    sg.theme('TemaClinica')
    
    
    medicos = estado_simulacao["medicos"]
    tempo_atual = estado_simulacao.get("tempo_atual", 480)
    
    
    dados = []
    for i, medico in enumerate(medicos):
        
       
        tempo_ocupado = medico.get("tempo_total_ocupado", 0)
        taxa_ocupacao = (tempo_ocupado / tempo_atual * 100) if tempo_atual > 0 else 0
        num_atendimentos = medico.get("num_atendimentos", 0)
        
        
        historico = estado_simulacao.get("historico_atendimentos", [])
        atendimentos_corretos = 0
        atendimentos_medico = 0
        
        for atendimento in historico:
            if atendimento.get("medico") == medico.get("id"):
                atendimentos_medico = atendimentos_medico + 1
                if atendimento.get("especialidade_correta", False):
                    atendimentos_corretos = atendimentos_corretos + 1
        
        taxa_correspondencia = (atendimentos_corretos / atendimentos_medico * 100) if atendimentos_medico > 0 else 0
        
        dados.append([
            medico.get("nome", f"Médico {i+1}"),
            medico.get("especialidade", "Geral"),
            num_atendimentos,
            f"{taxa_ocupacao:.1f}%",
            f"{taxa_correspondencia:.1f}%"
        ])
    
    layout = [
        [sg.Text("Análise Rápida - Desempenho Médico", font=("Helvetica", 16, "bold"), justification="center")],
        [sg.Text(f"Tempo atual da simulação: {tempo_atual:.0f} minutos", font=("Helvetica", 12))],
        [sg.Table(values=dados,
                 headings=["Médico", "Especialidade", "Atendimentos", "Ocupação", "Precisão"],
                 auto_size_columns=True,
                 justification='center',
                 num_rows=10,
                 font=("Helvetica", 10),
                 header_font=("Helvetica", 10, "bold"))],
        [sg.Button("Relatório Completo", key="-RELATORIO_COMPLETO-", button_color=('white',escuro)),
         sg.Button("Fechar", button_color=('white',escuro))]
    ]
    
    window = sg.Window("Análise Rápida", layout, modal=True, finalize=True)
    
    continuar = True
    while continuar:
        event, values = window.read()
        
        if event in (sg.WINDOW_CLOSED, "Fechar"):
            continuar = False
        
        elif event == "-RELATORIO_COMPLETO-":
            window.close()
            gerar_relatorio_desempenho_medicos()
            continuar = False
    
    window.close()

def exportar_resultados_pacientes(pacientes_atendidos, titulo):
    texto_exportar = f"RELATÓRIO DE PACIENTES ATENDIDOS - {titulo}\n"
    texto_exportar += "=" * 80 + "\n"
    texto_exportar += f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
    texto_exportar += f"Total de pacientes: {len(pacientes_atendidos)}\n\n"
    
    for paciente in pacientes_atendidos:
        texto_exportar += f"ID: {paciente['id']}\n"
        texto_exportar += f"Nome: {paciente['nome']}\n"
        texto_exportar += f"Idade: {paciente['idade']}\n"
        texto_exportar += f"Sexo: {paciente['sexo']}\n"
        texto_exportar += f"Doença: {paciente['doenca']}\n"
        texto_exportar += f"Prioridade: {paciente['prioridade']}\n"
        texto_exportar += f"Fumador: {'Sim' if paciente['fumador'] == True else 'Não' if paciente['fumador'] == False else 'N/A'}\n"
        texto_exportar += f"Consome Álcool: {'Sim' if paciente['consome_alcool'] == True else 'Não' if paciente['consome_alcool'] == False else 'N/A'}\n"
        texto_exportar += f"Atividade Física: {paciente['atividade_fisica']}\n"
        texto_exportar += f"Doença Crônica: {'Sim' if paciente['cronico'] == True else 'Não' if paciente['cronico'] == False else 'N/A'}\n"
        texto_exportar += f"Telefone: {paciente['telefone']}\n"
        texto_exportar += f"Email: {paciente['email']}\n"
        texto_exportar += f"Consulta Marcada: {'Sim' if paciente['consulta_marcada'] else 'Não'}\n"
        texto_exportar += f"Tempo Chegada: {paciente['tempo_chegada']:.0f} min\n"
        texto_exportar += f"Especialidade Necessária: {paciente['especialidade_necessaria']}\n"
        texto_exportar += f"Tempo de Espera: {paciente['tempo_espera']:.1f} min\n"
        texto_exportar += f"Duração Consulta: {paciente['duracao_consulta']:.1f} min\n"
        texto_exportar += f"Médico: {paciente['medico_nome']}\n"
        texto_exportar += f"Especialidade Médico: {paciente['medico_especialidade']}\n"
        if paciente["especialidade_correta"]:
            texto_exportar += "Especialidade Correta: Sim\n"
        else:
            texto_exportar += "Especialidade Correta: Não\n"
        texto_exportar += "-" * 50 + "\n"
    
    nome_arquivo = f"pacientes_atendidos_{titulo.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    return salvar_arquivo(texto_exportar, nome_arquivo)

def mostrar_estatisticas_pacientes(pacientes_atendidos):
    if not pacientes_atendidos:
        return
    
    total_pacientes = len(pacientes_atendidos)
    
    prioridades = {}
    especialidades = {}
    sexos = {}
    fumadores = {"Sim": 0, "Não": 0, "N/A": 0}
    alcool = {"Sim": 0, "Não": 0, "N/A": 0}
    atividades = {"baixa": 0, "moderada": 0, "alta": 0, "N/A": 0}
    cronicos = {"Sim": 0, "Não": 0, "N/A": 0}
    
    for paciente in pacientes_atendidos:
        prioridade = paciente["prioridade"]
        especialidade = paciente["especialidade_necessaria"]
        sexo = paciente["sexo"]
        
        prioridades[prioridade] = prioridades.get(prioridade, 0) + 1
        especialidades[especialidade] = especialidades.get(especialidade, 0) + 1
        sexos[sexo] = sexos.get(sexo, 0) + 1
        
        if paciente["fumador"] == True:
            fumadores["Sim"] = fumadores["Sim"] + 1
        elif paciente["fumador"] == False:
            fumadores["Não"] = fumadores["Não"] + 1
        else:
            fumadores["N/A"] = fumadores["N/A"] + 1
        
        if paciente["consome_alcool"] == True:
            alcool["Sim"] = alcool["Sim"] + 1
        elif paciente["consome_alcool"] == False:
            alcool["Não"] = alcool["Não"] + 1
        else:
            alcool["N/A"] = alcool["N/A"] + 1
        
        atividade = paciente["atividade_fisica"]
        if atividade in atividades:
            atividades[atividade] = atividades[atividade] + 1
        else:
            atividades["N/A"] = atividades["N/A"] + 1
        
        if paciente["cronico"] == True:
            cronicos["Sim"] = cronicos["Sim"] + 1
        elif paciente["cronico"] == False:
            cronicos["Não"] = cronicos["Não"] + 1
        else:
            cronicos["N/A"] = cronicos["N/A"] + 1
    
    tempos_espera = []
    tempos_consulta = []
    especialidades_corretas = 0
    consultas_marcadas = 0
    
    for paciente in pacientes_atendidos:
        tempos_espera.append(paciente["tempo_espera"])
        tempos_consulta.append(paciente["duracao_consulta"])
        if paciente["especialidade_correta"]:
            especialidades_corretas = especialidades_corretas + 1
        if paciente["consulta_marcada"]:
            consultas_marcadas = consultas_marcadas + 1
    
    media_espera = np.mean(tempos_espera) if tempos_espera else 0
    media_consulta = np.mean(tempos_consulta) if tempos_consulta else 0
    taxa_correspondencia = (especialidades_corretas / total_pacientes * 100) if total_pacientes > 0 else 0
    taxa_marcadas = (consultas_marcadas / total_pacientes * 100) if total_pacientes > 0 else 0
    
    stats_text = f"ESTATÍSTICAS DOS PACIENTES\n"
    stats_text += f"Total de pacientes: {total_pacientes}\n\n"
    
    stats_text += f"Distribuição por Prioridade:\n"
    for prioridade, count in prioridades.items():
        percent = (count / total_pacientes * 100) if total_pacientes > 0 else 0
        stats_text += f"  {prioridade}: {count} ({percent:.1f}%)\n"
    
    stats_text += f"\nDistribuição por Sexo:\n"
    for sexo, count in sexos.items():
        percent = (count / total_pacientes * 100) if total_pacientes > 0 else 0
        stats_text += f"  {sexo}: {count} ({percent:.1f}%)\n"
    
    stats_text += f"\nHábitos de Saúde:\n"
    stats_text += f"  Fumadores: {fumadores['Sim']} ({fumadores['Sim']/total_pacientes*100:.1f}%)\n"
    stats_text += f"  Consomem Álcool: {alcool['Sim']} ({alcool['Sim']/total_pacientes*100:.1f}%)\n"
    stats_text += f"  Atividade Física Baixa: {atividades['baixa']} ({atividades['baixa']/total_pacientes*100:.1f}%)\n"
    stats_text += f"  Doenças Crônicas: {cronicos['Sim']} ({cronicos['Sim']/total_pacientes*100:.1f}%)\n"
    
    stats_text += f"\nDistribuição por Especialidade:\n"
    especialidades_sorted = sorted(especialidades.items(), key=lambda x: x[1], reverse=True)
    for especialidade, count in especialidades_sorted:
        percent = (count / total_pacientes * 100) if total_pacientes > 0 else 0
        stats_text += f"  {especialidade}: {count} ({percent:.1f}%)\n"
    
    stats_text += f"\nMédias do Atendimento:\n"
    stats_text += f"  Tempo médio de espera: {media_espera:.1f} min\n"
    stats_text += f"  Tempo médio de consulta: {media_consulta:.1f} min\n"
    stats_text += f"  Taxa de especialidade correta: {taxa_correspondencia:.1f}%\n"
    stats_text += f"  Taxa de consultas marcadas: {taxa_marcadas:.1f}%\n"
    
    sg.popup(stats_text, title="Estatísticas dos Pacientes", keep_on_top=True)


# ============================================================================
# FUNÇÕES DE SISTEMA E SIMULAÇÃO
# ============================================================================

def processar_desistencias():
    tempo_atual = estado_simulacao["tempo_atual"]
    fila_nova = []
    
    tempo_max_espera = estado_simulacao.get("tempo_max_espera", TEMPO_MAX_ESPERA)
    prob_desistencia = estado_simulacao.get("prob_desistencia", PROB_DESISTENCIA)
    
    fila_temporaria = estado_simulacao["fila_espera"].copy()
    
    while not queue_empty(fila_temporaria):
        paciente, fila_temporaria = remover_da_fila(fila_temporaria)
        tempo_espera = tempo_atual - paciente.get("tempo_chegada", tempo_atual)

        if tempo_espera > tempo_max_espera:
            if random.random() < prob_desistencia:
                paciente["tempo_espera"] = tempo_espera
                paciente["motivo_desistencia"] = f"Esperou {tempo_espera:.1f} min (> {tempo_max_espera} min)"
                estado_simulacao["pacientes_desistentes"].append(paciente)
            else:
                fila_nova = adicionar_a_fila(fila_nova, paciente)
        else:
            fila_nova = adicionar_a_fila(fila_nova, paciente)
    
    estado_simulacao["fila_espera"] = fila_nova
    estado_simulacao["fila_espera"] = ordenar_fila_por_prioridade(
        estado_simulacao["fila_espera"], PRIORIDADES
    )
def atualizar_simulacao(incremento_tempo):
    if not estado_simulacao["simulacao_ativa"]:
        return
    
    estado_simulacao["tempo_atual"] = estado_simulacao["tempo_atual"] + incremento_tempo
    tempo_atual = estado_simulacao["tempo_atual"]

    if len(estado_simulacao["dados_historicos"]) == 0 or tempo_atual - estado_simulacao["dados_historicos"][-1]["tempo"] >= 1.0:
        coletar_dados_historicos()

    if tempo_atual >= estado_simulacao["tempo_simulacao"]:
        estado_simulacao["simulacao_ativa"] = False
        salvar_resultado_simulacao()
        return
    
    medicos = estado_simulacao["medicos"]
    num_medicos_total = len(medicos)
    max_pausa_simultanea = min(
        estado_simulacao.get("max_pausa_simultanea", MAX_MEDICOS_PAUSA_SIMULTANEA),
        max(1, num_medicos_total // 3)
    )

    medicos_em_pausa = 0
    i = 0
    while i < len(medicos):
        if medicos[i]["em_pausa"]:
            medicos_em_pausa = medicos_em_pausa + 1
        i = i + 1

    pausas_permitidas = max_pausa_simultanea
    tamanho_fila_atual = tamanho_fila(estado_simulacao["fila_espera"])
    num_medicos = len(medicos)
    
    if tamanho_fila_atual > num_medicos * 6:
        pausas_permitidas = max(0, max_pausa_simultanea // 2)
    elif tamanho_fila_atual > num_medicos * 4:
        pausas_permitidas = max(1, max_pausa_simultanea * 2 // 3)
    
    medicos_disponiveis_pausa = []
    i = 0
    while i < len(medicos):
        medico = medicos[i]
        pode_pausar = (
            not medico["em_pausa"] and 
            medico["num_pausas_realizadas"] < medico["num_pausas"] and
            tempo_atual >= (medico["num_pausas_realizadas"] + 1) * medico["frequencia_pausa"]
        )
        
        if pode_pausar:
            especialidade = medico["especialidade"]
            
            medicos_mesma_especialidade = []
            j = 0
            while j < len(medicos):
                if medicos[j]["especialidade"] == especialidade:
                    medicos_mesma_especialidade.append(medicos[j])
                j = j + 1
            
            medicos_trabalhando_mesma_espec = 0
            j = 0
            while j < len(medicos_mesma_especialidade):
                if not medicos_mesma_especialidade[j]["em_pausa"] and medicos_mesma_especialidade[j]["id"] != medico["id"]:
                    medicos_trabalhando_mesma_espec = medicos_trabalhando_mesma_espec + 1
                j = j + 1
            
            if len(medicos_mesma_especialidade) == 1:
                if tamanho_fila_atual < 3:
                    medicos_disponiveis_pausa.append(medico)
            elif medicos_trabalhando_mesma_espec > 0:
                medicos_disponiveis_pausa.append(medico)
        
        i = i + 1
    
    if medicos_disponiveis_pausa and medicos_em_pausa < pausas_permitidas:
        random.shuffle(medicos_disponiveis_pausa)
        vagas_pausa = pausas_permitidas - medicos_em_pausa
        medicos_para_pausa = medicos_disponiveis_pausa[:vagas_pausa]
        
        i = 0
        while i < len(medicos_para_pausa):
            medico = medicos_para_pausa[i]
            probabilidade_pausa = 0.7 if tamanho_fila_atual < 5 else 0.3
            if random.random() < probabilidade_pausa:
                medico["em_pausa"] = True
                medico["tempo_fim_pausa"] = tempo_atual + medico["duracao_pausa"]
                medico["ocupado"] = False
                medico["paciente_atual"] = None
                medicos_em_pausa = medicos_em_pausa + 1
            i = i + 1
    
    i = 0
    while i < len(medicos):
        medico = medicos[i]
        if medico["em_pausa"] and tempo_atual >= medico["tempo_fim_pausa"]:
            medico["em_pausa"] = False
            medico["num_pausas_realizadas"] = medico["num_pausas_realizadas"] + 1
            medico["pausas_realizadas"].append({
                "inicio": tempo_atual - medico["duracao_pausa"],
                "fim": tempo_atual
            })
            medicos_em_pausa = max(0, medicos_em_pausa - 1)
        i = i + 1
    
    if tempo_atual >= estado_simulacao["proximo_paciente_tempo"] and estado_simulacao["pacientes_disponiveis"]:
        paciente = estado_simulacao["pacientes_disponiveis"][0]
        estado_simulacao["pacientes_disponiveis"] = estado_simulacao["pacientes_disponiveis"][1:]
        
        paciente["tempo_chegada"] = tempo_atual
        
        estado_simulacao["fila_espera"] = adicionar_a_fila(estado_simulacao["fila_espera"], paciente)
        
        estado_simulacao["fila_espera"] = ordenar_fila_por_prioridade(
            estado_simulacao["fila_espera"], PRIORIDADES
        )
        
        if estado_simulacao["pacientes_disponiveis"]:
            lambda_chegada = estado_simulacao["lambda_chegada"]
            lambda_minuto = lambda_chegada / 60.0
            
            if lambda_minuto > 0:
                tempo_medio_entre_chegadas = 1.0 / lambda_minuto
            else:
                tempo_medio_entre_chegadas = 60.0
            
            proximo_tempo = np.random.exponential(scale=tempo_medio_entre_chegadas)
            proximo_tempo = max(0.5, proximo_tempo)
            estado_simulacao["proximo_paciente_tempo"] = tempo_atual + proximo_tempo
    
    i = 0
    while i < len(estado_simulacao["medicos"]):
        medico = estado_simulacao["medicos"][i]
        if medico["ocupado"] and tempo_atual >= medico["tempo_fim_consulta"]:
            finalizar_consulta(medico, tempo_atual)
        i = i + 1
    
    i = 0
    while i < len(estado_simulacao["medicos"]):
        medico = estado_simulacao["medicos"][i]
        
        if not medico["ocupado"] and not medico["em_pausa"]:
            if not queue_empty(estado_simulacao["fila_espera"]):
                finalizar_consulta(medico, tempo_atual)
        
        i = i + 1
    
    processar_desistencias()
    
    coletar_dados_historicos()
def salvar_resultado_simulacao():
    resultado = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "configuracao": {
            "lambda_chegada": estado_simulacao["lambda_chegada"],
            "tempo_medio_consulta": estado_simulacao["tempo_medio_consulta"],
            "num_medicos": len(estado_simulacao["medicos"]),
            "distribuicao": estado_simulacao["distribuicao"],
            "tempo_simulacao": estado_simulacao["tempo_simulacao"],
            "frequencia_pausa": estado_simulacao["medicos"][0]["frequencia_pausa"] if estado_simulacao["medicos"] else 0,
            "duracao_pausa": estado_simulacao["medicos"][0]["duracao_pausa"] if estado_simulacao["medicos"] else 0,
            "num_pausas": estado_simulacao["medicos"][0]["num_pausas"] if estado_simulacao["medicos"] else 0,
            "max_pausa_simultanea": estado_simulacao.get("max_pausa_simultanea", MAX_MEDICOS_PAUSA_SIMULTANEA)
        },
        "resultados_finais": {
            "atendidos": len(estado_simulacao["historico_atendimentos"]),
            "desistentes": len(estado_simulacao["pacientes_desistentes"]),
            "taxa_ocupacao_media": np.mean([m["tempo_total_ocupado"] / estado_simulacao["tempo_atual"] * 100 
                                          for m in estado_simulacao["medicos"]]) if estado_simulacao["tempo_atual"] > 0 else 0,
            "fila_maxima": max([d["fila_tamanho"] for d in estado_simulacao["dados_historicos"]] + [0]),
            "tempo_medio_espera": np.mean([d["tempo_medio_espera"] for d in estado_simulacao["dados_historicos"] if d["tempo_medio_espera"] > 0] + [0])
        },
        "dados_historicos": estado_simulacao["dados_historicos"].copy()
    }
    estado_simulacao["resultados_simulacoes"].append(resultado)
def iniciar_consulta(medico, paciente, tempo_atual):
    """Inicia uma consulta - VERSÃO CORRIGIDA"""
    

    duracao = gera_tempo_consulta(
        estado_simulacao["tempo_medio_consulta"], 
        estado_simulacao["distribuicao"]
    )
    

    medico["ocupado"] = True
    medico["paciente_atual"] = paciente["id"]
    medico["tempo_fim_consulta"] = tempo_atual + duracao
    medico["num_atendimentos"] = medico["num_atendimentos"] + 1
    

    especialidade_correta = medico["especialidade"] == paciente.get(
        "especialidade_necessaria", "Clínica Geral"
    )
    

    estado_simulacao["historico_atendimentos"].append({
        "paciente": paciente["id"],
        "medico": medico["id"],
        "inicio": tempo_atual,
        "duracao": duracao,
        "especialidade_correta": especialidade_correta
    })



def finalizar_consulta(medico, tempo_atual):
    """Finaliza consulta do médico e procura próximo paciente - VERSÃO CORRIGIDA"""
 
    if medico["ocupado"] and medico.get("tempo_fim_consulta", 0) > 0:
        duracao_consulta = estado_simulacao.get("tempo_medio_consulta", 15)
        tempo_inicio_consulta = medico["tempo_fim_consulta"] - duracao_consulta
        duracao_real = tempo_atual - tempo_inicio_consulta
 
        if duracao_real > 0:
            medico["tempo_total_ocupado"] = medico["tempo_total_ocupado"] + duracao_real

    medico["ocupado"] = False
    medico["paciente_atual"] = None
    medico["tempo_fim_consulta"] = 0

    if queue_empty(estado_simulacao["fila_espera"]):
        return

    tempo_max_espera = estado_simulacao.get("tempo_max_espera", TEMPO_MAX_ESPERA)
    medico_especialidade = medico["especialidade"]
    
    paciente_escolhido = None
    indice_escolhido = -1
    
    idx_busca = 0
    encontrou_paciente = False
    
    while idx_busca < len(estado_simulacao["fila_espera"]) and not encontrou_paciente:
        paciente = estado_simulacao["fila_espera"][idx_busca]
        paciente_prioridade = paciente.get("prioridade", "NORMAL")
        paciente_especialidade = paciente.get("especialidade_necessaria", "Clínica Geral")
        tempo_chegada = paciente.get("tempo_chegada", tempo_atual)
        tempo_espera = tempo_atual - tempo_chegada
        
        pode_atender = False

        if medico_especialidade == paciente_especialidade:

            tem_maior_prioridade_mesma_especialidade = False
            j = 0
            while j < idx_busca and not tem_maior_prioridade_mesma_especialidade:
                paciente_frente = estado_simulacao["fila_espera"][j]
                if paciente_frente.get("especialidade_necessaria") == paciente_especialidade:
                    frente_prioridade = paciente_frente.get("prioridade", "NORMAL")
                    if PRIORIDADES.get(frente_prioridade, 5) < PRIORIDADES.get(paciente_prioridade, 5):
                        tem_maior_prioridade_mesma_especialidade = True
                j = j + 1
            
            if not tem_maior_prioridade_mesma_especialidade:
                pode_atender = True
        else:

            if paciente_prioridade == "URGENTE" and tempo_espera > 5:
                pode_atender = True
            
            elif paciente_prioridade == "ALTA" and tempo_espera > (tempo_max_espera / 2):
                tem_urgente_na_frente = False
                j = 0
                while j < idx_busca and not tem_urgente_na_frente:
                    paciente_frente = estado_simulacao["fila_espera"][j]
                    if paciente_frente.get("prioridade") == "URGENTE":
                        tem_urgente_na_frente = True
                    j = j + 1
                
                if not tem_urgente_na_frente:
                    pode_atender = True
            
            elif paciente_prioridade == "NORMAL" and tempo_espera > tempo_max_espera and medico_especialidade == "Clínica Geral":
                tem_prioridade_na_frente = False
                j = 0
                while j < idx_busca and not tem_prioridade_na_frente:
                    paciente_frente = estado_simulacao["fila_espera"][j]
                    if paciente_frente.get("prioridade") in ["URGENTE", "ALTA"]:
                        tem_prioridade_na_frente = True
                    j = j + 1
                
                tem_especialista_da_especialidade = False
                k = 0
                while k < len(estado_simulacao["medicos"]) and not tem_especialista_da_especialidade:
                    outro_medico = estado_simulacao["medicos"][k]
                    if outro_medico["especialidade"] == paciente_especialidade:
                        if not outro_medico["ocupado"] and not outro_medico.get("em_pausa", False):
                            tem_especialista_da_especialidade = True
                    k = k + 1
                
                if not tem_prioridade_na_frente and not tem_especialista_da_especialidade:
                    pode_atender = True
        
        if pode_atender:
            paciente_escolhido = paciente
            indice_escolhido = idx_busca
            encontrou_paciente = True
        
        idx_busca = idx_busca + 1

    if paciente_escolhido is not None:
        nova_fila = []
        i = 0
        while i < len(estado_simulacao["fila_espera"]):
            if i != indice_escolhido:
                nova_fila.append(estado_simulacao["fila_espera"][i])
            i = i + 1
        estado_simulacao["fila_espera"] = nova_fila
        
        estado_simulacao["fila_espera"] = ordenar_fila_por_prioridade(
            estado_simulacao["fila_espera"], PRIORIDADES
        )
        
        iniciar_consulta(medico, paciente_escolhido, tempo_atual)
def obter_estatisticas():
    """Obtém estatísticas atuais da simulação - VERSÃO CORRIGIDA"""
    tempo_atual = estado_simulacao["tempo_atual"]
    
    stats = {
        "tempo_atual": tempo_atual,
        "tempo_simulacao": estado_simulacao["tempo_simulacao"],
        "doentes_atendidos": len(estado_simulacao["historico_atendimentos"]),
        "fila_espera": estado_simulacao["fila_espera"],
        "fila_len": tamanho_fila(estado_simulacao["fila_espera"]),
        "medicos": estado_simulacao["medicos"],
        "desistentes": len(estado_simulacao["pacientes_desistentes"]),
        "aguardando": len(estado_simulacao["pacientes_disponiveis"])
    }
    

    if tempo_atual > 0:
        taxas_ocupacao = []
        i = 0
        while i < len(estado_simulacao["medicos"]):
            medico = estado_simulacao["medicos"][i]
            tempo_ocupado = medico["tempo_total_ocupado"]
            
            
            if medico["ocupado"] and medico.get("tempo_fim_consulta", 0) > 0:
                tempo_medio = estado_simulacao.get("tempo_medio_consulta", 15)
                tempo_inicio_atual = medico["tempo_fim_consulta"] - tempo_medio
                tempo_ocupado_atual = tempo_atual - tempo_inicio_atual
                if tempo_ocupado_atual > 0:
                    tempo_ocupado = tempo_ocupado + tempo_ocupado_atual
            
           
            taxa = (tempo_ocupado / tempo_atual) * 100
            taxa = min(100.0, max(0.0, taxa))
            taxas_ocupacao.append(taxa)
            i = i + 1
        
        stats["taxa_ocupacao"] = np.mean(taxas_ocupacao) if taxas_ocupacao else 0
    else:
        stats["taxa_ocupacao"] = 0

    duracoes = []
    i = 0
    while i < len(estado_simulacao["historico_atendimentos"]):
        duracoes.append(estado_simulacao["historico_atendimentos"][i]["duracao"])
        i = i + 1
    stats["tempo_medio_consulta"] = np.mean(duracoes) if duracoes else 0

    atendimentos_especialidade_correta = 0
    i = 0
    while i < len(estado_simulacao["historico_atendimentos"]):
        h = estado_simulacao["historico_atendimentos"][i]
        if h.get("especialidade_correta", False):
            atendimentos_especialidade_correta = atendimentos_especialidade_correta + 1
        i = i + 1
    
    total_atendimentos = len(estado_simulacao["historico_atendimentos"])
    if total_atendimentos > 0:
        stats["taxa_correspondencia_especialidade"] = (atendimentos_especialidade_correta / total_atendimentos) * 100
    else:
        stats["taxa_correspondencia_especialidade"] = 0

    fila_por_especialidade = {}
    i = 0
    while i < len(estado_simulacao["fila_espera"]):
        paciente = estado_simulacao["fila_espera"][i]
        especialidade = paciente.get("especialidade_necessaria", "Clínica Geral")
        fila_por_especialidade[especialidade] = fila_por_especialidade.get(especialidade, 0) + 1
        i = i + 1
    
    stats["fila_por_especialidade"] = fila_por_especialidade
    
    return stats
def inicializar_simulacao(config):
    pessoas = carregar_pacientes_simula()
    if not pessoas:
        sg.popup_error("Não foi possível carregar pacientes!")
        return False
    
    medicos_dataset = carregar_medicos_simula()
    num_medicos = config.get("num_medicos", NUM_MEDICOS)
    medicos_dataset = medicos_dataset[:num_medicos]
    
    lambda_chegada = config.get("lambda_chegada", LAMBDA_CHEGADA)
    tempo_total = config.get("tempo_simulacao", TEMPO_SIMULACAO)
    tempo_total_horas = tempo_total / 60.0
    
    max_pacientes_dataset = len(pessoas)

    num_esperado_chegadas = lambda_chegada * tempo_total_horas

    num_pacientes_final = min(int(num_esperado_chegadas), max_pacientes_dataset)

    if num_esperado_chegadas >= max_pacientes_dataset:
        num_pacientes_final = max_pacientes_dataset
    if num_pacientes_final < max_pacientes_dataset:
        indices = list(range(max_pacientes_dataset))
        random.shuffle(indices)
        indices_selecionados = indices[:num_pacientes_final]
        pessoas_selecionadas = [pessoas[i] for i in indices_selecionados]
    else:
        pessoas_selecionadas = pessoas.copy()
    pessoas_simulacao = []
    for p in pessoas_selecionadas:
        p_copy = p.copy()
        p_copy["consulta_marcada"] = random.random() < 0.3
        pessoas_simulacao.append(p_copy)
    
    estado_simulacao["pessoas_dados"] = {p["id"]: p for p in pessoas_simulacao}
    
    estado_simulacao["medicos"] = []
    for medico_data in medicos_dataset:
        estado_simulacao["medicos"].append({
            "id": medico_data.get("id", "m_default"),
            "nome": medico_data.get("nome", "Médico"),
            "especialidade": medico_data.get("especialidade", "Geral"),
            "ocupado": False,
            "paciente_atual": None,
            "tempo_fim_consulta": 0,
            "tempo_total_ocupado": 0,
            "num_atendimentos": 0,
            "em_pausa": False,
            "tempo_fim_pausa": 0,
            "num_pausas_realizadas": 0,
            "frequencia_pausa": config.get("frequencia_pausa", PAUSA_FREQUENCIA),
            "duracao_pausa": config.get("duracao_pausa", DURACAO_PAUSA),
            "num_pausas": config.get("num_pausas", NUM_PAUSAS),
            "pausas_realizadas": []
        })
    
    estado_simulacao.update({
        "fila_espera": [],
        "historico_atendimentos": [],
        "tempo_atual": 0,
        "simulacao_ativa": True,
        "velocidade": config.get("velocidade", 5.0),
        "pacientes_disponiveis": pessoas_simulacao,
        "pacientes_desistentes": [],
        "lambda_chegada": lambda_chegada,
        "tempo_medio_consulta": config.get("tempo_medio_consulta", TEMPO_MEDIO_CONSULTA),
        "tempo_simulacao": config.get("tempo_simulacao", TEMPO_SIMULACAO),
        "distribuicao": config.get("distribuicao", "exponential"),
        "dados_historicos": [],
        "max_pausa_simultanea": config.get("max_pausa_simultanea", MAX_MEDICOS_PAUSA_SIMULTANEA),
        "tempo_max_espera": config.get("tempo_max_espera", TEMPO_MAX_ESPERA),
        "prob_desistencia": config.get("prob_desistencia", PROB_DESISTENCIA)
    })

    lambda_minuto = lambda_chegada / 60.0
    if lambda_minuto > 0:
        tempo_medio_entre_chegadas = 1.0 / lambda_minuto
    else:
        tempo_medio_entre_chegadas = 60.0
    
    primeiro_tempo = np.random.exponential(scale=tempo_medio_entre_chegadas)
    primeiro_tempo = max(0.1, primeiro_tempo)
    estado_simulacao["proximo_paciente_tempo"] = primeiro_tempo
    
    return True

# ============================================================================
# FUNÇÕES DE GRÁFICOS
# ============================================================================

def mostrar_graficos_simulacao(dados_historicos, titulo_simulacao):
    """Mostra gráficos da simulação com opção de exportar TXT"""
    
    
    if not dados_historicos:
        sg.popup_error("Nenhum dado disponível", title="Erro")
        return
    
    if not isinstance(dados_historicos, list):
        sg.popup_error("Dados devem ser uma lista", title="Erro")
        return
    
    
    dados_validos = 0
    i = 0
    while i < len(dados_historicos):
        item = dados_historicos[i]
        if isinstance(item, dict):
            dados_validos = dados_validos + 1
        i = i + 1
    
    if dados_validos == 0:
        sg.popup_error("Nenhum dado válido encontrado", title="Erro")
        return
    
    
    tempos = []
    fila_tamanhos = []
    taxas_ocupacao = []
    atendidos_lista = []
    desistentes_lista = []
    tempos_espera = []
    medicos_pausa_lista = []
    
    i = 0
    while i < len(dados_historicos):
        registro = dados_historicos[i]
        if isinstance(registro, dict):
            
            tempo_val = registro.get("tempo")
            if tempo_val is not None:
                if isinstance(tempo_val, (int, float)):
                    tempos.append(float(tempo_val))
                else:
                    tempos.append(0.0)
            else:
                tempos.append(0.0)
            
            
            fila_val = registro.get("fila_tamanho")
            if fila_val is not None:
                if isinstance(fila_val, (int, float)):
                    fila_tamanhos.append(float(fila_val))
                else:
                    fila_tamanhos.append(0.0)
            else:
                fila_tamanhos.append(0.0)
            
            
            ocupacao_val = registro.get("taxa_ocupacao")
            if ocupacao_val is not None:
                if isinstance(ocupacao_val, (int, float)):
                    taxas_ocupacao.append(float(ocupacao_val))
                else:
                    taxas_ocupacao.append(0.0)
            else:
                taxas_ocupacao.append(0.0)
            
            
            atendidos_val = registro.get("atendidos")
            if atendidos_val is not None:
                if isinstance(atendidos_val, (int, float)):
                    atendidos_lista.append(int(atendidos_val))
                else:
                    atendidos_lista.append(0)
            else:
                atendidos_lista.append(0)
            
            
            desistentes_val = registro.get("desistentes")
            if desistentes_val is not None:
                if isinstance(desistentes_val, (int, float)):
                    desistentes_lista.append(int(desistentes_val))
                else:
                    desistentes_lista.append(0)
            else:
                desistentes_lista.append(0)
            
            
            espera_val = registro.get("tempo_medio_espera")
            if espera_val is not None:
                if isinstance(espera_val, (int, float)):
                    tempos_espera.append(float(espera_val))
                else:
                    tempos_espera.append(0.0)
            else:
                tempos_espera.append(0.0)
            
            
            pausa_val = registro.get("medicos_em_pausa")
            if pausa_val is not None:
                if isinstance(pausa_val, (int, float)):
                    medicos_pausa_lista.append(float(pausa_val))
                else:
                    medicos_pausa_lista.append(0.0)
            else:
                medicos_pausa_lista.append(0.0)
        i = i + 1
    
    if len(tempos) < 2:
        sg.popup_error("Dados insuficientes. Precisa de pelo menos 2 pontos", title="Erro")
        return
    
    
    def exportar_dados_txt():
        """Exporta os dados da simulação para um arquivo TXT"""
        
        
        conteudo = []
        conteudo.append(f"RELATÓRIO DE DADOS DA SIMULAÇÃO")
        conteudo.append("=" * 80)
        conteudo.append(f"Título: {titulo_simulacao}")
        conteudo.append(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        conteudo.append(f"Total de registros: {len(dados_historicos)}")
        conteudo.append("")
        
        
        conteudo.append("DETALHES POR PONTO DE TEMPO")
        conteudo.append("=" * 80)
        conteudo.append(f"{'Tempo (min)':<12} {'Fila':<8} {'Ocupação (%)':<12} {'Atendidos':<10} {'Desistentes':<12} {'Espera (min)':<12} {'Méd. Pausa':<10}")
        conteudo.append("-" * 80)
        
        
        for i in range(min(len(tempos), len(dados_historicos))):
            tempo_str = f"{tempos[i]:.1f}" if i < len(tempos) else "N/A"
            fila_str = f"{fila_tamanhos[i]:.0f}" if i < len(fila_tamanhos) else "N/A"
            ocup_str = f"{taxas_ocupacao[i]:.1f}" if i < len(taxas_ocupacao) else "N/A"
            atend_str = f"{atendidos_lista[i]}" if i < len(atendidos_lista) else "N/A"
            desist_str = f"{desistentes_lista[i]}" if i < len(desistentes_lista) else "N/A"
            espera_str = f"{tempos_espera[i]:.1f}" if i < len(tempos_espera) else "N/A"
            pausa_str = f"{medicos_pausa_lista[i]:.0f}" if i < len(medicos_pausa_lista) else "N/A"
            
            conteudo.append(f"{tempo_str:<12} {fila_str:<8} {ocup_str:<12} {atend_str:<10} {desist_str:<12} {espera_str:<12} {pausa_str:<10}")
        
        conteudo.append("")
        conteudo.append("ESTATÍSTICAS GERAIS")
        conteudo.append("=" * 80)
        
        
        if tempos:
            conteudo.append(f"Tempo total: {tempos[-1]:.1f} minutos")
        
        if fila_tamanhos:
            max_fila = max(fila_tamanhos)
            media_fila = np.mean(fila_tamanhos)
            conteudo.append(f"Fila máxima: {max_fila:.0f} pacientes")
            conteudo.append(f"Fila média: {media_fila:.1f} pacientes")
        
        if taxas_ocupacao:
            media_ocupacao = np.mean(taxas_ocupacao)
            conteudo.append(f"Ocupação média: {media_ocupacao:.1f}%")
        
        if atendidos_lista:
            total_atendidos = atendidos_lista[-1] if atendidos_lista else 0
            conteudo.append(f"Total atendidos: {total_atendidos}")
        
        if desistentes_lista:
            total_desistentes = desistentes_lista[-1] if desistentes_lista else 0
            conteudo.append(f"Total desistentes: {total_desistentes}")
        
        if tempos_espera:
            tempos_positivos = [t for t in tempos_espera if t > 0]
            if tempos_positivos:
                media_espera = np.mean(tempos_positivos)
                conteudo.append(f"Espera média: {media_espera:.1f} minutos")
        
        conteudo.append("")
        conteudo.append("INFORMAÇÕES ADICIONAIS")
        conteudo.append("=" * 80)
        conteudo.append(f"Número de pontos de tempo: {len(tempos)}")
        conteudo.append(f"Dados válidos extraídos: {dados_validos}")
        
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_simplificado = titulo_simulacao.replace(" ", "_").replace(":", "").replace("/", "")
        nome_arquivo = f"dados_simulacao_{nome_simplificado}_{timestamp}.txt"
        
        
        try:
            with open(nome_arquivo, "w", encoding="utf-8") as f:
                f.write("\n".join(conteudo))
            
            sg.popup(f"Dados exportados com sucesso!\n\nArquivo: {nome_arquivo}", 
                    title="Exportação Concluída",
                    keep_on_top=True)
            return True
        except Exception as e:
            sg.popup_error(f"Erro ao exportar dados:\n{str(e)}", 
                          title="Erro na Exportação",
                          keep_on_top=True)
            return False
    
    
    tab1_layout = [
        [sg.Canvas(key="-CANVAS_FILA-", size=(600, 400), expand_x=True, expand_y=True)]
    ]
    
    tab2_layout = [
        [sg.Canvas(key="-CANVAS_OCUPACAO-", size=(600, 400), expand_x=True, expand_y=True)]
    ]
    
    tab3_layout = [
        [sg.Canvas(key="-CANVAS_ATENDIDOS-", size=(600, 400), expand_x=True, expand_y=True)]
    ]
    
    tab4_layout = [
        [sg.Canvas(key="-CANVAS_ESPERA-", size=(600, 400), expand_x=True, expand_y=True)]
    ]
    
    
    layout = [
        [sg.Text(f"Gráficos: {titulo_simulacao}", font=("Helvetica", 16), justification="center", expand_x=True)],
        [sg.TabGroup([
            [sg.Tab('Fila', tab1_layout)],
            [sg.Tab('Ocupação', tab2_layout)],
            [sg.Tab('Atendidos', tab3_layout)],
            [sg.Tab('Espera', tab4_layout)]
        ], key="-TABS-", expand_x=True, expand_y=True)],
        [sg.HorizontalSeparator()],
        [sg.Button("Exportar Dados (TXT)", size=(20, 1), button_color=('white', escuro), key="-EXPORTAR-"),
         sg.Button("Fechar", size=(12, 1), button_color=('white', escuro))]
    ]
    
    window = sg.Window(f"Gráficos - {titulo_simulacao}", 
                      layout, 
                      modal=True, 
                      finalize=True, 
                      size=(800, 600), 
                      resizable=True,
                      keep_on_top=True)
    
    
    fig1 = Figure(figsize=(8, 5), dpi=100)
    ax1 = fig1.add_subplot(111)
    
    
    tempos_fila = tempos
    fila_tamanhos_plot = fila_tamanhos
    if len(tempos) > 1000:
        passo = len(tempos) // 1000
        tempos_novos = []
        fila_novos = []
        i = 0
        while i < len(tempos):
            tempos_novos.append(tempos[i])
            fila_novos.append(fila_tamanhos[i])
            i = i + passo
        tempos_fila = tempos_novos
        fila_tamanhos_plot = fila_novos
    
    ax1.plot(tempos_fila, fila_tamanhos_plot, 'b-', linewidth=2)
    ax1.set_xlabel('Tempo (minutos)', fontsize=11)
    ax1.set_ylabel('Pacientes na Fila', fontsize=11)
    ax1.set_title('Tamanho da Fila', fontsize=13, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    
    if fila_tamanhos_plot:
        max_fila = max(fila_tamanhos_plot)
        ax1.set_ylim(0, max(1, max_fila * 1.1))
    
    fig1.tight_layout()
    canvas1 = fig_tk.FigureCanvasTkAgg(fig1, window["-CANVAS_FILA-"].TKCanvas)
    canvas1.draw()
    canvas1.get_tk_widget().pack(side='top', fill='both', expand=True)
    
    
    fig2 = Figure(figsize=(8, 5), dpi=100)
    ax2 = fig2.add_subplot(111)
    
    taxas_ocupacao_plot = taxas_ocupacao
    tempos_ocup = tempos
    if len(tempos) > len(taxas_ocupacao):
        tempos_ocup = tempos[:len(taxas_ocupacao)]
    
    ax2.plot(tempos_ocup, taxas_ocupacao_plot, 'r-', linewidth=2)
    ax2.set_xlabel('Tempo (minutos)', fontsize=11)
    ax2.set_ylabel('Taxa de Ocupação (%)', fontsize=11)
    ax2.set_title('Taxa de Ocupação', fontsize=13, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(0, 100)
    
    fig2.tight_layout()
    canvas2 = fig_tk.FigureCanvasTkAgg(fig2, window["-CANVAS_OCUPACAO-"].TKCanvas)
    canvas2.draw()
    canvas2.get_tk_widget().pack(side='top', fill='both', expand=True)
    
    
    fig3 = Figure(figsize=(8, 5), dpi=100)
    ax3 = fig3.add_subplot(111)
    
    atendidos_plot = atendidos_lista
    desistentes_plot = desistentes_lista
    tempos_atend = tempos
    
    tamanho_min = min(len(tempos), len(atendidos_plot), len(desistentes_plot))
    if tamanho_min > 0:
        tempos_atend = tempos[:tamanho_min]
        atendidos_plot = atendidos_plot[:tamanho_min]
        desistentes_plot = desistentes_plot[:tamanho_min]
    
    ax3.plot(tempos_atend, atendidos_plot, 'g-', linewidth=2, label='Atendidos')
    ax3.plot(tempos_atend, desistentes_plot, 'r--', linewidth=2, label='Desistentes')
    ax3.set_xlabel('Tempo (minutos)', fontsize=11)
    ax3.set_ylabel('Número de Pacientes', fontsize=11)
    ax3.set_title('Atendidos vs Desistentes', fontsize=13, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.legend(loc='best')
    
    fig3.tight_layout()
    canvas3 = fig_tk.FigureCanvasTkAgg(fig3, window["-CANVAS_ATENDIDOS-"].TKCanvas)
    canvas3.draw()
    canvas3.get_tk_widget().pack(side='top', fill='both', expand=True)
    
    
    fig4 = Figure(figsize=(8, 5), dpi=100)
    ax4 = fig4.add_subplot(111)
    
    
    tempos_espera_positivos = []
    tempos_filtrados = []
    i = 0
    while i < len(tempos_espera):
        if i < len(tempos) and tempos_espera[i] > 0:
            tempos_espera_positivos.append(tempos_espera[i])
            tempos_filtrados.append(tempos[i])
        i = i + 1
    
    if tempos_espera_positivos:
        ax4.plot(tempos_filtrados, tempos_espera_positivos, 'm-', linewidth=2)
    
    ax4.set_xlabel('Tempo (minutos)', fontsize=11)
    ax4.set_ylabel('Tempo de Espera (minutos)', fontsize=11)
    ax4.set_title('Tempo Médio de Espera', fontsize=13, fontweight='bold')
    ax4.grid(True, alpha=0.3)
    
    if tempos_espera_positivos:
        max_espera = max(tempos_espera_positivos)
        ax4.set_ylim(0, max(1, max_espera * 1.2))
    else:
        ax4.set_ylim(0, 30)
        ax4.text(0.5, 0.5, 'Sem dados de espera', 
                transform=ax4.transAxes, ha='center', va='center', fontsize=12)
    
    fig4.tight_layout()
    canvas4 = fig_tk.FigureCanvasTkAgg(fig4, window["-CANVAS_ESPERA-"].TKCanvas)
    canvas4.draw()
    canvas4.get_tk_widget().pack(side='top', fill='both', expand=True)
    
    
    continuar = True
    while continuar:
        event, values = window.read()
        
        if event == sg.WINDOW_CLOSED or event == "Fechar":
            continuar = False
        
        elif event == "-EXPORTAR-":
            exportar_dados_txt()
    
    window.close()

def gerar_graficos():
    """Interface para gerar gráficos"""
    sg.theme('TemaClinica')
    tem_dados_atuais = len(estado_simulacao.get("dados_historicos", [])) > 0
    tem_simulacoes_antigas = len(estado_simulacao.get("resultados_simulacoes", [])) > 0
    
    if not tem_dados_atuais and not tem_simulacoes_antigas:
        sg.popup_error("Sem dados de simulação", title="Erro")
        return
    opcoes = []
    
    if tem_dados_atuais:
        atendidos = len(estado_simulacao.get("historico_atendimentos", []))
        tempo = estado_simulacao.get("tempo_atual", 0)
        opcoes.append(f"Simulação Atual ({atendidos} atendidos, {tempo:.0f} min)")
    
    if tem_simulacoes_antigas:
        i = 0
        while i < len(estado_simulacao["resultados_simulacoes"]):
            sim = estado_simulacao["resultados_simulacoes"][i]
            config = sim.get("configuracao", {})
            timestamp = sim.get("timestamp", "")
            resultados = sim.get("resultados_finais", {})
            
            data_formatada = timestamp[:16]
            texto = f"λ={config.get('lambda_chegada', 0)} M={config.get('num_medicos', 0)} {data_formatada}"
            opcoes.append(texto)
            i = i + 1
    
    if not opcoes:
        sg.popup_error("Nenhuma simulação", title="Erro")
        return
    
    layout = [
        [sg.Text("Selecionar Simulação", font=("Helvetica", 14))],
        [sg.Listbox(opcoes, size=(80, 6), key="-ESCOLHA-")],
        [sg.Button("Gerar", button_color=('white', escuro)),
         sg.Button("Cancelar", button_color=('white', escuro))]
    ]
    
    window = sg.Window("Selecionar", layout, modal=True, finalize=True)
    
    continuar = True
    while continuar:
        event, values = window.read()
        
        if event == sg.WINDOW_CLOSED or event == "Cancelar":
            continuar = False
        
        elif event == "Gerar":
            if not values["-ESCOLHA-"]:
                sg.popup_error("Selecione", title="Erro")
            else:
                escolha = values["-ESCOLHA-"][0]
                window.close()
                
                if "Simulação Atual" in escolha:
                    dados = estado_simulacao.get("dados_historicos", [])
                    if dados:
                        mostrar_graficos_simulacao(dados, "Simulação Atual")
                    else:
                        sg.popup_error("Sem dados", title="Erro")
                else:
                    encontrou = False
                    i = 0
                    while i < len(estado_simulacao["resultados_simulacoes"]) and not encontrou:
                        sim = estado_simulacao["resultados_simulacoes"][i]
                        config = sim.get("configuracao", {})
                        timestamp = sim.get("timestamp", "")
                        resultados = sim.get("resultados_finais", {})
                        
                        data_formatada = timestamp[:16]
                        texto_sim = f"λ={config.get('lambda_chegada', 0)} M={config.get('num_medicos', 0)} {data_formatada}"
                        
                        if texto_sim == escolha:
                            dados = sim.get("dados_historicos", [])
                            if dados:
                                titulo = f"λ={config.get('lambda_chegada', 0)}"
                                mostrar_graficos_simulacao(dados, titulo)
                            else:
                                sg.popup_error("Sem dados", title="Erro")
                            encontrou = True
                        
                        i = i + 1
                    
                    if not encontrou:
                        sg.popup_error("Não encontrada", title="Erro")
                
                continuar = False
    
    window.close()
def comparar_simulacoes():
    """Comparar simulações com gráficos completos por abas - VERSÃO CORRIGIDA"""
    resultados = estado_simulacao.get("resultados_simulacoes", [])
    
    if len(resultados) < 2:
        sg.popup_error("Precisa de pelo menos 2 simulações para comparar!", title="Erro")
        return
    
    sg.theme('TemaClinica')
    
    simulacoes_lista = []
    i = 0
    while i < len(resultados):
        sim = resultados[i]
        config = sim.get("configuracao", {})
        timestamp = sim.get("timestamp", "")
        
        try:
            data_obj = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
            data_formatada = data_obj.strftime("%d/%m %H:%M")
        except:
            data_formatada = timestamp[:16]
        
        texto = f"[{i+1}] λ={config.get('lambda_chegada', 0):.1f} M={config.get('num_medicos', 0)} {data_formatada}"
        simulacoes_lista.append(texto)
        i = i + 1
    
    layout_selecao = [
        [sg.Text("Comparar Simulações", font=("Helvetica", 16), justification="center", expand_x=True)],
        [sg.Text("Selecione 2 ou mais simulações para comparar:")],
        [sg.Listbox(simulacoes_lista, size=(90, 8), key="-LISTA-", select_mode=sg.LISTBOX_SELECT_MODE_MULTIPLE)],
        [sg.Button("Comparar Gráficos", size=(18,1), button_color=('white', escuro)),
         sg.Button("Comparar Relatório", size=(18,1), button_color=('white', escuro)),
         sg.Button("Fechar", size=(12,1), button_color=('white', escuro))]
    ]
    
    window_selecao = sg.Window("Comparar Simulações", layout_selecao, modal=True, finalize=True, keep_on_top=True)
    
    indices_selecionados = []
    
    continuar_selecao = True
    while continuar_selecao:
        event_selecao, values_selecao = window_selecao.read()
        
        if event_selecao in (sg.WINDOW_CLOSED, "Fechar"):
            continuar_selecao = False
        
        elif event_selecao == "Comparar Gráficos":
            if not values_selecao["-LISTA-"] or len(values_selecao["-LISTA-"]) < 2:
                sg.popup_error("Selecione pelo menos 2 simulações!", title="Erro")
            else:
                indices_selecionados = []
                selecao_idx = 0
                while selecao_idx < len(values_selecao["-LISTA-"]):
                    selecao = values_selecao["-LISTA-"][selecao_idx]
                    
                    idx = 0
                    while idx < len(simulacoes_lista):
                        if simulacoes_lista[idx] == selecao:
                            indices_selecionados.append(idx)
                        idx = idx + 1
                    
                    selecao_idx = selecao_idx + 1
                
                if len(indices_selecionados) >= 2:
                    window_selecao.close()
                    continuar_selecao = False
                else:
                    sg.popup_error("Não foi possível identificar as simulações selecionadas!", title="Erro")
        
        elif event_selecao == "Comparar Relatório":
            if not values_selecao["-LISTA-"] or len(values_selecao["-LISTA-"]) < 2:
                sg.popup_error("Selecione pelo menos 2 simulações!", title="Erro")
            else:
                indices_relatorio = []
                selecao_idx = 0
                while selecao_idx < len(values_selecao["-LISTA-"]):
                    selecao = values_selecao["-LISTA-"][selecao_idx]
                    
                    idx = 0
                    while idx < len(simulacoes_lista):
                        if simulacoes_lista[idx] == selecao:
                            indices_relatorio.append(idx)
                        idx = idx + 1
                    
                    selecao_idx = selecao_idx + 1
                
                if len(indices_relatorio) >= 2:
                    window_selecao.close()
                    mostrar_relatorio_comparativo(indices_relatorio)
                    continuar_selecao = False
    
    window_selecao.close()

    if not indices_selecionados:
        return

    simulacoes = []
    cores = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray']
    legendas = []
    
    idx_selecao = 0
    while idx_selecao < len(indices_selecionados):
        idx = indices_selecionados[idx_selecao]
        if idx < len(estado_simulacao["resultados_simulacoes"]):
            sim = estado_simulacao["resultados_simulacoes"][idx]
            if sim.get("dados_historicos"):
                simulacoes.append(sim)
                
                config = sim["configuracao"]
                legendas.append(f"λ={config.get('lambda_chegada', 0):.1f} M={config.get('num_medicos', 0)}")
        
        idx_selecao = idx_selecao + 1
    
    if len(simulacoes) < 2:
        sg.popup_error("Dados insuficientes para comparação!", title="Erro")
        return

    dados_por_simulacao = []
    
    i = 0
    while i < len(simulacoes):
        sim = simulacoes[i]
        dados = sim.get("dados_historicos", [])
        
        tempos = []
        fila_tamanhos = []
        taxas_ocupacao = []
        atendidos_lista = []
        desistentes_lista = []
        tempos_espera = []
        
        dados_idx = 0
        while dados_idx < len(dados):
            registro = dados[dados_idx]
            if isinstance(registro, dict):

                tempo_val = registro.get("tempo")
                if tempo_val is not None and isinstance(tempo_val, (int, float)):
                    tempos.append(float(tempo_val))
                else:
                    tempos.append(0.0)

                fila_val = registro.get("fila_tamanho")
                if fila_val is not None and isinstance(fila_val, (int, float)):
                    fila_tamanhos.append(float(fila_val))
                else:
                    fila_tamanhos.append(0.0)
                

                ocupacao_val = registro.get("taxa_ocupacao")
                
                if ocupacao_val is not None and isinstance(ocupacao_val, (int, float)):

                    ocupacao_val = float(ocupacao_val)
                    ocupacao_val = min(100.0, max(0.0, ocupacao_val))
                    taxas_ocupacao.append(ocupacao_val)
                else:

                    taxas_ocupacao.append(0.0)

                atendidos_val = registro.get("atendidos")
                if atendidos_val is not None and isinstance(atendidos_val, (int, float)):
                    atendidos_lista.append(int(atendidos_val))
                else:
                    atendidos_lista.append(0)
                

                desistentes_val = registro.get("desistentes")
                if desistentes_val is not None and isinstance(desistentes_val, (int, float)):
                    desistentes_lista.append(int(desistentes_val))
                else:
                    desistentes_lista.append(0)
               

                espera_val = registro.get("tempo_medio_espera")
                if espera_val is not None and isinstance(espera_val, (int, float)):
                    tempos_espera.append(float(espera_val))
                else:
                    tempos_espera.append(0.0)
            
            dados_idx = dados_idx + 1
        
        dados_por_simulacao.append({
            "tempos": tempos,
            "fila_tamanhos": fila_tamanhos,
            "taxas_ocupacao": taxas_ocupacao,
            "atendidos_lista": atendidos_lista,
            "desistentes_lista": desistentes_lista,
            "tempos_espera": tempos_espera,
            "cor": cores[i % len(cores)],
            "legenda": legendas[i],
            "resultados_finais": sim.get("resultados_finais", {})
        })
        
        i = i + 1
    
    tab1_layout = [
        [sg.Text("Comparação: Tamanho da Fila", font=("Helvetica", 14))],
        [sg.Canvas(key="-CANVAS_COMP_FILA-", size=(700, 450), expand_x=True, expand_y=True)]
    ]
    
    tab2_layout = [
        [sg.Text("Comparação: Taxa de Ocupação", font=("Helvetica", 14))],
        [sg.Canvas(key="-CANVAS_COMP_OCUPACAO-", size=(700, 450), expand_x=True, expand_y=True)]
    ]
    
    tab3_layout = [
        [sg.Text("Comparação: Atendidos vs Tempo", font=("Helvetica", 14))],
        [sg.Canvas(key="-CANVAS_COMP_ATENDIDOS-", size=(700, 450), expand_x=True, expand_y=True)]
    ]
    
    tab4_layout = [
        [sg.Text("Comparação: Tempo de Espera", font=("Helvetica", 14))],
        [sg.Canvas(key="-CANVAS_COMP_ESPERA-", size=(700, 450), expand_x=True, expand_y=True)]
    ]
    
    tab5_layout = [
        [sg.Text("Comparação: Resumo Final", font=("Helvetica", 14))],
        [sg.Canvas(key="-CANVAS_COMP_RESUMO-", size=(700, 450), expand_x=True, expand_y=True)]
    ]
    
    layout_principal = [
        [sg.Text(f"Comparação de {len(simulacoes)} Simulações", font=("Helvetica", 16), justification="center", expand_x=True)],
        [sg.TabGroup([
            [sg.Tab('Fila', tab1_layout)],
            [sg.Tab('Ocupação', tab2_layout)],
            [sg.Tab('Atendidos', tab3_layout)],
            [sg.Tab('Espera', tab4_layout)],
            [sg.Tab('Resumo', tab5_layout)]
        ], expand_x=True, expand_y=True)],
        [
            sg.Button("Exportar Dados", size=(16,1), button_color=('white', escuro)),
            sg.Button("Fechar", size=(12,1), button_color=('white', escuro))
        ]
    ]
    
    window_principal = sg.Window("Comparação de Simulações", layout_principal, modal=True, finalize=True, 
                      size=(800, 600), resizable=True, keep_on_top=True)
    
    # Gráfico 1: Tamanho da Fila
    fig1 = Figure(figsize=(8, 5), dpi=100)
    ax1 = fig1.add_subplot(111)
    
    i = 0
    while i < len(dados_por_simulacao):
        dados = dados_por_simulacao[i]
        tempos = dados["tempos"]
        fila_tamanhos = dados["fila_tamanhos"]
        
        if len(tempos) > 200:
            tempos_reduzidos = []
            fila_reduzida = []
            passo = len(tempos) // 200
            j = 0
            while j < len(tempos):
                tempos_reduzidos.append(tempos[j])
                fila_reduzida.append(fila_tamanhos[j])
                j = j + passo
            tempos = tempos_reduzidos
            fila_tamanhos = fila_reduzida
        
        ax1.plot(tempos, fila_tamanhos, color=dados["cor"], linewidth=2, label=dados["legenda"])
        i = i + 1
    
    ax1.set_xlabel('Tempo (minutos)')
    ax1.set_ylabel('Pacientes na Fila')
    ax1.set_title('Comparação: Tamanho da Fila')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    fig1.tight_layout()
    
    canvas1 = fig_tk.FigureCanvasTkAgg(fig1, window_principal["-CANVAS_COMP_FILA-"].TKCanvas)
    canvas1.draw()
    canvas1.get_tk_widget().pack(side='top', fill='both', expand=True)
    

    fig2 = Figure(figsize=(8, 5), dpi=100)
    ax2 = fig2.add_subplot(111)
    
    i = 0
    while i < len(dados_por_simulacao):
        dados = dados_por_simulacao[i]
        tempos = dados["tempos"]
        taxas_ocupacao = dados["taxas_ocupacao"]
        

        tamanho_min = min(len(tempos), len(taxas_ocupacao))
        if tamanho_min > 0:
            tempos_ajustados = tempos[:tamanho_min]
            ocupacao_ajustada = taxas_ocupacao[:tamanho_min]
            

            ocupacao_validada = []
            j = 0
            while j < len(ocupacao_ajustada):
                val = ocupacao_ajustada[j]
                val = min(100.0, max(0.0, float(val)))
                ocupacao_validada.append(val)
                j = j + 1
            

            if len(tempos_ajustados) > 200:
                tempos_reduzidos = []
                ocupacao_reduzida = []
                passo = len(tempos_ajustados) // 200
                j = 0
                while j < len(tempos_ajustados):
                    tempos_reduzidos.append(tempos_ajustados[j])
                    ocupacao_reduzida.append(ocupacao_validada[j])
                    j = j + passo
                tempos_ajustados = tempos_reduzidos
                ocupacao_validada = ocupacao_reduzida
            

            if tempos_ajustados and ocupacao_validada:
                ax2.plot(tempos_ajustados, ocupacao_validada, color=dados["cor"], linewidth=2, label=dados["legenda"])
        
        i = i + 1
    
    ax2.set_xlabel('Tempo (minutos)')
    ax2.set_ylabel('Taxa de Ocupação (%)')
    ax2.set_title('Comparação: Taxa de Ocupação')
    ax2.legend()
    ax2.set_ylim(0, 100)
    ax2.grid(True, alpha=0.3)
    fig2.tight_layout()
    
    canvas2 = fig_tk.FigureCanvasTkAgg(fig2, window_principal["-CANVAS_COMP_OCUPACAO-"].TKCanvas)
    canvas2.draw()
    canvas2.get_tk_widget().pack(side='top', fill='both', expand=True)
    

    fig3 = Figure(figsize=(8, 5), dpi=100)
    ax3 = fig3.add_subplot(111)
    
    i = 0
    while i < len(dados_por_simulacao):
        dados = dados_por_simulacao[i]
        tempos = dados["tempos"]
        atendidos = dados["atendidos_lista"]
        
        tamanho_min = min(len(tempos), len(atendidos))
        if tamanho_min > 0:
            tempos_ajustados = tempos[:tamanho_min]
            atendidos_ajustados = atendidos[:tamanho_min]
        
            if len(tempos_ajustados) > 200:
                tempos_reduzidos = []
                atendidos_reduzidos = []
                passo = len(tempos_ajustados) // 200
                j = 0
                while j < len(tempos_ajustados):
                    tempos_reduzidos.append(tempos_ajustados[j])
                    atendidos_reduzidos.append(atendidos_ajustados[j])
                    j = j + passo
                tempos_ajustados = tempos_reduzidos
                atendidos_ajustados = atendidos_reduzidos
            
            ax3.plot(tempos_ajustados, atendidos_ajustados, color=dados["cor"], linewidth=2, label=dados["legenda"])
        
        i = i + 1
    
    ax3.set_xlabel('Tempo (minutos)')
    ax3.set_ylabel('Pacientes Atendidos')
    ax3.set_title('Comparação: Pacientes Atendidos')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    fig3.tight_layout()
    
    canvas3 = fig_tk.FigureCanvasTkAgg(fig3, window_principal["-CANVAS_COMP_ATENDIDOS-"].TKCanvas)
    canvas3.draw()
    canvas3.get_tk_widget().pack(side='top', fill='both', expand=True)


    fig4 = Figure(figsize=(8, 5), dpi=100)
    ax4 = fig4.add_subplot(111)
    
    i = 0
    while i < len(dados_por_simulacao):
        dados = dados_por_simulacao[i]
        tempos = dados["tempos"]
        tempos_espera = dados["tempos_espera"]

        tempos_filtrados = []
        espera_filtrada = []
        j = 0
        while j < len(tempos_espera):
            if j < len(tempos) and tempos_espera[j] > 0:
                tempos_filtrados.append(tempos[j])
                espera_filtrada.append(tempos_espera[j])
            j = j + 1
        
        if tempos_filtrados:
            if len(tempos_filtrados) > 200:
                tempos_reduzidos = []
                espera_reduzida = []
                passo = len(tempos_filtrados) // 200
                k = 0
                while k < len(tempos_filtrados):
                    tempos_reduzidos.append(tempos_filtrados[k])
                    espera_reduzida.append(espera_filtrada[k])
                    k = k + passo
                tempos_filtrados = tempos_reduzidos
                espera_filtrada = espera_reduzida
            
            ax4.plot(tempos_filtrados, espera_filtrada, color=dados["cor"], linewidth=2, label=dados["legenda"])
        
        i = i + 1
    
    ax4.set_xlabel('Tempo (minutos)')
    ax4.set_ylabel('Tempo de Espera (minutos)')
    ax4.set_title('Comparação: Tempo Médio de Espera')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    fig4.tight_layout()
    
    canvas4 = fig_tk.FigureCanvasTkAgg(fig4, window_principal["-CANVAS_COMP_ESPERA-"].TKCanvas)
    canvas4.draw()
    canvas4.get_tk_widget().pack(side='top', fill='both', expand=True)


    fig5 = Figure(figsize=(8, 5), dpi=100)
    ax5 = fig5.add_subplot(111)
    
    nomes_simulacoes = []
    atendidos_finais = []
    desistentes_finais = []
    ocupacao_media = []
    tempo_espera_medio = []
    
    i = 0
    while i < len(simulacoes):
        sim = simulacoes[i]
        resultados = sim.get("resultados_finais", {})
        
        nomes_simulacoes.append(f"Sim {i+1}")
        atendidos_finais.append(resultados.get("atendidos", 0))
        desistentes_finais.append(resultados.get("desistentes", 0))

        ocupacao_val = resultados.get("taxa_ocupacao_media", 0)
        if isinstance(ocupacao_val, (int, float)):
            ocupacao_val = float(ocupacao_val)
            ocupacao_val = min(100.0, max(0.0, ocupacao_val))
            ocupacao_media.append(ocupacao_val)
        else:
            ocupacao_media.append(0.0)
        
        tempo_espera = resultados.get("tempo_medio_espera", 0)
        if isinstance(tempo_espera, (int, float)):
            tempo_espera_medio.append(float(tempo_espera))
        else:
            tempo_espera_medio.append(0.0)
        
        i = i + 1

    x = np.arange(len(nomes_simulacoes))
    largura = 0.2
    
    ax5.bar(x - largura*1.5, atendidos_finais, largura, label='Atendidos', color='green', alpha=0.7)
    ax5.bar(x - largura*0.5, desistentes_finais, largura, label='Desistentes', color='red', alpha=0.7)
    ax5.bar(x + largura*0.5, ocupacao_media, largura, label='Ocupação Média (%)', color=escuro, alpha=0.7)
    ax5.bar(x + largura*1.5, tempo_espera_medio, largura, label='Espera Média (min)', color='orange', alpha=0.7)
    
    ax5.set_xlabel('Simulação')
    ax5.set_ylabel('Valores')
    ax5.set_title('Resumo Comparativo Final')
    ax5.set_xticks(x)
    ax5.set_xticklabels(nomes_simulacoes)
    ax5.legend()
    ax5.grid(True, alpha=0.3, axis='y')

    for idx, (atend, desist, ocup, espera) in enumerate(zip(atendidos_finais, desistentes_finais, ocupacao_media, tempo_espera_medio)):
        ax5.text(idx - largura*1.5, atend + 1, str(atend), ha='center', fontsize=9)
        ax5.text(idx - largura*0.5, desist + 0.5, str(desist), ha='center', fontsize=9)
        ax5.text(idx + largura*0.5, ocup + 1, f"{ocup:.0f}%", ha='center', fontsize=9)
        ax5.text(idx + largura*1.5, espera + 0.5, f"{espera:.0f}", ha='center', fontsize=9)
    
    fig5.tight_layout()
    
    canvas5 = fig_tk.FigureCanvasTkAgg(fig5, window_principal["-CANVAS_COMP_RESUMO-"].TKCanvas)
    canvas5.draw()
    canvas5.get_tk_widget().pack(side='top', fill='both', expand=True)
    
    continuar_principal = True
    while continuar_principal:
        event_principal, values_principal = window_principal.read()
        
        if event_principal in (sg.WINDOW_CLOSED, "Fechar"):
            continuar_principal = False
        
        elif event_principal == "Exportar Dados":
            dados_texto = "Simulação;Atendidos;Desistentes;Ocupação Média;Espera Média;Fila Máxima\n"
            i = 0
            while i < len(simulacoes):
                sim = simulacoes[i]
                config = sim["configuracao"]
                resultados = sim["resultados_finais"]
                
                dados_texto += f"Sim{i+1}_λ={config.get('lambda_chegada', 0):.1f};"
                dados_texto += f"{resultados.get('atendidos', 0)};"
                dados_texto += f"{resultados.get('desistentes', 0)};"
                dados_texto += f"{resultados.get('taxa_ocupacao_media', 0):.1f}%;"
                dados_texto += f"{resultados.get('tempo_medio_espera', 0):.1f};"
                dados_texto += f"{resultados.get('fila_maxima', 0)}\n"
                
                i = i + 1
            
            nome_arquivo = f"dados_comparacao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            arquivo_salvo = salvar_arquivo(dados_texto, nome_arquivo)
            if arquivo_salvo:
                sg.popup(f"Dados exportados para:\n{arquivo_salvo}", title="Sucesso", keep_on_top=True)
    
    window_principal.close()
def gerar_graficos_comparativos(indices):
    """Gráfico comparativo simples"""
    
    
    simulacoes = []
    idx_selecao = 0
    while idx_selecao < len(indices):
        idx = indices[idx_selecao]
        if idx < len(estado_simulacao["resultados_simulacoes"]):
            sim = estado_simulacao["resultados_simulacoes"][idx]
            if sim.get("dados_historicos"):
                simulacoes.append(sim)
        idx_selecao = idx_selecao + 1
    
    if len(simulacoes) < 2:
        sg.popup_error("Dados insuficientes", title="Erro")
        return
    
    
    layout = [
        [sg.Text("Comparação", font=("Helvetica", 14))],
        [sg.Canvas(key="-CANVAS-", size=(700, 500))],
        [sg.Button("Fechar", button_color=('white', escuro))]
    ]
    
    window = sg.Window("Comparação", layout, modal=True, finalize=True, size=(800, 600))
    
   
    fig = Figure(figsize=(8, 5), dpi=100)
    ax = fig.add_subplot(111)
    
    cores = ['blue', 'red', 'green', 'orange', 'purple']
    
    i = 0
    while i < len(simulacoes):
        sim = simulacoes[i]
        config = sim["configuracao"]
        dados = sim["dados_historicos"]
        
        
        tempos = []
        fila_tamanhos = []
        
        dados_idx = 0
        while dados_idx < len(dados):
            registro = dados[dados_idx]
            if isinstance(registro, dict):
                tempo_val = registro.get("tempo")
                fila_val = registro.get("fila_tamanho")
                
                if tempo_val is not None and fila_val is not None:
                    if isinstance(tempo_val, (int, float)) and isinstance(fila_val, (int, float)):
                        tempos.append(float(tempo_val))
                        fila_tamanhos.append(float(fila_val))
            
            dados_idx = dados_idx + 1
        
        if tempos and fila_tamanhos:
           
            if len(tempos) > 500:
                tempos_red = []
                fila_red = []
                j = 0
                while j < len(tempos):
                    tempos_red.append(tempos[j])
                    fila_red.append(fila_tamanhos[j])
                    j = j + 2  
                tempos = tempos_red
                fila_tamanhos = fila_red
            
            label = f"λ={config.get('lambda_chegada', 0):.1f}"
            cor = cores[i % len(cores)]
            ax.plot(tempos, fila_tamanhos, color=cor, linewidth=2, label=label)
        
        i = i + 1
    
    ax.set_xlabel('Tempo (minutos)')
    ax.set_ylabel('Pacientes na Fila')
    ax.set_title('Comparação - Tamanho da Fila')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    fig.tight_layout()
    canvas = fig_tk.FigureCanvasTkAgg(fig, window["-CANVAS-"].TKCanvas)
    canvas.draw()
    canvas.get_tk_widget().pack(side='top', fill='both', expand=True)
    
    continuar = True
    while continuar:
        event, values = window.read()
        if event == sg.WINDOW_CLOSED or event == "Fechar":
            continuar = False
    
    window.close()

def mostrar_relatorio_comparativo(indices_simulacoes):
    sg.theme('TemaClinica')
    
    relatorio = ["RELATÓRIO COMPARATIVO DE SIMULAÇÕES\n" + "="*50 + "\n"]
    relatorio.append(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
    
    for i, idx in enumerate(indices_simulacoes):
        simulacao = estado_simulacao["resultados_simulacoes"][idx]
        config = simulacao["configuracao"]
        resultados = simulacao["resultados_finais"]
        
        relatorio.append(f"\nSIMULAÇÃO {i+1}:")
        relatorio.append(f"Data/Hora: {simulacao['timestamp']}")
        relatorio.append(f"Lambda (chegadas/hora): {config['lambda_chegada']}")
        relatorio.append(f"Número de médicos: {config['num_medicos']}")
        relatorio.append(f"Tempo médio consulta: {config['tempo_medio_consulta']} min")
        relatorio.append(f"Distribuição: {config.get('distribuicao', 'exponential')}")
        relatorio.append(f"Tempo simulação: {config['tempo_simulacao']} min")
        relatorio.append(f"Pausas: {config.get('num_pausas', 0)} pausas de {config.get('duracao_pausa', 0)} min")
        relatorio.append(f"Máx. médicos em pausa simultânea: {config.get('max_pausa_simultanea', 2)}")
        relatorio.append("\nRESULTADOS:")
        relatorio.append(f"- Pacientes atendidos: {resultados['atendidos']}")
        relatorio.append(f"- Pacientes desistentes: {resultados['desistentes']}")
        relatorio.append(f"- Taxa ocupação média: {resultados['taxa_ocupacao_media']:.1f}%")
        relatorio.append(f"- Fila máxima: {resultados['fila_maxima']} pacientes")
        relatorio.append(f"- Tempo médio espera: {resultados['tempo_medio_espera']:.1f} min")
        relatorio.append("-" * 50)
    
    relatorio.append("\n\nANÁLISE COMPARATIVA:")
    relatorio.append("=" * 50)
    
    simulacoes_selecionadas = []
    for idx in indices_simulacoes:
        simulacoes_selecionadas.append(estado_simulacao["resultados_simulacoes"][idx])
    
    melhor_atendimento = max(simulacoes_selecionadas, key=lambda x: x["resultados_finais"]["atendidos"])
    idx_melhor = simulacoes_selecionadas.index(melhor_atendimento)
    
    relatorio.append(f"• Melhor taxa de atendimento: Simulação {idx_melhor + 1} ({melhor_atendimento['resultados_finais']['atendidos']} pacientes)")
    
    menor_espera = min(simulacoes_selecionadas, key=lambda x: x["resultados_finais"]["tempo_medio_espera"])
    idx_menor = simulacoes_selecionadas.index(menor_espera)
    
    relatorio.append(f"• Menor tempo de espera: Simulação {idx_menor + 1} ({menor_espera['resultados_finais']['tempo_medio_espera']:.1f} min)")
    
    melhor_ocupacao = max(simulacoes_selecionadas, key=lambda x: x["resultados_finais"]["taxa_ocupacao_media"])
    idx_ocupacao = simulacoes_selecionadas.index(melhor_ocupacao)
    
    relatorio.append(f"• Melhor taxa de ocupação: Simulação {idx_ocupacao + 1} ({melhor_ocupacao['resultados_finais']['taxa_ocupacao_media']:.1f}%)")
    
    menor_desistencia = min(simulacoes_selecionadas, key=lambda x: x["resultados_finais"]["desistentes"])
    idx_desistencia = simulacoes_selecionadas.index(menor_desistencia)
    
    relatorio.append(f"• Menor desistência: Simulação {idx_desistencia + 1} ({menor_desistencia['resultados_finais']['desistentes']} pacientes)")
    
    texto_relatorio = "\n".join(relatorio)
    
    layout = [
        [sg.Text("Relatório Comparativo", font=("Helvetica", 16), justification="center", expand_x=True)],
        [sg.Multiline(texto_relatorio, size=(80, 25), key="-RELATORIO-", font=("Courier", 10))],
        [sg.Button("Exportar para Arquivo", size=(20,1), button_color=('white',escuro)),
         sg.Button("Fechar", size=(12,1), button_color=('white',escuro))]
    ]
    
    window = sg.Window("Relatório Comparativo", layout, modal=True, resizable=True, keep_on_top=True)
    
    continuar = True
    while continuar:
        event, values = window.read()
        
        if event in (sg.WINDOW_CLOSED, "Fechar"):
            continuar = False
        
        elif event == "Exportar para Arquivo":
            nome_arquivo = f"relatorio_comparativo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            arquivo_salvo = salvar_arquivo(texto_relatorio, nome_arquivo)
            if arquivo_salvo:
                sg.popup(f"Relatório exportado para:\n{arquivo_salvo}", title="Sucesso")
            else:
                sg.popup_error("Falha ao salvar o relatório.", title="Erro")
    
    window.close()




def criar_layout_principal():
    sg.theme('TemaClinica')

    medicos_dataset = carregar_medicos_simula()
    num_medicos = len(medicos_dataset)

    col_esquerda = [
        [sg.Frame("Controlos da Simulação", [
            [sg.Button("Iniciar", expand_x=True, size=(8,1), button_color=('white',escuro), key="-PLAY-"),
             sg.Button("Pausar", expand_x=True, size=(8,1), button_color=('white',escuro), key="-PAUSE-", disabled=True)],
            [sg.Button("Parar", expand_x=True, size=(8,1), button_color=('white',escuro), key="-STOP-", disabled=True),
             sg.Button("Configurar", expand_x=True, size=(8,1), button_color=('white',escuro), key="-CONFIG-")],
            [sg.Text("Tempo:", size=(8,1)),
             sg.Text("0 / 0 min", key="-TEMPO-", expand_x=True, font=('Helvetica', 11, 'bold'))],
            [sg.Text("Progresso:")],
            [sg.ProgressBar(100, orientation='h', size=(18, 12), key="-PROGRESSO-", expand_x=True, bar_color=(escuro,claro))],
        ], expand_x=True, pad=(8,8))],

        [sg.Frame("Estatísticas em Tempo Real", [
            [sg.Text("Atendidos:", size=(15,1)), sg.Text("0", key="-ATENDIDOS-", font=('Helvetica', 11, 'bold'))],
            [sg.Text("Na fila:", size=(15,1)), sg.Text("0", key="-FILA-", font=('Helvetica', 11, 'bold'), text_color='orange')],
            [sg.Text("Desistentes:", size=(15,1)), sg.Text("0", key="-DESISTENTES-", font=('Helvetica', 11, 'bold'), text_color='red')],
            [sg.Text("A aguardar:", size=(15,1)), sg.Text("0", key="-AGUARDANDO-", font=('Helvetica', 11, 'bold'), text_color=escuro)],
            [sg.HorizontalSeparator()],
            [sg.Text("Tempo médio:", size=(15,1)), sg.Text("0 min", key="-TEMPO_MEDIO-")],
            [sg.Text("Taxa ocupação:", size=(15,1)), sg.Text("0%", key="-TAXA_OCUP-")],
        ], expand_x=True, pad=(8,8))],

        [sg.Frame("Análise e Ações", [
            [sg.Button("Gráficos", expand_x=True, size=(25,1), button_color=('white',escuro), key="-GRAFICOS-")],
            [sg.Button("Comparar Simulações", expand_x=True, size=(25,1), button_color=('white',escuro), key="-COMPARAR-")],
            [sg.Button("Lista de Atendimentos", expand_x=True, size=(25,1), button_color=('white',escuro), key="-LISTA_ATENDIMENTOS-", tooltip="Mostra a lista de pacientes atendidos por médico")],
            [sg.Button("Estatísticas Especialidades", expand_x=True, size=(25,1), button_color=('white',escuro), key="-ESTAT_ESPECIALIDADES-", tooltip="Mostra estatísticas detalhadas por especialidade médica")],
            [sg.Button("Desempenho Médicos", expand_x=True, size=(25,1), button_color=('white',escuro), key="-DESEMPENHO_MEDICOS-", tooltip="Mostra análise gráfica de desempenho médico")],
            [sg.Button("Análise Fila vs Taxa", expand_x=True, size=(25,1), button_color=('white',escuro), key="-ANALISE_FILA_TAXA-", tooltip="Análise do tamanho médio da fila vs taxa de chegada")],
            [sg.Button("Fechar", expand_x=True, size=(25,1), button_color=('white',escuro), key="-FECHAR-", tooltip="Fecha a aplicação de simulação")]
        ], expand_x=True, pad=(8,8))]
    ]

    col_central = [
        [sg.Frame("Estado da Equipa Médica", [
            [sg.Column(
                [
                    [sg.Text(f"Médico {i+1:02d}", key=f"-M{i}-NOME-", size=(20,1), font=('Helvetica', 9, 'bold')),
                     sg.VerticalSeparator(),
                     sg.Text("Livre", key=f"-M{i}-STATUS-", size=(25,1), text_color='green', font=('Helvetica', 9))]
                    for i in range(num_medicos)
                ],
                scrollable=True, 
                vertical_scroll_only=True, 
                size=(None, 400),  
                expand_x=False,
                expand_y=False,
                pad=(4,4)
            )]
        ], size=(300, 450), pad=(8,8))]  
    ]

    col_direita = [
        [sg.Frame("Fila de Espera em Tempo Real", [
            [sg.Listbox(values=[], size=(60, 18), key="-FILA_LISTA-", enable_events=True, 
                    expand_x=True, font=('Consolas', 9), no_scrollbar=False)],
            [sg.Button("Remover da Fila", key="-REMOVER_FILA-", expand_x=True, 
                    button_color=('white',escuro), pad=(5, 10))],
        ], expand_x=True, pad=(8,8))],

        [sg.Frame("Detalhes do Paciente Selecionado", [
            [sg.Text("ID:", size=(10,1)), sg.Text("-", key="-PAC_ID-", text_color='blue', font=('Helvetica', 9, 'bold'))],
            [sg.Text("Nome:", size=(10,1)), sg.Text("-", key="-PAC_NOME-", font=('Helvetica', 9))],
            [sg.Text("Prioridade:", size=(10,1)), sg.Text("-", key="-PAC_PRIOR-", font=('Helvetica', 9))],
            [sg.Text("Doença:", size=(10,1)), sg.Text("-", key="-PAC_DOENCA-", font=('Helvetica', 9))],
            [sg.Text("Estado:", size=(10,1)), sg.Text("-", key="-PAC_STATUS-", font=('Helvetica', 9))],
            [sg.Text("Espera:", size=(10,1)), sg.Text("-", key="-PAC_ESPERA-", font=('Helvetica', 9))],
        ], expand_x=True, pad=(8,8))]
    ]

    layout = [
        [
            sg.Column(col_esquerda, expand_y=True, element_justification='left', vertical_alignment='top', size=(250, None)),
            sg.VSeparator(),
            sg.Column(col_central, expand_y=True, vertical_alignment='top'),
            sg.VSeparator(),
            sg.Column(col_direita, expand_y=True, vertical_alignment='top', size=(450, None))
        ]
    ]

    return layout
def atualizar_interface(window, stats):
    tempo_atual = stats["tempo_atual"]
    tempo_total = stats["tempo_simulacao"]
    
    tempo_max_espera = estado_simulacao.get("tempo_max_espera", TEMPO_MAX_ESPERA)
    
    window["-TEMPO-"].update(f"{tempo_atual:.0f} / {tempo_total:.0f} min")
    progresso = min(100, int((tempo_atual / tempo_total) * 100))
    window["-PROGRESSO-"].update(progresso)
    
    window["-ATENDIDOS-"].update(str(stats["doentes_atendidos"]))
    window["-FILA-"].update(str(stats["fila_len"]))
    window["-DESISTENTES-"].update(str(stats["desistentes"]))
    window["-AGUARDANDO-"].update(str(stats["aguardando"]))
    window["-TEMPO_MEDIO-"].update(f"{stats['tempo_medio_consulta']:.1f} min")
    window["-TAXA_OCUP-"].update(f"{stats['taxa_ocupacao']:.1f}%")
    
    for i in range(len(stats["medicos"])):
        m = stats["medicos"][i]
        nome = f"{m['nome']} ({m['especialidade']})"
        
        if m.get("em_pausa", False):
            status = "Em pausa"
            cor = 'orange'
        elif m["ocupado"]:
            pac_nome = estado_simulacao["pessoas_dados"].get(m["paciente_atual"], {}).get("nome", "")
            status = f"Ocupado: {pac_nome}"
            cor = 'red'
        else:
            status = "Livre"
            cor = 'green'

        window[f"-M{i}-NOME-"].update(nome)
        window[f"-M{i}-STATUS-"].update(status, text_color=cor)

    fila_display = []
    
    if not queue_empty(stats["fila_espera"]):
        fila_display.append(f"{'Pos.':<5} | {'Prior.':<8} | {'Nome':<20} | {'Especialidade':<20} | {'Espera':<10}")
        fila_display.append("-" * 85)
        
        for i, paciente in enumerate(stats["fila_espera"]):
            prior = paciente.get("prioridade", "NORMAL")
            
            if prior == "URGENTE":
                simbolo_prior = "URGENTE"
                cor_prior = "red"
            elif prior == "ALTA":
                simbolo_prior = "ALTA"
                cor_prior = "orange"
            elif prior == "NORMAL":
                simbolo_prior = "NORMAL"
                cor_prior = "blue"
            else:
                simbolo_prior = "BAIXA"
                cor_prior = "green"
            
            tempo_espera = tempo_atual - paciente.get("tempo_chegada", 0)
            nome = paciente.get('nome','')[:18]
            especialidade = paciente.get('especialidade_necessaria','')[:18]
            
            if tempo_espera >= 60:
                horas = int(tempo_espera // 60)
                minutos = int(tempo_espera % 60)
                tempo_formatado = f"{horas}h{minutos:02d}m"
            else:
                tempo_formatado = f"{tempo_espera:.0f}m"
            
            if tempo_espera > tempo_max_espera:
                linha = f"{i+1:<5} | {simbolo_prior:<8} | {nome:<20} | {especialidade:<20} |   {tempo_formatado:>8}"
            elif tempo_espera > tempo_max_espera * 0.7:
                linha = f"{i+1:<5} | {simbolo_prior:<8} | {nome:<20} | {especialidade:<20} |   {tempo_formatado:>7}"
            elif tempo_espera > tempo_max_espera * 0.5:
                linha = f"{i+1:<5} | {simbolo_prior:<8} | {nome:<20} | {especialidade:<20} |   {tempo_formatado:>7}"
            else:
                linha = f"{i+1:<5} | {simbolo_prior:<8} | {nome:<20} | {especialidade:<20} | {tempo_formatado:>9}"
            
            fila_display.append(linha)
        
        fila_por_especialidade = {}
        for paciente in stats["fila_espera"]:
            especialidade = paciente.get("especialidade_necessaria", "Clínica Geral")
            fila_por_especialidade[especialidade] = fila_por_especialidade.get(especialidade, 0) + 1
        
        if fila_por_especialidade:
            fila_display.append("-" * 85)
            fila_display.append("Resumo por especialidade na fila:")
            for especialidade, count in sorted(fila_por_especialidade.items()):
                tempos_especialidade = []
                for paciente in stats["fila_espera"]:
                    if paciente.get("especialidade_necessaria") == especialidade:
                        tempo_espera = tempo_atual - paciente.get("tempo_chegada", 0)
                        tempos_especialidade.append(tempo_espera)
                
                if tempos_especialidade:
                    tempo_medio = np.mean(tempos_especialidade)
                    if tempo_medio >= 60:
                        horas = int(tempo_medio // 60)
                        minutos = int(tempo_medio % 60)
                        tempo_medio_str = f"{horas}h{minutos:02d}m"
                    else:
                        tempo_medio_str = f"{tempo_medio:.0f}m"
                    
                    fila_display.append(f"  {especialidade[:18]:<18}: {count:>2} pacientes (média: {tempo_medio_str})")
                else:
                    fila_display.append(f"  {especialidade[:18]:<18}: {count:>2} pacientes")
    else:
        fila_display.append("A fila de espera está vazia.")
    
    window["-FILA_LISTA-"].update(values=fila_display)
    
    if estado_simulacao.get("paciente_selecionado"):
        atualizar_detalhes_paciente(window)

def atualizar_detalhes_paciente(window):
    paciente_id = estado_simulacao.get("paciente_selecionado")
    tempo_atual = estado_simulacao["tempo_atual"]
    
    tempo_max_espera = estado_simulacao.get("tempo_max_espera", TEMPO_MAX_ESPERA)
    
    pessoa = estado_simulacao["pessoas_dados"].get(paciente_id, None)
    if not pessoa:
        window["-PAC_ID-"].update("-")
        window["-PAC_NOME-"].update("-")
        window["-PAC_PRIOR-"].update("-")
        window["-PAC_DOENCA-"].update("-")
        window["-PAC_STATUS-"].update("-")
        window["-PAC_ESPERA-"].update("-")
        return
    
    window["-PAC_ID-"].update(pessoa.get("id", "-"))
    window["-PAC_NOME-"].update(pessoa.get("nome", "-"))
    window["-PAC_PRIOR-"].update(pessoa.get("prioridade", "-"))
    
    if "especialidade_necessaria" in pessoa:
        doenca = pessoa.get("doenca", "Consulta")
        especialidade = pessoa.get("especialidade_necessaria", "Geral")
        window["-PAC_DOENCA-"].update(f"{doenca[:20]} ({especialidade[:15]})")
    else:
        window["-PAC_DOENCA-"].update(pessoa.get("doenca", "-")[:30])
    

    atendido = False
    historico = estado_simulacao["historico_atendimentos"]
    i = 0
    while i < len(historico):
        if historico[i].get("paciente") == paciente_id:
            atendido = True
        i = i + 1

    na_fila = False
    fila = estado_simulacao["fila_espera"]
    j = 0
    while j < len(fila):
        if fila[j].get("id") == paciente_id:
            na_fila = True
        j = j + 1

    em_consulta = False
    medicos = estado_simulacao["medicos"]
    k = 0
    while k < len(medicos):
        if medicos[k].get("paciente_atual") == paciente_id:
            em_consulta = True
        k = k + 1
    

    desistente = False
    desistentes = estado_simulacao.get("pacientes_desistentes", [])
    l = 0
    while l < len(desistentes):
        if desistentes[l].get("id") == paciente_id:
            desistente = True
        l = l + 1
    
    if desistente:
        window["-PAC_STATUS-"].update("Desistente", text_color='red')
        window["-PAC_ESPERA-"].update("-")
    elif atendido and not em_consulta:
        window["-PAC_STATUS-"].update("Atendido", text_color='green')
        window["-PAC_ESPERA-"].update("-")
    elif em_consulta:
        window["-PAC_STATUS-"].update("Em consulta", text_color='blue')
        window["-PAC_ESPERA-"].update("-")
    elif na_fila:
        window["-PAC_STATUS-"].update("Na fila", text_color='orange')
        encontrou = False
        m = 0
        while m < len(fila) and not encontrou:
            if fila[m].get("id") == paciente_id:
                tempo_espera = tempo_atual - fila[m].get("tempo_chegada", 0)
                if tempo_espera > tempo_max_espera * 0.7:
                    window["-PAC_ESPERA-"].update(f"⚠ {tempo_espera:.0f} min", text_color='red')
                elif tempo_espera > tempo_max_espera * 0.5:
                    window["-PAC_ESPERA-"].update(f"{tempo_espera:.0f} min", text_color='orange')
                else:
                    window["-PAC_ESPERA-"].update(f"{tempo_espera:.0f} min", text_color='green')
                encontrou = True
            m = m + 1
    else:
        window["-PAC_STATUS-"].update("À espera", text_color='gray')
        window["-PAC_ESPERA-"].update("-")
def apagar_interface_principal(window):
    window["-TEMPO-"].update("0 / 0 min")
    window["-PROGRESSO-"].update(0)
    window["-ATENDIDOS-"].update("0")
    window["-FILA-"].update("0")
    window["-DESISTENTES-"].update("0")
    window["-AGUARDANDO-"].update("0")
    window["-TEMPO_MEDIO-"].update("0 min")
    window["-TAXA_OCUP-"].update("0%")
    
    window["-FILA_LISTA-"].update(values=[])
    
    window["-PAC_ID-"].update("-")
    window["-PAC_NOME-"].update("-")
    window["-PAC_PRIOR-"].update("-")
    window["-PAC_DOENCA-"].update("-")
    window["-PAC_STATUS-"].update("-")
    window["-PAC_ESPERA-"].update("-")
    
    for i in range(len(window.AllKeysDict)):
        if f"-M{i}-NOME-" in window.AllKeysDict:
            window[f"-M{i}-NOME-"].update(f"Médico {i+1:02d}")
            window[f"-M{i}-STATUS-"].update("Livre", text_color='green')
    
    window["-PLAY-"].update(disabled=False)
    window["-PAUSE-"].update(disabled=True)
    window["-STOP-"].update(disabled=True)




def janela_configuracao():
    medicos_dataset = carregar_medicos_simula()
    pacientes_dataset = carregar_pacientes_simula()
    default_num_medicos = len(medicos_dataset)
    max_pacientes = len(pacientes_dataset)
    
    tempo_sim_padrao = TEMPO_SIMULACAO / 60.0
    lambda_maximo = 0
    if tempo_sim_padrao > 0:
        lambda_maximo = max_pacientes / tempo_sim_padrao
    else:
        lambda_maximo = 100
    
    sg.theme('TemaClinica')
    
    conteudo_layout = [
        [sg.Text("CONFIGURAÇÃO DA SIMULAÇÃO", font=("Helvetica", 16, "bold"), justification="center", expand_x=True)],
        [sg.HorizontalSeparator()],
        [sg.Frame("Parâmetros de Chegada (Distribuição de Poisson)", [
            [sg.Text("Taxa de chegada (λ) pacientes/hora:", size=(30,1)),
             sg.Input(default_text=str(LAMBDA_CHEGADA), key="-LAMBDA-", size=(10,1))],
            [sg.Text(f"Taxa de chegada(λ) máxima recomendado: {lambda_maximo:.1f} (para usar todo o dataset)", 
                    font=("Helvetica", 9), text_color='blue')],
            [sg.Text(f"Simulação padrão: {TEMPO_SIMULACAO} min = {tempo_sim_padrao:.1f} horas", 
                    font=("Helvetica", 9))]
        ], expand_x=True)],
        [sg.Frame("Recursos e Tempo", [
            [sg.Text("Tempo médio consulta (min):", size=(30,1)),
             sg.Input(default_text=str(TEMPO_MEDIO_CONSULTA), key="-TEMPO_CONSULTA-", size=(10,1))],
            [sg.Text("Tempo de simulação (minutos):", size=(30,1)),
             sg.Input(default_text=str(TEMPO_SIMULACAO), key="-TEMPO_SIM-", size=(10,1))],
            [sg.Text("Número de médicos:", size=(30,1)),
             sg.Input(default_text=str(default_num_medicos), key="-NUM_MEDICOS-", size=(10,1))]
        ], expand_x=True)],
        [sg.Frame("Pausas dos Médicos", [
            [sg.Text("Frequência das pausas (min):", size=(30,1)),
             sg.Input(default_text=str(PAUSA_FREQUENCIA), key="-FREQ_PAUSA-", size=(10,1))],
            [sg.Text("Duração das pausas (min):", size=(30,1)),
             sg.Input(default_text=str(DURACAO_PAUSA), key="-DUR_PAUSA-", size=(10,1))],
            [sg.Text("Número de pausas por médico:", size=(30,1)),
             sg.Input(default_text=str(NUM_PAUSAS), key="-NUM_PAUSAS-", size=(10,1))],
            [sg.Text("Máx. médicos em pausa simultânea:", size=(30,1)),
             sg.Input(default_text=str(MAX_MEDICOS_PAUSA_SIMULTANEA), key="-MAX_PAUSA_SIM-", size=(10,1))],
            [sg.Text("IMPORTANTE:", font=("Helvetica", 9, 'bold'), text_color='red')],
            [sg.Text("• Máx. 1/3 dos médicos em pausa simultânea", font=("Helvetica", 9), text_color='red')],
            [sg.Text("• Duração: mínimo 15 min, máximo 20 min", font=("Helvetica", 9), text_color='blue')],
            [sg.Text("• Pelo menos 1 médico por especialidade a trabalhar", font=("Helvetica", 9), text_color='blue')]
        ], expand_x=True)],
        [sg.Frame("Regras de Abandono", [
            [sg.Text("Tempo máx. espera (min):", size=(30,1)),
             sg.Input(default_text=str(TEMPO_MAX_ESPERA), key="-TEMPO_MAX_ESPERA-", size=(10,1))],
            [sg.Text("Probabilidade de desistência:", size=(30,1)),
             sg.Input(default_text=str(PROB_DESISTENCIA), key="-PROB_DESISTENCIA-", size=(10,1))]
        ], expand_x=True)],
        [sg.Frame("Opções de Simulação", [
            [sg.Text("Distribuição tempo consulta:", size=(30,1)),
             sg.Radio("Exponencial", "DIST", default=True, key="-DIST_EXP"),
             sg.Radio("Normal", "DIST", key="-DIST_NORM"),
             sg.Radio("Uniforme", "DIST", key="-DIST_UNI-")]
        ], expand_x=True)],
        [sg.Frame("Configuração por Arquivo", [
            [sg.Text("Carregar configuração de arquivo JSON:", size=(30,1)),
             sg.Button("Carregar Config", size=(15,1), key="-CARREGAR_CONFIG-", button_color=('white',escuro)),
             sg.Button("Salvar Config", size=(15,1), key="-SALVAR_CONFIG-", button_color=('white',escuro))]
        ], expand_x=True)],
    ]

    layout_final = [
        [sg.Column(conteudo_layout, scrollable=True, vertical_scroll_only=True, size=(600, 450), key="-CONFIG-SCROLL-")],
        [sg.HorizontalSeparator()],
        [sg.Button("Confirmar", size=(15,1), button_color=('white', escuro)),
         sg.Button("Cancelar", size=(15,1), button_color=('white', escuro))]
    ]

    window = sg.Window("Configuração", layout_final, modal=True, finalize=True)
    
    resultado = None
    continuar = True

    while continuar:
        event, values = window.read()

        if event in (sg.WINDOW_CLOSED, "Cancelar"):
            resultado = None
            continuar = False

        elif event == "-CARREGAR_CONFIG-":
            config_carregada = carregar_configuracao_json()
            if config_carregada:
                if "lambda_chegada" in config_carregada:
                    window["-LAMBDA-"].update(str(config_carregada["lambda_chegada"]))
                if "tempo_medio_consulta" in config_carregada:
                    window["-TEMPO_CONSULTA-"].update(str(config_carregada["tempo_medio_consulta"]))
                if "tempo_simulacao" in config_carregada:
                    window["-TEMPO_SIM-"].update(str(config_carregada["tempo_simulacao"]))
                if "num_medicos" in config_carregada:
                    window["-NUM_MEDICOS-"].update(str(config_carregada["num_medicos"]))
                if "frequencia_pausa" in config_carregada:
                    window["-FREQ_PAUSA-"].update(str(config_carregada["frequencia_pausa"]))
                if "duracao_pausa" in config_carregada:
                    window["-DUR_PAUSA-"].update(str(config_carregada["duracao_pausa"]))
                if "num_pausas" in config_carregada:
                    window["-NUM_PAUSAS-"].update(str(config_carregada["num_pausas"]))
                if "max_pausa_simultanea" in config_carregada:
                    window["-MAX_PAUSA_SIM-"].update(str(config_carregada["max_pausa_simultanea"]))
                if "tempo_max_espera" in config_carregada:
                    window["-TEMPO_MAX_ESPERA-"].update(str(config_carregada["tempo_max_espera"]))
                if "prob_desistencia" in config_carregada:
                    window["-PROB_DESISTENCIA-"].update(str(config_carregada["prob_desistencia"]))
                if "distribuicao" in config_carregada:
                    dist = config_carregada["distribuicao"]
                    if dist == "exponential":
                        window["-DIST_EXP"].update(True)
                    elif dist == "normal":
                        window["-DIST_NORM"].update(True)
                    elif dist == "uniform":
                        window["-DIST_UNI-"].update(True)

        elif event == "-SALVAR_CONFIG-":
            dados_validos = True
            erro_mensagem = ""
            
            lambda_str = values["-LAMBDA-"].strip()
            num_medicos_str = values["-NUM_MEDICOS-"].strip()
            dur_pausa_str = values["-DUR_PAUSA-"].strip()
            max_pausa_str = values["-MAX_PAUSA_SIM-"].strip()
            tempo_consulta_str = values["-TEMPO_CONSULTA-"].strip()
            tempo_sim_str = values["-TEMPO_SIM-"].strip()
            freq_pausa_str = values["-FREQ_PAUSA-"].strip()
            num_pausas_str = values["-NUM_PAUSAS-"].strip()
            tempo_max_espera_str = values["-TEMPO_MAX_ESPERA-"].strip()
            prob_desistencia_str = values["-PROB_DESISTENCIA-"].strip()
            
            lambda_val = 10.0
            tempo_consulta_val = 15.0
            tempo_sim_val = 480.0
            num_medicos = 0
            freq_pausa_val = 60.0
            dur_pausa = 0.0
            num_pausas_val = 2
            max_pausa = 0
            tempo_max_espera_val = 30.0
            prob_desistencia_val = 0.3
            
            if not lambda_str:
                dados_validos = False
                erro_mensagem = "ERRO: Taxa de chegada (λ) não pode ser vazia!"
            elif not lambda_str.replace('.','',1).replace('-','',1).isdigit():
                dados_validos = False
                erro_mensagem = "ERRO: λ deve ser numérico!"
            else:
                lambda_val = float(lambda_str)
                if lambda_val < 0:
                    dados_validos = False
                    erro_mensagem = "ERRO: λ não pode ser negativo!"
                elif lambda_val == 0:
                    dados_validos = False
                    erro_mensagem = "ERRO: λ não pode ser zero!"
            
            if dados_validos:
                if not tempo_consulta_str:
                    dados_validos = False
                    erro_mensagem = "ERRO: Tempo consulta não pode ser vazio!"
                elif not tempo_consulta_str.replace('.','',1).replace('-','',1).isdigit():
                    dados_validos = False
                    erro_mensagem = "ERRO: Tempo consulta numérico!"
                else:
                    tempo_consulta_val = float(tempo_consulta_str)
                    if tempo_consulta_val < 0:
                        dados_validos = False
                        erro_mensagem = "ERRO: Tempo consulta não pode ser negativo!"
                    elif tempo_consulta_val == 0:
                        dados_validos = False
                        erro_mensagem = "ERRO: Tempo consulta não pode ser zero!"
            
            if dados_validos:
                if not tempo_sim_str:
                    dados_validos = False
                    erro_mensagem = "ERRO: Tempo simulação não pode ser vazio!"
                elif not tempo_sim_str.replace('.','',1).replace('-','',1).isdigit():
                    dados_validos = False
                    erro_mensagem = "ERRO: Tempo simulação numérico!"
                else:
                    tempo_sim_val = float(tempo_sim_str)
                    if tempo_sim_val < 0:
                        dados_validos = False
                        erro_mensagem = "ERRO: Tempo simulação não pode ser negativo!"
                    elif tempo_sim_val == 0:
                        dados_validos = False
                        erro_mensagem = "ERRO: Tempo simulação não pode ser zero!"
                    elif tempo_sim_val >480:
                        dados_validos = False
                        erro_mensagem = "ERRO: O Tempo máximo de simulação é 480 min (8h)!"
            
            if dados_validos:
                if not num_medicos_str:
                    dados_validos = False
                    erro_mensagem = "ERRO: Nº médicos não pode ser vazio!"
                elif not num_medicos_str.replace('.','',1).replace('-','',1).isdigit():
                    dados_validos = False
                    erro_mensagem = "ERRO: Nº médicos deve ser numérico!"
                else:
                    num_medicos = int(float(num_medicos_str))
                    if num_medicos < 0:
                        dados_validos = False
                        erro_mensagem = "ERRO: Nº médicos não pode ser negativo!"
                    elif num_medicos == 0:
                        dados_validos = False
                        erro_mensagem = "ERRO: Nº médicos não pode ser zero!"
                    elif num_medicos > len(medicos_dataset):
                        dados_validos = False
                        erro_mensagem = f"ERRO: Nº médicos ({num_medicos}) é demasiado elevado para o dataset!\n" \
                                    f"Nº máximo permitido: {len(medicos_dataset)}"
            
            if dados_validos:
                if not freq_pausa_str:
                    dados_validos = False
                    erro_mensagem = "ERRO: Frequência pausas não pode ser vazia!"
                elif not freq_pausa_str.replace('.','',1).replace('-','',1).isdigit():
                    dados_validos = False
                    erro_mensagem = "ERRO: Frequência pausas numérico!"
                else:
                    freq_pausa_val = float(freq_pausa_str)
                    if freq_pausa_val < 0:
                        dados_validos = False
                        erro_mensagem = "ERRO: Frequência pausas não pode ser negativo!"
                    elif freq_pausa_val == 0:
                        dados_validos = False
                        erro_mensagem = "ERRO: Frequência pausas não pode ser zero!"
            
            if dados_validos:
                if not dur_pausa_str:
                    dados_validos = False
                    erro_mensagem = "ERRO: Duração pausas não pode ser vazia!"
                elif not dur_pausa_str.replace('.','',1).replace('-','',1).isdigit():
                    dados_validos = False
                    erro_mensagem = "ERRO: Duração pausas numérico!"
                else:
                    dur_pausa = float(dur_pausa_str)
                    if dur_pausa < 0:
                        dados_validos = False
                        erro_mensagem = "ERRO: Duração pausas não pode ser negativo!"
                    elif dur_pausa == 0:
                        dados_validos = False
                        erro_mensagem = "ERRO: Duração pausas não pode ser zero!"
            
            if dados_validos:
                if not num_pausas_str:
                    dados_validos = False
                    erro_mensagem = "ERRO: Nº pausas não pode ser vazio!"
                elif not num_pausas_str.replace('.','',1).replace('-','',1).isdigit():
                    dados_validos = False
                    erro_mensagem = "ERRO: Nº pausas numérico!"
                else:
                    num_pausas_val = int(float(num_pausas_str))
                    if num_pausas_val <=0:
                        dados_validos = False
                        erro_mensagem = "ERRO: Nº pausas não pode ser negativo nem zero!"
            
            if dados_validos:
                if not max_pausa_str:
                    dados_validos = False
                    erro_mensagem = "ERRO: Máx. pausa não pode ser vazio!"
                elif not max_pausa_str.replace('.','',1).replace('-','',1).isdigit():
                    dados_validos = False
                    erro_mensagem = "ERRO: Máx. pausa numérico!"
                else:
                    max_pausa = int(float(max_pausa_str))
                    if max_pausa < 0:
                        dados_validos = False
                        erro_mensagem = "ERRO: Máx. pausa não pode ser negativo!"
            
            if dados_validos:
                if not tempo_max_espera_str:
                    dados_validos = False
                    erro_mensagem = "ERRO: Tempo espera não pode ser vazio!"
                elif not tempo_max_espera_str.replace('.','',1).replace('-','',1).isdigit():
                    dados_validos = False
                    erro_mensagem = "ERRO: Tempo espera numérico!"
                else:
                    tempo_max_espera_val = float(tempo_max_espera_str)
                    if tempo_max_espera_val < 0:
                        dados_validos = False
                        erro_mensagem = "ERRO: Tempo espera não pode ser negativo!"
                    elif tempo_max_espera_val == 0:
                        dados_validos = False
                        erro_mensagem = "ERRO: Tempo espera não pode ser zero!"
            
            if dados_validos:
                if not prob_desistencia_str:
                    dados_validos = False
                    erro_mensagem = "ERRO: Probabilidade não pode ser vazia!"
                elif not prob_desistencia_str.replace('.','',1).replace('-','',1).isdigit():
                    dados_validos = False
                    erro_mensagem = "ERRO: Probabilidade numérico!"
                else:
                    prob_desistencia_val = float(prob_desistencia_str)
                    if prob_desistencia_val < 0:
                        dados_validos = False
                        erro_mensagem = "ERRO: Probabilidade não pode ser negativa!"
                    elif prob_desistencia_val == 0:
                        dados_validos = False
                        erro_mensagem = "ERRO: Probabilidade não pode ser zero!"
                    elif prob_desistencia_val > 1:
                        dados_validos = False
                        erro_mensagem = "ERRO: Probabilidade não pode ser maior que 1 (100%)!"
            
            if dados_validos:
                if lambda_val > lambda_maximo:
                    resposta = sg.popup_yes_no(
                        f"λ ({lambda_val:.1f}) > máximo ({lambda_maximo:.1f}).\nUsar máximo?",
                        title="λ Elevado"
                    )
                    
                    if resposta == "Yes":
                        lambda_val = lambda_maximo
                        window["-LAMBDA-"].update(str(lambda_maximo))
                    else:
                        dados_validos = False
                
                if dados_validos:
                    if dur_pausa < 15:
                        dados_validos = False
                        erro_mensagem = "ERRO: Pausas min 15 minutos!"
                    elif dur_pausa > 20:
                        dados_validos = False
                        erro_mensagem = "ERRO: Pausas max 20 minutos!"
                    
                    limite_maximo = max(1, num_medicos // 3)
                    if max_pausa > limite_maximo:
                        dados_validos = False
                        erro_mensagem = f"ERRO: Máx {limite_maximo} médicos em pausa ({max_pausa} > {limite_maximo})!"
            
            if dados_validos:
                config_atual = {
                    "lambda_chegada": lambda_val,
                    "tempo_medio_consulta": tempo_consulta_val,
                    "tempo_simulacao": tempo_sim_val,
                    "num_medicos": num_medicos,
                    "frequencia_pausa": freq_pausa_val,
                    "duracao_pausa": dur_pausa,
                    "num_pausas": num_pausas_val,
                    "max_pausa_simultanea": max_pausa,
                    "tempo_max_espera": tempo_max_espera_val,
                    "prob_desistencia": prob_desistencia_val,
                    "distribuicao": "exponential" if values["-DIST_EXP"] else "normal" if values["-DIST_NORM"] else "uniform"
                }
                salvar_configuracao_json(config_atual)
            else:
                sg.popup_error(erro_mensagem, title="Erro")
            
        elif event == "Confirmar":
            dados_validos = True
            erro_mensagem = ""
            
            lambda_str = values["-LAMBDA-"].strip()
            num_medicos_str = values["-NUM_MEDICOS-"].strip()
            dur_pausa_str = values["-DUR_PAUSA-"].strip()
            max_pausa_str = values["-MAX_PAUSA_SIM-"].strip()
            tempo_consulta_str = values["-TEMPO_CONSULTA-"].strip()
            tempo_sim_str = values["-TEMPO_SIM-"].strip()
            freq_pausa_str = values["-FREQ_PAUSA-"].strip()
            num_pausas_str = values["-NUM_PAUSAS-"].strip()
            tempo_max_espera_str = values["-TEMPO_MAX_ESPERA-"].strip()
            prob_desistencia_str = values["-PROB_DESISTENCIA-"].strip()
            
            lambda_val = 10.0
            tempo_consulta_val = 15.0
            tempo_sim_val = 480.0
            num_medicos = 0
            freq_pausa_val = 60.0
            dur_pausa = 0.0
            num_pausas_val = 2
            max_pausa = 0
            tempo_max_espera_val = 30.0
            prob_desistencia_val = 0.3
            
            if not lambda_str:
                dados_validos = False
                erro_mensagem = "ERRO: Taxa de chegada (λ) não pode ser vazia!"
            elif not lambda_str.replace('.','',1).replace('-','',1).isdigit():
                dados_validos = False
                erro_mensagem = "ERRO: λ deve ser numérico!"
            else:
                lambda_val = float(lambda_str)
                if lambda_val < 0:
                    dados_validos = False
                    erro_mensagem = "ERRO: λ não pode ser negativo!"
                elif lambda_val == 0:
                    dados_validos = False
                    erro_mensagem = "ERRO: λ não pode ser zero!"
            
            if dados_validos:
                if not tempo_consulta_str:
                    dados_validos = False
                    erro_mensagem = "ERRO: Tempo consulta não pode ser vazio!"
                elif not tempo_consulta_str.replace('.','',1).replace('-','',1).isdigit():
                    dados_validos = False
                    erro_mensagem = "ERRO: Tempo consulta numérico!"
                else:
                    tempo_consulta_val = float(tempo_consulta_str)
                    if tempo_consulta_val < 0:
                        dados_validos = False
                        erro_mensagem = "ERRO: Tempo consulta não pode ser negativo!"
                    elif tempo_consulta_val == 0:
                        dados_validos = False
                        erro_mensagem = "ERRO: Tempo consulta não pode ser zero!"
            
            if dados_validos:
                if not tempo_sim_str:
                    dados_validos = False
                    erro_mensagem = "ERRO: Tempo simulação não pode ser vazio!"
                elif not tempo_sim_str.replace('.','',1).replace('-','',1).isdigit():
                    dados_validos = False
                    erro_mensagem = "ERRO: Tempo simulação numérico!"
                else:
                    tempo_sim_val = float(tempo_sim_str)
                    if tempo_sim_val < 0:
                        dados_validos = False
                        erro_mensagem = "ERRO: Tempo simulação não pode ser negativo!"
                    elif tempo_sim_val == 0:
                        dados_validos = False
                        erro_mensagem = "ERRO: Tempo simulação não pode ser zero!"
                    elif tempo_sim_val >480:
                        dados_validos = False
                        erro_mensagem = "ERRO: O Tempo máximo de simulação é 480 min (8h)!"
            if dados_validos:
                if not num_medicos_str:
                    dados_validos = False
                    erro_mensagem = "ERRO: Nº médicos não pode ser vazio!"
                elif not num_medicos_str.replace('.','',1).replace('-','',1).isdigit():
                    dados_validos = False
                    erro_mensagem = "ERRO: Nº médicos deve ser numérico!"
                else:
                    num_medicos = int(float(num_medicos_str))
                    if num_medicos < 0:
                        dados_validos = False
                        erro_mensagem = "ERRO: Nº médicos não pode ser negativo!"
                    elif num_medicos == 0:
                        dados_validos = False
                        erro_mensagem = "ERRO: Nº médicos não pode ser zero!"
                    elif num_medicos > len(medicos_dataset):
                        dados_validos = False
                        erro_mensagem = f"ERRO: Nº médicos ({num_medicos}) é demasiado elevado para o dataset!\n" \
                                    f"Nº máximo permitido: {len(medicos_dataset)}"
            
            if dados_validos:
                if not freq_pausa_str:
                    dados_validos = False
                    erro_mensagem = "ERRO: Frequência pausas não pode ser vazia!"
                elif not freq_pausa_str.replace('.','',1).replace('-','',1).isdigit():
                    dados_validos = False
                    erro_mensagem = "ERRO: Frequência pausas numérico!"
                else:
                    freq_pausa_val = float(freq_pausa_str)
                    if freq_pausa_val < 0:
                        dados_validos = False
                        erro_mensagem = "ERRO: Frequência pausas não pode ser negativo!"
                    elif freq_pausa_val == 0:
                        dados_validos = False
                        erro_mensagem = "ERRO: Frequência pausas não pode ser zero!"
            
            if dados_validos:
                if not dur_pausa_str:
                    dados_validos = False
                    erro_mensagem = "ERRO: Duração pausas não pode ser vazia!"
                elif not dur_pausa_str.replace('.','',1).replace('-','',1).isdigit():
                    dados_validos = False
                    erro_mensagem = "ERRO: Duração pausas numérico!"
                else:
                    dur_pausa = float(dur_pausa_str)
                    if dur_pausa < 0:
                        dados_validos = False
                        erro_mensagem = "ERRO: Duração pausas não pode ser negativo!"
                    elif dur_pausa == 0:
                        dados_validos = False
                        erro_mensagem = "ERRO: Duração pausas não pode ser zero!"
            
            if dados_validos:
                if not num_pausas_str:
                    dados_validos = False
                    erro_mensagem = "ERRO: Nº pausas não pode ser vazio!"
                elif not num_pausas_str.replace('.','',1).replace('-','',1).isdigit():
                    dados_validos = False
                    erro_mensagem = "ERRO: Nº pausas numérico!"
                else:
                    num_pausas_val = int(float(num_pausas_str))
                    if num_pausas_val < 0:
                        dados_validos = False
                        erro_mensagem = "ERRO: Nº pausas não pode ser negativo!"
            
            if dados_validos:
                if not max_pausa_str:
                    dados_validos = False
                    erro_mensagem = "ERRO: Máx. pausa não pode ser vazio!"
                elif not max_pausa_str.replace('.','',1).replace('-','',1).isdigit():
                    dados_validos = False
                    erro_mensagem = "ERRO: Máx. pausa numérico!"
                else:
                    max_pausa = int(float(max_pausa_str))
                    if max_pausa < 0:
                        dados_validos = False
                        erro_mensagem = "ERRO: Máx. pausa não pode ser negativo!"
            
            if dados_validos:
                if not tempo_max_espera_str:
                    dados_validos = False
                    erro_mensagem = "ERRO: Tempo espera não pode ser vazio!"
                elif not tempo_max_espera_str.replace('.','',1).replace('-','',1).isdigit():
                    dados_validos = False
                    erro_mensagem = "ERRO: Tempo espera numérico!"
                else:
                    tempo_max_espera_val = float(tempo_max_espera_str)
                    if tempo_max_espera_val < 0:
                        dados_validos = False
                        erro_mensagem = "ERRO: Tempo espera não pode ser negativo!"
                    elif tempo_max_espera_val == 0:
                        dados_validos = False
                        erro_mensagem = "ERRO: Tempo espera não pode ser zero!"
            
            if dados_validos:
                if not prob_desistencia_str:
                    dados_validos = False
                    erro_mensagem = "ERRO: Probabilidade não pode ser vazia!"
                elif not prob_desistencia_str.replace('.','',1).replace('-','',1).isdigit():
                    dados_validos = False
                    erro_mensagem = "ERRO: Probabilidade numérico!"
                else:
                    prob_desistencia_val = float(prob_desistencia_str)
                    if prob_desistencia_val < 0:
                        dados_validos = False
                        erro_mensagem = "ERRO: Probabilidade não pode ser negativa!"
                    elif prob_desistencia_val == 0:
                        dados_validos = False
                        erro_mensagem = "ERRO: Probabilidade não pode ser zero!"
                    elif prob_desistencia_val > 1:
                        dados_validos = False
                        erro_mensagem = "ERRO: Probabilidade não pode ser maior que 1 (100%)!"
            
            if dados_validos:
                if lambda_val > lambda_maximo:
                    resposta = sg.popup_yes_no(
                        f"λ ({lambda_val:.1f}) > máximo ({lambda_maximo:.1f}).\nUsar máximo?",
                        title="λ Elevado"
                    )
                    
                    if resposta == "Yes":
                        lambda_val = lambda_maximo
                        window["-LAMBDA-"].update(str(lambda_maximo))
                    else:
                        dados_validos = False
                
                if dados_validos:
                    if dur_pausa < 15:
                        dados_validos = False
                        erro_mensagem = "ERRO: Pausas min 15 minutos!"
                    elif dur_pausa > 20:
                        dados_validos = False
                        erro_mensagem = "ERRO: Pausas max 20 minutos!"
                    
                    limite_maximo = max(1, num_medicos // 3)
                    if max_pausa > limite_maximo:
                        dados_validos = False
                        erro_mensagem = f"ERRO: Máx {limite_maximo} médicos em pausa ({max_pausa} > {limite_maximo})!"
            
            if dados_validos:
                if values["-DIST_EXP"]:
                    distribuicao_final = "exponential"
                elif values["-DIST_NORM"]:
                    distribuicao_final = "normal"
                else:
                    distribuicao_final = "uniform"
                
                resultado = {
                    "lambda_chegada": lambda_val,
                    "tempo_medio_consulta": tempo_consulta_val,
                    "tempo_simulacao": tempo_sim_val,
                    "num_medicos": num_medicos,
                    "frequencia_pausa": freq_pausa_val,
                    "duracao_pausa": dur_pausa,
                    "num_pausas": num_pausas_val,
                    "max_pausa_simultanea": max_pausa,
                    "tempo_max_espera": tempo_max_espera_val,
                    "prob_desistencia": prob_desistencia_val,
                    "distribuicao": distribuicao_final
                }
                continuar = False
            else:
                if erro_mensagem:
                    sg.popup_error(erro_mensagem, title="Erro")

    window.close()
    return resultado



def desenhar_grafico_desempenho_medico(canvas, dados_medicos):
    """
    Desenha um gráfico de barras comparativo entre médicos.
    """
    
    nomes = []
    taxas_ocupacao = []
    taxas_corresp = []
    
    for i, medico in enumerate(dados_medicos):
        nomes.append(medico.get("nome", f"M{i+1}"))
        taxas_ocupacao.append(medico.get("taxa_ocupacao", 0))
        taxas_corresp.append(medico.get("taxa_correspondencia", 0))

   
    fig = Figure(figsize=(8, 5), dpi=100)
    ax = fig.add_subplot(111)
    
    x = np.arange(len(nomes))
    largura = 0.35
    
    ax.bar(x - largura/2, taxas_ocupacao, largura, label='Taxa Ocupação (%)', color=escuro)
    ax.bar(x + largura/2, taxas_corresp, largura, label='Especialidade Correta (%)', color='#4caf50')
    
    ax.set_ylabel('Percentagem (%)')
    ax.set_title('Comparativo de Desempenho por Médico')
    ax.set_xticks(x)
    ax.set_xticklabels(nomes)
    ax.legend()
    ax.set_ylim(0, 110) 

    
    if canvas:
        
        if hasattr(canvas, 'children'):
            for child in canvas.children:
                child.destroy()
                
        fig_agg = fig_tk.FigureCanvasTkAgg(fig, canvas)
        fig_agg.draw()
        fig_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
        return fig_agg
    return None


def mostrar_relatorio_desempenho_com_abas(dados_selecionados, titulo):
    """Mostra relatório de desempenho com abas"""
    sg.theme('TemaClinica')
    medicos = dados_selecionados.get("medicos", [])
    
    if not medicos:
        sg.popup_error("Nenhum dado de médico disponível!", title="Erro")
        return
    
    
    tabela_conteudo = []
    for m in medicos:
        tabela_conteudo.append([
            m.get("nome", "-"),
            m.get("especialidade", "-"),
            m.get("num_atendimentos", 0),
            f"{m.get('taxa_ocupacao', 0):.1f}%",
            f"{m.get('taxa_correspondencia', 0):.1f}%"
        ])
    
    
    fig = Figure(figsize=(10, 6), dpi=100)
    ax = fig.add_subplot(111)
    
    nomes = []
    taxas_ocupacao = []
    taxas_correspondencia = []
    
    for m in medicos:
        nomes.append(m.get("nome", f"M{len(nomes)+1}"))
        taxas_ocupacao.append(m.get("taxa_ocupacao", 0))
        taxas_correspondencia.append(m.get("taxa_correspondencia", 0))
    
    x = np.arange(len(nomes))
    largura = 0.35
    
    ax.bar(x - largura/2, taxas_ocupacao, largura, label='Taxa Ocupação (%)', color=escuro)
    ax.bar(x + largura/2, taxas_correspondencia, largura, label='Especialidade Correta (%)', color='#4caf50')
    
    ax.set_ylabel('Percentagem (%)')
    ax.set_title('Comparativo de Desempenho por Médico')
    ax.set_xticks(x)
    ax.set_xticklabels(nomes, rotation=45, ha='right')
    ax.legend()
    ax.set_ylim(0, 110)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    
    
    tab_estatisticas_layout = [
        [sg.Text("Estatísticas de Desempenho", font=("Helvetica", 14, "bold"), text_color=escuro)],
        [sg.Table(values=tabela_conteudo, 
                  headings=["Médico", "Especialidade", "Atendimentos", "Ocupação (%)", "Precisão (%)"],
                  auto_size_columns=False,
                  col_widths=[20, 15, 12, 12, 12],
                  justification='center',
                  num_rows=10,
                  expand_x=True,
                  expand_y=True,
                  font=("Helvetica", 10),
                  header_font=("Helvetica", 10, "bold"),
                  alternating_row_color='lightblue',
                  key="-TABELA_DESEMPENHO-")]
    ]
    
    tab_grafico_layout = [
        [sg.Text("Gráfico Comparativo", font=("Helvetica", 14, "bold"), text_color=escuro)],
        [sg.Canvas(key="-CANVAS_DESEMPENHO-", size=(700, 500))]
    ]
    
    
    relatorio_texto = f"RELATÓRIO DE DESEMPENHO MÉDICO - {titulo}\n"
    relatorio_texto += "=" * 60 + "\n"
    relatorio_texto += f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
    relatorio_texto += f"Total de médicos: {len(medicos)}\n\n"
    
    for m in medicos:
        relatorio_texto += f"MÉDICO: {m.get('nome', '-')} ({m.get('especialidade', '-')})\n"
        relatorio_texto += f"  • Atendimentos realizados: {m.get('num_atendimentos', 0)}\n"
        relatorio_texto += f"  • Taxa de ocupação: {m.get('taxa_ocupacao', 0):.1f}%\n"
        relatorio_texto += f"  • Taxa correspondência especialidade: {m.get('taxa_correspondencia', 0):.1f}%\n"
        
        
        taxa_ocup = m.get('taxa_ocupacao', 0)
        taxa_corr = m.get('taxa_correspondencia', 0)
        
        if taxa_ocup > 80 and taxa_corr > 80:
            avaliacao = "EXCELENTE"
        elif taxa_ocup > 60 and taxa_corr > 70:
            avaliacao = "BOM"
        elif taxa_ocup > 40 and taxa_corr > 60:
            avaliacao = "REGULAR"
        else:
            avaliacao = "NEEDS IMPROVEMENT"
        
        relatorio_texto += f"  • Avaliação: {avaliacao}\n\n"
    
    tab_relatorio_layout = [
        [sg.Text("Relatório Detalhado", font=("Helvetica", 14, "bold"), text_color=escuro)],
        [sg.Multiline(relatorio_texto, size=(80, 25), key="-RELATORIO_DESEMPENHO-", 
                     font=("Courier New", 9), disabled=True, horizontal_scroll=True, autoscroll=True)]
    ]
    
    layout = [
        [sg.Text(f"Relatório de Desempenho Médico: {titulo}", 
                font=("Helvetica", 16, "bold"), justification="center", expand_x=True, pad=(10,10))],
        [sg.TabGroup([
            [sg.Tab('Estatísticas', tab_estatisticas_layout)],
            [sg.Tab('Gráfico', tab_grafico_layout)],
            [sg.Tab('Relatório', tab_relatorio_layout)]
        ], expand_x=True, expand_y=True)],
        [sg.Button("Exportar Relatório", size=(15,1), button_color=('white',escuro)),
         sg.Button("Fechar", size=(12,1), button_color=('white',escuro))]
    ]
    
    window = sg.Window(f"Desempenho Médico - {titulo}", layout, modal=True, finalize=True, size=(800, 700), resizable=True, keep_on_top=True)
    
    
    canvas = fig_tk.FigureCanvasTkAgg(fig, window["-CANVAS_DESEMPENHO-"].TKCanvas)
    canvas.draw()
    canvas.get_tk_widget().pack(side='top', fill='both', expand=1)
    
    continuar = True
    while continuar:
        event, values = window.read()
        
        if event in (sg.WINDOW_CLOSED, "Fechar"):
            continuar = False
        
        elif event == "Exportar Relatório":
            nome_arquivo = f"desempenho_medicos_{titulo.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            arquivo_salvo = salvar_arquivo(relatorio_texto, nome_arquivo)
            if arquivo_salvo:
                sg.popup(f"Relatório exportado para:\n{arquivo_salvo}", title="Sucesso", keep_on_top=True, modal=True)
            else:
                sg.popup_error("Falha ao salvar o relatório.", title="Erro",keep_on_top=True, modal=True)
    
    window.close()

def aplicar_filtros_pacientes(pacientes_atendidos, filtros):
    filtro_id = filtros.get("id", "").strip().lower()
    filtro_nome = filtros.get("nome", "").strip().lower()
    filtro_idade = filtros.get("idade", "Todas")
    filtro_doenca = filtros.get("doenca", "").strip().lower()
    filtro_especialidade = filtros.get("especialidade", "Todas")
    filtro_prioridade = filtros.get("prioridade", "Todas")
    filtro_sexo = filtros.get("sexo", "Todos")
    filtro_status = filtros.get("status", "Todos")
    ordenar_por = filtros.get("ordenar_por", "ID")
    
    pacientes_filtrados = []
    for paciente in pacientes_atendidos:
        passa_filtro = True
        
        if filtro_id and filtro_id not in paciente["id"].lower():
            passa_filtro = False
        
        if passa_filtro and filtro_nome and filtro_nome not in paciente["nome"].lower():
            passa_filtro = False
        
        if passa_filtro and filtro_idade != "Todas":
            idade_valor = paciente["idade"]
            if idade_valor != "N/A" and idade_valor != "" and idade_valor is not None:
                idade_num = 0
                if isinstance(idade_valor, (int, float)):
                    idade_num = int(idade_valor)
                elif isinstance(idade_valor, str):
                    numeros = []
                    for char in idade_valor:
                        if char.isdigit():
                            numeros.append(char)
                    
                    if numeros:
                        idade_str = ''.join(numeros)
                        if idade_str:
                            idade_num = int(idade_str)
                
                if idade_num > 0:
                    if filtro_idade == "Criança (0-12)":
                        if not (0 <= idade_num <= 12):
                            passa_filtro = False
                    elif filtro_idade == "Adolescente (13-17)":
                        if not (13 <= idade_num <= 17):
                            passa_filtro = False
                    elif filtro_idade == "Adulto (18-64)":
                        if not (18 <= idade_num <= 64):
                            passa_filtro = False
                    elif filtro_idade == "Idoso (65+)":
                        if idade_num < 65:
                            passa_filtro = False
        
        if passa_filtro and filtro_doenca and filtro_doenca not in paciente["doenca"].lower():
            passa_filtro = False
        
        if passa_filtro and filtro_especialidade != "Todas" and paciente["especialidade_necessaria"] != filtro_especialidade:
            passa_filtro = False
        
        if passa_filtro and filtro_prioridade != "Todas" and paciente["prioridade"] != filtro_prioridade:
            passa_filtro = False
        
        if passa_filtro and filtro_sexo != "Todos" and paciente["sexo"].lower() != filtro_sexo.lower():
            passa_filtro = False
        
        if passa_filtro and filtro_status != "Todos":
            status_paciente = paciente.get("status", "")
            if filtro_status == "Atendido" and status_paciente != "ATENDIDO":
                passa_filtro = False
            elif filtro_status == "Desistente" and status_paciente != "DESISTENTE":
                passa_filtro = False
            elif filtro_status == "Na Fila" and status_paciente != "NA FILA":
                passa_filtro = False
        
        if passa_filtro:
            pacientes_filtrados.append(paciente)
    
    if ordenar_por == "Nome (A-Z)":
        pacientes_filtrados.sort(key=lambda x: x["nome"].lower())
    elif ordenar_por == "Idade":
        pacientes_filtrados.sort(key=lambda x: 
            int(''.join(filter(str.isdigit, str(x["idade"])))) if any(c.isdigit() for c in str(x["idade"])) else 0)
    elif ordenar_por == "Prioridade":
        ordem_prioridade = {"URGENTE": 1, "ALTA": 2, "NORMAL": 3, "BAIXA": 4}
        pacientes_filtrados.sort(key=lambda x: ordem_prioridade.get(x["prioridade"], 5))
    elif ordenar_por == "Tempo Espera (crescente)":
        pacientes_filtrados.sort(key=lambda x: x["tempo_espera"])
    elif ordenar_por == "Tempo Espera (decrescente)":
        pacientes_filtrados.sort(key=lambda x: x["tempo_espera"], reverse=True)
    elif ordenar_por == "Doença":
        pacientes_filtrados.sort(key=lambda x: x["doenca"].lower())
    elif ordenar_por == "Tempo Chegada":
        pacientes_filtrados.sort(key=lambda x: x["tempo_chegada"])
    else:
        pacientes_filtrados.sort(key=lambda x: x["id"])
    
    return pacientes_filtrados



def atualizar_tabela_pacientes(pacientes_filtrados, pacientes_atendidos, window):
    tabela = []

    for p in pacientes_filtrados:
        tempo = p.get("tempo_espera", 0)
        if tempo >= 60:
            h = int(tempo // 60)
            m = int(tempo % 60)
            espera = f"{h}h{m:02d}m"
        else:
            espera = f"{int(tempo)}m"

        status = p.get("status", "N/A")

        medico_nome = p.get("medico_nome", "N/A")
        medico_id = p.get("medico_id", "")
        if medico_nome != "N/A" and medico_id != "":
            medico_display = f"{medico_nome} ({medico_id})"
        else:
            medico_display = "N/A"

        linha = [
            p.get("id", ""),
            p.get("nome", ""),
            p.get("idade", ""),
            p.get("sexo", ""),
            p.get("doenca", ""),
            p.get("especialidade_necessaria", ""),
            p.get("prioridade", ""),
            espera,
            status,
            medico_display
        ]

        tabela.append(linha)

    window["-TABELA_PACIENTES-"].update(values=tabela)
    window["-TOTAL_PACIENTES-"].update(
        f"Total: {len(pacientes_filtrados)} (de {len(pacientes_atendidos)})"
    )



def mostrar_lista_atendimentos(dados_simulacao, titulo):
    sg.theme('TemaClinica')
    
    dados_simulacao_antiga = False
    if isinstance(dados_simulacao, dict) and "resultados_finais" in dados_simulacao:
        dados_simulacao_antiga = True
        historico_atendimentos = dados_simulacao.get("historico_atendimentos", [])
        
        pacientes_carregados = carregar_pacientes_simula()
        pessoas_dados_recebidas = {}
        i = 0
        while i < len(pacientes_carregados):
            p = pacientes_carregados[i]
            pessoas_dados_recebidas[p.get("id")] = p
            i = i + 1
        
        medicos_carregados = carregar_medicos_simula()
        num_medicos_sim = dados_simulacao.get("configuracao", {}).get("num_medicos", 2)
        medicos_recebidos = []
        j = 0
        while j < num_medicos_sim and j < len(medicos_carregados):
            medicos_recebidos.append(medicos_carregados[j])
            j = j + 1
        
        pacientes = []
        
        k = 0
        while k < len(historico_atendimentos):
            atendimento = historico_atendimentos[k]
            if isinstance(atendimento, dict) and "paciente" in atendimento:
                paciente_id = atendimento.get("paciente", "")
                paciente_info = pessoas_dados_recebidas.get(paciente_id, {})
            
                paciente_dados = {
                    "id": paciente_id,
                    "nome": paciente_info.get("nome", f"Paciente {paciente_id}"),
                    "idade": paciente_info.get("idade", "N/A"),
                    "sexo": paciente_info.get("sexo", "N/A"),
                    "doenca": paciente_info.get("doenca", "Não especificada"),
                    "prioridade": paciente_info.get("prioridade", "NORMAL"),
                    "especialidade_necessaria": paciente_info.get("especialidade_necessaria", "Clínica Geral"),
                    "tempo_chegada": 0,
                    "tempo_espera": 0,
                    "duracao_consulta": atendimento.get("duracao", 0),
                    "especialidade_correta": atendimento.get("especialidade_correta", False),
                    "medico_nome": f"Médico {len(pacientes) + 1}",
                    "medico_especialidade": "Clínica Geral",
                    "inicio_atendimento": atendimento.get("inicio", 0),
                    "fim_atendimento": atendimento.get("inicio", 0) + atendimento.get("duracao", 0),
                    "status": "ATENDIDO",
                    "fumador": paciente_info.get("atributos", {}).get("fumador", "N/A"),
                    "consome_alcool": paciente_info.get("atributos", {}).get("consome_alcool", "N/A"),
                    "atividade_fisica": paciente_info.get("atributos", {}).get("atividade_fisica", "N/A"),
                    "cronico": paciente_info.get("atributos", {}).get("cronico", "N/A"),
                    "telefone": paciente_info.get("telefone", "N/A"),
                    "email": paciente_info.get("email", "N/A"),
                    "consulta_marcada": paciente_info.get("consulta_marcada", False)
                }
                pacientes.append(paciente_dados)
            k = k + 1
    else:
        dados_simulacao_antiga = False
        historico_atendimentos = dados_simulacao.get("historico_atendimentos", [])
        pessoas_dados_recebidas = dados_simulacao.get("pessoas_dados", {})
        medicos_recebidos = dados_simulacao.get("medicos", [])
        
        if not historico_atendimentos and not pessoas_dados_recebidas:
            historico_atendimentos = estado_simulacao.get("historico_atendimentos", [])
            pessoas_dados_recebidas = estado_simulacao.get("pessoas_dados", {})
            medicos_recebidos = estado_simulacao.get("medicos", [])
        
        if not pessoas_dados_recebidas:
            pacientes_carregados = carregar_pacientes_simula()
            pessoas_dados_recebidas = {}
            i = 0
            while i < len(pacientes_carregados):
                p = pacientes_carregados[i]
                pessoas_dados_recebidas[p.get("id")] = p
                i = i + 1
        
        if not medicos_recebidos:
            medicos_carregados = carregar_medicos_simula()
            medicos_recebidos = medicos_carregados
        
        pacientes = carregar_dados_pacientes_atendidos(historico_atendimentos, medicos_recebidos, pessoas_dados_recebidas)
    
    if not pacientes:
        sg.popup("Nenhum paciente encontrado.", title="Informação")
        return
    
    def extrair_numero_id(paciente_id):
        if isinstance(paciente_id, str):
            numeros_encontrados = []
            i = 0
            while i < len(paciente_id):
                if paciente_id[i].isdigit():
                    numero_str = ""
                    while i < len(paciente_id) and paciente_id[i].isdigit():
                        numero_str = numero_str + paciente_id[i]
                        i = i + 1
                    if numero_str:
                        numeros_encontrados.append(int(numero_str))
                else:
                    i = i + 1
            if numeros_encontrados:
                return numeros_encontrados[0]
        return 999999
    
    pacientes_ordenados = sorted(pacientes, key=lambda x: extrair_numero_id(x.get("id", "")))
    
    sexos_disponiveis = []
    i = 0
    while i < len(pacientes_ordenados):
        sexo = pacientes_ordenados[i].get("sexo", "N/A")
        if sexo not in sexos_disponiveis and sexo != "N/A":
            sexos_disponiveis.append(sexo)
        i = i + 1
    sexos_disponiveis.sort()
    
    especialidades_disponiveis = []
    i = 0
    while i < len(pacientes_ordenados):
        especialidade = pacientes_ordenados[i].get("especialidade_necessaria", "Clínica Geral")
        if especialidade not in especialidades_disponiveis:
            especialidades_disponiveis.append(especialidade)
        i = i + 1
    especialidades_disponiveis.sort()

    status_disponiveis = ["Todos", "ATENDIDO", "NA FILA", "DESISTENTE"]

    prioridades_disponiveis = []
    i = 0
    while i < len(pacientes_ordenados):
        prioridade = pacientes_ordenados[i].get("prioridade", "NORMAL")
        if prioridade not in prioridades_disponiveis:
            prioridades_disponiveis.append(prioridade)
        i = i + 1
    prioridades_disponiveis.sort(key=lambda x: PRIORIDADES.get(x, 99))
 
    medicos_disponiveis = []
    i = 0
    while i < len(pacientes_ordenados):
        if pacientes_ordenados[i].get("status") == "ATENDIDO":
            medico_nome = pacientes_ordenados[i].get("medico_nome", "")
            if medico_nome != "N/A" and medico_nome != "" and medico_nome not in medicos_disponiveis:
                medicos_disponiveis.append(medico_nome)
        i = i + 1
    medicos_disponiveis.sort()

    faixas_etarias = ["Todas", "0-18", "19-30", "31-50", "51-65", "66+"]

    sexos_disponiveis.insert(0, "Todos")
    especialidades_disponiveis.insert(0, "Todas")
    prioridades_disponiveis.insert(0, "Todas")
    medicos_disponiveis.insert(0, "Todos")

    dados_tabela = []
    for p in pacientes_ordenados:
        tempo_espera = p.get("tempo_espera", 0)
        if tempo_espera >= 60:
            horas = int(tempo_espera // 60)
            minutos = int(tempo_espera % 60)
            tempo_espera_str = f"{horas}h{minutos:02d}m"
        else:
            tempo_espera_str = f"{tempo_espera:.0f}m"
     
        duracao_consulta = p.get("duracao_consulta", 0)
        if duracao_consulta >= 60:
            horas = int(duracao_consulta // 60)
            minutos = int(duracao_consulta % 60)
            duracao_str = f"{horas}h{minutos:02d}m"
        else:
            duracao_str = f"{duracao_consulta:.0f}m"
        
        status = p.get("status", "")
        if status == "ATENDIDO":
            status_str = "Atendido"
        elif status == "NA FILA":
            status_str = "Na fila"
        else:
            status_str = "Desistente"
        
        dados_tabela.append([
            p.get("id", ""),
            p.get("nome", "")[:20],
            p.get("sexo", "N/A"),
            p.get("idade", "N/A"),
            p.get("prioridade", ""),
            p.get("especialidade_necessaria", "")[:20],
            status_str,
            tempo_espera_str,
            duracao_str,
            p.get("medico_nome", "N/A")[:15]
        ])

    filtros_layout = [
        [sg.Text("FILTROS AVANÇADOS", font=("Helvetica", 12, "bold"), text_color=escuro)],
        [sg.HorizontalSeparator(color=claro, pad=(0, 5))],
        
        [sg.Text("ID:", size=(8, 1), font=("Helvetica", 10)), 
         sg.Input("", key="-FILTRO_ID-", size=(15, 1), font=("Helvetica", 10), enable_events=True,
                 tooltip="Digite parte do ID do paciente")],
        [sg.Text("Nome:", size=(8, 1), font=("Helvetica", 10)), 
         sg.Input("", key="-FILTRO_NOME-", size=(15, 1), font=("Helvetica", 10), enable_events=True,
                 tooltip="Digite parte do nome do paciente")],
        [sg.Text("Sexo:", size=(8, 1), font=("Helvetica", 10)), 
         sg.Combo(sexos_disponiveis, default_value="Todos", key="-FILTRO_SEXO-", 
                 size=(15, 1), font=("Helvetica", 10), enable_events=True)],
        
        [sg.Text("Idade:", size=(8, 1), font=("Helvetica", 10)), 
         sg.Combo(faixas_etarias, default_value="Todas", key="-FILTRO_IDADE-", 
                 size=(15, 1), font=("Helvetica", 10), enable_events=True)],
        
        [sg.Text("Especialidade:", size=(12, 1), font=("Helvetica", 10)), 
         sg.Combo(especialidades_disponiveis, default_value="Todas", key="-FILTRO_ESPEC-", 
                 size=(15, 1), font=("Helvetica", 10), enable_events=True)],
        [sg.Text("Médico:", size=(12, 1), font=("Helvetica", 10)), 
         sg.Combo(medicos_disponiveis, default_value="Todos", key="-FILTRO_MEDICO-", 
                 size=(15, 1), font=("Helvetica", 10), enable_events=True)],

        [sg.Text("Status:", size=(8, 1), font=("Helvetica", 10)), 
         sg.Combo(status_disponiveis, default_value="Todos", key="-FILTRO_STATUS-", 
                 size=(15, 1), font=("Helvetica", 10), enable_events=True)],
        [sg.Text("Prioridade:", size=(8, 1), font=("Helvetica", 10)), 
         sg.Combo(prioridades_disponiveis, default_value="Todas", key="-FILTRO_PRIORIDADE-", 
                 size=(15, 1), font=("Helvetica", 10), enable_events=True)],
        
        [sg.Button("Limpar Filtros", size=(15, 1), key="-LIMPAR_FILTROS-", 
                  button_color=('white', escuro), font=("Helvetica", 10), pad=(5, 10))],
    ]

    ordenacao_layout = [
        [sg.Text("ORDENAÇÃO", font=("Helvetica", 12, "bold"), text_color=escuro)],
        [sg.HorizontalSeparator(color=claro, pad=(0, 5))],

        [sg.Radio("ID (crescente)", "ORDENACAO", default=True, 
                 key="-ORD_ID_CRESC-", enable_events=True, font=("Helvetica", 10))],
        [sg.Radio("ID (decrescente)", "ORDENACAO", 
                 key="-ORD_ID_DECRESC-", enable_events=True, font=("Helvetica", 10))],

        [sg.Radio("Nome (A-Z)", "ORDENACAO", 
                 key="-ORD_NOME_ASC-", enable_events=True, font=("Helvetica", 10))],
        [sg.Radio("Nome (Z-A)", "ORDENACAO", 
                 key="-ORD_NOME_DESC-", enable_events=True, font=("Helvetica", 10))],

        [sg.Radio("Idade (menor-maior)", "ORDENACAO", 
                 key="-ORD_IDADE_ASC-", enable_events=True, font=("Helvetica", 10))],
        [sg.Radio("Idade (maior-menor)", "ORDENACAO", 
                 key="-ORD_IDADE_DESC-", enable_events=True, font=("Helvetica", 10))],

        [sg.Radio("Prioridade (urgente-baixa)", "ORDENACAO", 
                 key="-ORD_PRIORIDADE_DESC-", enable_events=True, font=("Helvetica", 10))],
        [sg.Radio("Prioridade (baixa-urgente)", "ORDENACAO", 
                 key="-ORD_PRIORIDADE_ASC-", enable_events=True, font=("Helvetica", 10))],

        [sg.Radio("Tempo Espera (menor)", "ORDENACAO", 
                 key="-ORD_ESPERA_ASC-", enable_events=True, font=("Helvetica", 10))],
        [sg.Radio("Tempo Espera (maior)", "ORDENACAO", 
                 key="-ORD_ESPERA_DESC-", enable_events=True, font=("Helvetica", 10))],

        [sg.Radio("Especialidade (A-Z)", "ORDENACAO", 
                 key="-ORD_ESPEC_ASC-", enable_events=True, font=("Helvetica", 10))],
    ]

    tabela_layout = [
        [sg.Table(
            values=dados_tabela,
            headings=["ID", "Nome", "Sexo", "Idade", "Prioridade", "Especialidade", "Status", "Espera", "Duração", "Médico"],
            auto_size_columns=False,
            col_widths=[8, 20, 8, 8, 10, 18, 12, 10, 10, 15],
            justification='left',
            num_rows=min(20, len(dados_tabela)),
            key="-TABELA_PACIENTES-",
            enable_events=True,
            expand_x=True,
            expand_y=True,
            font=("Helvetica", 9),
            header_font=("Helvetica", 9, "bold"),
            alternating_row_color='#f0f0f0',
            row_colors=[
                (6, '#d4edda'),  
                (6, '#fff3cd'),  
                (6, '#f8d7da')   
            ]
        )],
        [sg.Text(f"Total de pacientes: {len(pacientes_ordenados)}", 
                key="-TOTAL_PACIENTES-", 
                font=("Helvetica", 10, "bold"), 
                text_color=escuro,
                pad=(0, 10))],
    ]
    
    layout = [
        [sg.Text(f"LISTA DE PACIENTES - {titulo}", 
                font=("Helvetica", 16, "bold"), 
                text_color=escuro,
                justification="center", 
                expand_x=True,
                pad=(0, 10))],
        [sg.HorizontalSeparator(color=escuro, pad=(0, 10))],
        [
            sg.Column(filtros_layout, vertical_alignment='top', size=(250, 400), pad=(5, 5), scrollable=True, vertical_scroll_only=True),
            sg.VerticalSeparator(color=escuro, pad=(5, 5)),
            sg.Column(ordenacao_layout, vertical_alignment='top', size=(250, 400), pad=(5, 5), scrollable=True, vertical_scroll_only=True),
            sg.VerticalSeparator(color=escuro, pad=(5, 5)),
            sg.Column(tabela_layout, expand_x=True, expand_y=True, pad=(5, 5))
        ],
        [sg.HorizontalSeparator(color=escuro, pad=(10, 10))],
        [
            sg.Button("Ver Detalhes", size=(15, 1), key="-VER_DETALHES-", 
                     button_color=('white', escuro), font=("Helvetica", 10)),
            sg.Button("Estatísticas", size=(15, 1), key="-ESTATISTICAS-", 
                     button_color=('white', escuro), font=("Helvetica", 10)),
            sg.Button("Exportar TXT", size=(15, 1), key="-EXPORTAR_TXT-", 
                     button_color=('white', escuro), font=("Helvetica", 10)),
            sg.Button("Fechar", size=(12, 1), key="-FECHAR-", 
                     button_color=('white', escuro), font=("Helvetica", 10))
        ]
    ]
    
    window = sg.Window(f"Lista de Pacientes - {titulo}", layout, modal=True, finalize=True, size=(1400, 800), resizable=True)

    valores_janela = {
        "-FILTRO_ID-": "",
        "-FILTRO_NOME-": "",
        "-FILTRO_SEXO-": "Todos",
        "-FILTRO_IDADE-": "Todas",
        "-FILTRO_ESPEC-": "Todas",
        "-FILTRO_MEDICO-": "Todos",
        "-FILTRO_STATUS-": "Todos",
        "-FILTRO_PRIORIDADE-": "Todas",
        "-ORD_ID_CRESC-": True,
        "-ORD_ID_DECRESC-": False,
        "-ORD_NOME_ASC-": False,
        "-ORD_NOME_DESC-": False,
        "-ORD_IDADE_ASC-": False,
        "-ORD_IDADE_DESC-": False,
        "-ORD_PRIORIDADE_DESC-": False,
        "-ORD_PRIORIDADE_ASC-": False,
        "-ORD_ESPERA_ASC-": False,
        "-ORD_ESPERA_DESC-": False,
        "-ORD_ESPEC_ASC-": False
    }
 
    pacientes_original = pacientes.copy()
    pacientes_filtrados_atual = pacientes_ordenados.copy()

    def verificar_faixa_etaria(idade_str, faixa):
        if faixa == "Todas" or idade_str == "N/A":
            return True
        
        try:
            idade = int(idade_str)
        except:
            return False
        
        if faixa == "0-18":
            return 0 <= idade <= 18
        elif faixa == "19-30":
            return 19 <= idade <= 30
        elif faixa == "31-50":
            return 31 <= idade <= 50
        elif faixa == "51-65":
            return 51 <= idade <= 65
        elif faixa == "66+":
            return idade >= 66
        
        return True

    def aplicar_filtros_completos(dados_originais, filtros):
        dados_filtrados = []
        
        i = 0
        while i < len(dados_originais):
            paciente = dados_originais[i]
            incluir = True
            
            filtro_id = filtros.get("id", "").lower().strip()
            if filtro_id:
                paciente_id = paciente.get("id", "").lower()
                if filtro_id not in paciente_id:
                    incluir = False
            
            filtro_nome = filtros.get("nome", "").lower().strip()
            if incluir and filtro_nome:
                paciente_nome = paciente.get("nome", "").lower()
                if filtro_nome not in paciente_nome:
                    incluir = False
            
            filtro_sexo = filtros.get("sexo", "Todos")
            if incluir and filtro_sexo != "Todos" and paciente.get("sexo") != filtro_sexo:
                incluir = False

            filtro_idade = filtros.get("idade", "Todas")
            if incluir and filtro_idade != "Todas":
                if not verificar_faixa_etaria(paciente.get("idade", "N/A"), filtro_idade):
                    incluir = False

            filtro_espec = filtros.get("especialidade", "Todas")
            if incluir and filtro_espec != "Todas" and paciente.get("especialidade_necessaria") != filtro_espec:
                incluir = False

            filtro_medico = filtros.get("medico", "Todos")
            if incluir and filtro_medico != "Todos" and paciente.get("medico_nome") != filtro_medico:
                incluir = False

            filtro_status = filtros.get("status", "Todos")
            if incluir and filtro_status != "Todos" and paciente.get("status") != filtro_status:
                incluir = False
   
            filtro_prioridade = filtros.get("prioridade", "Todas")
            if incluir and filtro_prioridade != "Todas" and paciente.get("prioridade") != filtro_prioridade:
                incluir = False
            
            if incluir:
                dados_filtrados.append(paciente)
            
            i = i + 1
        
        return dados_filtrados
    
    def aplicar_ordenacao(dados, ordenacao):
        if ordenacao == "id_crescente":
            return sorted(dados, key=lambda x: extrair_numero_id(x.get("id", "")))
        elif ordenacao == "id_decrescente":
            return sorted(dados, key=lambda x: extrair_numero_id(x.get("id", "")), reverse=True)
        elif ordenacao == "nome_asc":
            return sorted(dados, key=lambda x: x.get("nome", "").lower())
        elif ordenacao == "nome_desc":
            return sorted(dados, key=lambda x: x.get("nome", "").lower(), reverse=True)
        elif ordenacao == "idade_asc":
            def idade_para_ordenar(p):
                idade_str = p.get("idade", "N/A")
                if idade_str == "N/A":
                    return 9999
                try:
                    return int(idade_str)
                except:
                    return 9998
            return sorted(dados, key=idade_para_ordenar)
        elif ordenacao == "idade_desc":
            def idade_para_ordenar(p):
                idade_str = p.get("idade", "N/A")
                if idade_str == "N/A":
                    return 0
                try:
                    return int(idade_str)
                except:
                    return 1
            return sorted(dados, key=idade_para_ordenar, reverse=True)
        elif ordenacao == "prioridade_desc":
            prioridade_ordem = {"URGENTE": 1, "ALTA": 2, "NORMAL": 3, "BAIXA": 4}
            return sorted(dados, key=lambda x: prioridade_ordem.get(x.get("prioridade", "NORMAL"), 3))
        elif ordenacao == "prioridade_asc":
            prioridade_ordem = {"URGENTE": 4, "ALTA": 3, "NORMAL": 2, "BAIXA": 1}
            return sorted(dados, key=lambda x: prioridade_ordem.get(x.get("prioridade", "NORMAL"), 2))
        elif ordenacao == "espera_asc":
            return sorted(dados, key=lambda x: x.get("tempo_espera", 0))
        elif ordenacao == "espera_desc":
            return sorted(dados, key=lambda x: x.get("tempo_espera", 0), reverse=True)
        elif ordenacao == "espec_asc":
            return sorted(dados, key=lambda x: x.get("especialidade_necessaria", "").lower())
        else:
            return dados
    
    def mostrar_detalhes_paciente(paciente_selecionado):
        if not paciente_selecionado:
            return
        
        sg.theme('TemaClinica')
        
        dados_pessoais = [
            ["ID:", paciente_selecionado.get("id", "N/A")],
            ["Nome:", paciente_selecionado.get("nome", "N/A")],
            ["Idade:", paciente_selecionado.get("idade", "N/A")],
            ["Sexo:", paciente_selecionado.get("sexo", "N/A")],
            ["Prioridade:", paciente_selecionado.get("prioridade", "N/A")]
        ]
        
        dados_consulta = [
            ["Status:", paciente_selecionado.get("status", "N/A")],
            ["Especialidade:", paciente_selecionado.get("especialidade_necessaria", "N/A")],
            ["Espera:", f"{paciente_selecionado.get('tempo_espera', 0):.1f} min"],
            ["Duração:", f"{paciente_selecionado.get('duracao_consulta', 0):.1f} min"]
        ]
        
        if paciente_selecionado.get("status") == "ATENDIDO":
            dados_consulta.append(["Médico:", paciente_selecionado.get("medico_nome", "N/A")])
        
        dados_saude = [
            ["Fumador:", 'Sim' if paciente_selecionado.get('fumador') else 'Não'],
            ["Álcool:", 'Sim' if paciente_selecionado.get('consome_alcool') else 'Não'],
            ["Crónico:", 'Sim' if paciente_selecionado.get('cronico') else 'Não']
        ]

        conteudo_layout = [
            [sg.Text("FICHA DO PACIENTE", font=("Helvetica", 14, "bold"), text_color=escuro, pad=(0, 5))],
            
            [sg.Frame("DADOS PESSOAIS", [
                [sg.Column([[sg.Text(l, size=(12, 1), font=("Helvetica", 9)), 
                            sg.Text(v, font=("Helvetica", 9, "bold"), text_color=escuro)] 
                            for l, v in dados_pessoais], pad=(5, 2))]
            ], expand_x=True, pad=(5, 5))],
            
            [sg.Frame("DADOS DA CONSULTA", [
                [sg.Column([[sg.Text(l, size=(12, 1), font=("Helvetica", 9)), 
                            sg.Text(v, font=("Helvetica", 9, "bold"), text_color=escuro)] 
                            for l, v in dados_consulta], pad=(5, 2))]
            ], expand_x=True, pad=(5, 5))],
            
            [sg.Frame("HÁBITOS DE SAÚDE", [
                [sg.Column([[sg.Text(l, size=(12, 1), font=("Helvetica", 9)), 
                            sg.Text(v, font=("Helvetica", 9, "bold"), text_color=escuro)] 
                            for l, v in dados_saude], pad=(5, 2))]
            ], expand_x=True, pad=(5, 5))],
            
            [sg.Button("Fechar", size=(10, 1), button_color=('white', escuro), pad=(0, 10))]
        ]

        layout = [[sg.Column(conteudo_layout, scrollable=True, vertical_scroll_only=True, 
                            size=(480, 560), element_justification='center', key='-COL-')]]
        
        window_detalhes = sg.Window(f"Ficha: {paciente_selecionado.get('nome', 'N/A')}", 
                                layout, modal=True, finalize=True, size=(500, 580), 
                                element_justification='center', keep_on_top=True)
        
        window_detalhes['-COL-'].contents_changed()

        while True:
            event, values = window_detalhes.read()
            if event in (sg.WINDOW_CLOSED, "Fechar"):
                window_detalhes.close()
                return
        
    def atualizar_tabela_com_valores(valores_atual, pacientes_lista):
        filtros_dict = {
            "id": valores_atual.get("-FILTRO_ID-", ""),
            "nome": valores_atual.get("-FILTRO_NOME-", ""),
            "sexo": valores_atual.get("-FILTRO_SEXO-", "Todos"),
            "idade": valores_atual.get("-FILTRO_IDADE-", "Todas"),
            "especialidade": valores_atual.get("-FILTRO_ESPEC-", "Todas"),
            "medico": valores_atual.get("-FILTRO_MEDICO-", "Todos"),
            "status": valores_atual.get("-FILTRO_STATUS-", "Todos"),
            "prioridade": valores_atual.get("-FILTRO_PRIORIDADE-", "Todas")
        }
        
        ordenacao = "id_crescente"
        if valores_atual.get("-ORD_ID_DECRESC-"):
            ordenacao = "id_decrescente"
        elif valores_atual.get("-ORD_NOME_ASC-"):
            ordenacao = "nome_asc"
        elif valores_atual.get("-ORD_NOME_DESC-"):
            ordenacao = "nome_desc"
        elif valores_atual.get("-ORD_IDADE_ASC-"):
            ordenacao = "idade_asc"
        elif valores_atual.get("-ORD_IDADE_DESC-"):
            ordenacao = "idade_desc"
        elif valores_atual.get("-ORD_PRIORIDADE_DESC-"):
            ordenacao = "prioridade_desc"
        elif valores_atual.get("-ORD_PRIORIDADE_ASC-"):
            ordenacao = "prioridade_asc"
        elif valores_atual.get("-ORD_ESPERA_ASC-"):
            ordenacao = "espera_asc"
        elif valores_atual.get("-ORD_ESPERA_DESC-"):
            ordenacao = "espera_desc"
        elif valores_atual.get("-ORD_ESPEC_ASC-"):
            ordenacao = "espec_asc"
        
        dados_filtrados = aplicar_filtros_completos(pacientes_lista, filtros_dict)
        dados_filtrados_ordenados = aplicar_ordenacao(dados_filtrados, ordenacao)
        
        nova_tabela = []
        for p in dados_filtrados_ordenados:
            tempo_espera = p.get("tempo_espera", 0)
            if tempo_espera >= 60:
                horas = int(tempo_espera // 60)
                minutos = int(tempo_espera % 60)
                tempo_espera_str = f"{horas}h{minutos:02d}m"
            else:
                tempo_espera_str = f"{tempo_espera:.0f}m"
            
            duracao_consulta = p.get("duracao_consulta", 0)
            if duracao_consulta >= 60:
                horas = int(duracao_consulta // 60)
                minutos = int(duracao_consulta % 60)
                duracao_str = f"{horas}h{minutos:02d}m"
            else:
                duracao_str = f"{duracao_consulta:.0f}m"
            
            status = p.get("status", "")
            if status == "ATENDIDO":
                status_str = "Atendido"
            elif status == "NA FILA":
                status_str = "Na fila"
            else:
                status_str = "Desistente"
            
            nova_tabela.append([
                p.get("id", ""),
                p.get("nome", "")[:20],
                p.get("sexo", "N/A"),
                p.get("idade", "N/A"),
                p.get("prioridade", ""),
                p.get("especialidade_necessaria", "")[:18],
                status_str,
                tempo_espera_str,
                duracao_str,
                p.get("medico_nome", "N/A")[:15]
            ])
        
        window["-TABELA_PACIENTES-"].update(values=nova_tabela)
        total_filtrados = len(dados_filtrados_ordenados)
        texto_total = f"Total de pacientes: {len(pacientes_original)} (filtrados: {total_filtrados})"
        window["-TOTAL_PACIENTES-"].update(texto_total)
        
        return dados_filtrados_ordenados
   
    pacientes_filtrados_atual = atualizar_tabela_com_valores(valores_janela, pacientes_original)
    
    continuar = True
    while continuar:
        event, values = window.read()
        
        if event == sg.WINDOW_CLOSED or event == "-FECHAR-":
            continuar = False
        
        elif event in ["-FILTRO_ID-", "-FILTRO_NOME-", "-FILTRO_SEXO-", "-FILTRO_IDADE-",
                      "-FILTRO_ESPEC-", "-FILTRO_MEDICO-", "-FILTRO_STATUS-", "-FILTRO_PRIORIDADE-",
                      "-ORD_ID_CRESC-", "-ORD_ID_DECRESC-", "-ORD_NOME_ASC-", "-ORD_NOME_DESC-",
                      "-ORD_IDADE_ASC-", "-ORD_IDADE_DESC-", "-ORD_PRIORIDADE_DESC-", "-ORD_PRIORIDADE_ASC-",
                      "-ORD_ESPERA_ASC-", "-ORD_ESPERA_DESC-", "-ORD_ESPEC_ASC-"]:
            
            if event == "-FILTRO_ID-":
                valores_janela["-FILTRO_ID-"] = values.get("-FILTRO_ID-", "")
            elif event == "-FILTRO_NOME-":
                valores_janela["-FILTRO_NOME-"] = values.get("-FILTRO_NOME-", "")
            elif event == "-FILTRO_SEXO-":
                valores_janela["-FILTRO_SEXO-"] = values.get("-FILTRO_SEXO-", "Todos")
            elif event == "-FILTRO_IDADE-":
                valores_janela["-FILTRO_IDADE-"] = values.get("-FILTRO_IDADE-", "Todas")
            elif event == "-FILTRO_ESPEC-":
                valores_janela["-FILTRO_ESPEC-"] = values.get("-FILTRO_ESPEC-", "Todas")
            elif event == "-FILTRO_MEDICO-":
                valores_janela["-FILTRO_MEDICO-"] = values.get("-FILTRO_MEDICO-", "Todos")
            elif event == "-FILTRO_STATUS-":
                valores_janela["-FILTRO_STATUS-"] = values.get("-FILTRO_STATUS-", "Todos")
            elif event == "-FILTRO_PRIORIDADE-":
                valores_janela["-FILTRO_PRIORIDADE-"] = values.get("-FILTRO_PRIORIDADE-", "Todas")
            
            elif event == "-ORD_ID_CRESC-":
                valores_janela["-ORD_ID_CRESC-"] = True
                valores_janela["-ORD_ID_DECRESC-"] = False
                valores_janela["-ORD_NOME_ASC-"] = False
                valores_janela["-ORD_NOME_DESC-"] = False
                valores_janela["-ORD_IDADE_ASC-"] = False
                valores_janela["-ORD_IDADE_DESC-"] = False
                valores_janela["-ORD_PRIORIDADE_DESC-"] = False
                valores_janela["-ORD_PRIORIDADE_ASC-"] = False
                valores_janela["-ORD_ESPERA_ASC-"] = False
                valores_janela["-ORD_ESPERA_DESC-"] = False
                valores_janela["-ORD_ESPEC_ASC-"] = False
            elif event == "-ORD_ID_DECRESC-":
                valores_janela["-ORD_ID_CRESC-"] = False
                valores_janela["-ORD_ID_DECRESC-"] = True
                valores_janela["-ORD_NOME_ASC-"] = False
                valores_janela["-ORD_NOME_DESC-"] = False
                valores_janela["-ORD_IDADE_ASC-"] = False
                valores_janela["-ORD_IDADE_DESC-"] = False
                valores_janela["-ORD_PRIORIDADE_DESC-"] = False
                valores_janela["-ORD_PRIORIDADE_ASC-"] = False
                valores_janela["-ORD_ESPERA_ASC-"] = False
                valores_janela["-ORD_ESPERA_DESC-"] = False
                valores_janela["-ORD_ESPEC_ASC-"] = False
            elif event == "-ORD_NOME_ASC-":
                valores_janela["-ORD_ID_CRESC-"] = False
                valores_janela["-ORD_ID_DECRESC-"] = False
                valores_janela["-ORD_NOME_ASC-"] = True
                valores_janela["-ORD_NOME_DESC-"] = False
                valores_janela["-ORD_IDADE_ASC-"] = False
                valores_janela["-ORD_IDADE_DESC-"] = False
                valores_janela["-ORD_PRIORIDADE_DESC-"] = False
                valores_janela["-ORD_PRIORIDADE_ASC-"] = False
                valores_janela["-ORD_ESPERA_ASC-"] = False
                valores_janela["-ORD_ESPERA_DESC-"] = False
                valores_janela["-ORD_ESPEC_ASC-"] = False
            elif event == "-ORD_NOME_DESC-":
                valores_janela["-ORD_ID_CRESC-"] = False
                valores_janela["-ORD_ID_DECRESC-"] = False
                valores_janela["-ORD_NOME_ASC-"] = False
                valores_janela["-ORD_NOME_DESC-"] = True
                valores_janela["-ORD_IDADE_ASC-"] = False
                valores_janela["-ORD_IDADE_DESC-"] = False
                valores_janela["-ORD_PRIORIDADE_DESC-"] = False
                valores_janela["-ORD_PRIORIDADE_ASC-"] = False
                valores_janela["-ORD_ESPERA_ASC-"] = False
                valores_janela["-ORD_ESPERA_DESC-"] = False
                valores_janela["-ORD_ESPEC_ASC-"] = False
            elif event == "-ORD_IDADE_ASC-":
                valores_janela["-ORD_ID_CRESC-"] = False
                valores_janela["-ORD_ID_DECRESC-"] = False
                valores_janela["-ORD_NOME_ASC-"] = False
                valores_janela["-ORD_NOME_DESC-"] = False
                valores_janela["-ORD_IDADE_ASC-"] = True
                valores_janela["-ORD_IDADE_DESC-"] = False
                valores_janela["-ORD_PRIORIDADE_DESC-"] = False
                valores_janela["-ORD_PRIORIDADE_ASC-"] = False
                valores_janela["-ORD_ESPERA_ASC-"] = False
                valores_janela["-ORD_ESPERA_DESC-"] = False
                valores_janela["-ORD_ESPEC_ASC-"] = False
            elif event == "-ORD_IDADE_DESC-":
                valores_janela["-ORD_ID_CRESC-"] = False
                valores_janela["-ORD_ID_DECRESC-"] = False
                valores_janela["-ORD_NOME_ASC-"] = False
                valores_janela["-ORD_NOME_DESC-"] = False
                valores_janela["-ORD_IDADE_ASC-"] = False
                valores_janela["-ORD_IDADE_DESC-"] = True
                valores_janela["-ORD_PRIORIDADE_DESC-"] = False
                valores_janela["-ORD_PRIORIDADE_ASC-"] = False
                valores_janela["-ORD_ESPERA_ASC-"] = False
                valores_janela["-ORD_ESPERA_DESC-"] = False
                valores_janela["-ORD_ESPEC_ASC-"] = False
            elif event == "-ORD_PRIORIDADE_DESC-":
                valores_janela["-ORD_ID_CRESC-"] = False
                valores_janela["-ORD_ID_DECRESC-"] = False
                valores_janela["-ORD_NOME_ASC-"] = False
                valores_janela["-ORD_NOME_DESC-"] = False
                valores_janela["-ORD_IDADE_ASC-"] = False
                valores_janela["-ORD_IDADE_DESC-"] = False
                valores_janela["-ORD_PRIORIDADE_DESC-"] = True
                valores_janela["-ORD_PRIORIDADE_ASC-"] = False
                valores_janela["-ORD_ESPERA_ASC-"] = False
                valores_janela["-ORD_ESPERA_DESC-"] = False
                valores_janela["-ORD_ESPEC_ASC-"] = False
            elif event == "-ORD_PRIORIDADE_ASC-":
                valores_janela["-ORD_ID_CRESC-"] = False
                valores_janela["-ORD_ID_DECRESC-"] = False
                valores_janela["-ORD_NOME_ASC-"] = False
                valores_janela["-ORD_NOME_DESC-"] = False
                valores_janela["-ORD_IDADE_ASC-"] = False
                valores_janela["-ORD_IDADE_DESC-"] = False
                valores_janela["-ORD_PRIORIDADE_DESC-"] = False
                valores_janela["-ORD_PRIORIDADE_ASC-"] = True
                valores_janela["-ORD_ESPERA_ASC-"] = False
                valores_janela["-ORD_ESPERA_DESC-"] = False
                valores_janela["-ORD_ESPEC_ASC-"] = False
            elif event == "-ORD_ESPERA_ASC-":
                valores_janela["-ORD_ID_CRESC-"] = False
                valores_janela["-ORD_ID_DECRESC-"] = False
                valores_janela["-ORD_NOME_ASC-"] = False
                valores_janela["-ORD_NOME_DESC-"] = False
                valores_janela["-ORD_IDADE_ASC-"] = False
                valores_janela["-ORD_IDADE_DESC-"] = False
                valores_janela["-ORD_PRIORIDADE_DESC-"] = False
                valores_janela["-ORD_PRIORIDADE_ASC-"] = False
                valores_janela["-ORD_ESPERA_ASC-"] = True
                valores_janela["-ORD_ESPERA_DESC-"] = False
                valores_janela["-ORD_ESPEC_ASC-"] = False
            elif event == "-ORD_ESPERA_DESC-":
                valores_janela["-ORD_ID_CRESC-"] = False
                valores_janela["-ORD_ID_DECRESC-"] = False
                valores_janela["-ORD_NOME_ASC-"] = False
                valores_janela["-ORD_NOME_DESC-"] = False
                valores_janela["-ORD_IDADE_ASC-"] = False
                valores_janela["-ORD_IDADE_DESC-"] = False
                valores_janela["-ORD_PRIORIDADE_DESC-"] = False
                valores_janela["-ORD_PRIORIDADE_ASC-"] = False
                valores_janela["-ORD_ESPERA_ASC-"] = False
                valores_janela["-ORD_ESPERA_DESC-"] = True
                valores_janela["-ORD_ESPEC_ASC-"] = False
            elif event == "-ORD_ESPEC_ASC-":
                valores_janela["-ORD_ID_CRESC-"] = False
                valores_janela["-ORD_ID_DECRESC-"] = False
                valores_janela["-ORD_NOME_ASC-"] = False
                valores_janela["-ORD_NOME_DESC-"] = False
                valores_janela["-ORD_IDADE_ASC-"] = False
                valores_janela["-ORD_IDADE_DESC-"] = False
                valores_janela["-ORD_PRIORIDADE_DESC-"] = False
                valores_janela["-ORD_PRIORIDADE_ASC-"] = False
                valores_janela["-ORD_ESPERA_ASC-"] = False
                valores_janela["-ORD_ESPERA_DESC-"] = False
                valores_janela["-ORD_ESPEC_ASC-"] = True
            
            pacientes_filtrados_atual = atualizar_tabela_com_valores(valores_janela, pacientes_original)
        
        elif event == "-LIMPAR_FILTROS-":
            window["-FILTRO_ID-"].update("")
            window["-FILTRO_NOME-"].update("")
            window["-FILTRO_SEXO-"].update("Todos")
            window["-FILTRO_IDADE-"].update("Todas")
            window["-FILTRO_ESPEC-"].update("Todas")
            window["-FILTRO_MEDICO-"].update("Todos")
            window["-FILTRO_STATUS-"].update("Todos")
            window["-FILTRO_PRIORIDADE-"].update("Todas")
            window["-ORD_ID_CRESC-"].update(True)
            
            valores_janela["-FILTRO_ID-"] = ""
            valores_janela["-FILTRO_NOME-"] = ""
            valores_janela["-FILTRO_SEXO-"] = "Todos"
            valores_janela["-FILTRO_IDADE-"] = "Todas"
            valores_janela["-FILTRO_ESPEC-"] = "Todas"
            valores_janela["-FILTRO_MEDICO-"] = "Todos"
            valores_janela["-FILTRO_STATUS-"] = "Todos"
            valores_janela["-FILTRO_PRIORIDADE-"] = "Todas"
            valores_janela["-ORD_ID_CRESC-"] = True
            valores_janela["-ORD_ID_DECRESC-"] = False
            valores_janela["-ORD_NOME_ASC-"] = False
            valores_janela["-ORD_NOME_DESC-"] = False
            valores_janela["-ORD_IDADE_ASC-"] = False
            valores_janela["-ORD_IDADE_DESC-"] = False
            valores_janela["-ORD_PRIORIDADE_DESC-"] = False
            valores_janela["-ORD_PRIORIDADE_ASC-"] = False
            valores_janela["-ORD_ESPERA_ASC-"] = False
            valores_janela["-ORD_ESPERA_DESC-"] = False
            valores_janela["-ORD_ESPEC_ASC-"] = False
            
            pacientes_filtrados_atual = atualizar_tabela_com_valores(valores_janela, pacientes_original)
        
        elif event == "-VER_DETALHES-":
            if values and "-TABELA_PACIENTES-" in values and values["-TABELA_PACIENTES-"]:
                selected_index = values["-TABELA_PACIENTES-"][0]
                if selected_index < len(pacientes_filtrados_atual):
                    mostrar_detalhes_paciente(pacientes_filtrados_atual[selected_index])
            else:
                sg.popup("Selecione um paciente para ver os detalhes.", title="Aviso")
        
        elif event == "-ESTATISTICAS-":
            if pacientes_filtrados_atual:
                mostrar_estatisticas_pacientes(pacientes_filtrados_atual)
            else:
                sg.popup("Nenhum paciente para gerar estatísticas.", title="Aviso")
        
        elif event == "-EXPORTAR_TXT-":
            if pacientes_filtrados_atual:
                nome_arquivo = f"pacientes_{titulo.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
                conteudo = f"LISTA DE PACIENTES - {titulo}\n"
                conteudo += "=" * 80 + "\n"
                conteudo += f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
                conteudo += f"Total de pacientes: {len(pacientes_filtrados_atual)}\n\n"
                
                for i, paciente in enumerate(pacientes_filtrados_atual):
                    conteudo += f"PACIENTE {i+1}:\n"
                    conteudo += f"  ID: {paciente.get('id', 'N/A')}\n"
                    conteudo += f"  Nome: {paciente.get('nome', 'N/A')}\n"
                    conteudo += f"  Idade: {paciente.get('idade', 'N/A')}\n"
                    conteudo += f"  Sexo: {paciente.get('sexo', 'N/A')}\n"
                    conteudo += f"  Doença: {paciente.get('doenca', 'N/A')}\n"
                    conteudo += f"  Prioridade: {paciente.get('prioridade', 'N/A')}\n"
                    conteudo += f"  Status: {paciente.get('status', 'N/A')}\n"
                    conteudo += f"  Especialidade Necessária: {paciente.get('especialidade_necessaria', 'N/A')}\n"
                    conteudo += f"  Tempo de Espera: {paciente.get('tempo_espera', 0):.1f} minutos\n"
                    
                    if paciente.get("status") == "ATENDIDO":
                        conteudo += f"  Médico Atendente: {paciente.get('medico_nome', 'N/A')}\n"
                        conteudo += f"  Correspondência Especialidade: {'Correta' if paciente.get('especialidade_correta') else 'Incorreta'}\n"
                        conteudo += f"  Duração da Consulta: {paciente.get('duracao_consulta', 0):.1f} minutos\n"
                    
                    conteudo += f"  Hábitos de Saúde:\n"
                    conteudo += f"    - Fumador: {'Sim' if paciente.get('fumador') == True else 'Não' if paciente.get('fumador') == False else 'N/A'}\n"
                    conteudo += f"    - Consome Álcool: {'Sim' if paciente.get('consome_alcool') == True else 'Não' if paciente.get('consome_alcool') == False else 'N/A'}\n"
                    conteudo += f"    - Atividade Física: {paciente.get('atividade_fisica', 'N/A')}\n"
                    conteudo += f"    - Doença Crônica: {'Sim' if paciente.get('cronico') == True else 'Não' if paciente.get('cronico') == False else 'N/A'}\n"
                    conteudo += "-" * 50 + "\n"
                
                arquivo_salvo = False
                f = None
                f = open(nome_arquivo, "w", encoding="utf-8")
                if f:
                    f.write(conteudo)
                    f.close()
                    arquivo_salvo = True
                
                if arquivo_salvo:
                    sg.popup(f"Arquivo exportado com sucesso!\n\n{nome_arquivo}", title="Exportação Concluída")
                else:
                    sg.popup_error("Erro ao exportar arquivo.", title="Erro")
            else:
                sg.popup("Nenhum paciente para exportar.", title="Aviso")
    
    window.close()



def gerar_relatorio_desempenho_medicos(medicos, tempo_atual, titulo_simulacao, estatisticas_especialidades=None):
    
    relatorio = []
    
    relatorio.append(f"RELATÓRIO DE DESEMPENHO MÉDICO - {titulo_simulacao}")
    relatorio.append("=" * 70)
    relatorio.append(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    relatorio.append(f"Tempo total de simulação: {tempo_atual:.0f} minutos ({tempo_atual/60:.1f} horas)")
    relatorio.append(f"Total de médicos analisados: {len(medicos)}")
    relatorio.append("")
    
    if medicos:
       
        total_atendimentos = 0
        soma_eficiencia = 0
        soma_tempo = 0
        soma_corresp = 0
        soma_ocup = 0
        
       
        especialidades_stats = {}
        
        i = 0
        while i < len(medicos):
            medico = medicos[i]
            total_atendimentos = total_atendimentos + medico.get('num_atendimentos', 0)
            soma_eficiencia = soma_eficiencia + medico.get('eficiencia', 0)
            soma_tempo = soma_tempo + medico.get('tempo_medio_consulta', 0)
            soma_corresp = soma_corresp + medico.get('taxa_correspondencia', 0)
            soma_ocup = soma_ocup + medico.get('taxa_ocupacao', 0)
            
            especialidade = medico.get('especialidade', 'Geral')
            if especialidade not in especialidades_stats:
                especialidades_stats[especialidade] = {
                    'count': 0,
                    'atendimentos': 0,
                    'eficiencia': 0,
                    'tempo_medio': 0,
                    'correspondencia': 0,
                    'ocupacao': 0
                }
            
            especialidades_stats[especialidade]['count'] += 1
            especialidades_stats[especialidade]['atendimentos'] += medico.get('num_atendimentos', 0)
            especialidades_stats[especialidade]['eficiencia'] += medico.get('eficiencia', 0)
            especialidades_stats[especialidade]['tempo_medio'] += medico.get('tempo_medio_consulta', 0)
            especialidades_stats[especialidade]['correspondencia'] += medico.get('taxa_correspondencia', 0)
            especialidades_stats[especialidade]['ocupacao'] += medico.get('taxa_ocupacao', 0)
            
            i = i + 1
        
        eficiencia_media = soma_eficiencia / len(medicos) if medicos else 0
        tempo_medio_consulta_media = soma_tempo / len(medicos) if medicos else 0
        taxa_correspondencia_media = soma_corresp / len(medicos) if medicos else 0
        taxa_ocupacao_media = soma_ocup / len(medicos) if medicos else 0
        
        relatorio.append("ESTATÍSTICAS GERAIS:")
        relatorio.append("-" * 50)
        relatorio.append(f"Total de atendimentos realizados: {total_atendimentos}")
        relatorio.append(f"Eficiência média: {eficiencia_media:.2f} pacientes/hora")
        relatorio.append(f"Tempo médio de consulta: {tempo_medio_consulta_media:.1f} minutos")
        relatorio.append(f"Taxa média de correspondência: {taxa_correspondencia_media:.1f}%")
        relatorio.append(f"Taxa média de ocupação: {taxa_ocupacao_media:.1f}%")
        relatorio.append("")
        
        
        if estatisticas_especialidades:
            relatorio.append("ESTATÍSTICAS POR ESPECIALIDADE:")
            relatorio.append("-" * 50)
            
            for especialidade, stats in especialidades_stats.items():
                count = stats['count']
                relatorio.append(f"\n{especialidade.upper()} ({count} médico{'s' if count > 1 else ''}):")
                relatorio.append(f"  • Atendimentos: {stats['atendimentos']}")
                relatorio.append(f"  • Eficiência média: {(stats['eficiencia']/count):.2f} pacientes/hora")
                relatorio.append(f"  • Tempo médio: {(stats['tempo_medio']/count):.1f} minutos")
                relatorio.append(f"  • Correspondência: {(stats['correspondencia']/count):.1f}%")
                relatorio.append(f"  • Ocupação: {(stats['ocupacao']/count):.1f}%")
            relatorio.append("")
        
       
        if medicos:
            melhor_eficiencia_idx = 0
            pior_eficiencia_idx = 0
            melhor_corresp_idx = 0
            pior_corresp_idx = 0
            
            i = 1
            while i < len(medicos):
                if medicos[i].get('eficiencia', 0) > medicos[melhor_eficiencia_idx].get('eficiencia', 0):
                    melhor_eficiencia_idx = i
                if medicos[i].get('eficiencia', 0) < medicos[pior_eficiencia_idx].get('eficiencia', 0):
                    pior_eficiencia_idx = i
                if medicos[i].get('taxa_correspondencia', 0) > medicos[melhor_corresp_idx].get('taxa_correspondencia', 0):
                    melhor_corresp_idx = i
                if medicos[i].get('taxa_correspondencia', 0) < medicos[pior_corresp_idx].get('taxa_correspondencia', 0):
                    pior_corresp_idx = i
                i = i + 1
            
            relatorio.append("MÉDICOS DESTAQUE:")
            relatorio.append("-" * 50)
            relatorio.append(f"Melhor eficiência: M{melhor_eficiencia_idx+1} ({medicos[melhor_eficiencia_idx].get('eficiencia', 0):.2f} pacientes/hora)")
            relatorio.append(f"Melhor correspondência: M{melhor_corresp_idx+1} ({medicos[melhor_corresp_idx].get('taxa_correspondencia', 0):.1f}%)")
            relatorio.append("")
    
    relatorio.append("DETALHES POR MÉDICO:")
    relatorio.append("-" * 50)
    
    i = 0
    while i < len(medicos):
        medico = medicos[i]
        
       
        id_simples = f"M{i+1}"
        medico_nome = medico.get('nome', f'Médico {i+1}')
        
        num_atendimentos = medico.get('num_atendimentos', 0)
        eficiencia = medico.get('eficiencia', 0)
        tempo_medio = medico.get('tempo_medio_consulta', 0)
        taxa_corresp = medico.get('taxa_correspondencia', 0)
        taxa_ocup = medico.get('taxa_ocupacao', 0)
        
        relatorio.append(f"\n{id_simples} - {medico_nome} ({medico.get('especialidade', 'Geral')}):")
        relatorio.append(f"   • Atendimentos: {num_atendimentos}")
        relatorio.append(f"   • Eficiência: {eficiencia:.2f} pacientes/hora")
        relatorio.append(f"   • Tempo médio consulta: {tempo_medio:.1f} minutos")
        relatorio.append(f"   • Correspondência: {taxa_corresp:.1f}%")
        relatorio.append(f"   • Ocupação: {taxa_ocup:.1f}%")
        
        i = i + 1
    
    relatorio.append("\n" + "=" * 70)
    relatorio.append("LEGENDA:")
    relatorio.append("- Eficiência: Pacientes atendidos por hora de trabalho")
    relatorio.append("- Correspondência: % de consultas com especialista adequado")
    relatorio.append("- Ocupação: % do tempo em que o médico está ocupado")
    relatorio.append("- IDs: M1, M2, M3... correspondem à ordem dos médicos na simulação")
    
    return "\n".join(relatorio)

def mostrar_desempenho_medicos():
    """Mostra análise de desempenho dos médicos - APENAS SIMULAÇÃO ATUAL"""
    sg.theme('TemaClinica')
    
    historico_atendimentos = estado_simulacao.get("historico_atendimentos", [])
    medicos_atuais = estado_simulacao.get("medicos", [])
    
    tem_dados_atuais = len(historico_atendimentos) > 0 and len(medicos_atuais) > 0

    if not tem_dados_atuais:
        sg.popup_error("Nenhuma simulação com atendimentos disponível!\nExecute uma simulação primeiro.", title="Erro")
        return

    tempo_total_min = max(1, estado_simulacao.get("tempo_atual", 1))
    horas_trabalhadas = tempo_total_min / 60.0
    medicos_processados = []

    for idx, medico in enumerate(medicos_atuais):
        id_medico = medico.get("id", "")
        
        cont_atend = 0
        cont_corretos = 0
        lista_duracoes = []

        for atend in historico_atendimentos:
            id_atend = atend.get("medico", "")
            if str(id_medico).lower().strip() == str(id_atend).lower().strip():
                cont_atend += 1
                duracao_atend = atend.get("duracao", 0)
                if duracao_atend > 0:
                    lista_duracoes.append(duracao_atend)
                if atend.get("especialidade_correta", False):
                    cont_corretos += 1

        soma_duracao = sum(lista_duracoes) if lista_duracoes else 0
        eficiencia_calc = cont_atend / horas_trabalhadas if horas_trabalhadas > 0 else 0
        t_medio_calc = soma_duracao / len(lista_duracoes) if lista_duracoes else 0
        t_corresp_calc = (cont_corretos / cont_atend * 100) if cont_atend > 0 else 0
        
        tempo_ocupado = medico.get("tempo_total_ocupado", soma_duracao)
        t_ocup_calc = (tempo_ocupado / tempo_total_min * 100) if tempo_total_min > 0 else 0
        t_ocup_calc = min(100.0, max(0.0, t_ocup_calc))

        medicos_processados.append({
            "id": medico.get("id", f"M{idx+1}"),
            "nome": medico.get("nome", f"Médico {idx+1}"),
            "especialidade": medico.get("especialidade", "Geral"),
            "num_atendimentos": cont_atend,
            "tempo_total_ocupado": tempo_ocupado,
            "tempo_medio_consulta": t_medio_calc,
            "taxa_correspondencia": t_corresp_calc,
            "taxa_ocupacao": t_ocup_calc,
            "eficiencia": eficiencia_calc
        })

    dados_selecionados = {
        "medicos": medicos_processados, 
        "tempo_atual": tempo_total_min, 
        "titulo": "Simulação Atual",
        "historico_atendimentos": historico_atendimentos
    }

    mostrar_analise_completa_medicos(dados_selecionados)

def mostrar_analise_completa_medicos(dados_simulacao):
    """Mostra análise completa dos médicos com gráficos simplificados"""
    medicos = dados_simulacao["medicos"]
    tempo_atual = dados_simulacao["tempo_atual"]
    titulo_simulacao = dados_simulacao.get("titulo", "Simulação Clínica")

    especialidades_stats = {}
    for medico in medicos:
        especialidade = medico.get('especialidade', 'Geral')
        if especialidade not in especialidades_stats:
            especialidades_stats[especialidade] = {
                'count': 0,
                'eficiencia_media': 0,
                'tempo_medio': 0,
                'taxa_corresp_media': 0,
                'taxa_ocup_media': 0,
                'atendimentos_total': 0
            }
        
        especialidades_stats[especialidade]['count'] += 1
        especialidades_stats[especialidade]['eficiencia_media'] += medico.get('eficiencia', 0)
        especialidades_stats[especialidade]['tempo_medio'] += medico.get('tempo_medio_consulta', 0)
        especialidades_stats[especialidade]['taxa_corresp_media'] += medico.get('taxa_correspondencia', 0)
        especialidades_stats[especialidade]['taxa_ocup_media'] += medico.get('taxa_ocupacao', 0)
        especialidades_stats[especialidade]['atendimentos_total'] += medico.get('num_atendimentos', 0)
    
    for especialidade in especialidades_stats:
        count = especialidades_stats[especialidade]['count']
        if count > 0:
            especialidades_stats[especialidade]['eficiencia_media'] /= count
            especialidades_stats[especialidade]['tempo_medio'] /= count
            especialidades_stats[especialidade]['taxa_corresp_media'] /= count
            especialidades_stats[especialidade]['taxa_ocup_media'] /= count
    

    relatorio_texto = gerar_relatorio_desempenho_medicos(medicos, tempo_atual, titulo_simulacao, especialidades_stats)
    

    ids_medicos = []
    especialidades = []
    eficiencias = []
    tempos_medios = []
    taxas_corresp = []
    taxas_ocup = []
    
    i = 0
    while i < len(medicos):
        
        id_simples = f"M{i+1}"
        ids_medicos.append(id_simples)
        
        medico = medicos[i]
        especialidades.append(medico.get("especialidade", "Geral"))
        eficiencias.append(medico.get("eficiencia", 0))
        tempos_medios.append(medico.get("tempo_medio_consulta", 0))
        taxas_corresp.append(medico.get("taxa_correspondencia", 0))
        taxas_ocup.append(medico.get("taxa_ocupacao", 0))
        i = i + 1
    
    tab1_layout = [
        [sg.Text("Eficiência por Médico", font=("Helvetica", 14))],
        [sg.Canvas(key="-CANVAS_EFICIENCIA-", size=(650, 450))]
    ]
    
    tab2_layout = [
        [sg.Text("Tempo Médio de Consulta", font=("Helvetica", 14))],
        [sg.Canvas(key="-CANVAS_TEMPO-", size=(650, 450))]
    ]
    
    tab3_layout = [
        [sg.Text("Correspondência de Especialidade", font=("Helvetica", 14))],
        [sg.Canvas(key="-CANVAS_CORRESP-", size=(650, 450))]
    ]
    
    tab4_layout = [
        [sg.Text("Taxa de Ocupação", font=("Helvetica", 14))],
        [sg.Canvas(key="-CANVAS_OCUPACAO-", size=(650, 450))]
    ]
    
    tab5_layout = [
        [sg.Text("Relatório Completo", font=("Helvetica", 14))],
        [sg.Multiline(relatorio_texto, size=(85, 30), key="-RELATORIO-",
                     font=("Courier New", 9), disabled=True, 
                     horizontal_scroll=True, autoscroll=True,
                     expand_x=True, expand_y=True)]
    ]
    
    layout = [
        [sg.Text(f"Análise de Desempenho Médico: {titulo_simulacao}", 
                font=("Helvetica", 16), justification="center", expand_x=True)],
        [sg.TabGroup([
            [sg.Tab('Eficiência', tab1_layout)],
            [sg.Tab('Tempo', tab2_layout)],
            [sg.Tab('Correspondência', tab3_layout)],
            [sg.Tab('Ocupação', tab4_layout)],
            [sg.Tab('Relatório', tab5_layout)]  
        ], expand_x=True, expand_y=True)],
        [
            sg.Button("Exportar Relatório", size=(18,1), button_color=('white', escuro)),
            sg.Button("Fechar", size=(12,1), button_color=('white', escuro))
        ]
    ]
    
    window = sg.Window(f"Desempenho Médico - {titulo_simulacao}", 
                      layout, 
                      modal=True, 
                      finalize=True, 
                      size=(800, 650), 
                      resizable=True, 
                      keep_on_top=True)

    figsize_large = (8, 5)  
    dpi_value = 100
    

    try:
        fig1 = Figure(figsize=figsize_large, dpi=dpi_value)
        ax1 = fig1.add_subplot(111)
        
        indices = range(len(ids_medicos))
        if len(indices) > 0:
            bars1 = ax1.bar(indices, eficiencias, color=escuro, edgecolor='black', width=0.6, alpha=0.8)
            
            ax1.set_xlabel('Médico (ID)', fontsize=11)
            ax1.set_ylabel('Pacientes/Hora', fontsize=11)
            ax1.set_title('Eficiência dos Médicos', fontsize=13, fontweight='bold')
            ax1.set_xticks(indices)
            ax1.set_xticklabels(ids_medicos, rotation=45, ha='right', fontsize=9)
            ax1.grid(True, axis='y', alpha=0.3)
            
            if eficiencias:
                media_eficiencia = np.mean(eficiencias)
                ax1.axhline(y=media_eficiencia, color='red', linestyle='-', 
                           linewidth=1.5, alpha=0.7, label=f'Média: {media_eficiencia:.1f}')
                ax1.legend(loc='upper right')
        else:
            ax1.text(0.5, 0.5, 'Sem dados de eficiência', 
                    fontsize=12, ha='center', va='center', transform=ax1.transAxes)
            ax1.set_title('Eficiência dos Médicos', fontsize=13, fontweight='bold')
        
        fig1.tight_layout(pad=2.0)
        
        canvas1 = fig_tk.FigureCanvasTkAgg(fig1, window["-CANVAS_EFICIENCIA-"].TKCanvas)
        canvas1.draw()
        canvas1.get_tk_widget().pack(side='top', fill='both', expand=True)
    except Exception as e:
        print(f"Erro no gráfico de eficiência: {e}")
    
    try:
        fig2 = Figure(figsize=figsize_large, dpi=dpi_value)
        ax2 = fig2.add_subplot(111)
        
        if len(indices) > 0:
            bars2 = ax2.bar(indices, tempos_medios, color='#ff9800', edgecolor='black', width=0.6, alpha=0.8)
            
            ax2.set_xlabel('Médico (ID)', fontsize=11)
            ax2.set_ylabel('Minutos', fontsize=11)
            ax2.set_title('Tempo Médio de Consulta', fontsize=13, fontweight='bold')
            ax2.set_xticks(indices)
            ax2.set_xticklabels(ids_medicos, rotation=45, ha='right', fontsize=9)
            ax2.grid(True, axis='y', alpha=0.3)
            
            
            ax2.axhline(y=15, color='green', linestyle='--', linewidth=1.5, alpha=0.7, label='Meta: 15 min')
            
            if tempos_medios:
                media_tempo = np.mean(tempos_medios)
                ax2.axhline(y=media_tempo, color='blue', linestyle='-', linewidth=1.5, alpha=0.7, 
                           label=f'Média: {media_tempo:.1f} min')
                ax2.legend(loc='upper right')
        else:
            ax2.text(0.5, 0.5, 'Sem dados de tempo', 
                    fontsize=12, ha='center', va='center', transform=ax2.transAxes)
            ax2.set_title('Tempo Médio de Consulta', fontsize=13, fontweight='bold')
        
        fig2.tight_layout(pad=2.0)
        
        canvas2 = fig_tk.FigureCanvasTkAgg(fig2, window["-CANVAS_TEMPO-"].TKCanvas)
        canvas2.draw()
        canvas2.get_tk_widget().pack(side='top', fill='both', expand=True)
    except Exception as e:
        print(f"Erro no gráfico de tempo: {e}")
    
    try:
        fig3 = Figure(figsize=figsize_large, dpi=dpi_value)
        ax3 = fig3.add_subplot(111)
        
        if len(indices) > 0:
            bars3 = ax3.bar(indices, taxas_corresp, color='#4caf50', edgecolor='black', width=0.6, alpha=0.8)
            
            ax3.set_xlabel('Médico (ID)', fontsize=11)
            ax3.set_ylabel('Percentagem (%)', fontsize=11)
            ax3.set_title('Taxa de Correspondência de Especialidade', fontsize=13, fontweight='bold')
            ax3.set_xticks(indices)
            ax3.set_xticklabels(ids_medicos, rotation=45, ha='right', fontsize=9)
            ax3.set_ylim(0, 100)
            ax3.grid(True, axis='y', alpha=0.3)
            
            ax3.axhline(y=70, color='orange', linestyle='--', linewidth=1.5, alpha=0.7, label='Meta: 70%')
            
            if taxas_corresp:
                media_corresp = np.mean(taxas_corresp)
                ax3.axhline(y=media_corresp, color='purple', linestyle='-', linewidth=1.5, alpha=0.7, 
                           label=f'Média: {media_corresp:.1f}%')
                ax3.legend(loc='upper right')
        else:
            ax3.text(0.5, 0.5, 'Sem dados de correspondência', 
                    fontsize=12, ha='center', va='center', transform=ax3.transAxes)
            ax3.set_title('Taxa de Correspondência de Especialidade', fontsize=13, fontweight='bold')
        
        fig3.tight_layout(pad=2.0)
        
        canvas3 = fig_tk.FigureCanvasTkAgg(fig3, window["-CANVAS_CORRESP-"].TKCanvas)
        canvas3.draw()
        canvas3.get_tk_widget().pack(side='top', fill='both', expand=True)
    except Exception as e:
        print(f"Erro no gráfico de correspondência: {e}")

    try:
        fig4 = Figure(figsize=figsize_large, dpi=dpi_value)
        ax4 = fig4.add_subplot(111)
        
        if len(indices) > 0:
            bars4 = ax4.bar(indices, taxas_ocup, color='#9c27b0', edgecolor='black', width=0.6, alpha=0.8)
            
            ax4.set_xlabel('Médico (ID)', fontsize=11)
            ax4.set_ylabel('Percentagem (%)', fontsize=11)
            ax4.set_title('Taxa de Ocupação dos Médicos', fontsize=13, fontweight='bold')
            ax4.set_xticks(indices)
            ax4.set_xticklabels(ids_medicos, rotation=45, ha='right', fontsize=9)
            ax4.set_ylim(0, 100)
            ax4.grid(True, axis='y', alpha=0.3)
 
            ax4.axhline(y=60, color='green', linestyle='--', linewidth=1.5, alpha=0.6, label='Ideal: 60-80%')
            ax4.axhline(y=80, color='orange', linestyle='--', linewidth=1.5, alpha=0.6)
            
            if taxas_ocup:
                media_ocup = np.mean(taxas_ocup)
                ax4.axhline(y=media_ocup, color='red', linestyle='-', linewidth=1.5, alpha=0.7, 
                           label=f'Média: {media_ocup:.1f}%')
                ax4.legend(loc='upper right')
        else:
            ax4.text(0.5, 0.5, 'Sem dados de ocupação', 
                    fontsize=12, ha='center', va='center', transform=ax4.transAxes)
            ax4.set_title('Taxa de Ocupação dos Médicos', fontsize=13, fontweight='bold')
        
        fig4.tight_layout(pad=2.0)
        
        canvas4 = fig_tk.FigureCanvasTkAgg(fig4, window["-CANVAS_OCUPACAO-"].TKCanvas)
        canvas4.draw()
        canvas4.get_tk_widget().pack(side='top', fill='both', expand=True)
    except Exception as e:
        print(f"Erro no gráfico de ocupação: {e}")
    
    continuar = True
    while continuar:
        event, values = window.read()
        
        if event == sg.WINDOW_CLOSED or event == "Fechar":
            continuar = False
        
        elif event == "Exportar Relatório":
            nome_arquivo = f"relatorio_desempenho_{titulo_simulacao.lower().replace(' ', '_').replace('/', '_').replace(':', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            arquivo_salvo = salvar_arquivo(relatorio_texto, nome_arquivo)
            if arquivo_salvo:
                sg.popup(f"Relatório exportado para:\n{arquivo_salvo}", title="Sucesso", keep_on_top=True, modal=True)
            else:
                sg.popup_error("Falha ao salvar o relatório.", title="Erro")
    
    window.close()

def abrir_simulacao():
    layout = criar_layout_principal()
    window = sg.Window("Sistema de Gestão de Clínica", layout, finalize=True, resizable=True, size=(1200,700), element_justification='center')
    window.move_to_center()
    config_atual = None
    continuar_principal = True
    while continuar_principal:
        timeout = 100 if estado_simulacao.get("simulacao_ativa", False) else None
        event, values = window.read(timeout=timeout)
        if event in (sg.WINDOW_CLOSED, 'Fechar Sistema', "-FECHAR-"):
            continuar_principal = False
        elif event == "-CONFIG-":
            config = janela_configuracao()
            if config:
                config_atual = config
                sg.popup("Configurações guardadas! Clique em 'Iniciar' para começar.", title="Sucesso")
        elif event == "-PLAY-":
            if not config_atual:
                config_atual = janela_configuracao()
            if config_atual:
                if config_atual["num_medicos"] <= 0:
                    sg.popup_error("Número de médicos deve ser maior que 0!")
                elif config_atual["tempo_simulacao"] <= 0:
                    sg.popup_error("Tempo de simulação deve ser maior que 0!")
                elif config_atual["lambda_chegada"] <= 0:
                    sg.popup_error("Taxa de chegada deve ser maior que 0!")
                elif config_atual["tempo_medio_consulta"] <= 0:
                    sg.popup_error("Tempo médio de consulta deve ser maior que 0!")
                else:
                    if inicializar_simulacao(config_atual):
                        window["-PLAY-"].update(disabled=True)
                        window["-PAUSE-"].update(disabled=False)
                        window["-STOP-"].update(disabled=False)
                        sg.popup("Simulação iniciada! Observe a fila em tempo real.", title="Iniciado", auto_close=True, auto_close_duration=2)
                    else:
                        sg.popup_error("Erro ao iniciar a simulação! Verifique os dados de entrada.")
            else:
                sg.popup_error("Configuração necessária para iniciar a simulação!")
        elif event == "-PAUSE-":
            estado_simulacao["simulacao_ativa"] = not estado_simulacao.get("simulacao_ativa", False)
            if estado_simulacao["simulacao_ativa"]:
                window["-PAUSE-"].update("Pausar")
            else:
                window["-PAUSE-"].update("Retomar")
        elif event == "-STOP-":
            estado_simulacao["simulacao_ativa"] = False
            apagar_interface_principal(window)
            sg.popup("Simulação parada!", title="Parado", auto_close=True, auto_close_duration=1)
        elif event == "-GRAFICOS-":
            gerar_graficos()
        elif event == "-COMPARAR-":
            comparar_simulacoes()

        elif event == "-DESEMPENHO_MEDICOS-":
            mostrar_desempenho_medicos()
        elif event == "-ANALISE_FILA_TAXA-":
            gerar_grafico_fila_vs_taxa()
        elif event == "-FILA_LISTA-":
            if values["-FILA_LISTA-"]:
                texto_selecionado = values["-FILA_LISTA-"][0]
                if "|" in texto_selecionado:
                    pos_str = texto_selecionado.split("|")[0].strip()
                    if pos_str.isdigit():
                        idx = int(pos_str) - 1
                        if 0 <= idx < tamanho_fila(estado_simulacao["fila_espera"]):
                            estado_simulacao["paciente_selecionado"] = estado_simulacao["fila_espera"][idx]["id"]
                            atualizar_detalhes_paciente(window)
        elif event == "-REMOVER_FILA-":
            if values["-FILA_LISTA-"]:
                texto_selecionado = values["-FILA_LISTA-"][0]
                if "|" in texto_selecionado:
                    pos_str = texto_selecionado.split("|")[0].strip()
                    if pos_str.isdigit():
                        idx = int(pos_str) - 1
                        if 0 <= idx < tamanho_fila(estado_simulacao["fila_espera"]):
                            fila_temp = []
                            removido = None
                            i = 0
                            while not queue_empty(estado_simulacao["fila_espera"]):
                                paciente, estado_simulacao["fila_espera"] = remover_da_fila(estado_simulacao["fila_espera"])
                                if i == idx:
                                    removido = paciente
                                else:
                                    fila_temp = adicionar_a_fila(fila_temp, paciente)
                                i = i + 1
                            while not queue_empty(fila_temp):
                                paciente, fila_temp = remover_da_fila(fila_temp)
                                estado_simulacao["fila_espera"] = adicionar_a_fila(estado_simulacao["fila_espera"], paciente)
                            if removido:
                                sg.popup(f"Paciente {removido.get('nome')} removido da fila.", title="Removido")
                                if estado_simulacao.get("paciente_selecionado") == removido["id"]:
                                    estado_simulacao["paciente_selecionado"] = None
                                stats = obter_estatisticas()
                                atualizar_interface(window, stats)
            else:
                sg.popup("Selecione um paciente na fila para remover.", title="Aviso")
        elif event == "-LISTA_ATENDIMENTOS-":
            if estado_simulacao["historico_atendimentos"] or estado_simulacao["dados_historicos"]:
                mostrar_lista_atendimentos(estado_simulacao, "Histórico Global de Atendimento")
            else:
                sg.popup_error("Nenhum atendimento registado ainda. Execute a simulação primeiro.", title="Erro")
        elif event == "-ESTAT_ESPECIALIDADES-":
            if estado_simulacao["pessoas_dados"]:
                mostrar_estatisticas_especialidades()
            else:
                sg.popup_error("Nenhum dado de pacientes carregado. Configure e inicie a simulação primeiro.", title="Erro")
        if estado_simulacao.get("simulacao_ativa", False):
            velocidade = estado_simulacao.get("velocidade", 1.0)
            incremento = 0.1 * velocidade
            atualizar_simulacao(incremento)
            stats = obter_estatisticas()
            atualizar_interface(window, stats)
            if not estado_simulacao["simulacao_ativa"]:
                apagar_interface_principal(window)
                sg.popup("Simulação concluída!", title="Concluído", auto_close=True, auto_close_duration=2)
    window.close()


if __name__ == "__main__":
    abrir_simulacao() 



