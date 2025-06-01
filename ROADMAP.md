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

### ✅ Tarefa 9: Melhorias na Interface de Linha de Comando (CLI)
* **Status:** ✅ **Concluído**
* **Resumo:** Refatorada a interface de linha de comando em `main.py` para usar o módulo `argparse`. Argumentos existentes (`--authenticate`, `--list-local`, `--test-drive-ops`, `--sync`) foram convertidos para argumentos `argparse`. Adicionados novos argumentos para a ação `sync`: `--source-folder`, `--target-drive-folder-id` (para sobrescrever `config.ini`) e `--dry-run` (para simular a sincronização). Melhoradas as mensagens de ajuda. `sync_logic.py` foi adaptado para suportar o modo `--dry-run`.
* **Ficheiros Modificados:** `drivesync_app/main.py`, `drivesync_app/sync_logic.py`.

### ✅ Tarefa 10: Módulo de Verificação de Ficheiros
* **Status:** ✅ **Concluído**
* **Resumo:** Implementado o módulo de verificação de ficheiros em `drivesync_app/verificador.py` com a função `verify_sync`. Esta função itera pelos ficheiros locais, compara-os com o estado (`processed_items`) e verifica os metadados (nome, tamanho, estado de 'trashed') dos ficheiros correspondentes no Google Drive. Discrepâncias como ficheiros locais não presentes no estado, ficheiros no estado mas em falta no Drive (ou na lixeira), e incompatibilidades de tamanho são registadas. Integrado em `main.py` através de um novo argumento CLI `--verify`.
* **Ficheiros Modificados:** `drivesync_app/verificador.py`, `drivesync_app/main.py`.

### ✅ Tarefa 11: Otimização e Refinamentos
* **Status:** ✅ **Concluído**
* **Resumo:** Realizada uma revisão geral do código com foco em otimizações e refinamentos. Melhorado o tratamento de erros em `gerenciador_drive.py` (para `find_or_create_folder` e `list_folder_contents`) com logs mais detalhados, incluindo status HTTP e conteúdo do erro. A clareza do código em `sync_logic.py` foi aprimorada com comentários adicionais e um docstring mais completo para a função `run_sync`. Docstrings foram revisados e melhorados para funções chave em `verificador.py`, `autenticacao_drive.py`, `logger_config.py`, e `main.py`. Verificada a utilização correta de parâmetros em `processador_arquivos.py`.
* **Ficheiros Modificados:** `drivesync_app/gerenciador_drive.py`, `drivesync_app/sync_logic.py`, `drivesync_app/verificador.py`, `drivesync_app/autenticacao_drive.py`, `drivesync_app/logger_config.py`, `drivesync_app/main.py`, `drivesync_app/processador_arquivos.py`.

---

## Próximas Tarefas (para Jules)

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
