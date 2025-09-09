# Este script cria a interface gráfica para exibir documentos e, para usuários de Nível 3,
# fornece acesso às ferramentas de administração, que são importadas do módulo de utilidades.

import tkinter as tk
from tkinter import scrolledtext
import os

# --- IMPORTAÇÃO DAS FUNÇÕES CENTRALIZADAS ---
# Em vez de reescrever as funções, as importa diretamente do arquivo de utilidades.
from utils_admin import criar_novo_usuario_via_gui, adicionar_mais_fotos, excluir_usuario

# --- Configuração de Caminhos ---
base_dir = os.path.dirname(os.path.abspath(__file__))

# --- Funções Específicas da Interface ---

def abrir_arquivo(caminho_arquivo):
    """
    Abre uma nova janela Toplevel para exibir o conteúdo de um arquivo de texto.
    Esta função é específica para a interface gráfica e permanece neste arquivo.
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
    texto_arquivo.configure(state='disabled') # Bloqueia a edição do texto

    btn_fechar = tk.Button(janela_arquivo, text="Fechar", command=janela_arquivo.destroy)
    btn_fechar.pack(pady=10)


def mostrar_documentos(nivel_acesso):
    """
    Cria a interface principal que exibe os documentos com base no nível de acesso do usuário.
    Para o Nível 3, adiciona botões que chamam as funções de administração importadas.
    """
    janela = tk.Tk()
    janela.title("Visualizador de Documentos")
    janela.geometry("600x450")

    documentos_dir = os.path.join(base_dir, 'documentos')
    if not os.path.exists(documentos_dir):
        # Usando 'messagebox' importado de 'utils_admin' seria uma opção, mas para manter o desacoplamento,
        # Usar o do tkinter diretamente aqui, já que é uma UI.
        tk.messagebox.showerror("Erro de Arquivo", "Diretório 'documentos' não encontrado.")
        janela.destroy()
        return

    # Mapeamento de níveis para subpastas de documentos
    mapa_niveis = {
        "Nivel 1": ["nivel_1"],
        "Nivel 2": ["nivel_1", "nivel_2"],
        "Nivel 3": ["nivel_1", "nivel_2", "nivel_3"]
    }
    pastas_acesso = mapa_niveis.get(nivel_acesso, [])

    frame_principal = tk.Frame(janela, padx=10, pady=10)
    frame_principal.pack(fill=tk.BOTH, expand=True)

    # Título personalizado para cada nível
    titulos = { "Nivel 1": "Bem-vindo!", "Nivel 2": "Bem-vindo Diretor(a)!", "Nivel 3": "Bem-vindo Ministro(a)!" }
    titulo = tk.Label(frame_principal, text=titulos.get(nivel_acesso, "Bem-vindo!"), font=("Helvetica", 16))
    titulo.pack(pady=10)

    # Canvas para exibir a lista de arquivos com barra de rolagem
    canvas = tk.Canvas(frame_principal)
    scrollbar = tk.Scrollbar(frame_principal, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas)

    scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Loop para listar os arquivos das pastas permitidas
    arquivos_encontrados = False
    for pasta in pastas_acesso:
        caminho_pasta = os.path.join(documentos_dir, pasta)
        if os.path.exists(caminho_pasta):
            label_pasta = tk.Label(scrollable_frame, text=f"Pasta: {pasta.replace('_', ' ').title()}", font=("Helvetica", 12, "bold"))
            label_pasta.pack(pady=(10, 5), anchor='w')

            arquivos = [f for f in os.listdir(caminho_pasta) if os.path.isfile(os.path.join(caminho_pasta, f))]
            if arquivos:
                arquivos_encontrados = True
                for arquivo in arquivos:
                    caminho_arquivo_completo = os.path.join(caminho_pasta, arquivo)
                    btn_arquivo = tk.Button(scrollable_frame, text=f"  - {arquivo}", command=lambda path=caminho_arquivo_completo: abrir_arquivo(path), relief="flat", anchor='w')
                    btn_arquivo.pack(fill=tk.X, padx=20)

    if not arquivos_encontrados:
        label_nenhum_doc = tk.Label(scrollable_frame, text="Nenhum documento encontrado.")
        label_nenhum_doc.pack(pady=20)

    # --- PAINEL DE ADMINISTRAÇÃO (APENAS NÍVEL 3) ---
    # Se o usuário for Nível 3, cria os botões que chamam as funções importadas.
    if nivel_acesso == "Nivel 3":
        admin_frame = tk.LabelFrame(janela, text="Ferramentas de Administração", padx=10, pady=10)
        admin_frame.pack(fill=tk.X, padx=10, pady=5)

        # Cada botão chama a função correspondente do 'utils_admin.py'
        btn_criar_usuario = tk.Button(admin_frame, text="Criar Novo Usuário", command=criar_novo_usuario_via_gui)
        btn_criar_usuario.pack(side=tk.LEFT, expand=True, padx=5)

        btn_adicionar_fotos = tk.Button(admin_frame, text="Adicionar Fotos", command=adicionar_mais_fotos)
        btn_adicionar_fotos.pack(side=tk.LEFT, expand=True, padx=5)

        btn_excluir_usuario = tk.Button(admin_frame, text="Excluir Usuário", command=excluir_usuario, bg="#E74C3C", fg="white")
        btn_excluir_usuario.pack(side=tk.LEFT, expand=True, padx=5)

    btn_fechar_total = tk.Button(janela, text="Sair do Sistema", command=janela.destroy)
    btn_fechar_total.pack(pady=10)

    janela.mainloop()

# Este bloco permite testar este arquivo de forma independente.
if __name__ == '__main__':
    # Mude o nível aqui ("Nivel 1", "Nivel 2" ou "Nivel 3") para testar as diferentes visualizações.
    mostrar_documentos("Nivel 3")