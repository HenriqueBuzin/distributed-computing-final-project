FROM python:3.9

# Define o diretório de trabalho
WORKDIR /app

# Copia os arquivos de requisitos
COPY requirements.txt .

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código do aplicativo
COPY . .

# Define o comando padrão a ser executado quando o contêiner for iniciado
CMD [ "python", "app.py" ]
