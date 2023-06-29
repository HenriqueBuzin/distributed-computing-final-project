from p2p import p2p_start, send, broadcast

p2p_start('node-2', 2)

send('mensagem 1', 'node-1')

#broadcast('oi')