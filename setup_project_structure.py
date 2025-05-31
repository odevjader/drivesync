import os

# Conteúdo para o arquivo .gitignore
GITIGNORE_CONTENT = """\
# Byte-compiled / optimized / DLL files
__pycache__/
*.pyc
*.pyo
*.pyd

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
# Usually these files are written by a script so they are not needed
# in a repository.
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/

# Translations
*.mo
*.pot

# Django stuff:
# *.log  # Comentado pois queremos um log específico do app
local_settings.py
db.sqlite3
db.sqlite3-journal

# Flask stuff:
instance/
.webassets-cache

# Scrapy stuff:
.scrapy

# Sphinx documentation
docs/_build/

# PyBuilder
target/

# Jupyter Notebook
.ipynb_checkpoints

# IPython
profile_default/
ipython_config.py

# PEP 582; __pypackages__
__pypackages__/

# Celery stuff
celerybeat-schedule
celerybeat.pid

# SageMath parsed files
*.sage.py

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Spyder project settings
.spyderproject
.spyproject

# Rope project settings
.ropeproject

# mkdocs documentation
/site

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# Pyre type checker
.pyre/

# pytype static analyzer
.pytype/

# Cython debug symbols
cython_debug/

# DriveSync specific
# Arquivos de credenciais e estado - NUNCA envie para o GitHub!
credentials_target.json
token_target.pickle
*.db # Se usar SQLite para o estado
upload_state.json # Se usar JSON para o estado
app.log # Arquivo de log específico do aplicativo

# VSCode
.vscode/
"""

# Estrutura de pastas e arquivos do projeto
# (caminho_relativo, conteudo_inicial)
# Se conteudo_inicial for None, cria um arquivo vazio.
# Se for uma string, escreve essa string no arquivo.
PROJECT_STRUCTURE = {
    "folders": [
        "drivesync_app"
    ],
    "files": [
        ("drivesync_app/__init__.py", "# Inicializador do pacote drivesync_app\n"),
        ("drivesync_app/main.py", '"""Ponto de entrada principal do aplicativo DriveSync."""\n\nif __name__ == "__main__":\n    print("DriveSync App - Iniciando...")\n    # Lógica principal aqui\n'),
        ("drivesync_app/autenticacao_drive.py", '"""Módulo para autenticação com a API do Google Drive."""\n\n# Código de autenticação aqui\npass\n'),
        ("drivesync_app/gerenciador_drive.py", '"""Módulo para interagir com a API do Google Drive (uploads, pastas, etc.)."""\n\n# Código de gerenciamento do Drive aqui\npass\n'),
        ("drivesync_app/gerenciador_estado.py", '"""Módulo para carregar e salvar o estado da sincronização."""\n\n# Código de gerenciamento de estado aqui\npass\n'),
        ("drivesync_app/processador_arquivos.py", '"""Módulo para percorrer arquivos locais e coordenar o upload."""\n\n# Código de processamento de arquivos aqui\npass\n'),
        ("drivesync_app/verificador.py", '"""Módulo para verificar a integridade da sincronização."""\n\n# Código de verificação aqui\npass\n'),
        ("drivesync_app/logger_config.py", '"""Módulo para configuração do logger."""\n\nimport logging\n\ndef setup_logger():\n    # Configuração básica do logger\n    pass\n'),
        ("config.ini", "[DriveAPI]\nclient_secret_file = credentials_target.json\ntoken_file = token_target.pickle\n\n[Sync]\nsource_folder = C:/Caminho/Para/Sua/PastaLocal\ntarget_drive_folder_id = ID_DA_PASTA_RAIZ_NO_DRIVE_DESTINO\nstate_file = upload_state.json\n\n[Logging]\nlog_file = app.log\nlog_level = INFO\n"),
        (".gitignore", GITIGNORE_CONTENT),
        ("README.md", "# DriveSync Project\n\nDescrição do projeto DriveSync.\n\n## Configuração\n\n...\n\n## Uso\n\n...\n"),
        ("requirements.txt", "# Dependências do Python serão listadas aqui\n# Exemplo:\n# google-api-python-client\n# google-auth-httplib2\n# google-auth-oauthlib\n")
    ]
}

def create_project_structure(base_path="."):
    """
    Cria a estrutura de pastas e arquivos para o projeto.
    :param base_path: O caminho base onde a estrutura será criada. Padrão é o diretório atual.
    """
    print(f"Criando estrutura do projeto em: {os.path.abspath(base_path)}")

    # Criar pastas
    for folder_name in PROJECT_STRUCTURE["folders"]:
        path = os.path.join(base_path, folder_name)
        try:
            os.makedirs(path, exist_ok=True)
            print(f"Pasta criada: {path}")
        except OSError as e:
            print(f"Erro ao criar pasta {path}: {e}")

    # Criar arquivos
    for file_info in PROJECT_STRUCTURE["files"]:
        file_path_rel, content = file_info
        path = os.path.join(base_path, file_path_rel)

        # Garante que o diretório pai do arquivo exista (caso seja um arquivo dentro de uma subpasta nova)
        parent_dir = os.path.dirname(path)
        if parent_dir: # Verifica se não é um arquivo na raiz (parent_dir seria vazio)
            try:
                os.makedirs(parent_dir, exist_ok=True)
            except OSError as e:
                print(f"Erro ao criar diretório pai para {path}: {e}")
                continue # Pula a criação deste arquivo se o diretório pai falhar

        try:
            with open(path, "w", encoding="utf-8") as f:
                if content:
                    f.write(content)
            print(f"Arquivo criado: {path}")
        except IOError as e:
            print(f"Erro ao criar arquivo {path}: {e}")

if __name__ == "__main__":
    # Este script criará a estrutura no diretório onde ele mesmo está localizado.
    # Certifique-se de que você está no diretório raiz do projeto
    # (C:\Users\jader\OneDrive\Documentos\devhome\drivesync) ao executar.
    create_project_structure()
    print("\nEstrutura do projeto criada com sucesso!")
    print("Lembre-se de:")
    print("1. Inicializar o Git com 'git init' (se ainda não fez).")
    print("2. Criar e ativar um ambiente virtual (ex: 'python -m venv venv' e '.\\venv\\Scripts\\activate').")
    print("3. Adicionar os arquivos ao Git e fazer o primeiro commit.")