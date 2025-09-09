# utils_admin.py
# Módulo Central de Utilitários e Administração
#
# Propósito: Este arquivo serve como o "cérebro" para todas as operações de gerenciamento
# de usuários e manipulação de dados do projeto. Centralizar essas funções aqui permite
# que outros scripts (app.py, document_viewer.py) as utilizem sem duplicar código,
# tornando o projeto mais limpo, organizado e fácil de manter.

# --- Importação das Bibliotecas Necessárias ---
import os                   # Para interagir com o sistema operacional (criar pastas, verificar caminhos).
import json                 # Para manipular arquivos no formato JSON (ler e escrever dados).
import shutil               # Usado para operações de alto nível em arquivos, como remover uma pasta inteira.
import tkinter as tk        # A biblioteca padrão do Python para criar interfaces gráficas.
from tkinter import messagebox, simpledialog  # Módulos específicos do tkinter para caixas de diálogo simples.
import uuid                 # Para gerar identificadores únicos universais (usados para as pastas de fotos).
import cv2                  # A biblioteca OpenCV, essencial para a câmera e processamento de imagem.
import sys                  # Para interações com o sistema (atualmente não usado, mas bom para futuras expansões).
import numpy as np          # Biblioteca para computação numérica, usada aqui para criar o efeito de "flash".

# --- Configuração de Caminhos Globais ---
# Define o diretório base do projeto de forma dinâmica. Isso garante que o programa
# encontre seus arquivos, não importa de onde ele seja executado.
base_dir = os.path.dirname(os.path.abspath(__file__))

# Define os caminhos para as pastas importantes do projeto.
diretorio_de_faces = os.path.join(base_dir, 'faces')
diretorio_modelo = os.path.join(base_dir, 'Modelo_Treinamento')
diretorio_usuarios = os.path.join(base_dir, 'Usuarios_Cadastrados')

# Define os caminhos completos para os arquivos que o programa usará.
# 'os.path.join' constrói os caminhos de forma segura para qualquer sistema operacional.
caminho_modelo_salvo = os.path.join(diretorio_modelo, 'modelo_lbph.yml')
caminho_mapa_ids = os.path.join(diretorio_modelo, 'mapeamento_ids.json')
caminho_json_validacao = os.path.join(diretorio_usuarios, 'validation.json')
caminho_json_dados_usuario = os.path.join(diretorio_usuarios, 'userData.json')
face_cascade_path = os.path.join(base_dir, 'haarcascade_frontalface_default.xml')


# --- Funções de Otimização e Dados ---

def invalidar_modelo_treinado():
    """
    Exclui os arquivos do modelo treinado para forçar um novo treinamento.
    Esta função é a chave para a otimização: ao modificar os dados de treinamento (adicionar/excluir
    usuários ou fotos), chamamos esta função para garantir que o modelo antigo seja descartado.
    """
    if os.path.exists(caminho_modelo_salvo):
        os.remove(caminho_modelo_salvo)
        print("Modelo de reconhecimento invalidado (será retreinado na próxima execução).")
    if os.path.exists(caminho_mapa_ids):
        os.remove(caminho_mapa_ids)

def carregar_dados_json(caminho_arquivo):
    """
    Função segura para carregar dados de um arquivo JSON.
    Retorna o dicionário de dados ou um dicionário vazio em caso de erro ou se o arquivo não existir.
    """
    if not os.path.exists(caminho_arquivo):
        return {}
    try:
        # 'with open(...)' garante que o arquivo seja fechado corretamente após a leitura.
        # 'encoding="utf-8"' é crucial para ler caracteres com acentuação.
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        messagebox.showerror("Erro de Leitura", f"Erro ao carregar o arquivo JSON {caminho_arquivo}: {e}")
        return {}

