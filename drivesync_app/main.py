"""Ponto de entrada principal do aplicativo DriveSync."""

import argparse
import configparser
import logging
import os
# import sys # sys.argv will be replaced by argparse
from drivesync_app.logger_config import setup_logger
from drivesync_app.autenticacao_drive import get_drive_service
from drivesync_app.gerenciador_estado import load_state, save_state
from drivesync_app.gerenciador_drive import find_or_create_folder, list_folder_contents
from drivesync_app.processador_arquivos import walk_local_directory
from .sync_logic import run_sync # Main synchronization logic
from .verificador import verify_sync # Verification logic

def main():
    """
    Ponto de entrada principal do aplicativo DriveSync.

    Esta função orquestra o fluxo de trabalho da aplicação:
    1.  Lê as configurações do arquivo `config.ini`.
    2.  Configura o sistema de logging com base nas configurações.
    3.  Processa os argumentos da linha de comando usando `argparse`.
    4.  Sobrescreve as configurações do `config.ini` se argumentos CLI correspondentes
        (ex: --source-folder) forem fornecidos.
    5.  Carrega o estado da aplicação (de `drivesync_state.json` ou similar).
    6.  Inicializa o serviço do Google Drive (requer autenticação) se uma ação
        que o necessita (`--sync`, `--test-drive-ops`, `--verify`, ou `--authenticate` explícito)
        for especificada.
    7.  Executa a ação principal com base nos argumentos fornecidos:
        - `--authenticate`: Realiza o fluxo de autenticação OAuth 2.0.
        - `--list-local`: Lista os arquivos na pasta de origem local.
        - `--test-drive-ops`: Executa operações de teste no Google Drive.
        - `--sync`: Inicia o processo de sincronização (com suporte a `--dry-run`).
        - `--verify`: Verifica a consistência dos arquivos sincronizados.
    8.  Se nenhuma ação específica for solicitada, exibe a mensagem de ajuda.
    9.  Salva o estado atualizado da aplicação no final da execução (a menos que
        a ação seja um `--sync --dry-run` ou a verificação).
    """
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

    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(description="DriveSyncApp: Synchronizes a local folder with Google Drive.")
    parser.add_argument('--authenticate', action='store_true', help='Authenticate with Google Drive and save credentials.')
    parser.add_argument('--list-local', action='store_true', help='List local files in the configured source_folder.')
    parser.add_argument('--test-drive-ops', action='store_true', help='Run test operations on Google Drive (create folder, list root).')
    parser.add_argument('--sync', action='store_true', help='Initiate the synchronization process.')

    # Arguments for Sync
    parser.add_argument('--source-folder', type=str, default=None,
                        help='Override the source_folder from config.ini for the current run.')
    parser.add_argument('--target-drive-folder-id', type=str, default=None,
                        help='Override the target_drive_folder_id from config.ini for the current run.')
    parser.add_argument('--dry-run', action='store_true',
                        help='Simulate sync operations without making any changes to Google Drive or local state. Use with --sync.')
    parser.add_argument('--verify', action='store_true',
                        help='Verify synced files against Drive and local state. Compares local file sizes with Drive file sizes.')

    args = parser.parse_args()

    # --- Config Overrides ---
    if args.source_folder:
        if not config.has_section('Sync'):
            config.add_section('Sync')
        config['Sync']['source_folder'] = args.source_folder
        logger.info(f"Overridden source_folder with command line argument: {args.source_folder}")

    if args.target_drive_folder_id:
        if not config.has_section('Sync'):
            config.add_section('Sync')
        config['Sync']['target_drive_folder_id'] = args.target_drive_folder_id
        logger.info(f"Overridden target_drive_folder_id with command line argument: {args.target_drive_folder_id}")

    # Carregar o estado da aplicação
    estado_app = load_state(config)
    logger.info(f"Loaded state: {len(estado_app.get('processed_items', {}))} processed items, {len(estado_app.get('folder_mappings', {}))} folder mappings.")

    drive_service = None # Inicializar drive_service

    # Autenticação e obtenção do drive_service se argumentos específicos que o requerem forem passados
    if args.authenticate or args.test_drive_ops or args.sync or args.verify: # Added args.verify
        logger.info("Uma operação que requer autenticação do Drive foi solicitada.")
        drive_service = get_drive_service(config)

        if drive_service:
            logger.info("Serviço do Google Drive autenticado e obtido com sucesso.")
        elif not args.authenticate: # Only error if it wasn't an explicit auth attempt that failed
            logger.error("Falha ao obter o serviço do Google Drive. Verifique os logs e a configuração. Operações dependentes do Drive não podem continuar.")

    # If only --authenticate is passed, get_drive_service already handles it.
    # We can add an explicit message if only --authenticate was passed and it succeeded.
    if args.authenticate and drive_service:
        logger.info("Autenticação concluída e credenciais salvas (se aplicável).")
    elif args.authenticate and not drive_service:
        logger.error("Tentativa de autenticação explícita falhou.")


    # Lógica para --test-drive-ops
    if args.test_drive_ops:
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
        # No explicit 'else' needed if drive_service is None, as the error is logged during its acquisition attempt.


    # Lógica para --list-local
    if args.list_local:
        logger.info("Listagem de arquivos locais solicitada (--list-local)...")
        # source_folder will be read from config, potentially overridden by args.source_folder
        source_folder_val = None
        try:
            source_folder_val = config.get('Sync', 'source_folder') # Use .get for safer access
            if not source_folder_val:
                logger.error("Configuração 'source_folder' em [Sync] está vazia ou não definida (nem no config.ini nem via argumento). Defina o caminho da pasta de origem.")
        except (KeyError, configparser.NoSectionError):
            logger.error("Seção [Sync] ou configuração 'source_folder' não encontrada no config.ini e não fornecida via argumento.")

        if source_folder_val: # Proceed only if source_folder_val is not None or empty
            logger.info(f"Listando arquivos locais de: {source_folder_val}")
            try:
                item_count = 0
                # Corrected: Pass source_folder_val to walk_local_directory
                for item in walk_local_directory(source_folder_val):
                    item_count += 1
                    if item['type'] == 'file':
                        logger.info(f"  Encontrado: Tipo=arquivo, Nome='{item['name']}', CaminhoRelativo='{item['path']}', Tamanho={item['size']}")
                    else: # pasta
                        logger.info(f"  Encontrado: Tipo=pasta, Nome='{item['name']}', CaminhoRelativo='{item['path']}'")
                if item_count == 0:
                    # Corrected: Use source_folder_val in the log message
                    logger.info(f"Nenhum item encontrado em '{source_folder_val}'.")
            except Exception as e: # Catch potential errors from walk_local_directory itself if it raises them
                logger.error(f"Erro ao listar arquivos locais de '{source_folder_val}': {e}")
        # else: # Covered by the check for source_folder_val
            # logger.info("Listagem de arquivos locais não pode prosseguir devido à falta da configuração 'source_folder'.")


    # Lógica para --sync (deve ser após a obtenção do drive_service e carregamento do estado_app)
    if args.sync:
        if args.dry_run:
            logger.info("Modo DRY RUN ativado para sincronização. Nenhuma alteração real será feita.")
        logger.info("Processo de sincronização iniciado pelo argumento --sync.")

        if not config.get('Sync', 'source_folder', fallback=None):
            logger.error("Configuração 'source_folder' em [Sync] está vazia ou não definida. Defina o caminho da pasta de origem no config.ini ou via argumento --source-folder. Sincronização interrompida.")
        elif drive_service:
            if estado_app is not None:
                logger.info(f"Estado ANTES da sincronização: {len(estado_app.get('processed_items', {}))} itens processados, {len(estado_app.get('folder_mappings', {}))} mapeamentos de pastas.")

                run_sync(config, drive_service, estado_app, args.dry_run) # Passa args.dry_run

                logger.info(f"Chamada para run_sync concluída (Dry run: {args.dry_run}).")
                if args.dry_run:
                    logger.info("[Dry Run] Nenhuma alteração de estado foi salva.")
                # O estado será salvo no final da função main (se não for dry_run, run_sync modifica estado_app in-place)
            else:
                logger.error("Estado da aplicação não carregado. Sincronização interrompida.")
        else:
            logger.error("Falha ao autenticar com o Google Drive ou serviço não disponível. Sincronização interrompida.")

    # Lógica para --verify (deve ser após a obtenção do drive_service e carregamento do estado_app)
    if args.verify:
        logger.info("Processo de verificação iniciado pelo argumento --verify.")
        if drive_service:
            if estado_app is not None:
                verify_sync(config, drive_service, estado_app, logger) # Pass the main logger
                logger.info("Chamada para verify_sync concluída.")
            else:
                logger.error("Estado da aplicação não carregado. Verificação interrompida.")
        else:
            logger.error("Falha ao autenticar com o Google Drive ou serviço não disponível. Verificação interrompida.")

    # Default behavior: if no action argument is provided
    if not (args.authenticate or args.list_local or args.test_drive_ops or args.sync or args.verify): # Added args.verify
        logger.info("Nenhuma ação específica solicitada. Use --help para ver as opções.")
        parser.print_help()


    # Exemplo:
    # logger.debug("Este é um debug da aplicação principal.")
    # logger.warning("Atenção: Exemplo de warning.")

    # A linha abaixo pode ser removida se a interface for puramente por logs
    # ou se houver uma interface gráfica/web em outro lugar.
    # print("DriveSync App - Executando...") # Esta linha pode ser redundante se tudo for logado.

    # Salvar o estado da aplicação antes de finalizar
    # Se for dry_run, as modificações em `estado_app` dentro de `run_sync` foram condicionais
    # e não deveriam ter ocorrido, mas `save_state` é chamado de qualquer forma.
    # `run_sync` deve garantir que não modifica `estado_app` se `dry_run` for True.
    # Verification logic does not modify state, so save_state is fine after verify.
    if estado_app is not None:
        if args.sync and args.dry_run: # If sync was called with dry_run, state shouldn't have changed.
            logger.info("[Dry Run] Estado da aplicação não foi salvo pois nenhuma alteração de sincronização deveria ter ocorrido.")
        elif args.verify: # If verify was called, state is not modified by it.
            logger.info("Verificação concluída. O estado da aplicação não é modificado pela verificação.")
            # Optionally, could skip saving state here if no other action modified it, but saving is harmless.
            if save_state(config, estado_app): # Save state in case it was loaded and fixed (e.g. missing keys)
                logger.info("Estado da aplicação salvo (pós-verificação, sem alterações da verificação).")
            else:
                logger.error("Falha ao salvar o estado da aplicação (pós-verificação).")
        elif save_state(config, estado_app):
            logger.info("Estado da aplicação salvo com sucesso.")
        else:
            # This case would be for non-sync-dry_run, non-verify actions where save_state failed.
            logger.error("Falha ao salvar o estado da aplicação.")
    else:
        logger.warning("Variável de estado não definida, não foi possível salvar o estado.")

    logger.info("DriveSyncApp finalizando ou aguardando mais instruções (se aplicável).")


if __name__ == "__main__":
    main()
