# app.py
# Script Principal do Sistema de Reconhecimento Facial
#
# Fluxo de Execução:
# 1. Tenta carregar um modelo de reconhecimento facial previamente treinado.
# 2. Se não encontrar, ele treina um novo modelo com base nas fotos na pasta 'faces'.
# 3. Inicia a webcam para o reconhecimento em tempo real.
# 4. Ao reconhecer um rosto autorizado, concede acesso e abre o visualizador de documentos.

# --- Importação das Bibliotecas ---
import cv2                      # OpenCV: A principal biblioteca para visão computacional.
import os                       # Para interagir com o sistema operacional (ler arquivos e pastas).
import numpy as np              # Usada para trabalhar com arrays de imagens de forma eficiente.
import sys                      # Para interações com o sistema, como encerrar o programa.
import unicodedata              # Usado para normalizar texto e remover acentos.
import time                     # Para controlar o tempo, como o timer de 3 segundos para acesso.
import json                     # Necessário para salvar o mapa de IDs do modelo.

# --- Importações dos Módulos do Projeto ---
from utils_admin import carregar_dados_json, salvar_dados_json  # Funções centralizadas para manipular JSON.
from document_viewer import mostrar_documentos                # Função que cria a interface de visualização.

# --- Configurações Iniciais e Verificação de Arquivos ---
# Define o diretório base do projeto de forma dinâmica.
base_dir = os.path.dirname(os.path.abspath(__file__))

# Caminho para o classificador de faces (Haar Cascade).
face_cascade_path = os.path.join(base_dir, 'haarcascade_frontalface_default.xml')
if not os.path.exists(face_cascade_path):
    print(f"Erro: O arquivo '{os.path.basename(face_cascade_path)}' não foi encontrado. O programa não pode continuar.")
    exit()
classificador_de_faces = cv2.CascadeClassifier(face_cascade_path)

# Caminhos para as pastas e arquivos de dados, agora apontando para as subpastas organizadas.
diretorio_de_faces = os.path.join(base_dir, 'faces')
diretorio_modelo = os.path.join(base_dir, 'Modelo_Treinamento')
diretorio_usuarios = os.path.join(base_dir, 'Usuarios_Cadastrados')

caminho_modelo_salvo = os.path.join(diretorio_modelo, 'modelo_lbph.yml')
caminho_mapa_ids = os.path.join(diretorio_modelo, 'mapeamento_ids.json')
caminho_json_validacao = os.path.join(diretorio_usuarios, 'validation.json')
caminho_json_dados_usuario = os.path.join(diretorio_usuarios, 'userData.json')

# Limite de confiança: quanto MENOR o valor, mais CONFIANTE o sistema está.
# Pense nisso como a "distância" entre o rosto visto e os rostos no banco de dados.
# Distância pequena = rostos muito parecidos.
LIMITE_CONFIANCA = 60

# --- Funções Auxiliares ---
def remover_acentos(texto):
    """
    Remove acentos de uma string.
    O OpenCV pode ter problemas para exibir caracteres não-ASCII (com acentos) usando cv2.putText.
    Esta função normaliza o texto para garantir que ele seja exibido sem erros.
    """
    try:
        nfkd_form = unicodedata.normalize('NFKD', str(texto))
        return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])
    except Exception:
        return str(texto)

# --- Etapa 1: Treinamento do Modelo ---

