# app.py
# Este é o script principal do projeto de reconhecimento facial.
# Ele é responsável por treinar o modelo, abrir a webcam e
# realizar o reconhecimento em tempo real para conceder acesso.

import cv2
import os
import numpy as np
import sys
import unicodedata
import time

# --- Importações Centralizadas ---
# Importa a função de carregar JSON do nosso módulo de utilidades.
from utils_admin import carregar_dados_json
# Importa a função que cria a interface de documentos.
from document_viewer import mostrar_documentos

# --- Configurações Iniciais e Verificação de Arquivos ---
# Obtém o caminho absoluto do diretório onde o script está sendo executado.
base_dir = os.path.dirname(os.path.abspath(__file__))

# Caminho para o classificador de faces (Haar Cascade).
face_cascade_path = os.path.join(base_dir, 'haarcascade_frontalface_default.xml')
if not os.path.exists(face_cascade_path):
    print(f"Erro: O arquivo '{os.path.basename(face_cascade_path)}' não foi encontrado.")
    exit()

# Inicializa o classificador de faces.
classificador_de_faces = cv2.CascadeClassifier(face_cascade_path)

# Define os caminhos para as pastas e arquivos de dados.
diretorio_de_faces = os.path.join(base_dir, 'faces')
caminho_json_validacao = os.path.join(base_dir, 'validation.json')
caminho_json_dados_usuario = os.path.join(base_dir, 'userData.json')

# Limite de confiança para o reconhecimento. Valores menores são mais rigorosos.
LIMITE_CONFIANCA = 60

# --- Funções Auxiliares ---

def remover_acentos(texto):
    """
    Remove acentos de uma string para exibição correta no OpenCV.
    """
    try:
        nfkd_form = unicodedata.normalize('NFKD', str(texto))
        return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])
    except Exception:
        return str(texto)

# --- Etapa 1: Treinamento do Modelo ---

def obter_imagens_e_rotulos(ids_unicos):
    """
    Prepara as imagens e os rótulos (IDs) para o treinamento do modelo de reconhecimento.
    """
    faces = []
    ids = []
    mapeamento_ids_para_rotulo = {id_unico: i for i, id_unico in enumerate(ids_unicos)}

    print("Coletando dados de treinamento...")
    for id_unico in ids_unicos:
        diretorio_pessoa = os.path.join(diretorio_de_faces, id_unico)
        if not os.path.isdir(diretorio_pessoa):
            continue

        for nome_imagem in os.listdir(diretorio_pessoa):
            if nome_imagem.lower().endswith(('.jpg', '.png', '.jpeg')):
                caminho_imagem = os.path.join(diretorio_pessoa, nome_imagem)
                img = cv2.imread(caminho_imagem, cv2.IMREAD_GRAYSCALE)
                if img is None:
                    continue

                rostos_detectados = classificador_de_faces.detectMultiScale(img, 1.1, 5)
                for (x, y, w, h) in rostos_detectados:
                    roi = img[y:y+h, x:x+w]
                    roi_redimensionado = cv2.resize(roi, (200, 200), interpolation=cv2.INTER_LINEAR)
                    faces.append(roi_redimensionado)
                    ids.append(mapeamento_ids_para_rotulo[id_unico])

    if not faces:
        return None, None, None

    return np.array(faces), np.array(ids), list(mapeamento_ids_para_rotulo.keys())


def treinar_reconhecedor():
    """
    Orquestra o processo de treinamento do reconhecedor facial.
    """
    print("Iniciando o treinamento do modelo...")
    dados_usuario = carregar_dados_json(caminho_json_dados_usuario)
    if not dados_usuario:
        print("Erro: Nenhum dado de usuário encontrado.")
        return None, None

    ids_unicos = [dados['id'] for dados in dados_usuario.values()]
    if not ids_unicos:
        print("Erro: Nenhum ID de pessoa encontrado em userData.json.")
        return None, None

    faces, ids, ids_treinamento = obter_imagens_e_rotulos(ids_unicos)
    if faces is None:
        print("Erro: Nenhuma face encontrada para treinamento.")
        return None, None

    reconhecedor = cv2.face.LBPHFaceRecognizer_create()
    reconhecedor.train(faces, ids)
    print("Treinamento concluído com sucesso.")
    return reconhecedor, ids_treinamento

