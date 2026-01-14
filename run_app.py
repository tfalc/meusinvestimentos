import sys
import os
import streamlit.web.cli as stcli

def resolve_path(path):
    if getattr(sys, "frozen", False):
        basedir = sys._MEIPASS
    else:
        basedir = os.path.dirname(__file__)
    return os.path.join(basedir, path)

if __name__ == "__main__":
    # Configurar ambiente para o Streamlit
    if getattr(sys, "frozen", False):
        # Quando congelado, precisamos garantir que o streamlit encontre seus recursos
        os.environ["STREAMLIT_SERVER_PORT"] = "8501"
        os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
    
    # Caminho para o arquivo principal da aplicação
    app_path = resolve_path(os.path.join("application", "web.py"))
    
    # Simular argumentos de linha de comando
    sys.argv = [
        "streamlit",
        "run",
        app_path,
        "--global.developmentMode=false",
    ]
    
    sys.exit(stcli.main())
