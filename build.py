import PyInstaller.__main__
import os
import sys

# Separador de caminho depende do SO
sep = ';' if os.name == 'nt' else ':'

# Definição dos argumentos do PyInstaller
args = [
    'run_app.py',
    '--onefile',
    '--name=CalculadoraFII',
    '--clean',
    '--noconfirm',
    
    # Imports ocultos necessários para o Streamlit e dependências
    '--hidden-import=streamlit',
    '--hidden-import=pandas',
    '--hidden-import=altair',
    '--hidden-import=lxml',
    '--hidden-import=html5lib',
    '--hidden-import=yfinance',
    
    # Coletar pacotes inteiros (necessário para Streamlit)
    '--collect-all=streamlit',
    '--collect-all=altair',
    '--collect-all=pandas',
    '--collect-all=pyarrow',
    '--collect-all=yfinance',
    
    # Incluir pastas do projeto
    f'--add-data=application{sep}application',
    f'--add-data=adapters{sep}adapters',
    f'--add-data=core{sep}core',
    f'--add-data=.streamlit{sep}.streamlit',
]

print("Iniciando build do executável...")
PyInstaller.__main__.run(args)
print("Build concluído! O executável está na pasta 'dist'.")
