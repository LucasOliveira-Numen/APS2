# Sistema de Reconhecimento Facial com Controle de Acesso por Níveis
#
# Este módulo implementa um sistema completo de reconhecimento facial que utiliza
# o algoritmo LBPH (Local Binary Patterns Histograms) para identificar usuários
# e conceder acesso a documentos baseado em níveis de autorização.
#
# Fluxo de Execução:
# 1. Verificação do modo de desenvolvimento (opcional)
# 2. Carregamento de modelo existente ou treinamento de novo modelo
# 3. Inicialização da captura de vídeo para reconhecimento em tempo real
# 4. Validação de identidade e concessão de acesso baseada em níveis
# 5. Abertura da interface de visualização de documentos

# --- Importação das Bibliotecas ---
import cv2                      # OpenCV: Biblioteca principal para processamento de imagens e visão computacional
import os                       # Módulo para operações do sistema de arquivos e diretórios
import numpy as np              # Biblioteca para manipulação eficiente de arrays multidimensionais
import sys                      # Módulo para interação com o interpretador Python e sistema operacional
import unicodedata              # Módulo para normalização de caracteres Unicode (remoção de acentos)
import time                     # Módulo para operações relacionadas ao tempo e cronometragem
import json                     # Módulo para serialização e deserialização de dados JSON

# --- Importações dos Módulos do Projeto ---
from utils_admin import carregar_dados_json, salvar_dados_json  # Funções utilitárias para manipulação de dados JSON
from document_viewer import mostrar_documentos                # Interface gráfica para visualização de documentos

# --- Configurações Iniciais e Verificação de Arquivos ---
# Define o diretório base do projeto de forma dinâmica para garantir portabilidade
base_dir = os.path.dirname(os.path.abspath(__file__))

# Configuração do classificador Haar Cascade para detecção de faces
face_cascade_path = os.path.join(base_dir, 'haarcascade_frontalface_default.xml')
if not os.path.exists(face_cascade_path):
    print(f"Erro: O arquivo '{os.path.basename(face_cascade_path)}' não foi encontrado. O programa não pode continuar.")
    exit()
classificador_de_faces = cv2.CascadeClassifier(face_cascade_path)

# Definição dos diretórios e arquivos do sistema
diretorio_de_faces = os.path.join(base_dir, 'faces')                    # Pasta contendo as imagens de treinamento
diretorio_modelo = os.path.join(base_dir, 'Modelo_Treinamento')         # Pasta para armazenar o modelo treinado
diretorio_usuarios = os.path.join(base_dir, 'Usuarios_Cadastrados')     # Pasta com dados dos usuários

# Caminhos específicos para arquivos de dados
caminho_modelo_salvo = os.path.join(diretorio_modelo, 'modelo_lbph.yml')
caminho_mapa_ids = os.path.join(diretorio_modelo, 'mapeamento_ids.json')
caminho_json_validacao = os.path.join(diretorio_usuarios, 'validation.json')
caminho_json_dados_usuario = os.path.join(diretorio_usuarios, 'userData.json')

# --- Parâmetros de Configuração do Sistema ---

# Limite de confiança para reconhecimento facial
# Valores menores indicam maior confiança (menor distância entre rostos)
# Este parâmetro controla a sensibilidade do reconhecimento
LIMITE_CONFIANCA = 50

# Configurações de validação para detecção de faces
MIN_TAMANHO_ROSTO = 80                    # Tamanho mínimo do rosto detectado em pixels
MAX_TENTATIVAS_RECONHECIMENTO = 3         # Número de reconhecimentos consecutivos necessários

# Configuração de data augmentation para treinamento
USAR_DATA_AUGMENTATION = True             # Habilita criação de variações das imagens durante o treinamento

# --- Modo de Desenvolvimento ---
# Quando ativado, pula o reconhecimento facial e abre diretamente o painel administrativo
# Útil para testes e configuração do sistema
MODO_DESENVOLVEDOR = False

# --- Funções Auxiliares ---

