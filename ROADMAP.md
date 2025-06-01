# ROADMAP do Projeto DriveSync

Este documento detalha o plano de desenvolvimento para o projeto DriveSync, incluindo tarefas concluídas e as próximas etapas a serem implementadas, com prompts sugeridos para o agente de codificação Jules.

## Legenda de Status
* ✅ **Concluído**
* ⏳ **Em Andamento / Próxima Tarefa**
* 📋 **Planejado**

---

## Tarefas Concluídas

### ✅ Tarefa 1: Configuração de Logging e Carregamento de Configuração
* **Resumo:** Implementado `setup_logger` em `drivesync_app/logger_config.py` para logging configurável via `config.ini`. `main.py` modificado para ler `config.ini` e inicializar o logger.
* **Arquivos Modificados:** `drivesync_app/logger_config.py`, `drivesync_app/main.py`, `config.ini`.

### ✅ Tarefa 2: Módulo de Autenticação do Google Drive
* **Resumo:** Implementado o fluxo de autenticação OAuth 2.0 em `drivesync_app/autenticacao_drive.py` usando as bibliotecas da API do Google. `main.py` atualizado para acionar a autenticação via argumento CLI (`--authenticate`) e `requirements.txt` atualizado. `config.ini` atualizado para `token_target.json`.
* **Arquivos Modificados:** `drivesync_app/autenticacao_drive.py`, `drivesync_app/main.py`, `requirements.txt`, `config.ini`.

### ✅ Tarefa 3: Módulo de Gerenciamento de Estado
* **Status:** ✅ **Concluído**
* **Resumo:** Implementado o módulo de gerenciamento de estado em `drivesync_app/gerenciador_estado.py` com funções `load_state` e `save_state` para carregar e salvar o estado da aplicação (e.g., `drivesync_state.json`). Inclui escrita atômica para `save_state` e tratamento de erros. `main.py` atualizado para usar estas funções e `config.ini` atualizado com a chave `state_file`.
* **Arquivos Modificados:** `drivesync_app/gerenciador_estado.py`, `drivesync_app/main.py`, `config.ini`.

### ✅ Tarefa 4: Operações Principais do Drive (Criação de Pastas e Listagem de Arquivos)
* **Status:** ✅ **Concluído**
* **Resumo:** Implementado `find_or_create_folder` e `list_folder_contents` em `drivesync_app/gerenciador_drive.py`. Adicionado `--test-drive-ops` para `main.py` para testar estas interações com o Drive. Inclui tratamento básico de erros e paginação para listagem.
* **Arquivos Modificados:** `drivesync_app/gerenciador_drive.py`, `drivesync_app/main.py`.

### ✅ Tarefa 5: Módulo Processador de Arquivos (Travessia de Arquivos Locais)
* **Status:** ✅ **Concluído**
* **Resumo:** Implementado `walk_local_directory` em `drivesync_app/processador_arquivos.py` para travessia de sistema de arquivos local, usando `os.walk` e `pathlib`. Adicionado argumento `--list-local` a `main.py` para testar esta funcionalidade, lendo `source_folder` de `config.ini`. Bugfix aplicado para `NameError` relacionado a `source_folder`.
* **Arquivos Modificados:** `drivesync_app/processador_arquivos.py`, `drivesync_app/main.py`, `config.ini`.

### ✅ Tarefa 6: Lógica Principal de Sincronização - Fase 1 (Sincronização de Pastas e Upload Básico de Arquivos)
* **Status:** ✅ **Concluído**
* **Resumo:** Implementada a lógica inicial de sincronização em `drivesync_app/sync_logic.py` (invocada por `main.py` via argumento `--sync`). Mapeia estruturas de pastas locais para o Drive e realiza uploads básicos de arquivos. O estado das pastas (`folder_mappings`) é atualizado.
* **Arquivos Modificados:** `drivesync_app/sync_logic.py` (novo), `drivesync_app/main.py`, `drivesync_app/gerenciador_drive.py`.

