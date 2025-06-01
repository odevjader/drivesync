# DriveSync: Sincronizador de Arquivos para Google Drive

DriveSync é um aplicativo Python de linha de comando projetado para sincronizar de forma eficiente e confiável o conteúdo de uma pasta local para uma conta do Google Drive, mantendo a estrutura de pastas original. O projeto utiliza a API do Google Drive e é construído com foco em resumibilidade, tratamento de erros e configurabilidade.

## Funcionalidades

### v1.0 - Implementadas

* **Configuração Centralizada:** Fácil configuração através de um arquivo `config.ini` para caminhos, credenciais e outras definições.

* **Logging Detalhado:** Geração de logs em console e arquivo para acompanhamento e depuração, com nível de log configurável.

* **Autenticação Segura com Google Drive:** Utiliza o fluxo OAuth 2.0 para autorização segura com a API do Google Drive. Os tokens são armazenados localmente para sessões futuras.

* **Gerenciamento de Estado (SQLite):** Utiliza um banco de dados SQLite (ex: `drivesync_state.db`) para salvar o progresso da sincronização, permitindo que o aplicativo seja interrompido e retomado. Este método oferece melhor performance e escalabilidade em comparação com arquivos JSON, especialmente para grandes volumes de arquivos. Rastreia mapeamentos de pastas e arquivos processados (com base no tamanho e data de modificação) para evitar reprocessamento desnecessário.

* **Travessia** Recursiva de **Arquivos Locais:** Capacidade de percorrer recursivamente a estrutura de pastas locais e identificar arquivos e pastas.

* **Sincronização de Estrutura de Pastas:** Criação automática da estrutura de pastas no Google Drive para espelhar a organização local.

* **Upload Resumível de Arquivos:** Suporte a uploads resumíveis para arquivos grandes, garantindo a integridade em caso de interrupções, com tratamento básico de erros.

* **Interface de Linha de Comando (CLI) Avançada:** Utiliza `argparse` para um controle robusto das operações, incluindo:

  * `--authenticate`: Para iniciar o fluxo de autenticação.

  * `--list-local`: Para listar os arquivos locais que seriam considerados para sincronização.

  * `--test-drive-ops`: Para executar operações de teste no Google Drive.

  * `--sync`: Para iniciar o processo de sincronização.

    * `--source-folder`: Para sobrescrever a pasta de origem do `config.ini`.

    * `--target-drive-folder-id`: Para sobrescrever a pasta de destino no Drive do `config.ini`.

    * `--dry-run`: Para simular a sincronização sem fazer alterações reais.

  * `--verify`: Para verificar a consistência dos arquivos sincronizados entre o local, o estado da aplicação e o Google Drive.

* **Verificação de Sincronização:** Compara arquivos locais com o estado registrado e os metadados do Google Drive, reportando discrepâncias.

* **Tratamento Avançado de Erros e Retentativas para API:** Mecanismo configurável de retentativas com backoff exponencial para chamadas à API do Google Drive, aumentando a resiliência contra erros transitórios e limites de cota. (Configurável em `config.ini` na seção `[API_Retries]`)

* **Acompanhamento de Progresso Detalhado:** Exibição de barra de progresso no console (`tqdm`) durante a sincronização de arquivos e um relatório final resumindo a operação (total de arquivos, transferidos, ignorados, falhas, tempo total, etc.).

* **Documentação** e Testes **Manuais:** `README.md` detalhado, docstrings no código e um guia `TESTING_STRATEGY.md`.

### Planejadas (Melhorias Pós-v1.0)

* **Tratamento de Exclusões:** Lógica para lidar com arquivos excluídos localmente ou no Drive.

* **Comparação por Checksum (MD5):** Adicionar verificação opcional de arquivos por checksum MD5 para uma detecção de alterações mais robusta.

* **Suporte para Múltiplas Configurações de Sincronização:** Possibilidade de definir e executar diferentes perfis de sincronização.