def obter_imagens_e_rotulos(ids_unicos):
    """
    Prepara os dados para o treinamento.
    - Percorre a pasta 'faces'.
    - Para cada usuário, lê suas imagens.
    - Detecta o rosto em cada imagem.
    - Associa cada rosto detectado a um rótulo numérico (0, 1, 2...).
    """
    faces, ids = [], []
    # O treinador precisa de rótulos numéricos (0, 1, 2...). Este dicionário mapeia
    # o ID de texto único de cada usuário para um número inteiro.
    mapeamento_ids_para_rotulo = {id_unico: i for i, id_unico in enumerate(ids_unicos)}

    print("Coletando imagens e rótulos para o treinamento...")
    for id_unico in ids_unicos:
        diretorio_pessoa = os.path.join(diretorio_de_faces, id_unico)
        if not os.path.isdir(diretorio_pessoa): continue

        for nome_imagem in os.listdir(diretorio_pessoa):
            if nome_imagem.lower().endswith(('.jpg', '.png', '.jpeg')):
                caminho_imagem = os.path.join(diretorio_pessoa, nome_imagem)
                # Carrega a imagem em escala de cinza, formato necessário para o treinamento do LBPH.
                img = cv2.imread(caminho_imagem, cv2.IMREAD_GRAYSCALE)
                if img is None: continue

                # Detecta rostos na imagem de treinamento para garantir que apenas a face seja usada.
                rostos_detectados = classificador_de_faces.detectMultiScale(img, 1.1, 5)
                for (x, y, w, h) in rostos_detectados:
                    # Recorta a região de interesse (Region of Interest - ROI), que é o rosto.
                    roi = img[y:y+h, x:x+w]
                    # Redimensiona para um tamanho padrão (200x200 pixels) para garantir consistência no treinamento.
                    roi_redimensionado = cv2.resize(roi, (200, 200), interpolation=cv2.INTER_LINEAR)
                    faces.append(roi_redimensionado)
                    ids.append(mapeamento_ids_para_rotulo[id_unico])

    if not faces: return None, None, None
    # Converte as listas para arrays numpy, que é o formato de dados que o OpenCV utiliza.
    return np.array(faces), np.array(ids), list(mapeamento_ids_para_rotulo.keys())

def treinar_e_salvar_modelo():
    """
    Orquestra o processo de treinamento e salva o modelo e o mapa de IDs no disco.
    """
    print("Iniciando o treinamento do modelo...")
    dados_usuario = carregar_dados_json(caminho_json_dados_usuario)
    if not dados_usuario:
        print("Erro: Nenhum dado de usuário encontrado para treinar.")
        return None, None

    ids_unicos = [dados['id'] for dados in dados_usuario.values()]
    if not ids_unicos:
        print("Erro: Nenhum ID de pessoa encontrado para treinar.")
        return None, None

    faces, ids, ids_treinamento = obter_imagens_e_rotulos(ids_unicos)
    if faces is None:
        print("Erro: Nenhuma face encontrada nas pastas para treinamento.")
        return None, None

    # Cria uma instância do reconhecedor LBPH (Local Binary Patterns Histograms).
    reconhecedor = cv2.face.LBPHFaceRecognizer_create()
    # Treina o modelo com as faces e seus respectivos rótulos numéricos.
    reconhecedor.train(faces, ids)

    # Garante que a pasta 'Modelo_Treinamento' exista antes de tentar salvar.
    if not os.path.exists(diretorio_modelo):
        os.makedirs(diretorio_modelo)

    # Salva o estado treinado do reconhecedor em um arquivo .yml.
    reconhecedor.write(caminho_modelo_salvo)
    # Salva a lista de IDs na ordem exata em que foram treinados.
    # Isso é crucial para depois sabermos que o rótulo '0' corresponde ao primeiro ID da lista, etc.
    salvar_dados_json(caminho_mapa_ids, {"ids_treinamento": ids_treinamento})

    print("Treinamento concluído e modelo salvo com sucesso.")
    return reconhecedor, ids_treinamento

# --- Etapa 2: Reconhecimento em Tempo Real ---

def obter_nivel_e_status(cpf, dados_validacao):
    """Verifica no arquivo validation.json qual o nível de acesso de um determinado CPF."""
    for nivel, dados in dados_validacao.items():
        if cpf in dados.get('pessoas', []):
            return nivel, "Autorizado"
    return "Nível Desconhecido", "Não Autorizado"

