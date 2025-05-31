"""Ponto de entrada principal do aplicativo DriveSync."""

import configparser
import logging
import os
import sys # Importar sys
from drivesync_app.logger_config import setup_logger
from drivesync_app.autenticacao_drive import get_drive_service # Importar get_drive_service

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

    # Verificar argumento --authenticate
    if len(sys.argv) > 1 and sys.argv[1] == '--authenticate':
        logger.info("Autenticação solicitada via argumento --authenticate.")

        # O config já foi lido (ou está vazio se o arquivo falhou ao carregar,
        # get_drive_service tem sua própria lógica de fallback/erro para isso)
        drive_service = get_drive_service(config)

        if drive_service:
            logger.info("Serviço do Google Drive autenticado e obtido com sucesso.")
            # Aqui você poderia, por exemplo, armazenar o drive_service ou usá-lo
            # para uma operação inicial, ou apenas autenticar para futuras execuções.
        else:
            logger.error("Falha ao obter o serviço do Google Drive. Verifique os logs e a configuração.")
    else:
        logger.info("Nenhuma ação específica solicitada via argumentos. O aplicativo continuará normalmente se houver mais lógica.")
        # Lógica principal do aplicativo viria aqui se não for apenas autenticação

    # Exemplo:
    # logger.debug("Este é um debug da aplicação principal.")
    # logger.warning("Atenção: Exemplo de warning.")

    # A linha abaixo pode ser removida se a interface for puramente por logs
    # ou se houver uma interface gráfica/web em outro lugar.
    # print("DriveSync App - Executando...") # Esta linha pode ser redundante se tudo for logado.
    logger.info("DriveSyncApp finalizando ou aguardando mais instruções (se aplicável).")


if __name__ == "__main__":
    main()