* **Interface Gráfica (GUI):** Desenvolvimento de uma interface gráfica para facilitar o uso (consideração futura de longo prazo).

## Configuração e Instalação

1. **Clone o Repositório:**

   ```
   git clone <URL_DO_SEU_REPOSITORIO_NO_GITHUB>
   cd drivesync # Ou o nome da pasta do seu projeto
   
   ```

2. **Crie e Ative um Ambiente Virtual Python:**

   ```
   python -m venv venv
   # Windows (PowerShell)
   .\venv\Scripts\Activate.ps1
   # Windows (CMD)
   .\venv\Scripts\activate.bat
   # Linux/macOS
   source venv/bin/activate
   
   ```

3. **Instale as Dependências:**

   ```
   pip install -r requirements.txt
   
   ```

   *(O arquivo `requirements.txt` será atualizado à medida que novas dependências forem adicionadas).*

4. **Configure as Credenciais da API do Google Drive:**

   * Acesse o [Google Cloud Console](https://console.cloud.google.com/).

   * Crie um novo projeto ou selecione um existente.

   * Ative a "Google Drive API".

   * Crie credenciais do tipo "OAuth client ID" para "Desktop application".

   * Faça o download do arquivo JSON das credenciais. Renomeie este arquivo para o nome especificado em `config.ini` como `client_secret_file` (ex: `credentials_target.json`) e coloque-o na pasta raiz do projeto. **Este arquivo não deve ser enviado para o GitHub.**

   * Na "Tela de consentimento OAuth" do seu projeto no Google Cloud Console, adicione os e-mails dos usuários de teste enquanto o aplicativo estiver em fase de "Teste".

5. **Configure o Arquivo `config.ini`:**

   * Abra o arquivo `config.ini` na raiz do projeto.

   * Ajuste os seguintes valores conforme necessário:

     * `client_secret_file`: (Na seção `[DriveAPI]`) Nome do arquivo JSON de credenciais do Google.

     * `token_file`: (Na seção `[DriveAPI]`) Nome do arquivo onde os tokens OAuth serão armazenados (ex: `token_target.json`).

     * `source_folder`: (Na seção `[Sync]`) O caminho completo para a pasta local que você deseja sincronizar. **Este valor precisa ser configurado por você.**

     * `target_drive_folder_id`: (Na seção `[Sync]`, opcional) ID da pasta no Google Drive onde a sincronização será feita. Se vazio, usará a raiz do Drive.

     * `state_file`: (Na seção `[Sync]`) Nome do arquivo de banco de dados SQLite para armazenar o estado da sincronização (ex: `drivesync_state.db`).

     * `log_file`: (Na seção `[Logging]`) Nome do arquivo de log (ex: `app.log`).

     * `log_level`: (Na seção `[Logging]`) Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL).

     * A seção `[API_Retries]` (opcional, com valores padrão) permite configurar o comportamento de retentativas para chamadas à API do Google Drive, como `max_retries`, `initial_backoff_seconds`, `max_backoff_seconds` e `backoff_factor`.

   **Nota Importante:** Após preencher o `config.ini` e colocar o arquivo de credenciais (`client_secret_file`), execute o comando de autenticação pela primeira vez:

   ```
   python -m drivesync_app.main --authenticate
   
   ```

## Estado da Aplicação

A aplicação mantém seu estado de sincronização em um arquivo de banco de dados SQLite (por padrão `drivesync_state.db`, configurável em `config.ini`). Este arquivo armazena informações críticas para retomar tarefas de sincronização e rastrear itens sincronizados e estruturas de pastas do Drive. É ainda mais crítico não editar este arquivo manualmente, pois isso pode corromper o banco de dados e o estado da sincronização.

## Uso

O DriveSyncApp é controlado via argumentos de linha de comando. Abaixo estão os principais comandos e opções disponíveis.
Para uma lista completa de todos os argumentos e suas descrições, execute:

