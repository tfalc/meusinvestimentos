import sys
import subprocess

def main():
    print("Iniciando interface web...")
    # Executa o Streamlit como um módulo para evitar problemas de PATH
    # --server.headless=true desativa a abertura automática do navegador
    cmd = [sys.executable, "-m", "streamlit", "run", "application/web.py", "--server.headless=true"]
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar o Streamlit: {e}")
    except KeyboardInterrupt:
        print("\nServidor parado pelo usuário.")

if __name__ == "__main__":
    main()
