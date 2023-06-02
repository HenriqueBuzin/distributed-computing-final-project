import asyncio
from messaging import send, broadcast

async def main():
    destination = "1"
    message = "Olá, mundo!"

    await send(destination, message)
    
    # await broadcast(message)
asyncio.run(main())