### ✅ Tarefa 7: Uploads Resumíveis e Tratamento Avançado de Erros para Arquivos
* **Status:** ✅ **Concluído**
* **Resumo:** Aprimorada a função de upload de arquivos em `drivesync_app/gerenciador_drive.py` (agora `upload_file`) para suportar uploads resumíveis, progresso em chunks, e tratamento robusto de erros. `sync_logic.py` atualizado para usar esta nova função.
* **Arquivos Modificados:** `drivesync_app/gerenciador_drive.py`, `drivesync_app/sync_logic.py`.

### ✅ Tarefa 8: Integração Completa do Gerenciamento de Estado (Itens Processados)
* **Status:** ✅ **Concluído**
* **Resumo:** Integrado o gerenciamento de estado completo para arquivos em `drivesync_app/sync_logic.py`. Agora verifica `processed_items` (usando tamanho e data de modificação do arquivo local) para evitar re-uploads desnecessários e atualiza o estado após uploads bem-sucedidos.
* **Arquivos Modificados:** `drivesync_app/sync_logic.py`, `drivesync_app/gerenciador_estado.py`.

### ✅ Tarefa 9: Melhorias na Interface de Linha de Comando (CLI)
* **Status:** ✅ **Concluído**
* **Resumo:** Refatorada a interface de linha de comando em `main.py` para usar o módulo `argparse`. Argumentos existentes (`--authenticate`, `--list-local`, `--test-drive-ops`, `--sync`) foram convertidos para argumentos `argparse`. Adicionados novos argumentos para a ação `sync`: `--source-folder`, `--target-drive-folder-id` (para sobrescrever `config.ini`) e `--dry-run` (para simular a sincronização). Melhoradas as mensagens de ajuda. `sync_logic.py` foi adaptado para suportar o modo `--dry-run`.
* **Arquivos Modificados:** `drivesync_app/main.py`, `drivesync_app/sync_logic.py`.

### ✅ Tarefa 10: Módulo de Verificação de Arquivos
* **Status:** ✅ **Concluído**
* **Resumo:** Implementado o módulo de verificação de arquivos em `drivesync_app/verificador.py` com a função `verify_sync`. Esta função itera pelos arquivos locais, compara-os com o estado (`processed_items`) e verifica os metadados (nome, tamanho, estado de 'trashed') dos arquivos correspondentes no Google Drive. Discrepâncias como arquivos locais não presentes no estado, arquivos no estado mas em falta no Drive (ou na lixeira), e incompatibilidades de tamanho são registradas. Integrado em `main.py` através de um novo argumento CLI `--verify`.
* **Arquivos Modificados:** `drivesync_app/verificador.py`, `drivesync_app/main.py`.

### ✅ Tarefa 11: Otimização e Refinamentos
* **Status:** ✅ **Concluído**
* **Resumo:** Realizada uma revisão geral do código com foco em otimizações e refinamentos. Melhorado o tratamento de erros em `gerenciador_drive.py` (para `find_or_create_folder` e `list_folder_contents`) com logs mais detalhados, incluindo status HTTP e conteúdo do erro. A clareza do código em `sync_logic.py` foi aprimorada com comentários adicionais e um docstring mais completo para a função `run_sync`. Docstrings foram revisados e melhorados para funções chave em `verificador.py`, `autenticacao_drive.py`, `logger_config.py`, e `main.py`. Verificada a utilização correta de parâmetros em `processador_arquivos.py`.
* **Arquivos Modificados:** `drivesync_app/gerenciador_drive.py`, `drivesync_app/sync_logic.py`, `drivesync_app/verificador.py`, `drivesync_app/autenticacao_drive.py`, `drivesync_app/logger_config.py`, `drivesync_app/main.py`, `drivesync_app/processador_arquivos.py`.

