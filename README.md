# DriveSync: Sincronizador de Arquivos para Google Drive

DriveSync é um aplicativo Python de linha de comando projetado para sincronizar de forma eficiente e confiável o conteúdo de uma pasta local para uma conta do Google Drive, mantendo a estrutura de pastas original. O projeto utiliza a API do Google Drive e é construído com foco em resumibilidade, tratamento de erros e configurabilidade.

## Funcionalidades

### Implementadas / Em Andamento

* **Configuração Centralizada:** Fácil configuração através de um arquivo `config.ini` para caminhos, credenciais e outras definições.
* **Logging Detalhado:** Geração de logs em console e arquivo para acompanhamento e depuração, com nível de log configurável.
* **Autenticação Segura com Google Drive:** Utiliza o fluxo OAuth 2.0 para autorização segura com a API do Google Drive. Os tokens são armazenados localmente para sessões futuras.
* **Gerenciamento de Estado:** Salva o progresso da sincronização em um arquivo (ex: `drivesync_state.json`), permitindo que o aplicativo seja interrompido e retomado de onde parou, evitando reprocessamento desnecessário de itens já sincronizados e mapeamentos de pastas.
* **Travessia Recursiva de Arquivos:** Capacidade de percorrer recursivamente a estrutura de pastas locais e identificar ficheiros e pastas.
* **Sincronização Inteligente:** Sincronização da estrutura de pastas locais e upload resumível de arquivos para o Google Drive. Verifica o estado dos arquivos (tamanho e data de modificação) para evitar re-uploads desnecessários, com tratamento de erros e retentativas para maior confiabilidade.
* **Interface de Linha de Comando Avançada:** Utiliza `argparse` para um controle robusto das operações, incluindo a capacidade de sobrescrever configurações do `config.ini` (ex: `--source-folder`, `--target-drive-folder-id`) e realizar simulações (`--dry-run`).
* **Verificação de Sincronização:** Permite verificar a consistência dos arquivos sincronizados entre o local, o estado da aplicação e o Google Drive (`--verify`), reportando discrepâncias de tamanho ou arquivos ausentes.

### Planejadas

* **Tratamento de Exclusões:** Lógica para lidar com arquivos excluídos localmente ou no Drive (atualmente, arquivos excluídos não são processados ativamente para remoção no destino).
* **Comparação por Checksum (MD5):** Adicionar verificação opcional de arquivos por checksum MD5 para uma detecção de alterações mais robusta (além de tamanho e data de modificação).
* **Suporte para Múltiplas Configurações de Sincronização:** Possibilidade de definir e executar diferentes perfis de sincronização.
* **Interface Gráfica (GUI):** Desenvolvimento de uma interface gráfica para facilitar o uso por usuários não técnicos (consideração futura de longo prazo).

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
        * `client_secret_file`: (Na secção `[DriveAPI]`) Nome do arquivo JSON de credenciais do Google.
        * `token_file`: (Na secção `[DriveAPI]`) Nome do arquivo onde os tokens OAuth serão armazenados (ex: `token_target.json`).
        * `source_folder`: (Na secção `[Sync]`) O caminho completo para a pasta local que você deseja sincronizar. **Este valor precisa ser configurado por você.**
        * `target_drive_folder_id`: (Na secção `[Sync]`, opcional) ID da pasta no Google Drive onde a sincronização será feita. Se vazio, usará a raiz do Drive.
        * `state_file`: (Na secção `[Sync]`) Nome do arquivo para armazenar o estado da sincronização (ex: `drivesync_state.json`).
        * `log_file`: (Na secção `[Logging]`) Nome do arquivo de log (ex: `app.log`).
        * `log_level`: (Na secção `[Logging]`) Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL).

    **Nota Importante:** Após preencher o `config.ini` e colocar o arquivo de credenciais (`client_secret_file`), execute o comando de autenticação pela primeira vez:
    ```bash
    python -m drivesync_app.main --authenticate
    ```

## Application State

The application maintains its synchronization state in a JSON file (by default `drivesync_state.json`, configurable in `config.ini`). This file stores information critical for resuming synchronization tasks and keeping track of synced items and Drive folder structures. It's generally not recommended to edit this file manually.

## Uso

O DriveSyncApp é controlado via argumentos de linha de comando. Abaixo estão os principais comandos e opções disponíveis.
Para uma lista completa de todos os argumentos e suas descrições, execute:
```bash
python -m drivesync_app.main --help
```

