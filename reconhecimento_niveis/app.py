# app.py
# Este é o script principal do projeto de reconhecimento facial.
# Ele é responsável por treinar o modelo, abrir a webcam e
# realizar o reconhecimento em tempo real para conceder acesso.

import cv2
import os
import json
import numpy as np
import sys
import unicodedata
import time
from document_viewer import mostrar_documentos

# --- Configurações Iniciais e Verificação de Arquivos ---
# Obtém o caminho absoluto do diretório onde o script está sendo executado.
# Isso garante que o projeto funcione em qualquer computador, independente da pasta.
base_dir = os.path.dirname(os.path.abspath(__file__))

# Caminho para o classificador de faces (Haar Cascade).
# Este arquivo é um modelo pré-treinado para detectar rostos.
face_cascade_path = os.path.join(base_dir, 'haarcascade_frontalface_default.xml')
# Verifica se o arquivo do classificador de faces existe. Se não, o programa é encerrado.
if not os.path.exists(face_cascade_path):
    print(f"Erro: O arquivo '{os.path.basename(face_cascade_path)}' não foi encontrado. Por favor, baixe-o e coloque-o na mesma pasta do app.py.")
    exit()

# Inicializa o classificador de faces, que será usado para encontrar rostos nas imagens.
classificador_de_faces = cv2.CascadeClassifier(face_cascade_path)

# Caminho para a pasta onde as imagens de rostos para treinamento estão armazenadas.
diretorio_de_faces = os.path.join(base_dir, 'faces')
# Caminho para os arquivos de dados (JSON) que armazenam as informações dos usuários.
caminho_json_validacao = os.path.join(base_dir, 'validation.json')
caminho_json_dados_usuario = os.path.join(base_dir, 'userData.json')

# Variável ajustável para a sensibilidade do reconhecimento.
# Valores mais baixos tornam o reconhecimento mais rigoroso (menos falsos positivos).
# O padrão 60 é um bom ponto de partida.
LIMITE_CONFIANCA = 60

# --- Funções Auxiliares para Manipulação de Dados e Texto ---
def remover_acentos(texto):
    """
    Remove acentos e caracteres especiais de uma string.
    Isso é feito para evitar problemas de exibição com a fonte padrão do OpenCV,
    que pode não suportar caracteres como "á", "ç", "ã", etc.
    """
    try:
        texto = str(texto)
        nfkd_form = unicodedata.normalize('NFKD', texto)
        apenas_ascii = nfkd_form.encode('ASCII', 'ignore')
        return apenas_ascii.decode('utf-8')
    except Exception as e:
        print(f"Aviso: Não foi possível remover acentos do texto. Erro: {e}")
        return texto

def carregar_dados_json(caminho_arquivo):
    """
    Carrega dados de um arquivo JSON.
    Esta função verifica se o arquivo existe e trata possíveis erros na leitura.
    """
    if not os.path.exists(caminho_arquivo):
        print(f"Erro: O arquivo {caminho_arquivo} não foi encontrado.")
        return None
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Erro ao carregar o arquivo JSON {caminho_arquivo}: {e}")
        return None

