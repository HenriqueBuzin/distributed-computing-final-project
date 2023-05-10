import docker
from flask import Flask, render_template, jsonify

app = Flask(__name__)
client = docker.from_env()
containers = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create-container')
def create_container():
    try:
        container = client.containers.run('python:3.9', detach=True)
        container_id = container.id
        containers[container_id] = container
        return jsonify({'message': 'Contêiner Docker Python criado com sucesso!', 'container_id': container_id})
    except docker.errors.APIError as e:
        return jsonify({'error': 'Erro ao criar o contêiner Docker Python', 'message': str(e)})

@app.route('/get-nodes')
def get_nodes():
    node_list = list(containers.keys())
    return jsonify(node_list)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