def remover_acentos(texto):
    """
    Remove acentos e caracteres especiais de uma string.

    O OpenCV pode apresentar problemas na exibição de caracteres não-ASCII
    através da função cv2.putText. Esta função normaliza o texto utilizando
    a forma de decomposição Unicode NFKD para garantir compatibilidade.

    Args:
        texto (str): String de entrada que pode conter acentos

    Returns:
        str: String normalizada sem acentos ou caracteres especiais
    """
    try:
        nfkd_form = unicodedata.normalize('NFKD', str(texto))
        return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])
    except Exception:
        return str(texto)

# --- Módulo de Treinamento do Modelo ---

def obter_imagens_e_rotulos(ids_unicos):
    """
    Coleta e prepara as imagens de treinamento para o modelo de reconhecimento facial.

    Esta função processa todas as imagens armazenadas na pasta 'faces', aplica
    validação de qualidade, detecção de faces e data augmentation opcional.
    Cada face detectada é associada a um rótulo numérico para o treinamento.

    Args:
        ids_unicos (list): Lista de IDs únicos dos usuários cadastrados

    Returns:
        tuple: (faces, ids, ids_treinamento) ou (None, None, None) se nenhuma face for encontrada
            - faces: Array numpy contendo as imagens das faces processadas
            - ids: Array numpy contendo os rótulos numéricos correspondentes
            - ids_treinamento: Lista dos IDs na ordem de treinamento
    """
    faces, ids = [], []

    # Criação do mapeamento de IDs únicos para rótulos numéricos
    # O algoritmo LBPH requer rótulos numéricos sequenciais (0, 1, 2, ...)
    mapeamento_ids_para_rotulo = {id_unico: i for i, id_unico in enumerate(ids_unicos)}

    print("Coletando imagens e rótulos para o treinamento com data augmentation...")

    # Importação das funções de processamento de imagem
    from utils_admin import aplicar_data_augmentation, validar_qualidade_imagem

    # Processamento das imagens de cada usuário
    for id_unico in ids_unicos:
        diretorio_pessoa = os.path.join(diretorio_de_faces, id_unico)
        if not os.path.isdir(diretorio_pessoa):
            continue

        print(f"Processando usuário: {id_unico}")
        imagens_processadas = 0

        # Iteração sobre todas as imagens do usuário
        for nome_imagem in os.listdir(diretorio_pessoa):
            if nome_imagem.lower().endswith(('.jpg', '.png', '.jpeg')):
                caminho_imagem = os.path.join(diretorio_pessoa, nome_imagem)

                # Carregamento da imagem em escala de cinza (formato requerido pelo LBPH)
                img = cv2.imread(caminho_imagem, cv2.IMREAD_GRAYSCALE)
                if img is None:
                    continue

                # Validação da qualidade da imagem antes do processamento
                if not validar_qualidade_imagem(img):
                    print(f"  Imagem de baixa qualidade ignorada: {nome_imagem}")
                    continue

                # Detecção de faces na imagem de treinamento
                rostos_detectados = classificador_de_faces.detectMultiScale(
                    img, 1.1, 8, minSize=(100, 100)
                )

                # Processamento do primeiro rosto detectado em cada imagem
                for (x, y, w, h) in rostos_detectados:
                    # Extração da região de interesse (ROI) contendo o rosto
                    roi = img[y:y+h, x:x+w]

                    # Redimensionamento para tamanho padrão (200x200 pixels)
                    roi_redimensionado = cv2.resize(roi, (200, 200), interpolation=cv2.INTER_LINEAR)

                    # Aplicação de data augmentation baseada na configuração
                    if USAR_DATA_AUGMENTATION:
                        imagens_aumentadas = aplicar_data_augmentation(roi_redimensionado)
                        # Adição de todas as variações ao conjunto de treinamento
                        for img_aumentada in imagens_aumentadas:
                            faces.append(img_aumentada)
                            ids.append(mapeamento_ids_para_rotulo[id_unico])
                    else:
                        # Uso apenas da imagem original para máxima performance
                        faces.append(roi_redimensionado)
                        ids.append(mapeamento_ids_para_rotulo[id_unico])

                    imagens_processadas += 1
                    break  # Processa apenas o primeiro rosto detectado por imagem

        print(f"  {imagens_processadas} imagens processadas para {id_unico}")

    # Verificação se faces foram encontradas
    if not faces:
        return None, None, None

    print(f"Total de imagens para treinamento: {len(faces)}")

    # Conversão para arrays numpy (formato requerido pelo OpenCV)
    return np.array(faces), np.array(ids), list(mapeamento_ids_para_rotulo.keys())

