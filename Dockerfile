# Usar uma imagem base oficial do Python
FROM python:3.11-slim

# Definir o diretório de trabalho no container
WORKDIR /app

# Instalar dependências do sistema necessárias (opcional, mas recomendado)
# html5lib/lxml podem precisar de libs C
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar os arquivos de requisitos
COPY requirements.txt .

# Instalar as dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o restante do código da aplicação
COPY . .

# Expor a porta que o Streamlit usa (padrão 8501)
EXPOSE 8501

# Comando para rodar a aplicação
# Ajuste o caminho do script se necessário (ex: application/web.py)
CMD ["streamlit", "run", "application/web.py", "--server.address=0.0.0.0"]
