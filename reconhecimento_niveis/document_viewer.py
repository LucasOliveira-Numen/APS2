# Interface Gráfica para Visualização de Documentos e Administração do Sistema
#
# Este módulo implementa a interface gráfica principal do sistema de reconhecimento
# facial, fornecendo acesso a documentos baseado em níveis de autorização e
# ferramentas administrativas para usuários de Nível 3.
#
# Funcionalidades:
# - Visualização de documentos por nível de acesso
# - Interface administrativa para gerenciamento de usuários
# - Design moderno e responsivo
# - Controle de acesso baseado em níveis

import tkinter as tk
from tkinter import scrolledtext, ttk
import os

# --- Importação das Funções Administrativas ---
# Importação das funções centralizadas do módulo de utilitários
from utils_admin import criar_novo_usuario_via_gui, adicionar_mais_fotos, excluir_usuario, gerenciar_fotos_usuario

# --- Configuração de Caminhos ---
base_dir = os.path.dirname(os.path.abspath(__file__))

# --- Funções Específicas da Interface ---

def abrir_arquivo(caminho_arquivo):
    """
    Abre uma janela modal para exibir o conteúdo de um arquivo de texto.

    Esta função cria uma interface gráfica para visualização de documentos,
    implementando um design moderno com barra de título estilizada e
    área de conteúdo com scroll para arquivos longos.

    Args:
        caminho_arquivo (str): Caminho completo para o arquivo a ser exibido
    """
    janela_arquivo = tk.Toplevel()
    janela_arquivo.title(f"📄 {os.path.basename(caminho_arquivo)}")
    janela_arquivo.geometry("700x500")
    janela_arquivo.configure(bg='#f0f0f0')

    # Centralizar a janela
    janela_arquivo.transient()
    janela_arquivo.grab_set()

    # Frame principal com estilo
    main_frame = tk.Frame(janela_arquivo, bg='#f0f0f0', padx=20, pady=20)
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Título do arquivo
    titulo_frame = tk.Frame(main_frame, bg='#2c3e50', height=50)
    titulo_frame.pack(fill=tk.X, pady=(0, 15))
    titulo_frame.pack_propagate(False)

    titulo_label = tk.Label(titulo_frame, text=f"📄 {os.path.basename(caminho_arquivo)}",
                           font=('Segoe UI', 14, 'bold'), fg='white', bg='#2c3e50')
    titulo_label.pack(expand=True)

    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            conteudo = f.read()
    except Exception as e:
        conteudo = f"❌ Erro ao ler o arquivo: {e}"

    # Área de texto com estilo melhorado
    texto_frame = tk.Frame(main_frame, bg='white', relief='sunken', bd=2)
    texto_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

    texto_arquivo = scrolledtext.ScrolledText(texto_frame, wrap=tk.WORD, padx=15, pady=15,
                                            font=('Consolas', 10), bg='white', fg='#2c3e50',
                                            selectbackground='#3498db', selectforeground='white',
                                            relief='flat', bd=0)
    texto_arquivo.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    texto_arquivo.insert(tk.END, conteudo)
    texto_arquivo.configure(state='disabled') # Bloqueia a edição do texto

    # Botão de fechar com estilo
    btn_fechar = tk.Button(main_frame, text="✖ Fechar", command=janela_arquivo.destroy,
                          font=('Segoe UI', 10, 'bold'), bg='#e74c3c', fg='white',
                          relief='flat', bd=0, padx=20, pady=8,
                          activebackground='#c0392b', activeforeground='white',
                          cursor='hand2')
    btn_fechar.pack(pady=10)


