# Estratégia de Testes Manuais para o DriveSyncApp

Este documento descreve uma estratégia de testes manuais para verificar as principais funcionalidades do DriveSyncApp.

## Preparação do Ambiente de Teste

1.  **Conta Google Drive:** Utilize uma conta Google Drive para testes. É recomendável criar uma pasta de teste específica no Drive para evitar interferência com arquivos importantes.
2.  **Arquivo de Credenciais:** Obtenha o arquivo `credentials.json` (ou `client_secret.json`) do Google Cloud Console e coloque-o no diretório raiz do projeto (ou no local configurado).
3.  **Pasta Local de Teste:** Crie uma pasta local no seu sistema para ser o `source_folder`. Popule esta pasta com uma variedade de arquivos e subpastas:
    *   Arquivos pequenos e grandes.
    *   Diferentes tipos de arquivos (texto, imagens, etc.).
    *   Nomes de arquivos/pastas com espaços e caracteres especiais (se suportado).
    *   Estrutura de subpastas com alguma profundidade.
4.  **Arquivo `config.ini`:**
    *   Configure `client_secret_file` para apontar para o seu arquivo de credenciais.
    *   Configure `token_file` (e.g., `token_teste.json`).
    *   Configure `source_folder` para a sua pasta local de teste.
    *   Configure `target_drive_folder_id` para o ID da pasta de teste no Google Drive (ou deixe em branco/comente para usar a raiz, mas uma pasta específica é melhor para testes).
    *   Configure `state_file` (e.g., `estado_teste.json`).
    *   Configure `log_file` e `log_level` (e.g., `DEBUG` para testes detalhados).
5.  **Estado Inicial:** Para testes de sincronização inicial, certifique-se de que o `state_file` (e.g., `estado_teste.json`) não exista ou esteja vazio (`{}`). A pasta de destino no Drive também deve estar vazia.

## Casos de Teste

### 1. Autenticação (`--authenticate`)

*   **Ação:** Execute `python -m drivesync_app.main --authenticate`.
*   **Configuração Adicional:** Se `token_file` já existir, remova-o para simular a autenticação inicial.
*   **Resultado Esperado:**
    *   O navegador deve abrir uma página de login do Google e solicitar permissões.
    *   Após a autorização, o `token_file` especificado no `config.ini` deve ser criado/atualizado.
    *   Logs devem indicar sucesso na autenticação.
*   **Verificação Adicional:** Execute novamente com o `token_file` existente. A autenticação deve ocorrer sem abrir o navegador.

### 2. Listagem de Arquivos Locais (`--list-local`)

*   **Ação:** Execute `python -m drivesync_app.main --list-local`.
*   **Resultado Esperado:**
    *   Os logs devem listar todos os arquivos e pastas presentes na `source_folder` configurada, com seus caminhos relativos, nomes e tamanhos (para arquivos).
    *   A contagem de itens deve ser precisa.

### 3. Operações de Teste do Drive (`--test-drive-ops`)

*   **Ação:** Execute `python -m drivesync_app.main --test-drive-ops`. (Requer autenticação prévia).
*   **Resultado Esperado:**
    *   Logs devem indicar a tentativa de encontrar/criar uma pasta chamada "DriveSync Test Folder" na raiz do Drive (ou na pasta de destino, dependendo da implementação exata do teste).
    *   Logs devem listar o conteúdo da pasta raiz do Drive (ou da pasta de destino).
    *   Verifique no Google Drive se a pasta de teste foi criada.

### 4. Sincronização Inicial (`--sync`)

*   **Configuração Adicional:**
    *   `source_folder` populada com arquivos/pastas.
    *   `target_drive_folder_id` apontando para uma pasta vazia no Drive.
    *   `state_file` inexistente ou vazio.
*   **Ação:** Execute `python -m drivesync_app.main --sync`.
*   **Resultado Esperado:**
    *   Todos os arquivos e pastas da `source_folder` devem ser replicados no `target_drive_folder_id` no Google Drive.
    *   Logs devem indicar a criação de pastas e o upload de arquivos.
    *   O `state_file` deve ser criado e populado com `folder_mappings` e `processed_items` (com `drive_id`, `local_size`, `local_modified_time` para cada arquivo).
*   **Verificação:** Compare manualmente a estrutura e o conteúdo da `source_folder` com a pasta no Google Drive. Verifique o conteúdo do `state_file`.

### 5. Sincronização Incremental (Adicionar/Modificar Arquivos)

*   **Configuração Adicional:** Após uma sincronização inicial bem-sucedida.
    *   Adicione novos arquivos/pastas à `source_folder`.
    *   Modifique alguns arquivos existentes na `source_folder` (altere o conteúdo para mudar o tamanho e/ou data de modificação).
