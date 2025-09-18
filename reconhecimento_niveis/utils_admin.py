# Módulo Central de Utilitários e Administração do Sistema de Reconhecimento Facial
#
# Este módulo centraliza todas as operações de gerenciamento de usuários, manipulação
# de dados e processamento de imagens do sistema. Funciona como uma biblioteca de
# funções utilitárias que são utilizadas pelos demais módulos do projeto, garantindo
# consistência e evitando duplicação de código.
#
# Funcionalidades principais:
# - Gerenciamento de dados JSON (usuários e validação)
# - Captura e processamento de imagens faciais
# - Data augmentation para treinamento do modelo
# - Validação de qualidade de imagens
# - Interface administrativa para gerenciamento de usuários

# --- Importação das Bibliotecas ---
import os                   # Módulo para operações do sistema de arquivos e diretórios
import json                 # Módulo para serialização e deserialização de dados JSON
import shutil               # Módulo para operações avançadas de arquivos e diretórios
import tkinter as tk        # Biblioteca padrão para criação de interfaces gráficas
from tkinter import messagebox, simpledialog, ttk  # Componentes específicos do tkinter para diálogos
import uuid                 # Módulo para geração de identificadores únicos universais
import cv2                  # OpenCV para processamento de imagens e visão computacional
import sys                  # Módulo para interação com o interpretador Python
import numpy as np          # Biblioteca para computação numérica e manipulação de arrays
import random               # Módulo para geração de números aleatórios

# --- Configuração de Caminhos do Sistema ---
# Define o diretório base do projeto de forma dinâmica para garantir portabilidade
base_dir = os.path.dirname(os.path.abspath(__file__))

# Definição dos diretórios principais do sistema
diretorio_de_faces = os.path.join(base_dir, 'faces')                    # Pasta contendo as imagens de treinamento
diretorio_modelo = os.path.join(base_dir, 'Modelo_Treinamento')         # Pasta para armazenar o modelo treinado
diretorio_usuarios = os.path.join(base_dir, 'Usuarios_Cadastrados')     # Pasta com dados dos usuários

# Caminhos específicos para arquivos de dados e configuração
caminho_modelo_salvo = os.path.join(diretorio_modelo, 'modelo_lbph.yml')
caminho_mapa_ids = os.path.join(diretorio_modelo, 'mapeamento_ids.json')
caminho_json_validacao = os.path.join(diretorio_usuarios, 'validation.json')
caminho_json_dados_usuario = os.path.join(diretorio_usuarios, 'userData.json')
face_cascade_path = os.path.join(base_dir, 'haarcascade_frontalface_default.xml')


# --- Funções de Interface Melhorada ---

