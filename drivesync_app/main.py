"""Ponto de entrada principal do aplicativo DriveSync."""

import configparser
import logging
import os
import sys # Importar sys
from drivesync_app.logger_config import setup_logger
from drivesync_app.autenticacao_drive import get_drive_service
from drivesync_app.gerenciador_estado import load_state, save_state
from drivesync_app.gerenciador_drive import find_or_create_folder, list_folder_contents # Drive ops

def main():
    """Função principal para executar o aplicativo."""
    # Ler configuração
    config = configparser.ConfigParser()

    # Construir caminho absoluto para config.ini (um nível acima de main.py)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_file_path = os.path.join(script_dir, '..', 'config.ini')

    files_read = config.read(config_file_path)

    if not files_read:
        # Esta configuração básica de logging será usada apenas para logar o erro abaixo.
        # setup_logger irá reconfigurar o logging com base nos defaults ou no arquivo.
        logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
        logging.error(f"Arquivo de configuração '{config_file_path}' não encontrado ou vazio. Logger usará defaults internos.")

    # Configurar o logger
    # Passamos o config, que pode estar vazio se o arquivo não foi lido.
    # setup_logger é responsável por lidar com isso usando seus fallbacks.
    setup_logger(config)

    # Obter o logger para este módulo
    logger = logging.getLogger(__name__) # Logger para main.py
    logger.info("DriveSyncApp iniciado. Logger configurado.")

    # Carregar o estado da aplicação
    estado_app = load_state(config)
    logger.info(f"Loaded state: {len(estado_app.get('processed_items', {}))} processed items, {len(estado_app.get('folder_mappings', {}))} folder mappings.")

    drive_service = None # Inicializar drive_service

    # Autenticação e obtenção do drive_service se argumentos específicos forem passados
    if any(arg in sys.argv for arg in ['--authenticate', '--test-drive-ops']):
        logger.info("Autenticação ou operações de teste do Drive solicitadas.")
        drive_service = get_drive_service(config)

        if drive_service:
            logger.info("Serviço do Google Drive autenticado e obtido com sucesso.")
        else:
            logger.error("Falha ao obter o serviço do Google Drive. Verifique os logs e a configuração.")

    # Lógica para --test-drive-ops
    if "--test-drive-ops" in sys.argv:
        if drive_service:
            logger.info("Executando operações de teste do Drive (--test-drive-ops)...")

            # Testar find_or_create_folder
            test_folder_name = "DriveSync Test Folder"
            logger.info(f"Tentando encontrar ou criar a pasta de teste: '{test_folder_name}' na raiz do Drive...")
            folder_id = find_or_create_folder(drive_service, 'root', test_folder_name)
            if folder_id:
                logger.info(f"Pasta de teste '{test_folder_name}' encontrada/criada com ID: {folder_id}")
            else:
                logger.error(f"Falha ao encontrar ou criar a pasta de teste '{test_folder_name}'.")

            # Testar list_folder_contents
            logger.info("Tentando listar o conteúdo da pasta raiz ('root')...")
            drive_contents = list_folder_contents(drive_service, 'root')
            if drive_contents is not None: # Checa se não é None (erro na chamada)
                if drive_contents: # Checa se o dicionário não está vazio
                    logger.info("Conteúdo da pasta raiz (primeiros 5 itens):")
                    count = 0
                    for name, details in drive_contents.items():
                        if count < 5:
                            logger.info(f"- {name} ({details.get('mimeType', 'N/A')})")
                            count += 1
                        else:
                            break
                    if not drive_contents: # Este caso é coberto pelo if drive_contents:, mas para segurança
                        logger.info("A pasta raiz está vazia ou nenhum conteúdo foi recuperado.")
                else: # drive_contents é um dicionário vazio
                    logger.info("A pasta raiz está vazia.")
            else: # drive_contents é None
                logger.error("Falha ao listar o conteúdo da pasta raiz.")
        else:
            logger.warning("Não foi possível executar as operações de teste do Drive porque o serviço do Drive não está disponível.")

    if not any(arg in sys.argv for arg in ['--authenticate', '--test-drive-ops']):
        logger.info("Nenhuma ação específica (--authenticate, --test-drive-ops) solicitada via argumentos. O aplicativo continuará se houver mais lógica principal.")
        # Lógica principal do aplicativo viria aqui

    # Exemplo:
    # logger.debug("Este é um debug da aplicação principal.")
    # logger.warning("Atenção: Exemplo de warning.")

    # A linha abaixo pode ser removida se a interface for puramente por logs
    # ou se houver uma interface gráfica/web em outro lugar.
    # print("DriveSync App - Executando...") # Esta linha pode ser redundante se tudo for logado.

    # Salvar o estado da aplicação antes de finalizar
    if estado_app is not None: # Assegurar que estado_app foi definido
        if save_state(config, estado_app):
            logger.info("Estado da aplicação salvo com sucesso.")
        else:
            logger.error("Falha ao salvar o estado da aplicação.")
    else:
        logger.warning("Variável de estado não definida, não foi possível salvar o estado.")

    logger.info("DriveSyncApp finalizando ou aguardando mais instruções (se aplicável).")


if __name__ == "__main__":
    main()
