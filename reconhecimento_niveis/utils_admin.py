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
from tkinter import messagebox, simpledialog, ttk  # Módulos específicos do tkinter para caixas de diálogo simples.
import uuid                 # Para gerar identificadores únicos universais (usados para as pastas de fotos).
import cv2                  # A biblioteca OpenCV, essencial para a câmera e processamento de imagem.
import sys                  # Para interações com o sistema (atualmente não usado, mas bom para futuras expansões).
import numpy as np          # Biblioteca para computação numérica, usada aqui para criar o efeito de "flash".
import random               # Para geração de números aleatórios no data augmentation.

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

# --- Funções de Data Augmentation ---

def aplicar_data_augmentation(imagem):
    """
    Aplica transformações de data augmentation otimizadas para melhorar o treinamento.
    Cria variações da imagem original para aumentar a robustez do modelo.
    Versão otimizada para melhor performance.
    """
    imagens_aumentadas = [imagem]  # Inclui a imagem original

    # 1. Rotação leve (apenas 2 ângulos para otimizar)
    for angulo in [-3, 3]:
        h, w = imagem.shape[:2]
        centro = (w // 2, h // 2)
        matriz_rotacao = cv2.getRotationMatrix2D(centro, angulo, 1.0)
        imagem_rotacionada = cv2.warpAffine(imagem, matriz_rotacao, (w, h))
        imagens_aumentadas.append(imagem_rotacionada)

    # 2. Brilho ajustado (apenas 1 variação)
    imagem_brilho = cv2.convertScaleAbs(imagem, alpha=1.1, beta=0)
    imagens_aumentadas.append(imagem_brilho)

    # 3. Contraste ajustado (apenas 1 variação)
    imagem_contraste = cv2.convertScaleAbs(imagem, alpha=0.95, beta=0)
    imagens_aumentadas.append(imagem_contraste)

    # 4. Ruído gaussiano leve (reduzido)
    ruido = np.random.normal(0, 5, imagem.shape).astype(np.uint8)
    imagem_ruido = cv2.add(imagem, ruido)
    imagens_aumentadas.append(imagem_ruido)

    return imagens_aumentadas

def validar_qualidade_imagem(imagem):
    """
    Valida se a imagem tem qualidade suficiente para treinamento.
    Versão otimizada para melhor performance.
    Retorna True se a imagem for adequada, False caso contrário.
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