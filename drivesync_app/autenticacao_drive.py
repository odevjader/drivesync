"""Módulo para autenticação com a API do Google Drive."""

import os
import logging
import configparser
from google.auth.transport.requests import Request as GoogleAuthRequest
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError

# Escopo para acesso completo ao Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive']

logger = logging.getLogger(__name__)

def get_drive_service(config: configparser.ConfigParser):
    """
    Autentica com a API do Google Drive e retorna um objeto de serviço.

    Utiliza o fluxo OAuth 2.0 para autenticação. Procura por um arquivo de token
    existente (ex: `token.json`, configurável). Se não existir, estiver inválido ou
    expirado e não puder ser atualizado, inicia um novo fluxo de autenticação.
    Neste caso, o usuário será solicitado a autorizar o aplicativo através do navegador.
    As novas credenciais são então salvas no arquivo de token para uso futuro.

    Args:
        config (configparser.ConfigParser): Objeto ConfigParser contendo as
            configurações da aplicação, incluindo os caminhos para o
            `client_secret_file` (obtido do Google Cloud Console) e o
            `token_file` (onde as credenciais do usuário são armazenadas).

    Returns:
        googleapiclient.discovery.Resource: Um objeto de serviço da API do Google Drive
                                            autenticado e pronto para uso, ou None se
                                            a autenticação falhar.
    """
    creds = None
    token_file_path = None
    client_secret_file_path = None

    try:
        # Obter caminhos dos arquivos de configuração
        # Assumindo que os caminhos em config.ini são relativos ao diretório raiz do projeto
        # ou são caminhos absolutos.
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Project root /app

        raw_token_file = config.get('DriveAPI', 'token_file', fallback='token.pickle') # Default from problem description, but .json is more common
        raw_client_secret_file = config.get('DriveAPI', 'client_secret_file', fallback='credentials.json') # Default from problem

        # Se os caminhos no config.ini forem apenas nomes de arquivos, considerá-los relativos ao root
        if not os.path.isabs(raw_token_file):
            token_file_path = os.path.join(base_path, raw_token_file)
        else:
            token_file_path = raw_token_file

        if not os.path.isabs(raw_client_secret_file):
            client_secret_file_path = os.path.join(base_path, raw_client_secret_file)
        else:
            client_secret_file_path = raw_client_secret_file

        logger.info(f"Caminho do arquivo de token: {token_file_path}")
        logger.info(f"Caminho do arquivo de client_secret: {client_secret_file_path}")

        # Verificar se o client_secret_file existe
        if not os.path.exists(client_secret_file_path):
            logger.error(f"Arquivo client_secret não encontrado em: {client_secret_file_path}")
            return None

        # Carregar credenciais existentes do arquivo de token
        if os.path.exists(token_file_path):
            try:
                creds = Credentials.from_authorized_user_file(token_file_path, SCOPES)
                logger.info("Credenciais carregadas do arquivo de token.")
            except Exception as e:
                logger.warning(f"Não foi possível carregar credenciais de {token_file_path}: {e}. Será tentado um novo fluxo.")
                creds = None # Garantir que creds seja None se o carregamento falhar

        # Se não há credenciais válidas, tentar atualizar ou obter novas
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("Credenciais expiradas. Tentando atualizar...")
                try:
                    creds.refresh(GoogleAuthRequest())
                    logger.info("Credenciais atualizadas com sucesso.")
                except Exception as e:
                    logger.error(f"Erro ao atualizar credenciais: {e}")
                    creds = None # Falha na atualização, precisa de novo login

            if not creds: # Entra aqui se o refresh falhou ou se não havia token/refresh_token
                logger.info("Nenhuma credencial válida encontrada ou atualização falhou. Iniciando novo fluxo OAuth.")
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        client_secret_file_path, SCOPES, redirect_uri='http://localhost:8080/'
                    )
                    # flow.run_console() é uma alternativa se o servidor local não for desejado/possível
                    creds = flow.run_local_server(port=8080)
                    logger.info("Novo token obtido através do fluxo OAuth.")
                except Exception as e:
                    logger.error(f"Erro durante o fluxo OAuth: {e}")
                    return None # Não foi possível obter credenciais

            # Salvar as novas credenciais (ou atualizadas) no arquivo de token
            try:
                with open(token_file_path, 'w') as token_file:
                    token_file.write(creds.to_json())
                logger.info(f"Credenciais salvas em: {token_file_path}")
            except IOError as e:
                logger.error(f"Erro ao salvar o arquivo de token em {token_file_path}: {e}")
                # Continuar mesmo assim, o serviço pode funcionar nesta sessão

        # Construir e retornar o serviço da API
        try:
            service = build('drive', 'v3', credentials=creds)
            logger.info("Serviço Google Drive API construído com sucesso.")
            return service
        except HttpError as e:
            logger.error(f"Erro ao construir o serviço Google Drive: {e}")
            return None
        except Exception as e:
            logger.error(f"Erro inesperado ao construir o serviço Google Drive: {e}")
            return None

    except configparser.NoSectionError as e:
        logger.error(f"Erro de configuração: Seção '[DriveAPI]' não encontrada em config.ini. Detalhes: {e}")
        return None
    except configparser.NoOptionError as e:
        logger.error(f"Erro de configuração: Opção não encontrada na seção '[DriveAPI]'. Detalhes: {e}")
        return None
    except Exception as e:
        logger.error(f"Erro inesperado na função get_drive_service: {e}")
        return None
