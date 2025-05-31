# DriveSync: Sincronizador de Arquivos para Google Drive

DriveSync é um aplicativo Python de linha de comando projetado para sincronizar de forma eficiente e confiável o conteúdo de uma pasta local para uma conta do Google Drive, mantendo a estrutura de pastas original. O projeto utiliza a API do Google Drive e é construído com foco em resumibilidade, tratamento de erros e configurabilidade.

## Funcionalidades

### Implementadas / Em Andamento
* **Configuração Centralizada:** Fácil configuração através de um arquivo `config.ini` para caminhos, credenciais e outras definições.
* **Logging Detalhado:** Geração de logs em console e arquivo para acompanhamento e depuração, com nível de log configurável.
* **Autenticação Segura com Google Drive:** Utiliza o fluxo OAuth 2.0 para autorização segura com a API do Google Drive. Os tokens são armazenados localmente para sessões futuras.

### Planejadas
* **Gerenciamento de Estado:** Salva o progresso da sincronização, permitindo que o aplicativo seja interrompido e retomado de onde parou, evitando reprocessamento desnecessário.
* **Travessia Recursiva de Arquivos:** Capacidade de percorrer recursivamente a estrutura de pastas locais.
* **Espelhamento de Estrutura no Drive:** Criação automática da estrutura de pastas no Google Drive para espelhar a organização local.
* **Upload Resumível de Arquivos:** Suporte a uploads resumíveis para arquivos grandes, garantindo a integridade em caso de interrupções.
* **Ignorar Arquivos Já Sincronizados:** Verifica o estado para pular arquivos que já foram carregados com sucesso.
* **Tratamento Robusto de Erros e Retentativas:** Mecanismos para lidar com erros de rede, limites da API e outras falhas, com lógica de retentativa.
* **Verificação de Arquivos (Opcional):** Funcionalidade para verificar se todos os arquivos locais foram corretamente carregados no Google Drive.
* **Interface de Linha de Comando (CLI) Amigável:** Argumentos para controlar diferentes modos de operação (sincronizar, autenticar, verificar).
* **Documentação Interna:** Docstrings e comentários no código para facilitar a manutenção.

## Configuração e Instalação

1.  **Clone o Repositório:**
    ```bash
    git clone <URL_DO_SEU_REPOSITORIO_NO_GITHUB>
    cd drivesync # Ou o nome da pasta do seu projeto
    ```

2.  **Crie e Ative um Ambiente Virtual Python:**
    ```bash
    python -m venv venv
    # Windows (PowerShell)
    .\venv\Scripts\Activate.ps1
    # Windows (CMD)
    .\venv\Scripts\activate.bat
    # Linux/macOS
    source venv/bin/activate
    ```

3.  **Instale as Dependências:**
    ```bash
    pip install -r requirements.txt
    ```
    *(O arquivo `requirements.txt` será atualizado à medida que novas dependências forem adicionadas).*

4.  **Configure as Credenciais da API do Google Drive:**
    * Acesse o [Google Cloud Console](https://console.cloud.google.com/).
    * Crie um novo projeto ou selecione um existente.
    * Ative a "Google Drive API".
    * Crie credenciais do tipo "OAuth client ID" para "Desktop application".
    * Faça o download do arquivo JSON das credenciais. Renomeie este arquivo para o nome especificado em `config.ini` como `client_secret_file` (ex: `credentials_target.json`) e coloque-o na pasta raiz do projeto. **Este arquivo não deve ser enviado para o GitHub.**
    * Na "Tela de consentimento OAuth" do seu projeto no Google Cloud Console, adicione os e-mails dos usuários de teste enquanto o aplicativo estiver em fase de "Teste".

5.  **Configure o Arquivo `config.ini`:**
    * Abra o arquivo `config.ini` na raiz do projeto.
    * Ajuste os seguintes valores conforme necessário:
        * `client_secret_file`: Nome do arquivo JSON de credenciais do Google.
        * `token_file`: Nome do arquivo onde os tokens OAuth serão armazenados (ex: `token_target.json`).
        * `source_folder`: Caminho absoluto para a pasta local que você deseja sincronizar.
        * `target_drive_folder_id`: (Opcional) ID da pasta no Google Drive onde a sincronização será feita. Se vazio, usará a raiz do Drive.
        * `state_file`: Nome do arquivo para armazenar o estado da sincronização (ex: `upload_state.json`).
        * `log_file`: Nome do arquivo de log (ex: `app.log`).
        * `log_level`: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL).

## Uso

(Esta seção será atualizada à medida que a CLI for desenvolvida)

Para autenticar o aplicativo com o Google Drive (necessário na primeira execução ou se o token expirar):
```bash
python -m drivesync_app.main --authenticate
