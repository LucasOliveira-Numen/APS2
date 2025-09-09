# utils_admin.py
# (versão atualizada para salvar o modelo em uma pasta dedicada)

import os
import json
import shutil
import tkinter as tk
from tkinter import messagebox, simpledialog
import uuid
import cv2
import sys

# --- Configuração de Caminhos Globais ---
base_dir = os.path.dirname(os.path.abspath(__file__))
diretorio_de_faces = os.path.join(base_dir, 'faces')
caminho_json_validacao = os.path.join(base_dir, 'validation.json')
caminho_json_dados_usuario = os.path.join(base_dir, 'userData.json')
face_cascade_path = os.path.join(base_dir, 'haarcascade_frontalface_default.xml')

# --- CAMINHOS ATUALIZADOS PARA O MODELO SALVO ---
# Criamos uma variável para o novo diretório.
diretorio_modelo = os.path.join(base_dir, 'Modelo_Treinamento')
# Apontamos os caminhos dos arquivos para dentro do novo diretório.
caminho_modelo_salvo = os.path.join(diretorio_modelo, 'modelo_lbph.yml')
caminho_mapa_ids = os.path.join(diretorio_modelo, 'mapeamento_ids.json')

# (O restante do arquivo permanece exatamente o mesmo)

def invalidar_modelo_treinado():
    """
    Exclui os arquivos do modelo treinado para forçar um novo treinamento.
    """
    if os.path.exists(caminho_modelo_salvo):
        os.remove(caminho_modelo_salvo)
        print("Modelo de reconhecimento invalidado (será retreinado na próxima execução).")
    if os.path.exists(caminho_mapa_ids):
        os.remove(caminho_mapa_ids)

def carregar_dados_json(caminho_arquivo):
    if not os.path.exists(caminho_arquivo): return {}
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as f: return json.load(f)
    except Exception as e:
        messagebox.showerror("Erro de Leitura", f"Erro ao carregar o arquivo JSON {caminho_arquivo}: {e}")
        return {}

def salvar_dados_json(caminho_arquivo, dados):
    try:
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        messagebox.showerror("Erro de Escrita", f"Erro ao salvar os dados no arquivo JSON {caminho_arquivo}: {e}")
        return False