def criar_dialogo_personalizado(titulo, mensagem, tipo="info"):
    """
    Cria uma caixa de diálogo personalizada com melhor aparência.
    """
    root = tk.Tk()
    root.withdraw()

    # Configurar cores baseadas no tipo
    cores = {
        "info": ("#3498db", "#2c3e50"),
        "success": ("#27ae60", "#2c3e50"),
        "warning": ("#f39c12", "#2c3e50"),
        "error": ("#e74c3c", "#2c3e50")
    }

    cor_bg, cor_texto = cores.get(tipo, cores["info"])

    # Criar janela personalizada
    dialog = tk.Toplevel(root)
    dialog.title(titulo)
    dialog.geometry("400x200")
    dialog.configure(bg='#ecf0f1')
    dialog.resizable(False, False)

    # Centralizar na tela
    dialog.transient(root)
    # dialog.grab_set()  # Removido para evitar conflitos

    x = (dialog.winfo_screenwidth() // 2) - (400 // 2)
    y = (dialog.winfo_screenheight() // 2) - (200 // 2)
    dialog.geometry(f"400x200+{x}+{y}")

    # Frame principal
    main_frame = tk.Frame(dialog, bg='#ecf0f1', padx=20, pady=20)
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Ícone baseado no tipo
    icones = {
        "info": "ℹ️",
        "success": "✅",
        "warning": "⚠️",
        "error": "❌"
    }

    # Título com ícone
    titulo_frame = tk.Frame(main_frame, bg=cor_bg, height=50)
    titulo_frame.pack(fill=tk.X, pady=(0, 15))
    titulo_frame.pack_propagate(False)

    titulo_label = tk.Label(titulo_frame, text=f"{icones.get(tipo, 'ℹ️')} {titulo}",
                           font=('Segoe UI', 14, 'bold'), fg='white', bg=cor_bg)
    titulo_label.pack(expand=True)

    # Mensagem
    msg_label = tk.Label(main_frame, text=mensagem, font=('Segoe UI', 11),
                        fg=cor_texto, bg='#ecf0f1', wraplength=350, justify='center')
    msg_label.pack(expand=True, pady=10)

    # Botão OK
    btn_ok = tk.Button(main_frame, text="OK", command=dialog.destroy,
                      font=('Segoe UI', 10, 'bold'), bg=cor_bg, fg='white',
                      relief='flat', bd=0, padx=20, pady=8,
                      activebackground=cor_bg, activeforeground='white',
                      cursor='hand2')
    btn_ok.pack(pady=10)

    # Focar no botão OK
    btn_ok.focus_set()

    # Bind Enter para fechar
    dialog.bind('<Return>', lambda e: dialog.destroy())

    dialog.wait_window()
    root.destroy()

def criar_input_dialogo(titulo, prompt, tipo_input="string"):
    """
    Cria uma caixa de diálogo personalizada para entrada de dados.
    """
    root = tk.Tk()
    root.withdraw()

    # Criar janela personalizada
    dialog = tk.Toplevel(root)
    dialog.title(titulo)
    dialog.geometry("450x250")
    dialog.configure(bg='#ecf0f1')
    dialog.resizable(False, False)

    # Centralizar na tela
    dialog.transient(root)
    # dialog.grab_set()  # Removido para evitar conflitos

    x = (dialog.winfo_screenwidth() // 2) - (450 // 2)
    y = (dialog.winfo_screenheight() // 2) - (250 // 2)
    dialog.geometry(f"450x250+{x}+{y}")

    # Frame principal
    main_frame = tk.Frame(dialog, bg='#ecf0f1', padx=20, pady=20)
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Título
    titulo_frame = tk.Frame(main_frame, bg='#3498db', height=50)
    titulo_frame.pack(fill=tk.X, pady=(0, 15))
    titulo_frame.pack_propagate(False)

    titulo_label = tk.Label(titulo_frame, text=f"📝 {titulo}",
                           font=('Segoe UI', 14, 'bold'), fg='white', bg='#3498db')
    titulo_label.pack(expand=True)

    # Prompt
    prompt_label = tk.Label(main_frame, text=prompt, font=('Segoe UI', 11),
                           fg='#2c3e50', bg='#ecf0f1', wraplength=400, justify='center')
    prompt_label.pack(pady=(0, 15))

    # Campo de entrada
    entry_frame = tk.Frame(main_frame, bg='white', relief='sunken', bd=2)
    entry_frame.pack(fill=tk.X, pady=(0, 15))

    entry_var = tk.StringVar()
    entry = tk.Entry(entry_frame, textvariable=entry_var, font=('Segoe UI', 11),
                    relief='flat', bd=0, bg='white', fg='#2c3e50')
    entry.pack(fill=tk.X, padx=10, pady=10)

    # Botões
    buttons_frame = tk.Frame(main_frame, bg='#ecf0f1')
    buttons_frame.pack(fill=tk.X)

    resultado = [None]  # Lista para capturar o resultado

    def confirmar():
        resultado[0] = entry_var.get()
        dialog.destroy()

    def cancelar():
        resultado[0] = None
        dialog.destroy()

    btn_ok = tk.Button(buttons_frame, text="✅ Confirmar", command=confirmar,
                      font=('Segoe UI', 10, 'bold'), bg='#27ae60', fg='white',
                      relief='flat', bd=0, padx=15, pady=8,
                      activebackground='#229954', activeforeground='white',
                      cursor='hand2')
    btn_ok.pack(side=tk.LEFT, expand=True, padx=(0, 5))

    btn_cancel = tk.Button(buttons_frame, text="❌ Cancelar", command=cancelar,
                          font=('Segoe UI', 10, 'bold'), bg='#95a5a6', fg='white',
                          relief='flat', bd=0, padx=15, pady=8,
                          activebackground='#7f8c8d', activeforeground='white',
                          cursor='hand2')
    btn_cancel.pack(side=tk.LEFT, expand=True, padx=(5, 0))

    # Focar no campo de entrada
    entry.focus_set()

    # Bind Enter para confirmar
    dialog.bind('<Return>', lambda e: confirmar())
    dialog.bind('<Escape>', lambda e: cancelar())

    dialog.wait_window()
    root.destroy()

    return resultado[0]

def criar_dialogo_confirmacao(titulo, mensagem):
    """
    Cria uma caixa de diálogo de confirmação personalizada.
    """
    root = tk.Tk()
    root.withdraw()

    # Criar janela personalizada
    dialog = tk.Toplevel(root)
    dialog.title(titulo)
    dialog.geometry("450x250")
    dialog.configure(bg='#ecf0f1')
    dialog.resizable(False, False)

    # Centralizar na tela
    dialog.transient(root)
    # dialog.grab_set()  # Removido para evitar conflitos

    x = (dialog.winfo_screenwidth() // 2) - (450 // 2)
    y = (dialog.winfo_screenheight() // 2) - (250 // 2)
    dialog.geometry(f"450x250+{x}+{y}")

    # Frame principal
    main_frame = tk.Frame(dialog, bg='#ecf0f1', padx=20, pady=20)
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Título
    titulo_frame = tk.Frame(main_frame, bg='#f39c12', height=50)
    titulo_frame.pack(fill=tk.X, pady=(0, 15))
    titulo_frame.pack_propagate(False)

    titulo_label = tk.Label(titulo_frame, text=f"⚠️ {titulo}",
                           font=('Segoe UI', 14, 'bold'), fg='white', bg='#f39c12')
    titulo_label.pack(expand=True)

    # Mensagem
    msg_label = tk.Label(main_frame, text=mensagem, font=('Segoe UI', 11),
                        fg='#2c3e50', bg='#ecf0f1', wraplength=400, justify='center')
    msg_label.pack(expand=True, pady=10)

    # Botões
    buttons_frame = tk.Frame(main_frame, bg='#ecf0f1')
    buttons_frame.pack(fill=tk.X)

    resultado = [False]  # Lista para capturar o resultado

    def confirmar():
        resultado[0] = True
        dialog.destroy()

    def cancelar():
        resultado[0] = False
        dialog.destroy()

    btn_sim = tk.Button(buttons_frame, text="✅ Sim", command=confirmar,
                       font=('Segoe UI', 10, 'bold'), bg='#e74c3c', fg='white',
                       relief='flat', bd=0, padx=15, pady=8,
                       activebackground='#c0392b', activeforeground='white',
                       cursor='hand2')
    btn_sim.pack(side=tk.LEFT, expand=True, padx=(0, 5))

    btn_nao = tk.Button(buttons_frame, text="❌ Não", command=cancelar,
                        font=('Segoe UI', 10, 'bold'), bg='#95a5a6', fg='white',
                        relief='flat', bd=0, padx=15, pady=8,
                        activebackground='#7f8c8d', activeforeground='white',
                        cursor='hand2')
    btn_nao.pack(side=tk.LEFT, expand=True, padx=(5, 0))

    # Focar no botão "Não" por segurança
    btn_nao.focus_set()

    # Bind Enter para confirmar, Escape para cancelar
    dialog.bind('<Return>', lambda e: confirmar())
    dialog.bind('<Escape>', lambda e: cancelar())

    dialog.wait_window()
    root.destroy()

    return resultado[0]

# --- Módulo de Data Augmentation ---

def aplicar_data_augmentation(imagem):
    """
    Aplica transformações de data augmentation para aumentar a diversidade do dataset.

    Esta função cria variações controladas da imagem original através de ajustes
    de brilho e contraste, melhorando a robustez do modelo de reconhecimento
    facial sem comprometer significativamente a performance.

    Args:
        imagem (numpy.ndarray): Imagem em escala de cinza para processamento

    Returns:
        list: Lista contendo a imagem original e suas variações
    """
    imagens_aumentadas = [imagem]  # Inclui a imagem original

    # Criação de variações essenciais para treinamento robusto
    # Variação de brilho: aumento sutil para simular diferentes iluminações
    imagem_brilho = cv2.convertScaleAbs(imagem, alpha=1.05, beta=0)
    imagens_aumentadas.append(imagem_brilho)

    # Variação de contraste: redução sutil para simular condições de luz variáveis
    imagem_contraste = cv2.convertScaleAbs(imagem, alpha=0.98, beta=0)
    imagens_aumentadas.append(imagem_contraste)

    return imagens_aumentadas

def validar_qualidade_imagem(imagem):
    """
    Valida a qualidade de uma imagem para uso no treinamento do modelo.

    Esta função implementa verificações de qualidade baseadas em brilho,
    contraste e detecção de faces para garantir que apenas imagens
    adequadas sejam utilizadas no treinamento do modelo.

    Args:
        imagem (numpy.ndarray): Imagem em escala de cinza para validação

    Returns:
        bool: True se a imagem atende aos critérios de qualidade, False caso contrário
    """
    # Verifica se a imagem não está muito escura ou clara (otimizado)
    brilho_medio = np.mean(imagem)
    if brilho_medio < 40 or brilho_medio > 200:  # Ajustado para ser menos restritivo
        return False

    # Verifica contraste (diferença entre pixels claros e escuros) - otimizado
    contraste = np.std(imagem)
    if contraste < 15:  # Contraste muito baixo - menos restritivo
        return False

    # Verifica se há rosto detectado na imagem (otimizado)
    classificador_de_faces = cv2.CascadeClassifier(face_cascade_path)
    rostos = classificador_de_faces.detectMultiScale(imagem, 1.2, 3, minSize=(50, 50))  # Parâmetros mais rápidos
    if len(rostos) == 0:  # Nenhum rosto detectado
        return False

    return True

# --- Funções de Otimização e Dados ---

def invalidar_modelo_treinado():
    """
    Exclui os arquivos do modelo treinado para forçar um novo treinamento.
    Esta função é a chave para a otimização: ao modificar os dados de treinamento (adicionar/excluir
    usuários ou fotos), chama esta função para garantir que o modelo antigo seja descartado.
    """
    if os.path.exists(caminho_modelo_salvo):
        os.remove(caminho_modelo_salvo)
        print("Modelo de reconhecimento invalidado (será retreinado na próxima execução).")
    if os.path.exists(caminho_mapa_ids):
        os.remove(caminho_mapa_ids)

def carregar_dados_json(caminho_arquivo):
    """
    Carrega dados de um arquivo JSON de forma segura.

    Esta função implementa tratamento de erros robusto para carregamento
    de arquivos JSON, retornando um dicionário vazio em caso de falha
    ou arquivo inexistente.

    Args:
        caminho_arquivo (str): Caminho completo para o arquivo JSON

    Returns:
        dict: Dados carregados do arquivo ou dicionário vazio em caso de erro
    """
    if not os.path.exists(caminho_arquivo):
        return {}
    try:
        # Carregamento seguro com encoding UTF-8 para suporte a caracteres especiais
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        messagebox.showerror("Erro de Leitura", f"Erro ao carregar o arquivo JSON {caminho_arquivo}: {e}")
        return {}

def salvar_dados_json(caminho_arquivo, dados):
    """
    Salva dados em um arquivo JSON de forma segura.

    Esta função garante que o diretório de destino exista antes de salvar
    e implementa tratamento de erros robusto para operações de escrita.

    Args:
        caminho_arquivo (str): Caminho completo para o arquivo JSON de destino
        dados (dict): Dicionário contendo os dados a serem salvos

    Returns:
        bool: True se a operação foi bem-sucedida, False caso contrário
    """
    try:
        # Criação do diretório de destino se não existir
        os.makedirs(diretorio_usuarios, exist_ok=True)

        # Salvamento com formatação legível e suporte a caracteres especiais
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        messagebox.showerror("Erro de Escrita", f"Erro ao salvar os dados no arquivo JSON {caminho_arquivo}: {e}")
        return False

# --- Funções de Gerenciamento de Usuários e Captura de Imagem ---

def tirar_e_salvar_fotos(id_unico, cpf_usuario="novo_usuario"):
    """
    Captura fotos faciais através da webcam para treinamento do modelo.

    Esta função implementa uma interface interativa para captura de fotos
    faciais, incluindo feedback visual, validação de qualidade e orientações
    para o usuário. As fotos são salvas na pasta específica do usuário.

    Args:
        id_unico (str): Identificador único do usuário
        cpf_usuario (str): CPF do usuário para exibição (padrão: "novo_usuario")

    Returns:
        int: Número de fotos capturadas com sucesso
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
        cv2.rectangle(overlay, (0, 0), (frame.shape[1], 80), (0, 0, 0), -1)
        alpha = 0.7
        frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)

        # Título da janela
        cv2.putText(frame, "CAPTURA DE FOTOS", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

        # Instruções melhoradas
        texto_instrucao = f"Pressione 'S' para capturar ({fotos_tiradas}/{max_fotos}) | 'Q' para sair"
        cv2.putText(frame, texto_instrucao, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # Status das fotos
        status_cor = (0, 255, 0) if fotos_tiradas > 0 else (0, 255, 255)
        cv2.putText(frame, f"Fotos capturadas: {fotos_tiradas}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, status_cor, 1)

        # 2. Desenha um retângulo guia melhorado para o rosto no centro da tela.
        h, w, _ = frame.shape
        guia_x, guia_y, guia_w, guia_h = int(w/2 - 125), int(h/2 - 150), 250, 300

        # Retângulo principal
        cv2.rectangle(frame, (guia_x, guia_y), (guia_x + guia_w, guia_y + guia_h), (0, 255, 255), 3)

        # Cantos do retângulo
        corner_length = 30
        # Canto superior esquerdo
        cv2.line(frame, (guia_x, guia_y), (guia_x + corner_length, guia_y), (0, 255, 255), 5)
        cv2.line(frame, (guia_x, guia_y), (guia_x, guia_y + corner_length), (0, 255, 255), 5)
        # Canto superior direito
        cv2.line(frame, (guia_x + guia_w, guia_y), (guia_x + guia_w - corner_length, guia_y), (0, 255, 255), 5)
        cv2.line(frame, (guia_x + guia_w, guia_y), (guia_x + guia_w, guia_y + corner_length), (0, 255, 255), 5)
        # Canto inferior esquerdo
        cv2.line(frame, (guia_x, guia_y + guia_h), (guia_x + corner_length, guia_y + guia_h), (0, 255, 255), 5)
        cv2.line(frame, (guia_x, guia_y + guia_h), (guia_x, guia_y + guia_h - corner_length), (0, 255, 255), 5)
        # Canto inferior direito
        cv2.line(frame, (guia_x + guia_w, guia_y + guia_h), (guia_x + guia_w - corner_length, guia_y + guia_h), (0, 255, 255), 5)
        cv2.line(frame, (guia_x + guia_w, guia_y + guia_h), (guia_x + guia_w, guia_y + guia_h - corner_length), (0, 255, 255), 5)

        # Texto de instrução
        cv2.putText(frame, "Posicione o rosto aqui", (guia_x, guia_y - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # Barra de progresso visual
        progress_width = int((fotos_tiradas / max_fotos) * 200)
        cv2.rectangle(frame, (w - 220, h - 30), (w - 20, h - 10), (50, 50, 50), -1)
        cv2.rectangle(frame, (w - 220, h - 30), (w - 220 + progress_width, h - 10), (0, 255, 0), -1)
        cv2.putText(frame, f"Progresso: {fotos_tiradas}/{max_fotos}", (w - 220, h - 35), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        # --- Fim da Melhoria de UX ---

        cv2.imshow(nome_janela, frame)

        tecla = cv2.waitKey(1) & 0xFF
        if tecla == ord('s'):
            # Detecta rostos no frame atual com parâmetros mais restritivos.
            rostos_detectados = classificador_de_faces.detectMultiScale(frame, scaleFactor=1.1, minNeighbors=8, minSize=(100, 100))
            if len(rostos_detectados) > 0:
                # Pega o maior rosto detectado
                maior_rosto = max(rostos_detectados, key=lambda x: x[2] * x[3])
                x, y, w, h = maior_rosto

                # Extrai apenas o rosto
                rosto_extraido = frame[y:y+h, x:x+w]
                rosto_cinza = cv2.cvtColor(rosto_extraido, cv2.COLOR_BGR2GRAY)

                # Valida a qualidade da imagem
                if validar_qualidade_imagem(rosto_cinza):
                    nome_arquivo = f"{id_unico}_{uuid.uuid4().hex[:8]}.jpg"
                    caminho_foto = os.path.join(caminho_pasta_pessoa, nome_arquivo)
                    cv2.imwrite(caminho_foto, rosto_extraido)  # Salva apenas o rosto
                    fotos_tiradas += 1
                    print(f"Foto {fotos_tiradas} salva em: {caminho_foto}")
                else:
                    # Feedback visual para imagem de baixa qualidade
                    frame_qualidade = frame.copy()
                    overlay_amarelo = frame_qualidade.copy()
                    cv2.rectangle(overlay_amarelo, (0, 0), (frame_qualidade.shape[1], frame_qualidade.shape[0]), (0, 255, 255), -1)
                    alpha = 0.2
                    frame_qualidade = cv2.addWeighted(overlay_amarelo, alpha, frame_qualidade, 1 - alpha, 0)

                    texto_qualidade = "IMAGEM DE BAIXA QUALIDADE!"
                    text_size = cv2.getTextSize(texto_qualidade, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
                    text_x = (frame_qualidade.shape[1] - text_size[0]) // 2
                    text_y = (frame_qualidade.shape[0] + text_size[1]) // 2
                    cv2.putText(frame_qualidade, texto_qualidade, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

                    cv2.imshow(nome_janela, frame_qualidade)
                    cv2.waitKey(500)

                # --- Início do Feedback Visual de Captura ---
                # 3. Cria uma imagem branca (efeito de flash).
                flash = np.full(frame.shape, 255, dtype=np.uint8)
                cv2.imshow(nome_janela, flash)
                cv2.waitKey(150) # O flash dura 150 milissegundos

                # 4. Exibe o frame com uma mensagem de confirmação melhorada.
                frame_confirmacao = frame.copy()

                # Overlay verde para sucesso
                overlay_verde = frame_confirmacao.copy()
                cv2.rectangle(overlay_verde, (0, 0), (frame_confirmacao.shape[1], frame_confirmacao.shape[0]), (0, 255, 0), -1)
                alpha = 0.3
                frame_confirmacao = cv2.addWeighted(overlay_verde, alpha, frame_confirmacao, 1 - alpha, 0)

                # Texto de confirmação
                texto_confirmacao = "FOTO CAPTURADA!"
                text_size = cv2.getTextSize(texto_confirmacao, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 3)[0]
                text_x = (frame_confirmacao.shape[1] - text_size[0]) // 2
                text_y = (frame_confirmacao.shape[0] + text_size[1]) // 2

                # Sombra do texto
                cv2.putText(frame_confirmacao, texto_confirmacao, (text_x + 2, text_y + 2), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 3)
                # Texto principal
                cv2.putText(frame_confirmacao, texto_confirmacao, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)

                # Contador de fotos
                contador_texto = f"Foto {fotos_tiradas} de {max_fotos}"
                contador_size = cv2.getTextSize(contador_texto, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
                contador_x = (frame_confirmacao.shape[1] - contador_size[0]) // 2
                contador_y = text_y + 50
                cv2.putText(frame_confirmacao, contador_texto, (contador_x, contador_y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

                cv2.imshow(nome_janela, frame_confirmacao)
                cv2.waitKey(500) # A mensagem dura 500 milissegundos
                # --- Fim do Feedback Visual ---

            else:
                # Feedback visual para rosto não detectado
                frame_aviso = frame.copy()
                overlay_vermelho = frame_aviso.copy()
                cv2.rectangle(overlay_vermelho, (0, 0), (frame_aviso.shape[1], frame_aviso.shape[0]), (0, 0, 255), -1)
                alpha = 0.2
                frame_aviso = cv2.addWeighted(overlay_vermelho, alpha, frame_aviso, 1 - alpha, 0)

                texto_aviso = "ROSTO NAO DETECTADO!"
                text_size = cv2.getTextSize(texto_aviso, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
                text_x = (frame_aviso.shape[1] - text_size[0]) // 2
                text_y = (frame_aviso.shape[0] + text_size[1]) // 2
                cv2.putText(frame_aviso, texto_aviso, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

                cv2.imshow(nome_janela, frame_aviso)
                cv2.waitKey(300)
        if tecla == ord('q'): break

    captura.release()
    cv2.destroyAllWindows()
    return fotos_tiradas

# As funções abaixo orquestram o processo de gerenciamento, chamando as funções de base.

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
    else:
        messagebox.showinfo("Cancelado", "Nenhuma foto nova foi adicionada.")

def gerenciar_fotos_usuario():
    """Interface para gerenciar fotos de um usuário específico."""
    cpf = simpledialog.askstring("Gerenciar Fotos", "Digite o CPF do usuário:")
    if not cpf: return
    dados_usuario = carregar_dados_json(caminho_json_dados_usuario)
    if cpf not in dados_usuario:
        messagebox.showerror("Erro", "CPF não encontrado.")
        return

    nome_usuario = dados_usuario[cpf]['nome']
    id_unico = dados_usuario[cpf]['id']
    caminho_pasta_pessoa = os.path.join(diretorio_de_faces, id_unico)

    if not os.path.exists(caminho_pasta_pessoa):
        messagebox.showerror("Erro", "Pasta de fotos não encontrada.")
        return

    # Lista todas as fotos do usuário
    fotos = [f for f in os.listdir(caminho_pasta_pessoa) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]

    if not fotos:
        messagebox.showinfo("Info", f"Nenhuma foto encontrada para {nome_usuario}.")
        return

    # Mostra informações e opções
    mensagem = f"Usuário: {nome_usuario} (CPF: {cpf})\n"
    mensagem += f"Total de fotos: {len(fotos)}\n\n"
    mensagem += "Opções:\n"
    mensagem += "1. Adicionar mais fotos\n"
    mensagem += "2. Remover fotos antigas (manter apenas as 30 mais recentes)\n"
    mensagem += "3. Remover fotos antigas (manter apenas as 10 mais recentes)\n"
    mensagem += "4. Remover fotos antigas (manter apenas as 5 mais recentes)\n"
    mensagem += "5. Cancelar"

    opcao = simpledialog.askstring("Gerenciar Fotos", mensagem + "\n\nDigite o número da opção (1-5):")

    if opcao == "1":
        adicionar_mais_fotos()
    elif opcao == "2":
        manter_apenas_fotos_recentes(caminho_pasta_pessoa, fotos, 30, nome_usuario)
    elif opcao == "3":
        manter_apenas_fotos_recentes(caminho_pasta_pessoa, fotos, 10, nome_usuario)
    elif opcao == "4":
        manter_apenas_fotos_recentes(caminho_pasta_pessoa, fotos, 5, nome_usuario)
    elif opcao == "5":
        return
    else:
        messagebox.showwarning("Aviso", "Opção inválida.")

def manter_apenas_fotos_recentes(caminho_pasta, fotos, quantidade, nome_usuario):
    """Mantém apenas as N fotos mais recentes de um usuário."""
    if len(fotos) <= quantidade:
        messagebox.showinfo("Info", f"{nome_usuario} já tem apenas {len(fotos)} fotos.")
        return

    # Ordena as fotos por data de modificação (mais recentes primeiro)
    # A data de modificação corresponde ao tempo de inserção/criação da foto
    fotos_com_data = []
    for foto in fotos:
        caminho_foto = os.path.join(caminho_pasta, foto)
        data_modificacao = os.path.getmtime(caminho_foto)
        fotos_com_data.append((foto, data_modificacao))

    fotos_com_data.sort(key=lambda x: x[1], reverse=True)  # Mais recentes primeiro

    # Mostra informações sobre as fotos que serão mantidas e removidas
    import datetime
    fotos_para_manter = fotos_com_data[:quantidade]
    fotos_para_remover = fotos_com_data[quantidade:]

    # Mostra a foto mais antiga que será mantida e a mais recente que será removida
    if fotos_para_manter and fotos_para_remover:
        foto_mais_antiga_mantida = fotos_para_manter[-1]
        foto_mais_recente_removida = fotos_para_remover[0]

        data_antiga = datetime.datetime.fromtimestamp(foto_mais_antiga_mantida[1]).strftime("%d/%m/%Y %H:%M")
        data_recente = datetime.datetime.fromtimestamp(foto_mais_recente_removida[1]).strftime("%d/%m/%Y %H:%M")

        print(f"Foto mais antiga mantida: {foto_mais_antiga_mantida[0]} ({data_antiga})")
        print(f"Foto mais recente removida: {foto_mais_recente_removida[0]} ({data_recente})")

    # Remove as fotos mais antigas
    fotos_removidas = 0

    for foto, _ in fotos_para_remover:
        caminho_foto = os.path.join(caminho_pasta, foto)
        try:
            os.remove(caminho_foto)
            fotos_removidas += 1
        except Exception as e:
            print(f"Erro ao remover {foto}: {e}")

    if fotos_removidas > 0:
        messagebox.showinfo("Sucesso", f"Removidas {fotos_removidas} fotos antigas de {nome_usuario}.\nMantidas as {quantidade} fotos mais recentes.\n\nAs fotos são ordenadas pelo tempo de inserção.")
        invalidar_modelo_treinado()
    else:
        messagebox.showwarning("Aviso", "Nenhuma foto foi removida.")

def excluir_usuario():
    """Interface para excluir um usuário do sistema."""
    cpf = simpledialog.askstring("Excluir Usuário", "Digite o CPF do usuário que deseja excluir:")
    if not cpf: return
    dados_usuario, dados_validacao = carregar_dados_json(caminho_json_dados_usuario), carregar_dados_json(caminho_json_validacao)
    if cpf not in dados_usuario:
        messagebox.showerror("Erro", "CPF não encontrado.")
        return
    nome_usuario = dados_usuario[cpf]['nome']
    resposta = messagebox.askyesno("Confirmar Exclusão",
                                 f"Tem certeza que deseja excluir '{nome_usuario}' (CPF: {cpf})?\n\nEsta ação é irreversível e removerá:\n• Todas as fotos do usuário\n• Dados de acesso\n• Histórico de reconhecimento")
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
        messagebox.showinfo("Sucesso", f"Usuário '{nome_usuario}' (CPF: {cpf}) foi excluído com sucesso.")
        invalidar_modelo_treinado()
    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro ao excluir o usuário: {e}")