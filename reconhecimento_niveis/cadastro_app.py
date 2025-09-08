# cadastro_app.py
# Este script é usado para cadastrar novas pessoas, tirando fotos diretamente da webcam.

import os
import json
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import uuid
import cv2
import sys

# Obtenha o caminho absoluto do diretório onde o script está
base_dir = os.path.dirname(os.path.abspath(__file__))

# Caminhos para os diretórios e arquivos do projeto
diretorio_de_faces = os.path.join(base_dir, 'faces')
caminho_json_validacao = os.path.join(base_dir, 'validation.json')
caminho_json_dados_usuario = os.path.join(base_dir, 'userData.json')

# Caminho para o classificador de faces (Haar Cascade)
face_cascade_path = os.path.join(base_dir, 'haarcascade_frontalface_default.xml')
# Verifica se o arquivo do classificador existe
if not os.path.exists(face_cascade_path):
    messagebox.showerror("Erro", f"O arquivo '{os.path.basename(face_cascade_path)}' não foi encontrado. Por favor, baixe-o e coloque-o na mesma pasta do cadastro_app.py.")
    sys.exit()

classificador_de_faces = cv2.CascadeClassifier(face_cascade_path)

def garantir_diretorios_e_arquivos():
    """
    Função para garantir que os diretórios e arquivos necessários existam.
    Cria a pasta 'faces' e os arquivos JSON se eles não existirem.
    """
    if not os.path.exists(diretorio_de_faces):
        os.makedirs(diretorio_de_faces)
        print(f"Diretório '{diretorio_de_faces}' criado com sucesso.")

    if not os.path.exists(caminho_json_validacao):
        with open(caminho_json_validacao, 'w') as f:
            json.dump({}, f)
        print(f"Arquivo '{caminho_json_validacao}' criado com sucesso.")

    if not os.path.exists(caminho_json_dados_usuario):
        with open(caminho_json_dados_usuario, 'w') as f:
            json.dump({}, f)
        print(f"Arquivo '{caminho_json_dados_usuario}' criado com sucesso.")

def carregar_dados_json(caminho_arquivo):
    """
    Carrega dados de um arquivo JSON.
    Retorna o dicionário de dados ou um dicionário vazio em caso de erro.
    """
    if not os.path.exists(caminho_arquivo):
        return {}
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao carregar o arquivo JSON {caminho_arquivo}: {e}")
        return {}

def salvar_dados_json(caminho_arquivo, dados):
    """
    Salva dados em um arquivo JSON.
    """
    try:
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao salvar os dados no arquivo JSON {caminho_arquivo}: {e}")
        return False

def tirar_e_salvar_fotos(id_unico):
    """
    Abre a webcam, captura fotos e salva em uma pasta com o ID único.
    """
    caminho_pasta_pessoa = os.path.join(diretorio_de_faces, id_unico)

    # Cria a pasta
    try:
        os.makedirs(caminho_pasta_pessoa)
    except FileExistsError:
        messagebox.showerror("Erro", f"Uma pasta com o ID '{id_unico}' já existe. Tente novamente.")
        return 0

    captura = cv2.VideoCapture(0)
    if not captura.isOpened():
        messagebox.showerror("Erro", "Não foi possível acessar a webcam.")
        return 0

    fotos_tiradas = 0
    while True:
        ret, frame = captura.read()
        if not ret:
            break

        cv2.putText(frame, "Pressione 'S' para tirar a foto e 'Q' para sair", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.imshow("Tirar Fotos", frame)

        tecla = cv2.waitKey(1) & 0xFF
        if tecla == ord('s'):
            rostos_detectados = classificador_de_faces.detectMultiScale(frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
            if len(rostos_detectados) > 0:
                caminho_foto = os.path.join(caminho_pasta_pessoa, f"{id_unico}_{fotos_tiradas}.jpg")
                cv2.imwrite(caminho_foto, frame)
                fotos_tiradas += 1
                print(f"Foto salva em: {caminho_foto}")
            else:
                messagebox.showwarning("Aviso", "Nenhum rosto detectado. Posicione-se melhor.")

        if tecla == ord('q'):
            break

    captura.release()
    cv2.destroyAllWindows()

    return fotos_tiradas

def criar_novo_usuario_via_gui():
    """
    Cria a interface gráfica para um novo usuário.
    Esta função será chamada do document_viewer.py
    """
    nome_completo = simpledialog.askstring("Novo Usuário", "Digite o Nome Completo:")
    if not nome_completo:
        return

    cpf = simpledialog.askstring("Novo Usuário", "Digite o CPF (11 dígitos):")
    if not cpf:
        return

    nivel_digitado = simpledialog.askstring("Novo Usuário", "Digite o Nível (1, 2 ou 3):")
    if not nivel_digitado:
        return

    # Validação do CPF
    cpf_limpo = cpf.replace(".", "").replace("-", "")
    if len(cpf_limpo) != 11 or not cpf_limpo.isdigit():
        messagebox.showwarning("Aviso", "O CPF deve conter exatamente 11 dígitos numéricos.")
        return

    # Validação do Nível
    try:
        nivel_int = int(nivel_digitado)
        if nivel_int not in [1, 2, 3]:
            messagebox.showwarning("Aviso", "Por favor, digite um número de nível válido (1, 2 ou 3).")
            return
        nivel_formatado = f"Nivel {nivel_int}"
    except ValueError:
        messagebox.showwarning("Aviso", "O nível deve ser um número válido (1, 2 ou 3).")
        return

    # Carrega os dados existentes de validação e de usuário
    dados_validacao = carregar_dados_json(caminho_json_validacao)
    dados_usuario = carregar_dados_json(caminho_json_dados_usuario)

    # Verifica se já existe um cadastro com o mesmo CPF
    if cpf in dados_usuario:
        messagebox.showerror("Erro", f"O CPF '{cpf}' já está cadastrado.")
        return

    # Gera um ID único para a nova pessoa
    id_unico = str(uuid.uuid4())

    # Tira e salva as fotos, retornando o número de fotos capturadas
    fotos_tiradas = tirar_e_salvar_fotos(id_unico)

    if fotos_tiradas == 0:
        messagebox.showwarning("Aviso", "Nenhuma foto tirada. O cadastro foi cancelado.")
        return

    # Adiciona a nova pessoa (CPF) ao nível correspondente em validation.json
    if nivel_formatado not in dados_validacao:
        dados_validacao[nivel_formatado] = {"pessoas": []}

    if cpf not in dados_validacao[nivel_formatado]["pessoas"]:
        dados_validacao[nivel_formatado]["pessoas"].append(cpf)

    # Adiciona o nome, CPF e o ID único no userData.json
    dados_usuario[cpf] = {
        "nome": nome_completo,
        "id": id_unico
    }

    # Salva os dados atualizados em ambos os arquivos
    if salvar_dados_json(caminho_json_validacao, dados_validacao) and salvar_dados_json(caminho_json_dados_usuario, dados_usuario):
        messagebox.showinfo("Sucesso", f"Pessoa '{nome_completo}' (Nível: {nivel_digitado}) cadastrada com sucesso.\n{fotos_tiradas} fotos salvas.")

if __name__ == "__main__":
    # Garante a existência dos diretórios e arquivos iniciais
    garantir_diretorios_e_arquivos()
    # Esta parte só é executada se o script for rodado diretamente
    # Fornece um exemplo de uso
    janela_raiz = tk.Tk()
    janela_raiz.withdraw()
    criar_novo_usuario_via_gui()
    janela_raiz.destroy()
