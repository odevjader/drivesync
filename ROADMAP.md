# ROADMAP do Projeto DriveSync

Este documento detalha o plano de desenvolvimento para o projeto DriveSync, incluindo tarefas concluídas e as próximas etapas a serem implementadas, com prompts sugeridos para o agente de codificação Jules.

## Legenda de Status
* ✅ **Concluído**
* ⏳ **Em Andamento / Próxima Tarefa**
* 📋 **Planejado**

---

## Tarefas Concluídas

### ✅ Tarefa 1: Configuração de Logging e Carregamento de Configuração
* **Branch:** `feature/logging-config-setup` (ou similar)
* **Resumo:** Implementado `setup_logger` em `drivesync_app/logger_config.py` para logging configurável via `config.ini`. `main.py` modificado para ler `config.ini` e inicializar o logger.
* **Ficheiros Modificados:** `drivesync_app/logger_config.py`, `drivesync_app/main.py`, `config.ini`.

### ✅ Tarefa 2: Módulo de Autenticação do Google Drive
* **Branch:** `feature/drive-authentication` (ou similar)
* **Resumo:** Implementado o fluxo de autenticação OAuth 2.0 em `drivesync_app/autenticacao_drive.py` usando as bibliotecas da API do Google. `main.py` atualizado para acionar a autenticação via argumento CLI (`--authenticate`) e `requirements.txt` atualizado. `config.ini` atualizado para `token_target.json`.
* **Ficheiros Modificados:** `drivesync_app/autenticacao_drive.py`, `drivesync_app/main.py`, `requirements.txt`, `config.ini`.

### ✅ Tarefa 3: Módulo de Gerenciamento de Estado
* **Status:** ✅ **Concluído**
* **Branch:** `feature/state-management`
* **Resumo:** Implementado o módulo de gerenciamento de estado em `drivesync_app/gerenciador_estado.py` com funções `load_state` e `save_state` para carregar e salvar o estado da aplicação (e.g., `drivesync_state.json`). Inclui escrita atómica para `save_state` e tratamento de erros. `main.py` atualizado para usar estas funções e `config.ini` atualizado com a chave `state_file`.
* **Ficheiros Modificados:** `drivesync_app/gerenciador_estado.py`, `drivesync_app/main.py`, `config.ini`.

---

## Próximas Tarefas (para Jules)

### ⏳ Tarefa 4: Operações Principais do Drive (Criação de Pastas e Listagem de Ficheiros)
* **Branch Sugerida:** `feature/drive-core-operations`
* **Prompt para Jules (Inglês):**
    ```
    Implement core Google Drive operations in `drivesync_app/gerenciador_drive.py`.
    This module will use the authenticated Drive service object obtained from `autenticacao_drive.py`.

    Implement the following functions:

    1.  `find_or_create_folder(drive_service, parent_folder_id, folder_name)`:
        * Accepts the `drive_service` object, the `parent_folder_id` (can be 'root' or an actual folder ID for subfolders), and the `folder_name` to find or create.
        * Searches for a folder with `folder_name` and `mimeType='application/vnd.google-apps.folder'` under the specified `parent_folder_id`.
        * If multiple folders with the same name exist, log a warning and use the first one found.
        * If found, return its ID.
        * If not found, create the folder under `parent_folder_id` with `folder_name` and return the new folder's ID.
        * Implement robust error handling for API calls, including retries with exponential backoff for common transient errors (e.g., rate limits, server errors). Log API errors.

    2.  `list_folder_contents(drive_service, folder_id)`:
        * Accepts the `drive_service` object and a `folder_id`.
        * Lists all files and folders directly within the given `folder_id`.
        * The query should retrieve `id`, `name`, `mimeType`, `md5Checksum` (for files), and `modifiedTime` for each item.
        * Handle API pagination to retrieve all items if the folder contains many entries.
        * Return a dictionary where keys are item names and values are dictionaries containing their `id`, `mimeType`, `md5Checksum` (if applicable), and `modifiedTime`.
        * Implement error handling and retries as above.

    Modify `drivesync_app/main.py`:
    * Add a new command-line argument, e.g., `--test-drive-ops`.
    * If this argument is provided, after authentication, perform test operations:
        * Attempt to find or create a test folder (e.g., "DriveSync Test Folder") in the root of the user's Drive. Log the ID of this folder.
        * Attempt to list the contents of the user's root Drive folder. Log the names and types of the first few items found.
    ```