def mostrar_documentos(nivel_acesso):
    """
    Cria a interface principal do sistema de visualização de documentos.

    Esta função implementa a interface gráfica principal que exibe documentos
    baseados no nível de acesso do usuário e fornece ferramentas administrativas
    para usuários de Nível 3. A interface utiliza design moderno com cores
    diferenciadas por nível de acesso.

    Args:
        nivel_acesso (str): Nível de acesso do usuário ("Nivel 1", "Nivel 2", "Nivel 3")
    """
    janela = tk.Tk()
    janela.title("🔐 Sistema de Controle de Acesso - Visualizador de Documentos")
    janela.geometry("800x600")
    janela.configure(bg='#ecf0f1')
    janela.resizable(True, True)

    # Centralizar a janela na tela
    janela.update_idletasks()
    x = (janela.winfo_screenwidth() // 2) - (800 // 2)
    y = (janela.winfo_screenheight() // 2) - (600 // 2)
    janela.geometry(f"800x600+{x}+{y}")

    documentos_dir = os.path.join(base_dir, 'documentos')
    if not os.path.exists(documentos_dir):
        tk.messagebox.showerror("❌ Erro de Arquivo", "Diretório 'documentos' não encontrado.")
        janela.destroy()
        return

    # Mapeamento de níveis para subpastas de documentos
    mapa_niveis = {
        "Nivel 1": ["nivel_1"],
        "Nivel 2": ["nivel_1", "nivel_2"],
        "Nivel 3": ["nivel_1", "nivel_2", "nivel_3"]
    }
    pastas_acesso = mapa_niveis.get(nivel_acesso, [])

    # Frame principal com gradiente visual
    frame_principal = tk.Frame(janela, bg='#ecf0f1', padx=20, pady=20)
    frame_principal.pack(fill=tk.BOTH, expand=True)

    # Header com título e ícone
    header_frame = tk.Frame(frame_principal, bg='#2c3e50', height=80, relief='flat', bd=0)
    header_frame.pack(fill=tk.X, pady=(0, 20))
    header_frame.pack_propagate(False)

    # Título personalizado para cada nível com ícones
    titulos = {
        "Nivel 1": "👤 Bem-vindo!",
        "Nivel 2": "👔 Bem-vindo Diretor(a)!",
        "Nivel 3": "👑 Bem-vindo Ministro(a)!"
    }

    # Cores para cada nível
    cores_nivel = {
        "Nivel 1": "#27ae60",
        "Nivel 2": "#f39c12",
        "Nivel 3": "#8e44ad"
    }

    titulo = tk.Label(header_frame, text=titulos.get(nivel_acesso, "👤 Bem-vindo!"),
                     font=("Segoe UI", 18, "bold"), fg='white', bg='#2c3e50')
    titulo.pack(expand=True)

    # Subtítulo com nível de acesso
    subtitulo = tk.Label(header_frame, text=f"Nível de Acesso: {nivel_acesso}",
                        font=("Segoe UI", 12), fg=cores_nivel.get(nivel_acesso, "#3498db"), bg='#2c3e50')
    subtitulo.pack()

    # Frame para área de documentos
    docs_frame = tk.Frame(frame_principal, bg='white', relief='sunken', bd=2)
    docs_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

    # Título da seção de documentos
    docs_title = tk.Label(docs_frame, text="📁 Documentos Disponíveis",
                         font=("Segoe UI", 14, "bold"), fg='#2c3e50', bg='white')
    docs_title.pack(pady=(15, 10))

    # Canvas para exibir a lista de arquivos com barra de rolagem
    canvas = tk.Canvas(docs_frame, bg='white', highlightthickness=0)
    scrollbar = ttk.Scrollbar(docs_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg='white')

    scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(15, 5), pady=(0, 15))
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=(0, 15))

    # Loop para listar os arquivos das pastas permitidas
    arquivos_encontrados = False
    for pasta in pastas_acesso:
        caminho_pasta = os.path.join(documentos_dir, pasta)
        if os.path.exists(caminho_pasta):
            # Frame para cada pasta
            pasta_frame = tk.Frame(scrollable_frame, bg='#f8f9fa', relief='raised', bd=1)
            pasta_frame.pack(fill=tk.X, padx=10, pady=5)

            # Ícone e nome da pasta
            pasta_icon = "📂" if pasta == "nivel_1" else "📋" if pasta == "nivel_2" else "🔒"
            label_pasta = tk.Label(pasta_frame, text=f"{pasta_icon} {pasta.replace('_', ' ').title()}",
                                 font=("Segoe UI", 12, "bold"), fg='#2c3e50', bg='#f8f9fa')
            label_pasta.pack(pady=(10, 5), anchor='w', padx=15)

            arquivos = [f for f in os.listdir(caminho_pasta) if os.path.isfile(os.path.join(caminho_pasta, f))]
            if arquivos:
                arquivos_encontrados = True
                for arquivo in arquivos:
                    caminho_arquivo_completo = os.path.join(caminho_pasta, arquivo)
                    btn_arquivo = tk.Button(pasta_frame, text=f"📄 {arquivo}",
                                          command=lambda path=caminho_arquivo_completo: abrir_arquivo(path),
                                          relief="flat", anchor='w', font=("Segoe UI", 10),
                                          bg='white', fg='#2c3e50', bd=1,
                                          activebackground='#3498db', activeforeground='white',
                                          cursor='hand2', padx=15, pady=5)
                    btn_arquivo.pack(fill=tk.X, padx=20, pady=2)

    if not arquivos_encontrados:
        empty_frame = tk.Frame(scrollable_frame, bg='white')
        empty_frame.pack(expand=True, fill=tk.BOTH)

        label_nenhum_doc = tk.Label(empty_frame, text="📭 Nenhum documento encontrado",
                                   font=("Segoe UI", 12), fg='#7f8c8d', bg='white')
        label_nenhum_doc.pack(expand=True)

    # --- PAINEL DE ADMINISTRAÇÃO (APENAS NÍVEL 3) ---
    # Se o usuário for Nível 3, cria os botões que chamam as funções importadas.
    if nivel_acesso == "Nivel 3":
        admin_frame = tk.LabelFrame(frame_principal, text="⚙️ Ferramentas de Administração",
                                   font=("Segoe UI", 12, "bold"), fg='#2c3e50', bg='#ecf0f1',
                                   relief='raised', bd=2, padx=15, pady=15)
        admin_frame.pack(fill=tk.X, pady=(0, 15))

        # Frame para os botões de administração
        buttons_frame = tk.Frame(admin_frame, bg='#ecf0f1')
        buttons_frame.pack(fill=tk.X)

        # Cada botão chama a função correspondente do 'utils_admin.py'
        btn_criar_usuario = tk.Button(buttons_frame, text="👤 Criar Novo Usuário",
                                     command=criar_novo_usuario_via_gui,
                                     font=("Segoe UI", 10, "bold"), bg='#27ae60', fg='white',
                                     relief='flat', bd=0, padx=15, pady=10,
                                     activebackground='#229954', activeforeground='white',
                                     cursor='hand2')
        btn_criar_usuario.pack(side=tk.LEFT, expand=True, padx=5)

        btn_adicionar_fotos = tk.Button(buttons_frame, text="📷 Adicionar Fotos",
                                       command=adicionar_mais_fotos,
                                       font=("Segoe UI", 10, "bold"), bg='#3498db', fg='white',
                                       relief='flat', bd=0, padx=15, pady=10,
                                       activebackground='#2980b9', activeforeground='white',
                                       cursor='hand2')
        btn_adicionar_fotos.pack(side=tk.LEFT, expand=True, padx=5)

        btn_gerenciar_fotos = tk.Button(buttons_frame, text="⚙️ Gerenciar Fotos",
                                       command=gerenciar_fotos_usuario,
                                       font=("Segoe UI", 10, "bold"), bg='#f39c12', fg='white',
                                       relief='flat', bd=0, padx=15, pady=10,
                                       activebackground='#e67e22', activeforeground='white',
                                       cursor='hand2')
        btn_gerenciar_fotos.pack(side=tk.LEFT, expand=True, padx=5)

        btn_excluir_usuario = tk.Button(buttons_frame, text="🗑️ Excluir Usuário",
                                       command=excluir_usuario,
                                       font=("Segoe UI", 10, "bold"), bg='#e74c3c', fg='white',
                                       relief='flat', bd=0, padx=15, pady=10,
                                       activebackground='#c0392b', activeforeground='white',
                                       cursor='hand2')
        btn_excluir_usuario.pack(side=tk.LEFT, expand=True, padx=5)

    # Botão de sair com estilo
    btn_fechar_total = tk.Button(frame_principal, text="🚪 Sair do Sistema",
                                command=janela.destroy,
                                font=("Segoe UI", 12, "bold"), bg='#95a5a6', fg='white',
                                relief='flat', bd=0, padx=25, pady=12,
                                activebackground='#7f8c8d', activeforeground='white',
                                cursor='hand2')
    btn_fechar_total.pack(pady=10)

    janela.mainloop()

# Este bloco permite testar este arquivo de forma independente.
if __name__ == '__main__':
    # Mude o nível aqui ("Nivel 1", "Nivel 2" ou "Nivel 3") para testar as diferentes visualizações.
    mostrar_documentos("Nivel 3")