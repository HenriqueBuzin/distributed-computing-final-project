# distributed-computing-final-project
 Distributed Computing Final Project

## Enviar
Método: POST <br />
URL: http://localhost:8001/send <br />
JSON: <br />
{
  "destination": "server-2",
  "message": "Olá, servidor 2222!"
}

## Receber
Método: GET <br />
URL: http://localhost:8002/receive <br />
JSON: <br />
[
    {
        "server-2": "Olá, servidor 2!"
    }
]

## Broadcast
Método: POST <br />
URL: http://localhost:8001/broadcast <br />
JSON: <br />
[
    {
        "message": "Olá, servidor 2!"
    }
]