* **Ficheiros a Modificar:** `drivesync_app/gerenciador_drive.py`, `drivesync_app/main.py`.
* **Considerações:** Tratamento de erros da API do Drive, paginação, e a importância do `mimeType` para diferenciar ficheiros de pastas.

---

### 📋 Tarefa 5: Módulo Processador de Ficheiros (Travessia de Ficheiros Locais)
* **Branch Sugerida:** `feature/local-file-processor`
* **Prompt para Jules (Inglês):**
    ```
    Implement a module `drivesync_app/processador_arquivos.py` to handle local file system traversal.

    Create a function `walk_local_directory(local_folder_path)`:
    * Accepts the `local_folder_path` (to be read from `config.ini` eventually, but can be hardcoded for initial testing or passed as an argument).
    * Uses `os.walk()` to recursively traverse the given directory.
    * For each directory found, it should yield a dictionary containing: `{'type': 'folder', 'path': 'relative_path_to_folder', 'name': 'folder_name'}`. The path should be relative to the initial `local_folder_path`.
    * For each file found, it should yield a dictionary containing: `{'type': 'file', 'path': 'relative_path_to_file', 'name': 'file_name', 'full_path': 'absolute_path_to_file', 'size': file_size_in_bytes, 'modified_time': last_modified_timestamp}`. The path should be relative.
    * Log errors if any directory or file cannot be accessed (e.g., permission errors).
    * Ensure paths are handled correctly across different operating systems (consider using `pathlib`).

    Modify `drivesync_app/main.py`:
    * Add a new command-line argument, e.g., `--list-local`.
    * If this argument is provided:
        * Read the `source_folder` path from `config.ini`.
        * Call `walk_local_directory` with this path.
        * Iterate through the yielded items and log their details (type, relative path, name).
    ```
* **Ficheiros a Modificar:** `drivesync_app/processador_arquivos.py`, `drivesync_app/main.py`.
* **Considerações:** Uso de `os.walk()`, cálculo de caminhos relativos, e tratamento de erros de permissão. `pathlib` é recomendado para manipulação de caminhos.

---

### 📋 Tarefa 6: Lógica Principal de Sincronização - Fase 1 (Sincronização de Pastas e Upload Básico de Ficheiros)
* **Branch Sugerida:** `feature/sync-logic-phase1`
* **Prompt para Jules (Inglês):**
    ```
    Integrate the local file processing with Drive operations to implement the initial synchronization logic in `drivesync_app/main.py` or a new dedicated sync module if preferred.

    1.  **Define a main sync function/method:** This function will orchestrate the process.
    2.  **Command-Line Argument:** Add a `--sync` argument to `main.py` to trigger this function.
    3.  **Process Flow:**
        * Load configuration, setup logger, authenticate with Google Drive, load state.
        * Get the `source_folder` from config and `target_drive_folder_id` (or 'root' if not specified).
        * Use `processador_arquivos.walk_local_directory()` to iterate through local items.
        * **For each local folder:**
            * Use `gerenciador_estado.load_state()` to check if this folder's relative path has already been mapped to a Drive folder ID (`folder_mappings`).
            * If not mapped, or if you want to ensure it exists, use `gerenciador_drive.find_or_create_folder()` to find/create the corresponding folder on Google Drive. The parent ID for subfolders will be the Drive ID of their local parent folder (this requires careful tracking of parent Drive IDs).
            * Store the mapping (local relative path -> Drive folder ID) in the `folder_mappings` part of the state using `gerenciador_estado.save_state()` after each successful mapping or in batches.
        * **For each local file:**
            * (For this phase, a basic check) Use `gerenciador_estado.load_state()` to check if this file (e.g., by its relative path) is in `processed_items`. If so, log and skip for now.
            * Determine its parent Drive folder ID using the `folder_mappings` from the state.
            * Implement a basic file upload in `gerenciador_drive.py`: `upload_basic_file(drive_service, local_file_path, file_name, parent_drive_folder_id)`. This initial version can use `MediaFileUpload` without advanced resumable features for now.
            * Call this upload function.
            * Log success/failure. (State update for files will be in a later task).
        * Ensure `gerenciador_estado.save_state()` is called periodically or at the end to save `folder_mappings`.

    Focus on correctly mapping and creating the folder structure on Drive and performing basic uploads. Detailed file state tracking and resumable uploads will be next.
    ```
