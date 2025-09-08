# document_viewer.py
# Este script cria a interface gráfica para exibir documentos e, para usuários de Nível 3,
# também fornece ferramentas de administração.

import tkinter as tk
from tkinter import messagebox, scrolledtext, simpledialog
import os
import sys
import json
import shutil
import cv2
import uuid
import unicodedata
import subprocess

# Obtenha o caminho base do projeto
base_dir = os.path.dirname(os.path.abspath(__file__))

# Caminhos para os diretórios e arquivos do projeto
diretorio_de_faces = os.path.join(base_dir, 'faces')
caminho_json_validacao = os.path.join(base_dir, 'validation.json')
caminho_json_dados_usuario = os.path.join(base_dir, 'userData.json')

# Caminho para o classificador de faces (Haar Cascade)
face_cascade_path = os.path.join(base_dir, 'haarcascade_frontalface_default.xml')
# Verifica se o arquivo do classificador existe
if not os.path.exists(face_cascade_path):
    messagebox.showerror("Erro", f"O arquivo '{os.path.basename(face_cascade_path)}' não foi encontrado. Por favor, baixe-o e coloque-o na mesma pasta do documento_viewer.py.")
    sys.exit()
classificador_de_faces = cv2.CascadeClassifier(face_cascade_path)


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
                print(f"Foto adicionada em: {caminho_foto}")
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


def adicionar_mais_fotos():
    """
    Abre a webcam para tirar mais fotos de um usuário existente.
    """
    cpf = simpledialog.askstring("Adicionar Fotos", "Digite o CPF do usuário:")
    if not cpf:
        return

    dados_usuario = carregar_dados_json(caminho_json_dados_usuario)
    if cpf not in dados_usuario:
        messagebox.showerror("Erro", "CPF não encontrado. Verifique o CPF e tente novamente.")
        return

    id_unico = dados_usuario[cpf]['id']
    caminho_pasta_pessoa = os.path.join(diretorio_de_faces, id_unico)

    if not os.path.exists(caminho_pasta_pessoa):
        messagebox.showerror("Erro", f"Diretório de fotos para o usuário '{cpf}' não encontrado.")
        return

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


def excluir_usuario():
    """
    Remove todos os dados de um usuário do sistema.
    """
    cpf = simpledialog.askstring("Excluir Usuário", "Digite o CPF do usuário que deseja excluir:")
    if not cpf:
        return

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


def abrir_arquivo(caminho_arquivo):
    """
    Abre uma nova janela para exibir o conteúdo de um arquivo de texto.
    """
    janela_arquivo = tk.Toplevel()
    janela_arquivo.title(os.path.basename(caminho_arquivo))
    janela_arquivo.geometry("500x400")

    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            conteudo = f.read()
    except Exception as e:
        conteudo = f"Erro ao ler o arquivo: {e}"

    texto_arquivo = scrolledtext.ScrolledText(janela_arquivo, wrap=tk.WORD, padx=10, pady=10)
    texto_arquivo.pack(fill=tk.BOTH, expand=True)
    texto_arquivo.insert(tk.END, conteudo)
    texto_arquivo.configure(state='disabled')

    btn_fechar = tk.Button(janela_arquivo, text="Fechar", command=janela_arquivo.destroy)
    btn_fechar.pack(pady=10)


def mostrar_documentos(nivel_acesso):
    """
    Cria a interface gráfica para exibir documentos e, para usuários de Nível 3,
    também fornece ferramentas de administração.
    """
    janela = tk.Tk()
    janela.title("Visualizador de Documentos")
    janela.geometry("600x400")

    documentos_dir = os.path.join(base_dir, 'documentos')
    if not os.path.exists(documentos_dir):
        messagebox.showerror("Erro de Arquivo", "Diretório 'documentos' não encontrado. Por favor, crie-o na pasta do projeto.")
        janela.destroy()
        return

    # Mapeamento de níveis para subpastas
    mapa_niveis = {
        "Nivel 1": ["nivel_1"],
        "Nivel 2": ["nivel_1", "nivel_2"],
        "Nivel 3": ["nivel_1", "nivel_2", "nivel_3"]
    }

    # Obtém as pastas que o usuário pode acessar
    pastas_acesso = mapa_niveis.get(nivel_acesso, [])

    frame_principal = tk.Frame(janela, padx=10, pady=10)
    frame_principal.pack(fill=tk.BOTH, expand=True)

    # Título personalizado
    titulos = {
        "Nivel 1": "Bem-vindo!",
        "Nivel 2": "Bem-vindo Diretor(a)!",
        "Nivel 3": "Bem-vindo Ministro(a)!"
    }
    titulo = tk.Label(frame_principal, text=titulos.get(nivel_acesso, "Bem-vindo!"), font=("Helvetica", 16))
    titulo.pack(pady=10)


    # Exibe os arquivos em um campo de texto rolável
    canvas = tk.Canvas(frame_principal, width=500, height=250)
    scrollbar = tk.Scrollbar(frame_principal, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    arquivos_encontrados = False
    for pasta in pastas_acesso:
        caminho_pasta = os.path.join(documentos_dir, pasta)
        if os.path.exists(caminho_pasta):
            label_pasta = tk.Label(scrollable_frame, text=f"Pasta: {pasta.capitalize().replace('_', ' ')}", font=("Helvetica", 12, "bold"))
            label_pasta.pack(pady=(10, 5))

            arquivos = [f for f in os.listdir(caminho_pasta) if os.path.isfile(os.path.join(caminho_pasta, f))]

            if arquivos:
                arquivos_encontrados = True
                for arquivo in arquivos:
                    caminho_arquivo = os.path.join(caminho_pasta, arquivo)
                    btn_arquivo = tk.Button(scrollable_frame, text=f" - {arquivo}", command=lambda path=caminho_arquivo: abrir_arquivo(path))
                    btn_arquivo.pack(fill=tk.X, padx=20)
            else:
                label_nenhum_arquivo = tk.Label(scrollable_frame, text="    Nenhum arquivo encontrado.", font=("Helvetica", 10))
                label_nenhum_arquivo.pack()

    if not arquivos_encontrados:
        label_nenhum_doc = tk.Label(scrollable_frame, text="Nenhum documento encontrado nas pastas acessíveis.", font=("Helvetica", 10))
        label_nenhum_doc.pack()

    # Se for Nível 3, adiciona os botões de administração
    if nivel_acesso == "Nivel 3":
        frame_admin = tk.Frame(janela, padx=10, pady=10)
        frame_admin.pack(fill=tk.X)

        btn_criar_usuario = tk.Button(frame_admin, text="Criar Novo Usuário", command=criar_novo_usuario_via_gui)
        btn_criar_usuario.pack(side=tk.LEFT, expand=True, padx=5, pady=5)

        btn_adicionar_fotos = tk.Button(frame_admin, text="Adicionar Fotos a Usuário", command=adicionar_mais_fotos)
        btn_adicionar_fotos.pack(side=tk.LEFT, expand=True, padx=5, pady=5)

        btn_excluir_usuario = tk.Button(frame_admin, text="Excluir Usuário", command=excluir_usuario, bg="red", fg="white")
        btn_excluir_usuario.pack(side=tk.LEFT, expand=True, padx=5, pady=5)

    btn_fechar = tk.Button(janela, text="Fechar", command=janela.destroy)
    btn_fechar.pack(pady=10)

    janela.mainloop()

if __name__ == '__main__':
    # Exemplo de como a função pode ser chamada diretamente para testes
    # Mude o nível para testar as permissões
    mostrar_documentos("Nivel 3")
