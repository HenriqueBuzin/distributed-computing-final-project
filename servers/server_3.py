from messaging import get_port
from flask import Flask
import os

app = Flask(__name__)

nome_arquivo = os.path.basename(__file__)
port = get_port(nome_arquivo)

@app.route('/')
def index():
    return 'Página inicial'

@app.route('/about')
def about():
    return 'Sobre nós'

if __name__ == '__main__':
    app.run(port=port)