* **Ficheiros a Modificar:** `drivesync_app/main.py`, `drivesync_app/gerenciador_drive.py`, `drivesync_app/processador_arquivos.py` (potentially for easier integration), `drivesync_app/gerenciador_estado.py` (to ensure state structure supports folder mappings).
* **Considerações:** Esta é uma tarefa complexa. A lógica de mapear a estrutura de pastas locais para o Drive e gerir os IDs das pastas pai no Drive é crucial.

---

### 📋 Tarefa 7: Uploads Resumíveis e Tratamento Avançado de Erros para Ficheiros
* **Branch Sugerida:** `feature/resumable-uploads`
* **Prompt para Jules (Inglês):**
    ```
    Enhance the file upload functionality in `drivesync_app/gerenciador_drive.py` to support resumable uploads for large files and implement more robust error handling.

    1.  **Modify/Create `upload_file(drive_service, local_file_path, file_name, parent_drive_folder_id, mime_type=None)` function:**
        * Use `MediaFileUpload` with `resumable=True`.
        * Allow specifying `mime_type`; if None, try to guess it (e.g., using `mimetypes` module).
        * Implement a loop to handle `next_chunk()` for resumable uploads, logging progress (e.g., percentage complete).
        * Implement robust error handling for API calls during upload (e.g., `googleapiclient.errors.HttpError`), including retries with exponential backoff for transient errors.
        * Return the Drive file ID upon successful upload, or None/raise exception on failure.
    2.  **Integrate with `main.py`'s sync logic:** Replace the `upload_basic_file` call with this new `upload_file` function.
    ```
* **Ficheiros a Modificar:** `drivesync_app/gerenciador_drive.py`, `drivesync_app/main.py`.
* **Considerações:** Detalhes da API de upload resumível do Google.

---

### 📋 Tarefa 8: Integração Completa do Gerenciamento de Estado (Itens Processados)
* **Branch Sugerida:** `feature/full-state-integration`
* **Prompt para Jules (Inglês):**
    ```
    Fully integrate state management with the file processing and upload logic.

    1.  **Refine State Structure for `processed_items`:** The value for each processed item (keyed by its relative local path) in `gerenciador_estado.state_data['processed_items']` should store information like:
        * `drive_id`: The Google Drive ID of the uploaded file.
        * `local_size`: Size of the local file when it was uploaded.
        * `local_modified_time`: Last modified timestamp of the local file.
        * `md5_checksum_drive` (Optional, if retrieved post-upload): MD5 checksum from Drive.
    2.  **Update Sync Logic in `main.py`:**
        * Before attempting to upload a file, check `processed_items`:
            * If the file's relative path exists in `processed_items`, compare its current `local_size` and `local_modified_time` with the stored values.
            * If they match, log that the file is already synced and skip it.
            * If they differ, log that the file has changed and proceed to re-upload (potentially deleting the old one on Drive or versioning - for now, simple re-upload is fine).
        * After a successful file upload using `gerenciador_drive.upload_file()`, update the `processed_items` in the state with the new file's details (Drive ID, local size, local modified time).
        * Ensure `gerenciador_estado.save_state(config, current_state)` is called after processing each file or in small batches to persist progress.
    ```
* **Ficheiros a Modificar:** `drivesync_app/main.py`, `drivesync_app/gerenciador_estado.py`.
* **Considerações:** Decidir a estratégia para ficheiros modificados (re-upload, versionamento). Garantir que o estado é salvo frequentemente.

---

