# utils_admin.py
# Este arquivo centraliza todas as funções de utilidade e administração do projeto.
# Ele lida com a manipulação de arquivos JSON e o gerenciamento de perfis de usuários
# (criar, adicionar fotos e excluir), evitando a duplicação de código em outros scripts.

# --- Importação das Bibliotecas Necessárias ---
import os                   # Para interagir com o sistema operacional (criar pastas, verificar caminhos).
import json                 # Para manipular arquivos no formato JSON (ler e escrever dados).
import shutil               # Usado para operações de alto nível em arquivos, como remover uma pasta inteira.
import tkinter as tk        # A biblioteca padrão do Python para criar interfaces gráficas.
from tkinter import messagebox, simpledialog  # Módulos específicos do tkinter para caixas de diálogo simples.
import uuid                 # Para gerar identificadores únicos universais (usados para as pastas de fotos).
import cv2                  # A biblioteca OpenCV, essencial para tudo relacionado à câmera e processamento de imagem.
import sys                  # Para interações com o sistema, como encerrar o programa em caso de erro crítico.

# --- Configuração de Caminhos Globais ---
# Define o diretório base do projeto. '__file__' é uma variável que contém o caminho do script atual.
# 'os.path.abspath' obtém o caminho completo, e 'os.path.dirname' pega apenas o diretório.
# Isso garante que o programa encontre seus arquivos, não importa de onde ele seja executado.
base_dir = os.path.dirname(os.path.abspath(__file__))

# Define os caminhos completos para os arquivos e pastas que o programa usará.
# 'os.path.join' é a forma correta de juntar caminhos, pois funciona em qualquer sistema operacional.
diretorio_de_faces = os.path.join(base_dir, 'faces')
caminho_json_validacao = os.path.join(base_dir, 'validation.json')
caminho_json_dados_usuario = os.path.join(base_dir, 'userData.json')
face_cascade_path = os.path.join(base_dir, 'haarcascade_frontalface_default.xml')

# --- Funções de Manipulação de Dados (JSON) ---

def carregar_dados_json(caminho_arquivo):
    """
    Função segura para carregar dados de um arquivo JSON.
    - Verifica se o arquivo existe antes de tentar abri-lo.
    - Usa um bloco 'try...except' para capturar erros que possam ocorrer durante a leitura.
    - 'encoding="utf-8"' garante que caracteres especiais (como acentos) sejam lidos corretamente.
    """
    if not os.path.exists(caminho_arquivo):
        return {}  # Se o arquivo não existe, retorna um dicionário vazio para evitar erros.
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            # 'json.load(f)' lê o conteúdo do arquivo (f) e o converte de JSON para um dicionário Python.
            return json.load(f)
    except Exception as e:
        messagebox.showerror("Erro de Leitura", f"Erro ao carregar o arquivo JSON {caminho_arquivo}: {e}")
        return {} # Em caso de erro, retorna um dicionário vazio.

def salvar_dados_json(caminho_arquivo, dados):
    """
    Função segura para salvar um dicionário Python em um arquivo JSON.
    - 'w' no open() significa que o arquivo será aberto para escrita (write).
    - 'json.dump()' faz o processo inverso do load: converte um dicionário Python para o formato JSON.
    - 'indent=2' formata o JSON de forma legível para humanos (com indentação de 2 espaços).
    - 'ensure_ascii=False' permite que caracteres especiais (acentos) sejam salvos corretamente no arquivo.
    """
    try:
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados, f, indent=2, ensure_ascii=False)
        return True  # Retorna True se a operação foi bem-sucedida.
    except Exception as e:
        messagebox.showerror("Erro de Escrita", f"Erro ao salvar os dados no arquivo JSON {caminho_arquivo}: {e}")
        return False # Retorna False se ocorreu um erro.

# --- Funções de Gerenciamento de Usuários e Captura de Imagem ---