def treinar_e_salvar_modelo():
    """
    Executa o processo completo de treinamento do modelo de reconhecimento facial.

    Esta função coordena todo o processo de treinamento: carrega os dados dos usuários,
    processa as imagens, treina o modelo LBPH e salva os arquivos necessários para
    posterior carregamento e uso do modelo.

    Returns:
        tuple: (reconhecedor, ids_treinamento) ou (None, None) em caso de erro
            - reconhecedor: Instância treinada do reconhecedor LBPH
            - ids_treinamento: Lista dos IDs na ordem de treinamento
    """
    print("Iniciando o treinamento do modelo...")

    # Carregamento dos dados dos usuários
    dados_usuario = carregar_dados_json(caminho_json_dados_usuario)
    if not dados_usuario:
        print("Erro: Nenhum dado de usuário encontrado para treinar.")
        return None, None

    # Extração dos IDs únicos dos usuários
    ids_unicos = [dados['id'] for dados in dados_usuario.values()]
    if not ids_unicos:
        print("Erro: Nenhum ID de pessoa encontrado para treinar.")
        return None, None

    # Processamento das imagens e preparação dos dados de treinamento
    faces, ids, ids_treinamento = obter_imagens_e_rotulos(ids_unicos)
    if faces is None:
        print("Erro: Nenhuma face encontrada nas pastas para treinamento.")
        return None, None

    # Criação e treinamento do reconhecedor LBPH
    reconhecedor = cv2.face.LBPHFaceRecognizer_create()
    reconhecedor.train(faces, ids)

    # Criação do diretório de modelo se não existir
    if not os.path.exists(diretorio_modelo):
        os.makedirs(diretorio_modelo)

    # Salvamento do modelo treinado
    reconhecedor.write(caminho_modelo_salvo)

    # Salvamento do mapeamento de IDs para correlação posterior
    # Este arquivo é essencial para associar rótulos numéricos aos IDs únicos
    salvar_dados_json(caminho_mapa_ids, {"ids_treinamento": ids_treinamento})

    print("Treinamento concluído e modelo salvo com sucesso.")
    return reconhecedor, ids_treinamento

# --- Módulo de Reconhecimento em Tempo Real ---

def obter_nivel_e_status(cpf, dados_validacao):
    """
    Determina o nível de acesso e status de autorização de um usuário.

    Consulta o arquivo de validação para verificar se o CPF fornecido
    possui autorização e em qual nível de acesso.

    Args:
        cpf (str): CPF do usuário a ser verificado
        dados_validacao (dict): Dados de validação carregados do arquivo JSON

    Returns:
        tuple: (nivel, status)
            - nivel (str): Nível de acesso (ex: "Nivel 1", "Nivel 2", "Nivel 3")
            - status (str): "Autorizado" ou "Não Autorizado"
    """
    for nivel, dados in dados_validacao.items():
        if cpf in dados.get('pessoas', []):
            return nivel, "Autorizado"
    return "Nível Desconhecido", "Não Autorizado"