### 📋 Tarefa 9: Melhorias na Interface de Linha de Comando (CLI)
* **Branch Sugerida:** `feature/cli-improvements`
* **Prompt para Jules (Inglês):**
    ```
    Enhance the command-line interface in `drivesync_app/main.py` using the `argparse` module.

    1.  **Implement `argparse`:**
        * Define a main parser and subparsers if necessary (e.g., for `sync`, `auth`, `verify` commands).
        * Current arguments like `--authenticate`, `--list-local`, `--test-drive-ops`, `--sync` should be converted to proper `argparse` arguments or subcommands.
    2.  **Arguments for `sync` command (if using subparsers):**
        * Optional: `--source-folder` (override `config.ini`).
        * Optional: `--target-drive-folder-id` (override `config.ini`).
        * Optional: `--dry-run` (simulate sync without making changes).
    3.  **Help Messages:** Provide clear help messages for all arguments and commands.
    4.  **Refactor `main.py`:** Structure the main execution block to call different functions based on the parsed arguments.
    ```
* **Ficheiros a Modificar:** `drivesync_app/main.py`.
* **Considerações:** Design de uma CLI intuitiva.

---

### 📋 Tarefa 10: Módulo de Verificação de Ficheiros
* **Branch Sugerida:** `feature/file-verification`
* **Prompt para Jules (Inglês):**
    ```
    Implement the file verification module in `drivesync_app/verificador.py` and integrate it into `main.py`.

    1.  **Create `verify_sync(config, drive_service, current_state)` function in `verificador.py`:**
        * Iterate through local files using `processador_arquivos.walk_local_directory()`.
        * For each local file, check if it's listed in `current_state['processed_items']`.
            * If not, log it as "local file not found in sync state".
            * If yes, retrieve its Drive ID from the state.
            * (Optional but recommended) Use `drive_service.files().get()` with `fields='id,name,md5Checksum,size'` to fetch metadata for the file from Drive using its ID.
            * Compare local file size with Drive file size (if available in Drive metadata).
            * (More advanced) If local MD5 can be calculated, compare with `md5Checksum` from Drive.
            * Log any discrepancies found (e.g., "size mismatch", "checksum mismatch", "file missing on Drive but in state").
        * (Optional) List files in the target Drive folder structure and check if any exist on Drive but are not in the local source or in the sync state (orphaned files on Drive).
    2.  **Integrate into `main.py`:**
        * Add a `--verify` command-line argument.
        * If `--verify` is passed, after authentication and loading state, call `verificador.verify_sync()`.
    ```
* **Ficheiros a Modificar:** `drivesync_app/verificador.py`, `drivesync_app/main.py`.
* **Considerações:** A verificação pode ser intensiva em API calls. Cálculo de MD5 local pode ser lento para ficheiros grandes.

---

### 📋 Tarefa 11: Otimização e Refinamentos
* **Branch Sugerida:** `feature/optimizations`
* **Prompt para Jules (Inglês):**
    ```
    Review the entire codebase for potential optimizations and refinements.
    Tasks could include:
    1.  **Performance:** Identify any bottlenecks. Can API calls be batched (if supported and beneficial)? Is local file processing efficient?
    2.  **Error Handling:** Ensure consistent and comprehensive error logging across all modules. Are there any unhandled exceptions?
    3.  **Code Clarity:** Refactor complex sections for better readability. Improve comments and docstrings.
    4.  **Resource Management:** Ensure API service objects, file handles, etc., are managed correctly.
    5.  **Configuration:** Are all necessary options configurable? Is `config.ini` well-structured?
    ```
* **Ficheiros a Modificar:** Vários, conforme necessário.
* **Considerações:** Esta é uma tarefa mais aberta, focada na qualidade geral do código.

---

### 📋 Tarefa 12: Documentação Final e Testes
* **Branch Sugerida:** `feature/final-docs-testing`
* **Prompt para Jules (Inglês):**
    ```
    Finalize all documentation and add more comprehensive testing notes or examples.
    Tasks:
    1.  **Update `README.md`:** Ensure all features, setup instructions, and usage examples are complete and accurate.
    2.  **Docstrings and Comments:** Review all modules and functions to ensure they have clear, concise docstrings and inline comments where necessary.
    3.  **Usage Examples:** Provide more detailed usage examples in the `README.md` or a separate `USAGE.md` file.
    4.  **Testing Strategy (Notes):** Document a manual testing strategy or provide examples of how to test different functionalities. (Automated tests are out of scope for Jules for now unless specifically requested later).
    ```
* **Ficheiros a Modificar:** `README.md`, todos os ficheiros `.py` para docstrings/comentários.
* **Considerações:** Foco na usabilidade e manutenibilidade do projeto.

---
