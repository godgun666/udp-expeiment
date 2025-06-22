import socket
import random
port = 2601
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
try:
    sock.bind(('0.0.0.0', port))
    print(f"成功在 {port} 接口上开启服务")
    connected = False
    client = None
    while not connected:
        data, addr = sock.recvfrom(1024)
        if data == b'SYN':
            print(f"收到来自 {addr} 的连接请求 SYN")
            sock.sendto(b'SYN-ACK', addr)#发送SYN-ACK报文
        elif data == b'ACK':
            print(f"与 {addr} 的连接建立成功！")
            client = addr
            connected = True
    exseq=1
    while True:
        data, addr = sock.recvfrom(1024)
        if addr != client:
            continue
        if random.random() < 0.0601:
            print("模拟丢包")
            continue
        seq = int.from_bytes(data[:4], byteorder='big')
        content = data[6:]
        if seq == exseq:
            print(f"收到按序包 {seq}（第 {(seq - 1) * 80}~{seq * 80 - 1} 字节）")
            print(f"内容：{content.decode()}")
            exseq += 1
        else:
            print(f"收到乱序包 {seq}，期望的是 {exseq}，丢弃")
        ack = (exseq - 1).to_bytes(4, byteorder='big')
        sock.sendto(ack+b'\x06\x01', addr)#发送数据包的ACK报文
finally:
    sock.close()