def tirar_e_salvar_fotos(id_unico, cpf_usuario="novo_usuario"):
    if not os.path.exists(face_cascade_path):
        messagebox.showerror("Erro", f"O arquivo '{os.path.basename(face_cascade_path)}' não foi encontrado.")
        return 0
    classificador_de_faces = cv2.CascadeClassifier(face_cascade_path)
    caminho_pasta_pessoa = os.path.join(diretorio_de_faces, id_unico)
    if not os.path.exists(caminho_pasta_pessoa): os.makedirs(caminho_pasta_pessoa)
    captura = cv2.VideoCapture(0)
    if not captura.isOpened():
        messagebox.showerror("Erro", "Não foi possível acessar a webcam.")
        return 0
    fotos_tiradas = 0
    max_fotos = 10
    while fotos_tiradas < max_fotos:
        ret, frame = captura.read()
        if not ret: break
        texto_instrucao = f"Pressione 'S' para foto ({fotos_tiradas}/{max_fotos}). 'Q' para sair."
        cv2.putText(frame, texto_instrucao, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.imshow(f"Captura de Fotos para {cpf_usuario}", frame)
        tecla = cv2.waitKey(1) & 0xFF
        if tecla == ord('s'):
            rostos_detectados = classificador_de_faces.detectMultiScale(frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
            if len(rostos_detectados) > 0:
                nome_arquivo = f"{id_unico}_{uuid.uuid4().hex[:8]}.jpg"
                caminho_foto = os.path.join(caminho_pasta_pessoa, nome_arquivo)
                cv2.imwrite(caminho_foto, frame)
                fotos_tiradas += 1
                print(f"Foto {fotos_tiradas} salva em: {caminho_foto}")
            else: messagebox.showwarning("Aviso", "Nenhum rosto detectado. Posicione-se melhor e tente novamente.")
        if tecla == ord('q'): break
    captura.release()
    cv2.destroyAllWindows()
    return fotos_tiradas

def criar_novo_usuario_via_gui():
    nome_completo = simpledialog.askstring("Novo Usuário", "Digite o Nome Completo:")
    if not nome_completo: return
    cpf = simpledialog.askstring("Novo Usuário", "Digite o CPF (apenas números):")
    if not cpf: return
    nivel_digitado = simpledialog.askstring("Novo Usuário", "Digite o Nível (1, 2 ou 3):")
    if not nivel_digitado: return
    cpf_limpo = cpf.replace(".", "").replace("-", "")
    if len(cpf_limpo) != 11 or not cpf_limpo.isdigit():
        messagebox.showwarning("Aviso", "O CPF deve conter exatamente 11 dígitos numéricos.")
        return
    try:
        nivel_int = int(nivel_digitado)
        if nivel_int not in [1, 2, 3]: raise ValueError
        nivel_formatado = f"Nivel {nivel_int}"
    except ValueError:
        messagebox.showwarning("Aviso", "O nível deve ser um número válido (1, 2 ou 3).")
        return
    dados_validacao, dados_usuario = carregar_dados_json(caminho_json_validacao), carregar_dados_json(caminho_json_dados_usuario)
    if cpf_limpo in dados_usuario:
        messagebox.showerror("Erro", f"O CPF '{cpf_limpo}' já está cadastrado.")
        return
    id_unico = str(uuid.uuid4())
    fotos_tiradas = tirar_e_salvar_fotos(id_unico, cpf_limpo)
    if fotos_tiradas == 0:
        pasta_criada = os.path.join(diretorio_de_faces, id_unico)
        if os.path.exists(pasta_criada): shutil.rmtree(pasta_criada)
        messagebox.showwarning("Aviso", "Nenhuma foto tirada. O cadastro foi cancelado.")
        return
    if nivel_formatado not in dados_validacao: dados_validacao[nivel_formatado] = {"pessoas": []}
    dados_validacao[nivel_formatado]["pessoas"].append(cpf_limpo)
    dados_usuario[cpf_limpo] = {"nome": nome_completo, "id": id_unico}
    if salvar_dados_json(caminho_json_validacao, dados_validacao) and salvar_dados_json(caminho_json_dados_usuario, dados_usuario):
        messagebox.showinfo("Sucesso", f"Usuário '{nome_completo}' cadastrado com sucesso.")
        invalidar_modelo_treinado()

def adicionar_mais_fotos():
    cpf = simpledialog.askstring("Adicionar Fotos", "Digite o CPF do usuário:")
    if not cpf: return
    dados_usuario = carregar_dados_json(caminho_json_dados_usuario)
    if cpf not in dados_usuario:
        messagebox.showerror("Erro", "CPF não encontrado.")
        return
    id_unico = dados_usuario[cpf]['id']
    fotos_adicionadas = tirar_e_salvar_fotos(id_unico, cpf)
    if fotos_adicionadas > 0:
        messagebox.showinfo("Sucesso", f"{fotos_adicionadas} fotos adicionadas.")
        invalidar_modelo_treinado()
    else: messagebox.showinfo("Cancelado", "Nenhuma foto nova foi adicionada.")

def excluir_usuario():
    cpf = simpledialog.askstring("Excluir Usuário", "Digite o CPF do usuário que deseja excluir:")
    if not cpf: return
    dados_usuario, dados_validacao = carregar_dados_json(caminho_json_dados_usuario), carregar_dados_json(caminho_json_validacao)
    if cpf not in dados_usuario:
        messagebox.showerror("Erro", "CPF não encontrado.")
        return
    nome_usuario = dados_usuario[cpf]['nome']
    resposta = messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja excluir '{nome_usuario}' (CPF: {cpf})?\nEsta ação é irreversível.")
    if not resposta: return
    try:
        id_unico = dados_usuario[cpf]['id']
        caminho_pasta_pessoa = os.path.join(diretorio_de_faces, id_unico)
        if os.path.exists(caminho_pasta_pessoa): shutil.rmtree(caminho_pasta_pessoa)
        for nivel in dados_validacao:
            if cpf in dados_validacao[nivel].get('pessoas', []):
                dados_validacao[nivel]['pessoas'].remove(cpf)
                break
        del dados_usuario[cpf]
        salvar_dados_json(caminho_json_validacao, dados_validacao)
        salvar_dados_json(caminho_json_dados_usuario, dados_usuario)
        messagebox.showinfo("Sucesso", f"Usuário com CPF '{cpf}' foi excluído com sucesso.")
        invalidar_modelo_treinado()
    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro ao excluir o usuário: {e}")