def tirar_e_salvar_fotos(id_unico, cpf_usuario="novo_usuario"):
    """
    Abre a webcam, detecta um rosto, captura fotos e as salva na pasta correta.
    Retorna o número de fotos que foram tiradas com sucesso.
    """
    # Carrega o modelo pré-treinado do OpenCV para detectar faces.
    if not os.path.exists(face_cascade_path):
        messagebox.showerror("Erro", f"O arquivo '{os.path.basename(face_cascade_path)}' não foi encontrado.")
        return 0
    classificador_de_faces = cv2.CascadeClassifier(face_cascade_path)

    # Cria o caminho completo para a pasta onde as fotos do usuário serão salvas.
    caminho_pasta_pessoa = os.path.join(diretorio_de_faces, id_unico)
    if not os.path.exists(caminho_pasta_pessoa):
        os.makedirs(caminho_pasta_pessoa) # Cria a pasta se ela não existir.

    # Inicializa a webcam. O '0' geralmente se refere à câmera padrão do dispositivo.
    captura = cv2.VideoCapture(0)
    if not captura.isOpened():
        messagebox.showerror("Erro", "Não foi possível acessar a webcam.")
        return 0

    fotos_tiradas = 0
    max_fotos = 10  # Define um limite de fotos a serem capturadas.

    # Loop principal que continua enquanto a câmera está aberta e o limite de fotos não foi atingido.
    while fotos_tiradas < max_fotos:
        ret, frame = captura.read() # 'ret' é um booleano (True/False) se o frame foi lido, 'frame' é a imagem.
        if not ret:
            break

        # Escreve o texto de instrução diretamente no vídeo.
        texto_instrucao = f"Pressione 'S' para foto ({fotos_tiradas}/{max_fotos}). 'Q' para sair."
        cv2.putText(frame, texto_instrucao, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.imshow(f"Captura de Fotos para {cpf_usuario}", frame) # Exibe a janela da webcam.

        tecla = cv2.waitKey(1) & 0xFF # Espera por uma tecla ser pressionada (o '& 0xFF' é um detalhe técnico de compatibilidade).

        if tecla == ord('s'): # Se a tecla 's' for pressionada...
            # O classificador tenta encontrar rostos no frame atual.
            rostos_detectados = classificador_de_faces.detectMultiScale(frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
            if len(rostos_detectados) > 0: # Se pelo menos um rosto for detectado...
                # Gera um nome de arquivo aleatório e único para a foto para evitar sobreposições.
                nome_arquivo = f"{id_unico}_{uuid.uuid4().hex[:8]}.jpg"
                caminho_foto = os.path.join(caminho_pasta_pessoa, nome_arquivo)
                cv2.imwrite(caminho_foto, frame) # Salva a imagem (o frame atual) no disco.
                fotos_tiradas += 1
                print(f"Foto {fotos_tiradas} salva em: {caminho_foto}")
            else:
                messagebox.showwarning("Aviso", "Nenhum rosto detectado. Posicione-se melhor e tente novamente.")

        if tecla == ord('q'): # Se a tecla 'q' for pressionada, o loop é interrompido.
            break

    # Libera a webcam para que outros programas possam usá-la e fecha todas as janelas do OpenCV.
    captura.release()
    cv2.destroyAllWindows()

    return fotos_tiradas

def criar_novo_usuario_via_gui():
    """
    Orquestra o processo de criação de um novo usuário através de caixas de diálogo.
    """
    # Pede as informações do usuário através de janelas pop-up.
    nome_completo = simpledialog.askstring("Novo Usuário", "Digite o Nome Completo:")
    if not nome_completo: return # Se o usuário cancelar, a função termina.

    cpf = simpledialog.askstring("Novo Usuário", "Digite o CPF (apenas números):")
    if not cpf: return

    nivel_digitado = simpledialog.askstring("Novo Usuário", "Digite o Nível (1, 2 ou 3):")
    if not nivel_digitado: return

    # --- Validação dos Dados de Entrada ---
    cpf_limpo = cpf.replace(".", "").replace("-", "") # Limpa o CPF de formatação.
    if len(cpf_limpo) != 11 or not cpf_limpo.isdigit():
        messagebox.showwarning("Aviso", "O CPF deve conter exatamente 11 dígitos numéricos.")
        return

    try:
        nivel_int = int(nivel_digitado)
        if nivel_int not in [1, 2, 3]: raise ValueError # Força um erro se o número não for 1, 2 ou 3.
        nivel_formatado = f"Nivel {nivel_int}"
    except ValueError:
        messagebox.showwarning("Aviso", "O nível deve ser um número válido (1, 2 ou 3).")
        return

    # Carrega os dados atuais para verificação.
    dados_validacao = carregar_dados_json(caminho_json_validacao)
    dados_usuario = carregar_dados_json(caminho_json_dados_usuario)

    # Verifica se o CPF já existe para evitar duplicatas.
    if cpf_limpo in dados_usuario:
        messagebox.showerror("Erro", f"O CPF '{cpf_limpo}' já está cadastrado.")
        return

    # --- Processo de Cadastro ---
    id_unico = str(uuid.uuid4()) # Gera um ID seguro e aleatório para o usuário.
    fotos_tiradas = tirar_e_salvar_fotos(id_unico, cpf_limpo) # Chama a função de captura de fotos.

    if fotos_tiradas == 0:
        pasta_criada = os.path.join(diretorio_de_faces, id_unico)
        if os.path.exists(pasta_criada):
            shutil.rmtree(pasta_criada) # Remove a pasta vazia se o usuário cancelou a captura.
        messagebox.showwarning("Aviso", "Nenhuma foto tirada. O cadastro foi cancelado.")
        return

    # Atualiza os dicionários com os novos dados.
    if nivel_formatado not in dados_validacao:
        dados_validacao[nivel_formatado] = {"pessoas": []}
    dados_validacao[nivel_formatado]["pessoas"].append(cpf_limpo)

    dados_usuario[cpf_limpo] = {"nome": nome_completo, "id": id_unico}

    # Salva os dicionários atualizados de volta nos arquivos JSON.
    if salvar_dados_json(caminho_json_validacao, dados_validacao) and salvar_dados_json(caminho_json_dados_usuario, dados_usuario):
        messagebox.showinfo("Sucesso", f"Usuário '{nome_completo}' (Nível {nivel_digitado}) cadastrado com sucesso com {fotos_tiradas} fotos.")

def adicionar_mais_fotos():
    """
    Adiciona mais fotos a um perfil de usuário que já existe.
    """
    cpf = simpledialog.askstring("Adicionar Fotos", "Digite o CPF do usuário:")
    if not cpf: return

    dados_usuario = carregar_dados_json(caminho_json_dados_usuario)
    if cpf not in dados_usuario:
        messagebox.showerror("Erro", "CPF não encontrado.")
        return

    # Pega o ID único do usuário existente e chama a mesma função de tirar fotos.
    id_unico = dados_usuario[cpf]['id']
    fotos_adicionadas = tirar_e_salvar_fotos(id_unico, cpf)

    if fotos_adicionadas > 0:
        messagebox.showinfo("Sucesso", f"{fotos_adicionadas} fotos adicionadas ao perfil do usuário {cpf}.")
    else:
        messagebox.showinfo("Cancelado", "Nenhuma foto nova foi adicionada.")

def excluir_usuario():
    """
    Remove completamente um usuário do sistema: sua pasta de fotos e seus registros nos arquivos JSON.
    """
    cpf = simpledialog.askstring("Excluir Usuário", "Digite o CPF do usuário que deseja excluir:")
    if not cpf: return

    dados_usuario = carregar_dados_json(caminho_json_dados_usuario)
    dados_validacao = carregar_dados_json(caminho_json_validacao)

    if cpf not in dados_usuario:
        messagebox.showerror("Erro", "CPF não encontrado.")
        return

    # Mensagem de confirmação para evitar exclusões acidentais.
    nome_usuario = dados_usuario[cpf]['nome']
    resposta = messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja excluir '{nome_usuario}' (CPF: {cpf})?\nEsta ação é irreversível.")
    if not resposta:
        return

    try:
        # Passo 1: Excluir a pasta de fotos.
        id_unico = dados_usuario[cpf]['id']
        caminho_pasta_pessoa = os.path.join(diretorio_de_faces, id_unico)
        if os.path.exists(caminho_pasta_pessoa):
            shutil.rmtree(caminho_pasta_pessoa) # 'shutil.rmtree' remove a pasta e todo o seu conteúdo.

        # Passo 2: Remover o CPF do arquivo de validação.
        for nivel in dados_validacao:
            if cpf in dados_validacao[nivel].get('pessoas', []):
                dados_validacao[nivel]['pessoas'].remove(cpf)
                break

        # Passo 3: Remover a entrada do usuário do arquivo de dados.
        del dados_usuario[cpf]

        # Passo 4: Salvar as alterações nos dois arquivos.
        salvar_dados_json(caminho_json_validacao, dados_validacao)
        salvar_dados_json(caminho_json_dados_usuario, dados_usuario)

        messagebox.showinfo("Sucesso", f"Usuário com CPF '{cpf}' foi excluído com sucesso.")

    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro ao excluir o usuário: {e}")