def reconhecer_faces_webcam(reconhecedor, ids_treinamento, dados_validacao, dados_usuario):
    """
    Função principal que abre a webcam, detecta e reconhece faces em tempo real.
    """
    captura_de_video = cv2.VideoCapture(0)
    if not captura_de_video.isOpened():
        print("Erro: Não foi possível acessar a webcam.")
        return

    print("Reconhecimento facial iniciado. Pressione 'q' para sair.")
    acesso_concedido_tempo = None # Variável para controlar o timer de acesso.

    # Loop infinito que lê cada frame da webcam.
    while True:
        ret, frame = captura_de_video.read()
        if not ret: break

        frame_cinza = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rostos_detectados = classificador_de_faces.detectMultiScale(frame_cinza, 1.1, 5)

        # Se nenhum rosto for detectado no frame, reseta o timer.
        if len(rostos_detectados) == 0:
            acesso_concedido_tempo = None

        for (x, y, w, h) in rostos_detectados:
            roi_cinza = frame_cinza[y:y+h, x:x+w]
            # O modelo prevê a identidade do rosto. Retorna o rótulo (ex: 0) e a confiança.
            rotulo_id, confianca = reconhecedor.predict(roi_cinza)

            # Se a confiança for boa (menor que o limite) e o rótulo for válido...
            if confianca < LIMITE_CONFIANCA and rotulo_id < len(ids_treinamento):
                # ...traduz o rótulo numérico de volta para o ID único do usuário.
                id_unico_encontrado = ids_treinamento[rotulo_id]
                # ...e encontra o CPF associado a esse ID único.
                cpf_encontrado = next((cpf for cpf, data in dados_usuario.items() if data['id'] == id_unico_encontrado), None)

                if cpf_encontrado:
                    # Com o CPF, busca o nome e o nível de acesso.
                    nome_completo = dados_usuario[cpf_encontrado]['nome']
                    nivel, status = obter_nivel_e_status(cpf_encontrado, dados_validacao)

                    # Prepara os textos para serem exibidos no vídeo.
                    texto_nome = f"Nome: {remover_acentos(nome_completo)}"
                    cor_status = (0, 255, 0) if status == "Autorizado" else (0, 0, 255) # Verde ou vermelho
                    texto_status = f"Status: {status} ({remover_acentos(nivel)})"

                    # Desenha o retângulo e os textos na tela.
                    cv2.rectangle(frame, (x, y), (x+w, y+h), cor_status, 2)
                    cv2.putText(frame, texto_nome, (x, y-45), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    cv2.putText(frame, texto_status, (x, y-20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, cor_status, 2)

                    # Lógica do timer de 3 segundos para conceder acesso.
                    if status == "Autorizado":
                        if acesso_concedido_tempo is None:
                            acesso_concedido_tempo = time.time() # Inicia o timer na primeira detecção.

                        if time.time() - acesso_concedido_tempo >= 3:
                            captura_de_video.release()
                            cv2.destroyAllWindows()
                            mostrar_documentos(nivel) # Abre a interface de documentos.
                            return
                        else:
                            tempo_restante = 3 - int(time.time() - acesso_concedido_tempo)
                            texto_timer = f"Acesso em {tempo_restante}s..."
                            cv2.putText(frame, texto_timer, (x, y+h+30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                else:
                    acesso_concedido_tempo = None # Reseta se o ID não for encontrado (caso raro).
            else:
                acesso_concedido_tempo = None # Reseta o timer se o rosto for desconhecido.
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
                cv2.putText(frame, "Desconhecido", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

        cv2.imshow('Reconhecimento Facial', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break # Encerra o loop se 'q' for pressionado.

    captura_de_video.release()
    cv2.destroyAllWindows()
    sys.exit()

# --- Bloco Principal de Execução ---
# Este bloco é o ponto de entrada quando o script é executado.
if __name__ == "__main__":
    dados_validacao = carregar_dados_json(caminho_json_validacao)
    dados_usuario = carregar_dados_json(caminho_json_dados_usuario)

    if not dados_usuario:
        print("Nenhum usuário cadastrado. Execute o `cadastro_app.py` para adicionar usuários.")
        sys.exit()

    # --- LÓGICA DE CARREGAMENTO OU TREINAMENTO ---
    # Verifica se os arquivos de modelo já existem.
    if os.path.exists(caminho_modelo_salvo) and os.path.exists(caminho_mapa_ids):
        # Se existem, carrega o modelo em vez de treinar.
        print("Carregando modelo de reconhecimento facial existente...")
        reconhecedor = cv2.face.LBPHFaceRecognizer_create()
        reconhecedor.read(caminho_modelo_salvo)
        mapa_ids = carregar_dados_json(caminho_mapa_ids)
        ids_treinamento = mapa_ids.get("ids_treinamento")
        print("Modelo carregado com sucesso.")
    else:
        # Se não existem, executa o treinamento completo e salva os arquivos.
        print("Nenhum modelo treinado encontrado. Iniciando novo treinamento...")
        reconhecedor, ids_treinamento = treinar_e_salvar_modelo()

    # Inicia o reconhecimento com o modelo (seja ele carregado ou recém-treinado).
    if reconhecedor and ids_treinamento:
        reconhecer_faces_webcam(reconhecedor, ids_treinamento, dados_validacao, dados_usuario)
    else:
        print("Falha ao carregar ou treinar o modelo. Encerrando o programa.")

    sys.exit()