def reconhecer_faces_webcam(reconhecedor, ids_treinamento, dados_validacao, dados_usuario):
    """
    Executa o reconhecimento facial em tempo real através da webcam.

    Esta função implementa o loop principal de reconhecimento, capturando frames
    da webcam, detectando faces, validando identidades e concedendo acesso
    baseado em níveis de autorização. Inclui validações múltiplas para reduzir
    falsos positivos e um sistema de congelamento da tela após reconhecimento.

    Args:
        reconhecedor: Modelo LBPH treinado para reconhecimento facial
        ids_treinamento (list): Lista dos IDs na ordem de treinamento
        dados_validacao (dict): Dados de validação de acesso por nível
        dados_usuario (dict): Dados completos dos usuários cadastrados
    """
    captura_de_video = cv2.VideoCapture(0)
    if not captura_de_video.isOpened():
        print("Erro: Não foi possível acessar a webcam.")
        return

    print("Reconhecimento facial iniciado. Pressione 'q' para sair.")

    # Variáveis de controle para validação de reconhecimento
    acesso_concedido_tempo = None           # Controle do timer de acesso
    tentativas_reconhecimento = 0           # Contador de tentativas consecutivas
    ultimo_rosto_reconhecido = None         # Validação de consistência

    # Loop principal de captura e processamento de frames
    while True:
        ret, frame = captura_de_video.read()
        if not ret: break

        # Conversão para escala de cinza para processamento
        frame_cinza = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detecção de faces com parâmetros otimizados
        rostos_detectados = classificador_de_faces.detectMultiScale(
            frame_cinza,
            scaleFactor=1.1,                                    # Fator de escala para detecção
            minNeighbors=6,                                     # Número mínimo de vizinhos para confirmação
            minSize=(MIN_TAMANHO_ROSTO, MIN_TAMANHO_ROSTO),     # Tamanho mínimo do rosto
            flags=cv2.CASCADE_SCALE_IMAGE                       # Otimização de performance
        )

        # Reset dos contadores quando nenhum rosto é detectado
        if len(rostos_detectados) == 0:
            acesso_concedido_tempo = None
            tentativas_reconhecimento = 0
            ultimo_rosto_reconhecido = None

        for (x, y, w, h) in rostos_detectados:
            # Validação adicional: rosto deve ter tamanho mínimo
            if w < MIN_TAMANHO_ROSTO or h < MIN_TAMANHO_ROSTO:
                continue

            roi_cinza = frame_cinza[y:y+h, x:x+w]
            # O modelo prevê a identidade do rosto. Retorna o rótulo (ex: 0) e a confiança.
            rotulo_id, confianca = reconhecedor.predict(roi_cinza)

            # Validação mais rigorosa: confiança deve ser muito boa
            if confianca < LIMITE_CONFIANCA and rotulo_id < len(ids_treinamento):
                # ...traduz o rótulo numérico de volta para o ID único do usuário.
                id_unico_encontrado = ids_treinamento[rotulo_id]
                # ...e encontra o CPF associado a esse ID único.
                cpf_encontrado = next((cpf for cpf, data in dados_usuario.items() if data['id'] == id_unico_encontrado), None)

                if cpf_encontrado:
                    # Validação de consistência: o mesmo rosto deve ser reconhecido várias vezes
                    if ultimo_rosto_reconhecido == cpf_encontrado:
                        tentativas_reconhecimento += 1
                    else:
                        tentativas_reconhecimento = 1
                        ultimo_rosto_reconhecido = cpf_encontrado

                    # Com o CPF, busca o nome e o nível de acesso.
                    nome_completo = dados_usuario[cpf_encontrado]['nome']
                    nivel, status = obter_nivel_e_status(cpf_encontrado, dados_validacao)

                    # Prepara os textos para serem exibidos no vídeo.
                    texto_nome = f"Nome: {remover_acentos(nome_completo)}"
                    cor_status = (0, 255, 0) if status == "Autorizado" else (0, 0, 255) # Verde ou vermelho
                    texto_status = f"Status: {status} ({remover_acentos(nivel)})"
                    texto_confianca = f"Confianca: {confianca:.1f} | Tentativas: {tentativas_reconhecimento}"

                    # Desenha o retângulo e os textos na tela.
                    cv2.rectangle(frame, (x, y), (x+w, y+h), cor_status, 2)
                    cv2.putText(frame, texto_nome, (x, y-65), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    cv2.putText(frame, texto_status, (x, y-40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, cor_status, 2)
                    cv2.putText(frame, texto_confianca, (x, y-15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

                    # Lógica do timer de acesso com validação de tentativas
                    if status == "Autorizado" and tentativas_reconhecimento >= MAX_TENTATIVAS_RECONHECIMENTO:
                        print(f"Rosto reconhecido: {nome_completo} - Congelando tela por 2 segundos...")

                        # Congela a tela por 2 segundos com o temporizador
                        frame_congelado = frame.copy()

                        # Adiciona informações do usuário ao frame congelado
                        cv2.rectangle(frame_congelado, (x, y), (x+w, y+h), (0, 255, 0), 3)
                        cv2.putText(frame_congelado, texto_nome, (x, y-65), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                        cv2.putText(frame_congelado, texto_status, (x, y-40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                        cv2.putText(frame_congelado, texto_confianca, (x, y-15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

                        # Loop de 2 segundos mostrando o temporizador
                        tempo_inicio = time.time()
                        while time.time() - tempo_inicio < 2:
                            tempo_restante = 2 - int(time.time() - tempo_inicio)
                            if tempo_restante > 0:
                                texto_timer = f"Acesso em {tempo_restante}s..."
                                # Cria uma cópia do frame para não sobrescrever
                                frame_timer = frame_congelado.copy()
                                cv2.putText(frame_timer, texto_timer, (x, y+h+20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                                cv2.imshow('Reconhecimento Facial', frame_timer)
                                cv2.waitKey(100)  # Atualiza a cada 100ms
                            else:
                                break

                        print(f"Acesso concedido para: {nome_completo}")
                        captura_de_video.release()
                        cv2.destroyAllWindows()
                        mostrar_documentos(nivel) # Abre a interface de documentos.
                        return # Encerra a função de reconhecimento.

                    elif status == "Autorizado":
                        # Mostra que está validando
                        texto_validando = f"Validando... ({tentativas_reconhecimento}/{MAX_TENTATIVAS_RECONHECIMENTO})"
                        cv2.putText(frame, texto_validando, (x, y+h+20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                else:
                    acesso_concedido_tempo = None # Reseta se o ID não for encontrado (caso raro).
                    tentativas_reconhecimento = 0
            else:
                acesso_concedido_tempo = None # Reseta o timer se o rosto for desconhecido.
                tentativas_reconhecimento = 0
                ultimo_rosto_reconhecido = None
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
                cv2.putText(frame, "Desconhecido", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
                cv2.putText(frame, f"Confianca: {confianca:.1f}", (x, y+h+15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

        cv2.imshow('Reconhecimento Facial', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break # Encerra o loop se 'q' for pressionado.

    captura_de_video.release()
    cv2.destroyAllWindows()
    sys.exit()

# --- Bloco Principal de Execução ---
# Ponto de entrada do sistema quando o script é executado diretamente
if __name__ == "__main__":

    # Verificação do modo de desenvolvimento
    if MODO_DESENVOLVEDOR:
        print("="*40)
        print("MODO DE DESENVOLVIMENTO ATIVADO")
        print("Pulando reconhecimento facial e abrindo o painel de Nível 3.")
        print("="*40)
        mostrar_documentos("Nivel 3")
    else:
        # Carregamento dos dados de validação e usuários
        dados_validacao = carregar_dados_json(caminho_json_validacao)
        dados_usuario = carregar_dados_json(caminho_json_dados_usuario)

        # Verificação da existência de usuários cadastrados
        if not dados_usuario:
            print("Nenhum usuário cadastrado. Execute o `cadastro_app.py` para adicionar usuários.")
            sys.exit()

        # Lógica de carregamento ou treinamento do modelo
        if os.path.exists(caminho_modelo_salvo) and os.path.exists(caminho_mapa_ids):
            print("Carregando modelo de reconhecimento facial existente...")
            reconhecedor = cv2.face.LBPHFaceRecognizer_create()
            reconhecedor.read(caminho_modelo_salvo)
            mapa_ids = carregar_dados_json(caminho_mapa_ids)
            ids_treinamento = mapa_ids.get("ids_treinamento")
            print("Modelo carregado com sucesso.")
        else:
            print("Nenhum modelo treinado encontrado. Iniciando novo treinamento...")
            reconhecedor, ids_treinamento = treinar_e_salvar_modelo()

        # Inicialização do reconhecimento facial
        if reconhecedor and ids_treinamento:
            reconhecer_faces_webcam(reconhecedor, ids_treinamento, dados_validacao, dados_usuario)
        else:
            print("Falha ao carregar ou treinar o modelo. Encerrando o programa.")

    sys.exit()