### ✅ Tarefa 12: Documentação Final e Testes
* **Status:** ✅ **Concluído**
* **Resumo:** Finalizada a documentação do projeto. Realizada uma revisão completa do `README.md` para garantir que todas as funcionalidades (Tarefas 1-11) estão descritas, as instruções de configuração estão claras e os exemplos de uso da CLI são precisos. Adicionadas/verificadas docstrings em todos os módulos (`autenticacao_drive.py`, `gerenciador_drive.py`, `gerenciador_estado.py`, `logger_config.py`, `main.py`, `processador_arquivos.py`, `sync_logic.py`, `verificador.py`), incluindo docstrings de módulo para melhor entendimento geral. Criado o arquivo `TESTING_STRATEGY.md` com um guia detalhado para testes manuais das principais funcionalidades da aplicação.
* **Arquivos Modificados/Criados:** `README.md`, `TESTING_STRATEGY.md`, `drivesync_app/autenticacao_drive.py`, `drivesync_app/gerenciador_drive.py`, `drivesync_app/gerenciador_estado.py`, `drivesync_app/logger_config.py`, `drivesync_app/main.py`, `drivesync_app/processador_arquivos.py`, `drivesync_app/sync_logic.py`, `drivesync_app/verificador.py`.

---

## Melhorias Pós-v1.0 (Próximas Tarefas)

Com a v1.0 estabelecida, focaremos em robustez e usabilidade para grandes volumes de dados.

### ✅ Tarefa P1: Refatorar Gerenciamento de Estado para Usar SQLite
* **Status:** ✅ **Concluído**
* **Resumo:** Refatorado o `gerenciador_estado.py` para usar SQLite (`drivesync_state.db`) em vez de JSON. Isso incluiu a atualização de `main.py`, `sync_logic.py` e `verificador.py` para interagir com o banco de dados SQLite. O arquivo `config.ini` foi atualizado para o novo nome do arquivo de estado.
* **Objetivo:** Substituir o atual sistema de gerenciamento de estado baseado em JSON por um banco de dados SQLite para melhorar a performance, escalabilidade e robustez no manuseio de dezenas de milhares de arquivos.
* **Prompt para Jules (Inglês):**
    ```
    Refactor the state management module (`drivesync_app/gerenciador_estado.py`) to use SQLite instead of a JSON file for storing synchronization state. The SQLite database file path should be configurable via `state_file` in `config.ini` (e.g., `drivesync_state.db`).

    1.  **Database Schema:**
        * Create a table for `processed_items` with columns: `local_relative_path` (TEXT, PRIMARY KEY), `drive_id` (TEXT), `local_size` (INTEGER), `local_modified_time` (REAL or INTEGER), `drive_md5_checksum` (TEXT, NULLABLE).
        * Create a table for `folder_mappings` with columns: `local_relative_path` (TEXT, PRIMARY KEY), `drive_folder_id` (TEXT).
        * Add indexes on `local_relative_path` for both tables.

    2.  **Refactor `gerenciador_estado.py`**:
        * Replace `load_state` with `initialize_state_db(config)`: Connects to SQLite, creates tables if they don't exist.
        * Replace `save_state` with specific functions:
            * `get_processed_item(db_connection, relative_path)`: Retrieves a specific item's state.
            * `update_processed_item(db_connection, item_details)`: Inserts or updates an item in `processed_items` table. Use 'REPLACE' or 'INSERT OR IGNORE' appropriately.
            * `get_folder_mapping(db_connection, relative_path)`: Retrieves a folder mapping.
            * `update_folder_mapping(db_connection, mapping_details)`: Inserts or updates a folder mapping.
        * Ensure database connections are managed correctly (opened, closed, use context managers if possible).
        * Use transactions for database writes to ensure atomicity.

    3.  **Update `drivesync_app/main.py` and `drivesync_app/sync_logic.py`:**
        * Adapt these modules to use the new SQLite-based state management functions. Instead of loading the entire state into a dictionary, they will query the database for specific entries as needed and update entries individually or in batches.
        * The `app_state` variable might now hold just the DB connection or a state manager class instance.

    Add `sqlite3` (standard library) usage. Ensure robust error handling for all database operations.
    ```
* **Arquivos a Modificar:** `drivesync_app/gerenciador_estado.py`, `drivesync_app/main.py`, `drivesync_app/sync_logic.py`, `config.ini`.
* **Considerações:** Esta é uma mudança estrutural significativa, mas crucial para a performance e escalabilidade com mais de 100.000 arquivos.

---

