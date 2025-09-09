# app.py
# (versão final, comentada e com pastas organizadas)

# --- Importação das Bibliotecas ---
import cv2
import os
import numpy as np
import sys
import unicodedata
import time
import json # Necessário para salvar o mapa de IDs

# --- Importações dos Módulos do Projeto ---
from utils_admin import carregar_dados_json, salvar_dados_json
from document_viewer import mostrar_documentos

# --- Configurações Iniciais e Verificação de Arquivos ---
base_dir = os.path.dirname(os.path.abspath(__file__))
face_cascade_path = os.path.join(base_dir, 'haarcascade_frontalface_default.xml')
if not os.path.exists(face_cascade_path):
    print(f"Erro: O arquivo '{os.path.basename(face_cascade_path)}' não foi encontrado.")
    exit()
classificador_de_faces = cv2.CascadeClassifier(face_cascade_path)

# --- Caminhos Atualizados ---
diretorio_de_faces = os.path.join(base_dir, 'faces')
diretorio_modelo = os.path.join(base_dir, 'Modelo_Treinamento')
diretorio_usuarios = os.path.join(base_dir, 'Usuarios_Cadastrados')

caminho_modelo_salvo = os.path.join(diretorio_modelo, 'modelo_lbph.yml')
caminho_mapa_ids = os.path.join(diretorio_modelo, 'mapeamento_ids.json')
caminho_json_validacao = os.path.join(diretorio_usuarios, 'validation.json')
caminho_json_dados_usuario = os.path.join(diretorio_usuarios, 'userData.json')

# Limite de confiança: quanto MENOR o valor, mais CONFIANTE o sistema está.
# Um valor de 35 é mais rigoroso que um de 80.
LIMITE_CONFIANCA = 60

# --- Funções Auxiliares ---
def remover_acentos(texto):
    """Remove acentos para evitar problemas de exibição no OpenCV."""
    try:
        nfkd_form = unicodedata.normalize('NFKD', str(texto))
        return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])
    except Exception:
        return str(texto)

# --- Etapa 1: Treinamento do Modelo ---

def obter_imagens_e_rotulos(ids_unicos):
    """
    Percorre a pasta 'faces', coleta todas as imagens de cada usuário,
    detecta os rostos, e os associa a um rótulo numérico para o treinamento.
    """
    faces, ids = [], []
    # Cria um mapa: 'ID_unico_string' -> 0, 'outro_ID_unico' -> 1, etc.
    mapeamento_ids_para_rotulo = {id_unico: i for i, id_unico in enumerate(ids_unicos)}

    print("Coletando dados de treinamento...")
    for id_unico in ids_unicos:
        diretorio_pessoa = os.path.join(diretorio_de_faces, id_unico)
        if not os.path.isdir(diretorio_pessoa): continue
        for nome_imagem in os.listdir(diretorio_pessoa):
            if nome_imagem.lower().endswith(('.jpg', '.png', '.jpeg')):
                caminho_imagem = os.path.join(diretorio_pessoa, nome_imagem)
                # Carrega a imagem em escala de cinza, que é o formato necessário para o treinamento.
                img = cv2.imread(caminho_imagem, cv2.IMREAD_GRAYSCALE)
                if img is None: continue
                # Detecta rostos na imagem de treinamento.
                rostos_detectados = classificador_de_faces.detectMultiScale(img, 1.1, 5)
                for (x, y, w, h) in rostos_detectados:
                    # Recorta a região de interesse (Region of Interest - ROI), que é o rosto.
                    roi = img[y:y+h, x:x+w]
                    # Redimensiona para um tamanho padrão para garantir consistência.
                    roi_redimensionado = cv2.resize(roi, (200, 200), interpolation=cv2.INTER_LINEAR)
                    faces.append(roi_redimensionado)
                    ids.append(mapeamento_ids_para_rotulo[id_unico])
    if not faces: return None, None, None
    # Converte as listas para arrays numpy, que é o formato esperado pelo OpenCV.
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

    reconhecedor = cv2.face.LBPHFaceRecognizer_create()
    reconhecedor.train(faces, ids)

    # Garante que a pasta 'Modelo_Treinamento' exista antes de salvar.
    if not os.path.exists(diretorio_modelo):
        os.makedirs(diretorio_modelo)

    # Salva o modelo treinado em um arquivo.
    reconhecedor.write(caminho_modelo_salvo)
    # Salva a lista de IDs na ordem em que foram treinados.
    salvar_dados_json(caminho_mapa_ids, {"ids_treinamento": ids_treinamento})

    print("Treinamento concluído e modelo salvo com sucesso.")
    return reconhecedor, ids_treinamento

# --- Etapa 2: Reconhecimento em Tempo Real ---

def obter_nivel_e_status(cpf, dados_validacao):
    """Busca o nível de acesso de um usuário a partir do seu CPF."""
    for nivel, dados in dados_validacao.items():
        if cpf in dados.get('pessoas', []):
            return nivel, "Autorizado"
    return "Nível Desconhecido", "Não Autorizado"

def reconhecer_faces_webcam(reconhecedor, ids_treinamento, dados_validacao, dados_usuario):
    """Inicia a webcam e realiza o reconhecimento facial em tempo real."""
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
            acesso_concedido_tempo = None # Reseta o timer se o rosto sair da tela.

        for (x, y, w, h) in rostos_detectados:
            roi_cinza = frame_cinza[y:y+h, x:x+w]
            # 'predict' retorna o rótulo do ID mais provável e a 'confiança' (distância).
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
                        if tempo_decorrido >= 3: # Se o usuário autorizado for visto por 3 segundos...
                            captura_de_video.release()
                            cv2.destroyAllWindows()
                            mostrar_documentos(nivel) # Abre a interface de documentos.
                            return # Encerra a função de reconhecimento.
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
        if cv2.waitKey(1) & 0xFF == ord('q'): break

    captura_de_video.release()
    cv2.destroyAllWindows()
    sys.exit()

# --- Bloco Principal de Execução ---
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

    # Inicia o reconhecimento com o modelo (carregado ou recém-treinado).
    if reconhecedor and ids_treinamento:
        reconhecer_faces_webcam(reconhecedor, ids_treinamento, dados_validacao, dados_usuario)
    else:
        print("Falha ao carregar ou treinar o modelo. Encerrando o programa.")

    sys.exit()