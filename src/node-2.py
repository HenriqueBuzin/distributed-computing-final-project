from p2p import p2p_start, send, broadcast, receive, deliver
import time

p2p_start('node-2', 2)

#send('node-1', 'mensagem 1')

time.sleep(60)

print(receive())

print(deliver())