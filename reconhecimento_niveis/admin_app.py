# admin_app.py
# Este script fornece uma interface para usuários de Nível 3 gerenciarem os dados.

import os
import json
import shutil
import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
import uuid
import cv2
import sys
import unicodedata
import time

# Obtenha o caminho absoluto do diretório onde o script está
base_dir = os.path.dirname(os.path.abspath(__file__))

# Caminhos para os diretórios e arquivos do projeto
diretorio_de_faces = os.path.join(base_dir, 'faces')
caminho_json_validacao = os.path.join(base_dir, 'validation.json')
caminho_json_dados_usuario = os.path.join(base_dir, 'userData.json')

# Caminho para o classificador de faces (Haar Cascade)
face_cascade_path = os.path.join(base_dir, 'haarcascade_frontalface_default.xml')

def carregar_dados_json(caminho_arquivo):
    """
    Carrega dados de um arquivo JSON.
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

def adicionar_mais_fotos(cpf):
    """
    Abre a webcam para tirar mais fotos de um usuário existente.
    """
    dados_usuario = carregar_dados_json(caminho_json_dados_usuario)
    if cpf not in dados_usuario:
        messagebox.showerror("Erro", "CPF não encontrado. Verifique o CPF e tente novamente.")
        return

    id_unico = dados_usuario[cpf]['id']
    caminho_pasta_pessoa = os.path.join(diretorio_de_faces, id_unico)

    if not os.path.exists(caminho_pasta_pessoa):
        messagebox.showerror("Erro", f"Diretório de fotos para o usuário '{cpf}' não encontrado.")
        return

    # Inicia o classificador de faces
    if not os.path.exists(face_cascade_path):
        messagebox.showerror("Erro", f"O arquivo '{os.path.basename(face_cascade_path)}' não foi encontrado. Por favor, baixe-o e coloque-o na mesma pasta.")
        return
    classificador_de_faces = cv2.CascadeClassifier(face_cascade_path)

    captura = cv2.VideoCapture(0)
    if not captura.isOpened():
        messagebox.showerror("Erro", "Não foi possível acessar a webcam.")
        return

    fotos_adicionadas = 0
    while True:
        ret, frame = captura.read()
        if not ret:
            break

        cv2.putText(frame, "Pressione 'S' para tirar a foto e 'Q' para sair", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.imshow(f"Adicionar Fotos para {cpf}", frame)

        tecla = cv2.waitKey(1) & 0xFF
        if tecla == ord('s'):
            rostos_detectados = classificador_de_faces.detectMultiScale(frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
            if len(rostos_detectados) > 0:
                caminho_foto = os.path.join(caminho_pasta_pessoa, f"{id_unico}_{uuid.uuid4()}.jpg")
                cv2.imwrite(caminho_foto, frame)
                fotos_adicionadas += 1
                print(f"Foto adicionada em: {caminho_foto}")
            else:
                messagebox.showwarning("Aviso", "Nenhum rosto detectado. Posicione-se melhor.")

        if tecla == ord('q'):
            break

    captura.release()
    cv2.destroyAllWindows()
    messagebox.showinfo("Sucesso", f"{fotos_adicionadas} fotos foram adicionadas ao perfil do usuário {cpf}.")


def excluir_usuario(cpf):
    """
    Remove todos os dados de um usuário do sistema.
    """
    dados_usuario = carregar_dados_json(caminho_json_dados_usuario)
    dados_validacao = carregar_dados_json(caminho_json_validacao)

    if cpf not in dados_usuario:
        messagebox.showerror("Erro", "CPF não encontrado. Não é possível excluir.")
        return

    resposta = messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja excluir o usuário com CPF '{cpf}'? Esta ação é irreversível.")
    if not resposta:
        return

    try:
        # 1. Exclui a pasta de fotos do usuário
        id_unico = dados_usuario[cpf]['id']
        caminho_pasta_pessoa = os.path.join(diretorio_de_faces, id_unico)
        if os.path.exists(caminho_pasta_pessoa):
            shutil.rmtree(caminho_pasta_pessoa)
            print(f"Pasta de fotos '{id_unico}' excluída.")

        # 2. Remove o CPF do arquivo de validação
        for nivel, dados in dados_validacao.items():
            if cpf in dados.get('pessoas', []):
                dados['pessoas'].remove(cpf)
                break

        # 3. Remove o usuário do arquivo de dados
        del dados_usuario[cpf]

        # 4. Salva as mudanças
        salvar_dados_json(caminho_json_validacao, dados_validacao)
        salvar_dados_json(caminho_json_dados_usuario, dados_usuario)

        messagebox.showinfo("Sucesso", f"Usuário com CPF '{cpf}' excluído com sucesso.")

    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro ao excluir o usuário: {e}")


def criar_janela_admin():
    """
    Cria a interface gráfica do aplicativo de administração.
    """
    janela = tk.Tk()
    janela.title("Painel de Administração (Nível 3)")
    janela.geometry("450x300")

    # Widgets da interface
    label_cpf = tk.Label(janela, text="CPF do Usuário:", font=("Helvetica", 12))
    label_cpf.pack(pady=10)
    entry_cpf = tk.Entry(janela, width=40)
    entry_cpf.pack(pady=5)

    def adicionar():
        cpf = entry_cpf.get()
        adicionar_mais_fotos(cpf)

    def excluir():
        cpf = entry_cpf.get()
        excluir_usuario(cpf)

    btn_adicionar = tk.Button(janela, text="Adicionar Mais Fotos", command=adicionar)
    btn_adicionar.pack(pady=10, ipadx=10, ipady=5)

    btn_excluir = tk.Button(janela, text="Excluir Usuário", command=excluir, bg="red", fg="white")
    btn_excluir.pack(pady=10, ipadx=10, ipady=5)

    label_aviso = tk.Label(janela, text="Apenas para usuários autorizados Nível 3", fg="gray")
    label_aviso.pack(side=tk.BOTTOM, pady=10)

    janela.mainloop()

if __name__ == "__main__":
    # Este bloco só será executado se o admin_app.py for executado diretamente
    # Se for chamado de outro script, as funções serão importadas e usadas
    criar_janela_admin()