### ✅ Tarefa P2: Implementar Tratamento Avançado de Erros e Retentativas para API do Drive
* **Status:** ✅ **Concluído**
* **Resumo:** Implementado um mecanismo de retentativa configurável com backoff exponencial para todas as chamadas à API do Google Drive em `gerenciador_drive.py` usando um decorador. As configurações de retentativa (`max_retries`, `initial_backoff_seconds`, etc.) são definidas na nova seção `[API_Retries]` do `config.ini`. `sync_logic.py` e `verificador.py` foram atualizados para usar as funções com retentativa e para lidar com falhas persistentes de forma mais robusta.
* **Objetivo:** Tornar a aplicação significativamente mais resiliente a erros transitórios da API do Google Drive e a problemas de cota, implementando um mecanismo de retentativa configurável com backoff exponencial.
* **Prompt para Jules (Inglês):**
    ```
    Enhance all Google Drive API call handling in `drivesync_app/gerenciador_drive.py` to implement a sophisticated and configurable retry mechanism with exponential backoff for API errors. This should build upon or replace any basic retry logic currently in place.

    1.  **Create a Decorator or Wrapper Function for API Calls:**
        * This function (e.g., `@retry_with_backoff` or `execute_api_call_with_retry`) will wrap the actual Google Drive API calls (e.g., `drive_service.files().create(...)`, `drive_service.files().list(...)`, `drive_service.files().get(...)`).
        * It should handle the execution and retry logic.

    2.  **Configurable Retry Parameters (in `config.ini`****):**
        * Create a new section, e.g., `[API_Retries]`.
        * Add keys:
            * `max_retries`: Maximum number of retries for a single operation (e.g., 5).
            * `initial_backoff_seconds`: Initial wait time (e.g., 2).
            * `max_backoff_seconds`: Maximum wait time for a single retry (e.g., 60).
            * `backoff_factor`: Multiplier (e.g., 2 for exponential).
        * The wrapper/decorator should read these values from the loaded config.

    3.  **Error Identification for Retries:**
        * Specifically catch `googleapiclient.errors.HttpError`.
        * Retry on specific HTTP status codes: `403` (especially with reasons `rateLimitExceeded` or `userRateLimitExceeded`), `500`, `502`, `503`, `504`.
        * Other errors (e.g., `401 Invalid Credentials`, `404 Not Found` when the item *should* exist, `400 Bad Request`) should probably not be retried extensively or at all, and should be logged and propagated to let the calling function decide how to handle (e.g., skip item, mark as failed).

    4.  **Exponential Backoff and Jitter:**
        * Implement the exponential backoff: `wait_time = min(initial_backoff_seconds * (backoff_factor ** (attempt_number -1)), max_backoff_seconds)`.
        * Add a small amount of random jitter to the wait time (e.g., `wait_time += random.uniform(0, 0.2 * wait_time)`) to prevent thundering herd issues.
        * Log the error, retry attempt number, and calculated wait time before `time.sleep()`.

    5.  **Handling Max Retries Exceeded:**
        * If an operation fails after `max_retries`, log a critical error for that specific operation/item.
        * The wrapper should then re-raise the last encountered exception or return a specific failure indicator so that the calling code in `sync_logic.py` or `main.py` can mark the item as "failed" in the state and continue with other items, rather than halting the entire sync.

    6.  **Apply to All Relevant API Calls:**
        * Refactor all functions in `drivesync_app/gerenciador_drive.py` (`find_or_create_folder`, `list_folder_contents`, `upload_file`, and any new ones like `delete_file`, `update_file_metadata` if added later) to use this retry mechanism.
    ```
* **Arquivos a Modificar:** `drivesync_app/gerenciador_drive.py`, `config.ini`, `drivesync_app/sync_logic.py` (para lidar com falhas persistentes).
* **Considerações:** Essencial para a confiabilidade em sincronizações longas e com muitos arquivos, que certamente encontrarão limites de API.

---