### Comandos Principais

*   **Autenticação:**
    ```bash
    python -m drivesync_app.main --authenticate
    ```
    Este comando inicia o processo de autenticação com o Google Drive. Necessário na primeira execução ou se os tokens de acesso expirarem. As credenciais são salvas localmente (conforme configurado em `config.ini`).

*   **Sincronização:**
    ```bash
    python -m drivesync_app.main --sync [opções...]
    ```
    Inicia o processo de sincronização entre a pasta local de origem e a pasta de destino no Google Drive.
    *   **Opções de Sincronização:**
        *   `--source-folder CAMINHO_DA_PASTA_LOCAL`: Permite especificar uma pasta local de origem para esta execução, sobrescrevendo o valor de `source_folder` em `config.ini`.
        *   `--target-drive-folder-id ID_DA_PASTA_DRIVE`: Permite especificar um ID de pasta de destino no Google Drive para esta execução, sobrescrevendo o valor de `target_drive_folder_id` em `config.ini`.
        *   `--dry-run`: Simula o processo de sincronização sem realizar quaisquer alterações reais no Google Drive ou no arquivo de estado local. Útil para verificar quais arquivos seriam transferidos ou atualizados.

*   **Listar Arquivos Locais:**
    ```bash
    python -m drivesync_app.main --list-local
    ```
    Percorre e lista os arquivos e pastas no `source_folder` configurado (ou sobrescrito via `--source-folder`) que seriam considerados para sincronização.

*   **Testar Operações do Drive:**
    ```bash
    python -m drivesync_app.main --test-drive-ops
    ```
    Executa operações de teste no Google Drive, como tentar criar uma pasta de teste e listar o conteúdo da pasta raiz. Requer autenticação prévia.

*   **Verificar Sincronização:**
    ```bash
    python -m drivesync_app.main --verify
    ```
    Verifica a consistência dos arquivos sincronizados. Compara os arquivos locais com o estado registrado pelo DriveSync e os metadados dos arquivos correspondentes no Google Drive. Reporta discrepâncias como arquivos locais não presentes no estado, arquivos no estado mas ausentes no Drive (ou na lixeira), e incompatibilidades de tamanho. Requer autenticação prévia.

### Exemplos de Uso

1.  **Autenticar o aplicativo:**
    ```bash
    python -m drivesync_app.main --authenticate
    ```

2.  **Executar uma sincronização padrão (usando configurações do `config.ini`):**
    ```bash
    python -m drivesync_app.main --sync
    ```

3.  **Executar uma simulação de sincronização (dry run):**
    ```bash
    python -m drivesync_app.main --sync --dry-run
    ```

4.  **Sincronizar especificando uma pasta de origem e destino diferente:**
    ```bash
    python -m drivesync_app.main --sync --source-folder "/caminho/para/meus/documentos" --target-drive-folder-id "IDdaPastaNoMeuDrive"
    ```

5.  **Listar os arquivos locais que seriam sincronizados:**
    ```bash
    python -m drivesync_app.main --list-local
    ```

6.  **Verificar a integridade da sincronização:**
    ```bash
    python -m drivesync_app.main --verify
    ```

7.  **Ver todas as opções de ajuda:**
    ```bash
    python -m drivesync_app.main --help
    ```

## Estrutura do Projeto

* `drivesync/` (Pasta raiz do projeto)
    * `drivesync_app/`: Contém o código fonte principal do aplicativo.
        * `main.py`: Ponto de entrada do aplicativo.
        * `autenticacao_drive.py`: Lida com a autenticação OAuth 2.0.
        * `logger_config.py`: Configuração do sistema de logging.
        * `gerenciador_estado.py`: Gerencia o estado da sincronização.
        * `gerenciador_drive.py`: Interage com a API do Google Drive.
        * `processador_arquivos.py`: Processa arquivos e pastas locais.
        * `verificador.py`: Verifica a sincronização.
        * `__init__.py`: Define `drivesync_app` como um pacote Python.
    * `config.ini`: Arquivo de configuração.
    * `requirements.txt`: Lista de dependências Python.
    * `.gitignore`: Especifica arquivos ignorados pelo Git.
    * `README.md`: Este arquivo.

## Roteiro (Roadmap)

Veja o arquivo `ROADMAP.md` 
