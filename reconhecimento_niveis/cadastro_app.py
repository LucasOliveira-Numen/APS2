# cadastro_app.py
# Este script agora serve como um atalho para iniciar a interface de cadastro de novos usuários.
# Toda a lógica complexa de validação, captura de fotos e salvamento de dados
# foi movida para o módulo 'utils_admin.py' para ser reutilizada em todo o sistema.

import tkinter as tk
from tkinter import messagebox
import os

# --- Verificação de Dependências ---
# Verifica se o arquivo de utilidades existe antes de tentar importá-lo.
utils_path = os.path.join(os.path.dirname(__file__), 'utils_admin.py')
if not os.path.exists(utils_path):
    # Usamos uma janela raiz temporária para exibir o erro se o utils_admin não for encontrado.
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(
        "Erro Crítico",
        "O arquivo 'utils_admin.py' não foi encontrado. Este script não pode funcionar sem ele."
    )
    root.destroy()
    exit() # Encerra o script se a dependência principal estiver faltando.

# --- Importação da Função Centralizada ---
# Importamos apenas a função que precisamos do nosso módulo de utilidades.
from utils_admin import criar_novo_usuario_via_gui

# --- Execução Principal ---
if __name__ == "__main__":
    """
    Este bloco é executado quando o script 'cadastro_app.py' é rodado diretamente.
    Seu único propósito é chamar a função que cria a interface gráfica de cadastro.
    """
    # Cria uma janela raiz do tkinter, que é necessária para as caixas de diálogo funcionarem.
    janela_raiz = tk.Tk()
    # 'withdraw()' esconde a janela raiz, pois só precisamos das caixas de diálogo (simpledialog)
    # que a função importada irá criar.
    janela_raiz.withdraw()

    # Chama a função principal de cadastro importada do nosso módulo central.
    criar_novo_usuario_via_gui()

    # Destrói a janela raiz ao final do processo, encerrando o programa de forma limpa.
    janela_raiz.destroy()