### ✅ Tarefa P3: Implementar Acompanhamento Aprimorado de Progresso e Relatórios
* **Status:** ✅ **Concluído**
* **Resumo:** Adicionada barra de progresso (`tqdm`) para visualização do andamento da sincronização de arquivos em `sync_logic.py`. Implementado um relatório final detalhado ao término da sincronização, com estatísticas sobre arquivos processados, transferidos, ignorados, falhas, tempo total e volume de dados. `tqdm` adicionado às dependências.
* **Objetivo:** Fornecer feedback visual e sumários mais claros sobre o progresso da sincronização, especialmente útil para grandes volumes de dados, para que o utilizador entenda melhor o que está a acontecer e quanto falta.
* **Prompt para Jules (Inglês):**
    ```
    Enhance the application to provide better progress tracking for large synchronization tasks. This involves adding overall progress bars, per-file progress details, periodic summaries, and a final report.

    1.  **Overall Progress Bar (Console):**
        * Integrate the `tqdm` library (add `tqdm` to `requirements.txt`).
        * In `drivesync_app/sync_logic.py` (within the `run_sync` function):
            * Before starting the main loop over local files, if not already done, perform a preliminary scan using `processador_arquivos.walk_local_directory()` to get the total number of files to be processed (or total size).
            * Initialize a `tqdm` progress bar with this total.
            * Update the progress bar (`bar.update(1)`) after each file is processed (uploaded, skipped, or failed).
            * Set the progress bar's description to show the currently processing file name or action (e.g., `bar.set_description(f"Processing {item['name']}")`).

    2.  **Detailed Per-File Upload Progress:**
        * Modify the `upload_file` function in `drivesync_app/gerenciador_drive.py`.
        * When using `MediaFileUpload` with `resumable=True`, the `next_chunk()` method returns status information. Use this to log the percentage completion of the current large file upload or update a secondary `tqdm` bar if feasible for per-file progress, or update a dynamic part of the main `tqdm` bar's postfix.

    3.  **Periodic Summary Logs (Optional, if `tqdm` isn't sufficient):**
        * If the `tqdm` bar doesn't provide enough summary, consider adding logic in `sync_logic.py` to log a concise summary every N files or every X minutes (e.g., "INFO - Progress: 45200/100000 files. Uploaded: 350.7/1024 GB. Failed: 5 items.").

    4.  **Final Sync Report:**
        * At the end of the `run_sync` function in `sync_logic.py`, collect and log a comprehensive summary:
            * Total time taken for the sync operation.
            * Total local files scanned/considered.
            * Number of files successfully uploaded/updated.
            * Number of files skipped (already up-to-date).
            * Number of files that failed to sync (with a count).
            * Total data transferred during this session (approximate).
            * A message температураing to check `app.log` for detailed errors if failures occurred.

    Ensure these progress updates are well-integrated with the existing logging system and do not produce excessive noise if the user selects a higher log level like WARNING or ERROR. The `tqdm` output should go to `sys.stdout` or `sys.stderr` as appropriate and work alongside file logging.
    ```
* **Arquivos a Modificar:** `drivesync_app/sync_logic.py`, `drivesync_app/main.py`, `drivesync_app/gerenciador_drive.py`, `drivesync_app/processador_arquivos.py` (potencialmente para contagem total), `requirements.txt` (para adicionar `tqdm`), `config.ini` (potencialmente para configurações de resumo periódico).
* **Considerações:** A contagem inicial de todos os ficheiros/tamanho total para o `tqdm` pode adicionar um pequeno atraso no início de uma sincronização muito grande, mas o benefício do feedback visual geralmente compensa.

---

## Melhorias Pós-v1.0 Concluídas

Todas as tarefas de melhoria Pós-v1.0 planejadas (P1, P2, P3) foram concluídas. O foco agora se volta para os "Possíveis Trabalhos Futuros" listados abaixo.

## Possíveis Trabalhos Futuros (Fora do Escopo Original)
* Implementação de tratamento para exclusões de arquivos (local ou Drive).
* Comparação de arquivos por checksum MD5 para maior robustez na detecção de alterações (além de tamanho e data de modificação).
* Suporte para múltiplas configurações/perfis de sincronização.
* Desenvolvimento de uma interface gráfica (GUI).