*   **Ação:** Execute `python -m drivesync_app.main --sync`.
*   **Resultado Esperado:**
    *   Apenas os arquivos/pastas novos ou modificados devem ser processados (upload/criação).
    *   Arquivos não modificados devem ser ignorados (logs devem indicar "already synced and unchanged").
    *   Novos itens devem aparecer no Drive e no `state_file`.
    *   Itens modificados devem ter seus dados atualizados no `state_file` e serem re-uploadados.
*   **Verificação:** Verifique no Drive e no `state_file`.

### 6. Sincronização com `--dry-run`

*   **Configuração Adicional:** Similar à sincronização inicial ou incremental.
*   **Ação:** Execute `python -m drivesync_app.main --sync --dry-run`.
*   **Resultado Esperado:**
    *   Logs devem indicar as ações que *seriam* tomadas (criação de pastas, upload de arquivos) mas sem realmente executá-las.
    *   Nenhuma alteração deve ocorrer no Google Drive.
    *   O `state_file` não deve ser modificado (ou se for, deve ser revertido ou não salvo no final). (A implementação atual evita salvar o estado em dry run).
*   **Verificação:** Cheque o Google Drive e o `state_file` para confirmar que não houve mudanças.

### 7. Verificação de Sincronização (`--verify`)

*   **Cenário 1: Tudo Sincronizado**
    *   **Configuração:** Após uma sincronização bem-sucedida.
    *   **Ação:** `python -m drivesync_app.main --verify`.
    *   **Resultado:** Logs devem indicar que os arquivos locais correspondem ao estado e aos arquivos no Drive. Nenhuma discrepância deve ser reportada.
*   **Cenário 2: Arquivo Local Modificado (não sincronizado)**
    *   **Configuração:** Modifique um arquivo local *após* a última sincronização.
    *   **Ação:** `python -m drivesync_app.main --verify`.
    *   **Resultado:** Logs devem reportar uma incompatibilidade de tamanho/data para o arquivo modificado (comparando local com o *estado atual*, não com o Drive diretamente, mas o estado reflete o último upload ao Drive). A verificação compara o local com o estado, e o estado com o Drive. *Nota: O comportamento exato da verificação atual é comparar local com estado, e depois estado com Drive. Se o local mudou, e o estado não, `--verify` não necessariamente o detecta como um problema de sincronização do *Drive*, mas como uma mudança local pendente. A tarefa principal é verificar o estado contra o Drive.* A verificação atual da Task 10 foca no local vs estado, e estado vs Drive.
*   **Cenário 3: Arquivo Ausente no Drive (mas no estado)**
    *   **Configuração:** Delete um arquivo do Google Drive manualmente *após* ele ter sido sincronizado e estar no `state_file`.
    *   **Ação:** `python -m drivesync_app.main --verify`.
    *   **Resultado:** Logs devem reportar que o arquivo está ausente no Drive (erro 404 ou similar).
*   **Cenário 4: Arquivo Local Ausente (mas no estado)**
    *   **Configuração:** Delete um arquivo localmente *após* ele ter sido sincronizado e estar no `state_file`.
    *   **Ação:** `python -m drivesync_app.main --verify`.
    *   **Resultado:** A verificação atual itera pelos arquivos locais. Se um arquivo não está mais lá, ele não será verificado contra o estado/Drive. *Uma melhoria futura para `--verify` seria iterar pelos itens no estado e verificar sua existência local e no Drive.* Para a implementação atual, este cenário não é explicitamente coberto para gerar um erro.
*   **Cenário 5: Arquivo Local Novo (não no estado)**
    *   **Configuração:** Adicione um novo arquivo localmente.
    *   **Ação:** `python -m drivesync_app.main --verify`.
    *   **Resultado:** Logs devem indicar "Local file <path> NOT FOUND in sync state".

### 8. Argumentos de Override de Configuração (`--source-folder`, `--target-drive-folder-id`)

*   **Configuração:** Tenha uma pasta local secundária e/ou uma pasta de destino secundária no Drive.
*   **Ação:** Execute `python -m drivesync_app.main --sync --source-folder "/caminho/para/outra/pasta/local" --target-drive-folder-id "outro_id_de_pasta_drive"`.
*   **Resultado Esperado:** A sincronização deve ocorrer entre as pastas especificadas na linha de comando, ignorando as configuradas no `config.ini` para esta execução.
*   **Verificação:** Cheque as pastas secundárias no local e no Drive.

## Considerações Adicionais

*   **Logs:** Monitore de perto os arquivos de log (`drivesync.log` ou o configurado) durante todos os testes para mensagens de erro, warnings e informações detalhadas.
*   **Limpeza:** Após os testes, pode ser necessário limpar a pasta de teste no Google Drive e remover os arquivos `token_file` e `state_file` locais.
*   **Casos de Borda:** Considere testar com nomes de arquivos/pastas contendo espaços, caracteres especiais (se o OS e Drive suportarem bem), e estruturas de pastas muito profundas. Teste com arquivos vazios.
