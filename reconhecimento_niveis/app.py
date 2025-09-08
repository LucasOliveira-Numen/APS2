# app.py

import cv2
import os
import json
import numpy as np
import sys
import unicodedata
import time
from document_viewer import mostrar_documentos

# Obtenha o caminho absoluto do diretório onde o script está
base_dir = os.path.dirname(os.path.abspath(__file__))

# Configurações do projeto
# Caminho para o classificador de faces (Haar Cascade)
face_cascade_path = os.path.join(base_dir, 'haarcascade_frontalface_default.xml')
# Verifica se o arquivo do classificador existe
if not os.path.exists(face_cascade_path):
    print(f"Erro: O arquivo '{os.path.basename(face_cascade_path)}' não foi encontrado. Por favor, baixe-o e coloque-o na mesma pasta do app.py.")
    exit()

# Inicializa o classificador de faces
classificador_de_faces = cv2.CascadeClassifier(face_cascade_path)

# Caminho para a pasta de imagens de rostos
diretorio_de_faces = os.path.join(base_dir, 'faces')
# Caminho para os arquivos de dados
caminho_json_validacao = os.path.join(base_dir, 'validation.json')
caminho_json_dados_usuario = os.path.join(base_dir, 'userData.json')

# Variável ajustável para a sensibilidade do reconhecimento
# Valores mais baixos tornam o reconhecimento mais rigoroso (menos falsos positivos).
LIMITE_CONFIANCA = 60

def remover_acentos(texto):
    """
    Remove acentos e caracteres especiais de uma string para evitar problemas
    de exibição com a fonte padrão do OpenCV.
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
    Retorna o dicionário de dados ou None em caso de erro.
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

def obter_imagens_e_rotulos(ids_unicos):
    """
    Percorre a pasta de faces, carrega as imagens de cada pessoa,
    detecta os rostos e retorna as faces e seus IDs para treinamento do modelo.
    """
    faces = []
    ids = []
    # Mapeia os IDs únicos (nomes das pastas) para IDs numéricos para o treinamento do reconhecedor
    mapeamento_ids_para_rotulo = {id_unico: i for i, id_unico in enumerate(ids_unicos)}

    print("Coletando dados de treinamento...")
    for id_unico in ids_unicos:
        diretorio_pessoa = os.path.join(diretorio_de_faces, id_unico)
        if not os.path.isdir(diretorio_pessoa):
            print(f"Aviso: A pasta '{diretorio_pessoa}' não existe. Ignorando...")
            continue

        for nome_imagem in os.listdir(diretorio_pessoa):
            caminho_imagem = os.path.join(diretorio_pessoa, nome_imagem)

            if nome_imagem.lower().endswith(('.jpg', '.png', '.jpeg')):
                img = cv2.imread(caminho_imagem, cv2.IMREAD_GRAYSCALE)

                if img is None:
                    print(f"Aviso: Não foi possível ler a imagem {caminho_imagem}. Ignorando...")
                    continue

                rostos_detectados = classificador_de_faces.detectMultiScale(img, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

                if len(rostos_detectados) == 0:
                    print(f"Aviso: Nenhuma face detectada na imagem {caminho_imagem}. Ignorando...")
                    continue

                for (x, y, w, h) in rostos_detectados:
                    roi = img[y:y+h, x:x+w]
                    roi_redimensionado = cv2.resize(roi, (200, 200), interpolation=cv2.INTER_LINEAR)
                    faces.append(roi_redimensionado)
                    ids.append(mapeamento_ids_para_rotulo[id_unico])

    if not faces:
        print("Erro: Nenhuma face encontrada nas imagens de treinamento. Verifique a pasta 'faces'.")
        return None, None, None

    return np.array(faces), np.array(ids), list(mapeamento_ids_para_rotulo.keys())

def treinar_reconhecedor():
    """
    Treina o modelo de reconhecimento facial.
    Retorna o reconhecedor treinado e a lista de IDs únicos correspondente aos IDs.
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

    reconhecedor = cv2.face.LBPHFaceRecognizer_create()
    reconhecedor.train(faces, ids)
    print("Treinamento concluído com sucesso.")
    return reconhecedor, ids_treinamento

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

            rotulo_id, confianca = reconhecedor.predict(roi_cinza)

            # Condição de confiança para identificar a pessoa
            # Agora usa a variável ajustável LIMITE_CONFIANCA
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