# --- Etapa 2: Reconhecimento em Tempo Real ---

def obter_nivel_e_status(cpf, dados_validacao):
    """
    Busca o nível de acesso de um usuário a partir do seu CPF.
    """
    for nivel, dados in dados_validacao.items():
        if cpf in dados.get('pessoas', []):
            return nivel, "Autorizado"
    return "Nível Desconhecido", "Não Autorizado"

def reconhecer_faces_webcam(reconhecedor, ids_treinamento, dados_validacao, dados_usuario):
    """
    Inicia a webcam e realiza o reconhecimento facial em tempo real.
    """
    captura_de_video = cv2.VideoCapture(0)
    if not captura_de_video.isOpened():
        print("Erro: Não foi possível acessar a webcam.")
        return

    print("Reconhecimento facial iniciado. Pressione 'q' para sair.")
    acesso_concedido_tempo = None

    while True:
        ret, frame = captura_de_video.read()
        if not ret: break

        frame_cinza = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rostos_detectados = classificador_de_faces.detectMultiScale(frame_cinza, 1.1, 5)

        if len(rostos_detectados) == 0:
            acesso_concedido_tempo = None

        for (x, y, w, h) in rostos_detectados:
            roi_cinza = frame_cinza[y:y+h, x:x+w]
            rotulo_id, confianca = reconhecedor.predict(roi_cinza)

            if confianca < LIMITE_CONFIANCA and rotulo_id < len(ids_treinamento):
                id_unico_encontrado = ids_treinamento[rotulo_id]
                cpf_encontrado = next((cpf for cpf, data in dados_usuario.items() if data['id'] == id_unico_encontrado), None)

                if cpf_encontrado:
                    nome_completo = dados_usuario[cpf_encontrado]['nome']
                    nivel, status = obter_nivel_e_status(cpf_encontrado, dados_validacao)

                    texto_nome = f"Nome: {remover_acentos(nome_completo)}"
                    cor_status = (0, 255, 0) if status == "Autorizado" else (0, 0, 255)
                    texto_status = f"Status: {status} ({remover_acentos(nivel)})"

                    cv2.rectangle(frame, (x, y), (x+w, y+h), cor_status, 2)
                    cv2.putText(frame, texto_nome, (x, y-45), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    cv2.putText(frame, texto_status, (x, y-20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, cor_status, 2)

                    if status == "Autorizado":
                        if acesso_concedido_tempo is None:
                            acesso_concedido_tempo = time.time()

                        tempo_decorrido = time.time() - acesso_concedido_tempo
                        if tempo_decorrido >= 3:
                            captura_de_video.release()
                            cv2.destroyAllWindows()
                            mostrar_documentos(nivel)
                            return
                        else:
                            tempo_restante = 3 - int(tempo_decorrido)
                            texto_timer = f"Acesso em {tempo_restante}s..."
                            cv2.putText(frame, texto_timer, (x, y+h+30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                else:
                    acesso_concedido_tempo = None
            else:
                acesso_concedido_tempo = None
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
                cv2.putText(frame, "Desconhecido", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

        cv2.imshow('Reconhecimento Facial', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    captura_de_video.release()
    cv2.destroyAllWindows()
    sys.exit()

# --- Bloco Principal de Execução ---

if __name__ == "__main__":
    # Carrega os dados dos usuários e de validação usando a função centralizada.
    dados_validacao = carregar_dados_json(caminho_json_validacao)
    dados_usuario = carregar_dados_json(caminho_json_dados_usuario)

    if dados_validacao is not None and dados_usuario is not None:
        reconhecedor, ids_treinamento = treinar_reconhecedor()
        if reconhecedor and ids_treinamento:
            reconhecer_faces_webcam(reconhecedor, ids_treinamento, dados_validacao, dados_usuario)
    else:
        print("Erro: Não foi possível carregar os arquivos de dados necessários (validation.json ou userData.json).")

    sys.exit()