"""Ponto de entrada principal do aplicativo DriveSync."""

import configparser
import logging
import os # Added os module
from drivesync_app.logger_config import setup_logger

def main():
    """Função principal para executar o aplicativo."""
    # Ler configuração
    config = configparser.ConfigParser()

    # Construir caminho absoluto para config.ini (um nível acima de main.py)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_file_path = os.path.join(script_dir, '..', 'config.ini')

    files_read = config.read(config_file_path)

    if not files_read:
        # Se config.ini não foi encontrado ou está vazio, configurar um logger básico
        # para que o erro possa ser registrado e usar defaults.
        # Esta configuração básica de logging será usada apenas para logar o erro abaixo.
        # setup_logger irá reconfigurar o logging com base nos defaults ou no arquivo.
        logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
        logging.error(f"Arquivo de configuração '{config_file_path}' não encontrado ou vazio. Logger usará defaults internos.")
        # Não é estritamente necessário popular o config aqui se setup_logger tem fallbacks robustos,
        # mas pode ser feito se quisermos controlar os fallbacks de main.py de forma explícita.
        # Por ora, deixaremos que setup_logger use seus próprios fallbacks se o arquivo não for lido.
        # Se quiséssemos definir fallbacks aqui:
        # if not config.has_section('Logging'):
        # config.add_section('Logging')
        # config.set('Logging', 'log_file', 'main_fallback.log')
        # config.set('Logging', 'log_level', 'INFO')

    # Configurar o logger
    setup_logger(config) # Passamos o config, que pode estar vazio se o arquivo não foi lido.
                         # setup_logger é responsável por lidar com isso usando seus fallbacks.

    # Obter o logger para este módulo
    logger = logging.getLogger(__name__)
    logger.info("DriveSyncApp iniciado. Logger configurado.")

    # Lógica principal do aplicativo viria aqui
    # Exemplo:
    # logger.debug("Este é um debug da aplicação principal.")
    # logger.warning("Atenção: Exemplo de warning.")

    print("DriveSync App - Executando...") # Pode ser substituído por logging

if __name__ == "__main__":
    main()