```
python -m drivesync_app.main --help

```

### Comandos Principais

* **Autenticação:**

  ```
  python -m drivesync_app.main --authenticate
  
  ```

  Este comando inicia o processo de autenticação com o Google Drive. Necessário na primeira execução ou se os tokens de acesso expirarem. As credenciais são salvas localmente (conforme configurado em `config.ini`).

* **Sincronização:**

  ```
  python -m drivesync_app.main --sync [opções...]
  
  ```

  Inicia o processo de sincronização entre a pasta local de origem e a pasta de destino no Google Drive.

  * **Opções de Sincronização:**

    * `--source-folder CAMINHO_DA_PASTA_LOCAL`: Permite especificar uma pasta local de origem para esta execução, sobrescrevendo o valor de `source_folder` em `config.ini`.

    * `--target-drive-folder-id ID_DA_PASTA_DRIVE`: Permite especificar um ID de pasta de destino no Google Drive para esta execução, sobrescrevendo o valor de `target_drive_folder_id` em `config.ini`.

    * `--dry-run`: Simula o processo de sincronização sem realizar quaisquer alterações reais no Google Drive ou no arquivo de estado local. Útil para verificar quais arquivos seriam transferidos ou atualizados.

* **Listar Arquivos Locais:**

  ```
  python -m drivesync_app.main --list-local
  
  ```

  Percorre e lista os arquivos e pastas no `source_folder` configurado (ou sobrescrito via `--source-folder`) que seriam considerados para sincronização.

* **Testar Operações do Drive:**

  ```
  python -m drivesync_app.main --test-drive-ops
  
  ```

  Executa operações de teste no Google Drive, como tentar criar uma pasta de teste e listar o conteúdo da pasta raiz. Requer autenticação prévia.

* **Verificar Sincronização:**

  ```
  python -m drivesync_app.main --verify
  
  ```

  Verifica a consistência dos arquivos sincronizados. Compara os arquivos locais com o estado registrado pelo DriveSync e os metadados dos arquivos correspondentes no Google Drive. Reporta discrepâncias como arquivos locais não presentes no estado, arquivos no estado mas ausentes no Drive (ou na lixeira), e incompatibilidades de tamanho. Requer autenticação prévia.

### Exemplos de Uso

1. **Autenticar o aplicativo:**

   ```
   python -m drivesync_app.main --authenticate
   
   ```

2. **Executar uma sincronização padrão (usando configurações do `config.ini`):**

   ```
   python -m drivesync_app.main --sync
   
   ```

3. **Executar uma simulação de sincronização (dry run):**

   ```
   python -m drivesync_app.main --sync --dry-run
   
   ```

4. **Sincronizar especificando uma pasta de origem e destino diferente:**

   ```
   python -m drivesync_app.main --sync --source-folder "/caminho/para/meus/documentos" --target-drive-folder-id "IDdaPastaNoMeuDrive"
   
   ```

5. **Listar os arquivos locais que seriam sincronizados:**

   ```
   python -m drivesync_app.main --list-local
   
   ```

6. **Verificar a integridade da sincronização:**

   ```
   python -m drivesync_app.main --verify
   
   ```

7. **Ver todas as opções de ajuda:**

   ```
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

    * `sync_logic.py`: Contém a lógica principal de sincronização.

    * `verificador.py`: Verifica a sincronização.

    * `__init__.py`: Define `drivesync_app` como um pacote Python.

  * `config.ini`: Arquivo de configuração.

  * `requirements.txt`: Lista de dependências Python.

  * `.gitignore`: Especifica arquivos ignorados pelo Git.

  * `README.md`: Este arquivo.

  * `TESTING_STRATEGY.md`: Guia para testes manuais.

## Roteiro (Roadmap)

Veja o arquivo `ROADMAP.md` para o detalhamento das próximas etapas de desenvolvimento e tarefas planejadas.