def salvar_dados_json(caminho_arquivo, dados):
    """
    Função segura para salvar dados em um arquivo JSON, garantindo que o diretório de destino exista.
    """
    try:
        # Garante que o diretório ('Usuarios_Cadastrados') exista. Se não, ele é criado.
        # 'exist_ok=True' evita que um erro seja lançado se a pasta já existir.
        os.makedirs(diretorio_usuarios, exist_ok=True)

        # O modo 'w' (write) abre o arquivo para escrita, substituindo o conteúdo antigo.
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            # 'json.dump' escreve o dicionário 'dados' no arquivo 'f'.
            # 'indent=2' formata o arquivo para ser facilmente lido por humanos.
            # 'ensure_ascii=False' permite a escrita de caracteres acentuados.
            json.dump(dados, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        messagebox.showerror("Erro de Escrita", f"Erro ao salvar os dados no arquivo JSON {caminho_arquivo}: {e}")
        return False

# --- Funções de Gerenciamento de Usuários e Captura de Imagem ---

def tirar_e_salvar_fotos(id_unico, cpf_usuario="novo_usuario"):
    """
    Abre a webcam, captura um número definido de fotos com feedback visual e salva na pasta do usuário.
    """
    # Carrega o classificador Haar Cascade, o modelo pré-treinado do OpenCV para detectar faces.
    classificador_de_faces = cv2.CascadeClassifier(face_cascade_path)

    caminho_pasta_pessoa = os.path.join(diretorio_de_faces, id_unico)
    if not os.path.exists(caminho_pasta_pessoa):
        os.makedirs(caminho_pasta_pessoa)

    # Inicializa a webcam. O '0' geralmente se refere à câmera padrão do dispositivo.
    captura = cv2.VideoCapture(0)
    if not captura.isOpened():
        messagebox.showerror("Erro", "Não foi possível acessar a webcam.")
        return 0

    fotos_tiradas, max_fotos = 0, 10
    nome_janela = f"Captura de Fotos para {cpf_usuario}"

    while fotos_tiradas < max_fotos:
        ret, frame = captura.read()
        if not ret: break

        # --- Início da Melhoria de UX ---
        # 1. Adiciona um fundo semi-transparente para destacar o texto de instruções.
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (frame.shape[1], 50), (0, 0, 0), -1)
        alpha = 0.6
        frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)

        texto_instrucao = f"Pressione 'S' para foto ({fotos_tiradas}/{max_fotos}). 'Q' para sair."
        cv2.putText(frame, texto_instrucao, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # 2. Desenha um retângulo guia para o rosto no centro da tela.
        h, w, _ = frame.shape
        guia_x, guia_y, guia_w, guia_h = int(w/2 - 125), int(h/2 - 150), 250, 300
        cv2.rectangle(frame, (guia_x, guia_y), (guia_x + guia_w, guia_y + guia_h), (255, 255, 255), 2)
        cv2.putText(frame, "Posicione o rosto aqui", (guia_x, guia_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        # --- Fim da Melhoria de UX ---

        cv2.imshow(nome_janela, frame)

        tecla = cv2.waitKey(1) & 0xFF
        if tecla == ord('s'):
            # Detecta rostos no frame atual.
            rostos_detectados = classificador_de_faces.detectMultiScale(frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
            if len(rostos_detectados) > 0:
                nome_arquivo = f"{id_unico}_{uuid.uuid4().hex[:8]}.jpg"
                caminho_foto = os.path.join(caminho_pasta_pessoa, nome_arquivo)
                cv2.imwrite(caminho_foto, frame)
                fotos_tiradas += 1
                print(f"Foto {fotos_tiradas} salva em: {caminho_foto}")

                # --- Início do Feedback Visual de Captura ---
                # 3. Cria uma imagem branca (efeito de flash).
                flash = np.full(frame.shape, 255, dtype=np.uint8)
                cv2.imshow(nome_janela, flash)
                cv2.waitKey(100) # O flash dura 100 milissegundos

                # 4. Exibe o frame com uma mensagem de confirmação.
                texto_confirmacao = "FOTO CAPTURADA!"
                text_size = cv2.getTextSize(texto_confirmacao, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
                text_x = (frame.shape[1] - text_size[0]) // 2
                text_y = (frame.shape[0] + text_size[1]) // 2
                cv2.putText(frame, texto_confirmacao, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.imshow(nome_janela, frame)
                cv2.waitKey(400) # A mensagem dura 400 milissegundos
                # --- Fim do Feedback Visual ---

            else:
                messagebox.showwarning("Aviso", "Nenhum rosto detectado. Posicione-se melhor.")
        if tecla == ord('q'): break

    captura.release()
    cv2.destroyAllWindows()
    return fotos_tiradas

# As funções abaixo orquestram o processo de gerenciamento, chamando as funções de base.
# Seus comentários são mais simples pois sua lógica é direta.

def criar_novo_usuario_via_gui():
    """Interface para criar um novo usuário."""
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
    """Interface para adicionar mais fotos a um usuário existente."""
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
    """Interface para excluir um usuário do sistema."""
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