# --- Etapa 1: Treinamento do Modelo ---
def obter_imagens_e_rotulos(ids_unicos):
    """
    Percorre a pasta de faces, carrega as imagens de cada pessoa,
    detecta os rostos e retorna as faces e seus IDs para treinamento do modelo.
    """
    faces = []
    ids = []
    # Cria um mapeamento de IDs únicos (string) para IDs numéricos.
    # O reconhecedor de faces do OpenCV precisa de IDs numéricos para o treinamento.
    mapeamento_ids_para_rotulo = {id_unico: i for i, id_unico in enumerate(ids_unicos)}

    print("Coletando dados de treinamento...")
    for id_unico in ids_unicos:
        diretorio_pessoa = os.path.join(diretorio_de_faces, id_unico)
        if not os.path.isdir(diretorio_pessoa):
            print(f"Aviso: A pasta '{diretorio_pessoa}' não existe. Ignorando...")
            continue

        for nome_imagem in os.listdir(diretorio_pessoa):
            caminho_imagem = os.path.join(diretorio_pessoa, nome_imagem)

            # Verifica se o arquivo é uma imagem antes de tentar lê-lo.
            if nome_imagem.lower().endswith(('.jpg', '.png', '.jpeg')):
                img = cv2.imread(caminho_imagem, cv2.IMREAD_GRAYSCALE)

                # Se a imagem não puder ser lida, um aviso é exibido.
                if img is None:
                    print(f"Aviso: Não foi possível ler a imagem {caminho_imagem}. Ignorando...")
                    continue

                # Detecta rostos na imagem.
                rostos_detectados = classificador_de_faces.detectMultiScale(img, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

                # Se nenhum rosto for detectado, um aviso é exibido e a imagem é ignorada.
                if len(rostos_detectados) == 0:
                    print(f"Aviso: Nenhuma face detectada na imagem {caminho_imagem}. Ignorando...")
                    continue

                for (x, y, w, h) in rostos_detectados:
                    # Recorta a região de interesse (ROI) do rosto.
                    roi = img[y:y+h, x:x+w]
                    # Redimensiona a face para um tamanho padrão. Isso resolve o problema de
                    # "inhomogeneous shape" (forma não homogênea) durante o treinamento.
                    roi_redimensionado = cv2.resize(roi, (200, 200), interpolation=cv2.INTER_LINEAR)
                    faces.append(roi_redimensionado)
                    ids.append(mapeamento_ids_para_rotulo[id_unico])

    if not faces:
        print("Erro: Nenhuma face encontrada nas imagens de treinamento. Verifique a pasta 'faces'.")
        return None, None, None

    # Converte as listas para arrays do NumPy, que é o formato exigido pelo OpenCV.
    return np.array(faces), np.array(ids), list(mapeamento_ids_para_rotulo.keys())

def treinar_reconhecedor():
    """
    Função principal de treinamento.
    Carrega os dados de usuário, coleta as imagens e treina o modelo.
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
    if faces is None or ids is None:
        return None, None

    # Cria o modelo de reconhecimento facial.
    reconhecedor = cv2.face.LBPHFaceRecognizer_create()
    # Treina o modelo com as faces e os IDs coletados.
    reconhecedor.train(faces, ids)
    print("Treinamento concluído com sucesso.")
    return reconhecedor, ids_treinamento

# --- Etapa 2: Reconhecimento em Tempo Real ---
def obter_nivel_e_status(cpf, dados_validacao):
    """
    Busca o nível e o status de autorização de uma pessoa com base no CPF.
    """
    for nivel, dados in dados_validacao.items():
        if cpf in dados.get('pessoas', []):
            return nivel, "Autorizado"
    return "Nível Desconhecido", "Não Autorizado"

def reconhecer_faces_webcam(reconhecedor, ids_treinamento, dados_validacao, dados_usuario):
    """
    Abre a webcam, captura o vídeo e realiza o reconhecimento facial em tempo real.
    Exibe o nome, nível e status de autorização sobre o rosto detectado.
    """
    captura_de_video = cv2.VideoCapture(0)

    if not captura_de_video.isOpened():
        print("Erro: Não foi possível acessar a webcam. Verifique se a câmera está conectada e não está sendo usada por outro aplicativo.")
        return

    print("Reconhecimento facial iniciado. Pressione 'q' para sair.")

    # Variável para controlar o temporizador de acesso
    acesso_concedido_tempo = None

    while True:
        ret, frame = captura_de_video.read()
        if not ret:
            break

        frame_cinza = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        rostos_detectados = classificador_de_faces.detectMultiScale(frame_cinza, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        if len(rostos_detectados) == 0:
            acesso_concedido_tempo = None # Reseta o temporizador se a face sumir

        for (x, y, w, h) in rostos_detectados:
            roi_cinza = frame_cinza[y:y+h, x:x+w]

            # O modelo faz uma predição no rosto detectado.
            rotulo_id, confianca = reconhecedor.predict(roi_cinza)

            # Verifica se a confiança é alta o suficiente para um reconhecimento.
            # Um valor menor indica maior semelhança.
            if confianca < LIMITE_CONFIANCA and rotulo_id < len(ids_treinamento):
                id_unico_encontrado = ids_treinamento[rotulo_id]

                cpf_encontrado = None
                nome_completo = "Desconhecido"

                # Encontra o CPF e nome completo a partir do ID único no userData
                for cpf_user, dados in dados_usuario.items():
                    if dados['id'] == id_unico_encontrado:
                        cpf_encontrado = cpf_user
                        nome_completo = dados['nome']
                        break

                if cpf_encontrado:
                    nivel, status = obter_nivel_e_status(cpf_encontrado, dados_validacao)
                else:
                    nivel = "N/A"
                    status = "Não Autorizado"

                # Formata a string de status e nível
                if status == "Autorizado":
                    texto_status = f"Autorizado: {remover_acentos(nivel)}"
                else:
                    texto_status = "Nao Autorizado"

                # Formata o nome para exibição sem acentos
                texto_nome = f"Nome: {remover_acentos(nome_completo)}"

                cor_status = (0, 255, 0) if status == "Autorizado" else (0, 0, 255)

                cv2.rectangle(frame, (x, y), (x+w, y+h), cor_status, 2)
                cv2.putText(frame, texto_nome, (x, y-45), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                cv2.putText(frame, texto_status, (x, y-25), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

                # Se o usuário for autorizado, inicia ou continua o temporizador
                if status == "Autorizado":
                    if acesso_concedido_tempo is None:
                        acesso_concedido_tempo = time.time()

                    tempo_decorrido = time.time() - acesso_concedido_tempo
                    tempo_restante = 3 - int(tempo_decorrido)

                    if tempo_restante > 0:
                        texto_timer = f"Abrindo documentos em {tempo_restante}s..."
                        cv2.putText(frame, texto_timer, (x, y+h+20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    else:
                        captura_de_video.release()
                        cv2.destroyAllWindows()
                        mostrar_documentos(nivel)
                        return # Encerra a função após abrir a nova janela
            else:
                acesso_concedido_tempo = None # Reseta o temporizador se for um rosto desconhecido
                texto_desconhecido = "Desconhecido"
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
                cv2.putText(frame, texto_desconhecido, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

        cv2.imshow('Reconhecimento Facial', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    captura_de_video.release()
    cv2.destroyAllWindows()
    sys.exit() # Garante que o script se encerra corretamente

if __name__ == "__main__":
    dados_validacao = carregar_dados_json(caminho_json_validacao)
    dados_usuario = carregar_dados_json(caminho_json_dados_usuario)

    if dados_validacao and dados_usuario:
        reconhecedor, ids_treinamento = treinar_reconhecedor()
        if reconhecedor and ids_treinamento:
            reconhecer_faces_webcam(reconhecedor, ids_treinamento, dados_validacao, dados_usuario)
            sys.exit()
    else:
        print("Erro: Os arquivos de dados (validation.json ou userData.json) não puderam ser carregados.")
        sys.exit()
