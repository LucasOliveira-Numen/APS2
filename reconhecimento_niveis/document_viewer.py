# document_viewer.py

import tkinter as tk
from tkinter import messagebox, scrolledtext
import os
import sys

# Obtém o caminho base do projeto
base_dir = os.path.dirname(os.path.abspath(__file__))

def mostrar_documentos(nivel_acesso):
    """
    Cria a interface gráfica para exibir documentos com base no nível de acesso.
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

    titulo = tk.Label(frame_principal, text=f"Bem-vindo! Documentos do Nível {nivel_acesso[-1]}", font=("Helvetica", 16))
    titulo.pack(pady=10)

    # Exibe os arquivos em um campo de texto rolável
    lista_arquivos = scrolledtext.ScrolledText(frame_principal, wrap=tk.WORD, width=60, height=15)
    lista_arquivos.pack(pady=10, fill=tk.BOTH, expand=True)

    arquivos_encontrados = False

    for pasta in pastas_acesso:
        caminho_pasta = os.path.join(documentos_dir, pasta)
        if os.path.exists(caminho_pasta):
            lista_arquivos.insert(tk.END, f"----------------- Pasta: {pasta.capitalize().replace('_', ' ')} -----------------\n\n")

            arquivos = [f for f in os.listdir(caminho_pasta) if os.path.isfile(os.path.join(caminho_pasta, f))]

            if arquivos:
                arquivos_encontrados = True
                for arquivo in arquivos:
                    lista_arquivos.insert(tk.END, f"  - {arquivo}\n")
            else:
                lista_arquivos.insert(tk.END, "    Nenhum arquivo encontrado.\n")

            lista_arquivos.insert(tk.END, "\n")
        else:
            lista_arquivos.insert(tk.END, f"Aviso: Pasta '{pasta}' não encontrada.\n\n")

    if not arquivos_encontrados:
        lista_arquivos.insert(tk.END, "Nenhum documento encontrado nas pastas acessíveis.")

    lista_arquivos.configure(state='disabled') # Impede a edição do texto

    btn_fechar = tk.Button(janela, text="Fechar", command=janela.destroy)
    btn_fechar.pack(pady=10)

    janela.mainloop()

if __name__ == '__main__':
    # Exemplo de como a função pode ser chamada diretamente para testes
    # Mude o nível para testar as permissões
    mostrar_documentos("Nivel 1")
