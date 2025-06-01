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

### ✅ Tarefa 4: Operações Principais do Drive (Criação de Pastas e Listagem de Ficheiros)
* **Status:** ✅ **Concluído**
* **Branch:** `feature/drive-core-operations`
* **Resumo:** Implementado `find_or_create_folder` e `list_folder_contents` em `drivesync_app/gerenciador_drive.py`. Adicionado `--test-drive-ops` para `main.py` para testar estas interações com o Drive. Inclui tratamento básico de erros e paginação para listagem.
* **Ficheiros Modificados:** `drivesync_app/gerenciador_drive.py`, `drivesync_app/main.py`.

### ✅ Tarefa 5: Módulo Processador de Ficheiros (Travessia de Ficheiros Locais)
* **Status:** ✅ **Concluído**
* **Branch:** `feature/local-file-processor`
* **Resumo:** Implementado `walk_local_directory` em `drivesync_app/processador_arquivos.py` para travessia de sistema de ficheiros local, usando `os.walk` e `pathlib`. Adicionado argumento `--list-local` a `main.py` para testar esta funcionalidade, lendo `source_folder` de `config.ini`.
* **Ficheiros Modificados:** `drivesync_app/processador_arquivos.py`, `drivesync_app/main.py`, `config.ini`.

### ✅ Tarefa 6: Lógica Principal de Sincronização - Fase 1 (Sincronização de Pastas e Upload Básico de Ficheiros)
* **Status:** ✅ **Concluído**
* **Resumo:** Implementada a lógica inicial de sincronização em `drivesync_app/sync_logic.py` (invocada por `main.py` via argumento `--sync`). Mapeia estruturas de pastas locais para o Drive e realiza uploads básicos de arquivos. O estado das pastas (`folder_mappings`) é atualizado.
* **Ficheiros Modificados:** `drivesync_app/sync_logic.py`, `drivesync_app/main.py`, `drivesync_app/gerenciador_drive.py`.

### ✅ Tarefa 7: Uploads Resumíveis e Tratamento Avançado de Erros para Ficheiros
* **Status:** ✅ **Concluído**
* **Resumo:** Aprimorada a função de upload de arquivos em `drivesync_app/gerenciador_drive.py` (agora `upload_file`) para suportar uploads resumíveis, progresso em chunks, e tratamento robusto de erros com retentativas exponenciais. `sync_logic.py` atualizado para usar esta nova função.
* **Ficheiros Modificados:** `drivesync_app/gerenciador_drive.py`, `drivesync_app/sync_logic.py`.

### ✅ Tarefa 8: Integração Completa do Gerenciamento de Estado (Itens Processados)
* **Status:** ✅ **Concluído**
* **Resumo:** Integrado o gerenciamento de estado completo para arquivos em `drivesync_app/sync_logic.py`. Agora verifica `processed_items` (usando tamanho e data de modificação do arquivo local) para evitar re-uploads desnecessários e atualiza o estado após uploads bem-sucedidos.
* **Ficheiros Modificados:** `drivesync_app/sync_logic.py`, `drivesync_app/gerenciador_estado.py`.

---

## Próximas Tarefas (para Jules)

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
