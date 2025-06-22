import socket
import time
import random
import sys
import pandas as pd
def getrtt(times):#将存储的发送时间和当前时间相减得到RTT
    return (time.time() - times) * 1000
def is_valid_ip(ip):#检查输入的ip是否合法
    parts = ip.split(".")
    if len(parts) != 4:
        return False
    try:
        return all(0 <= int(p) <= 255 for p in parts)
    except ValueError:
        return False
if (len(sys.argv)!=3):
    print("参数数量错误，用法: python udpclient.py <ip> <port>")
    exit(1)
ip = sys.argv[1]
try:
    port = int(sys.argv[2])
except ValueError:
    print("端口号必须是整数")
    exit(1)
if not is_valid_ip(ip):
    print("无效的 IP 地址")
    exit(1)
if not (0 < port < 65536):
    print("端口号必须在 1~65535 范围内")
    exit(1)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(0.601)
while True:
    sock.sendto(b'SYN', (ip, port))#发送SYN报文
    print("发送 SYN 请求，等待服务端确认...")
    try:
        data, _ = sock.recvfrom(1024)
        if data == b'SYN-ACK':
            print("收到服务端 SYN-ACK")
            sock.sendto(b'ACK', (ip, port))#发送ACK报文
            print("发送 ACK，连接建立完成")
            break
    except socket.timeout:
        print("超时未响应，重新发送 SYN")
this = 1
next = 1
ackrecord = [False] * 30
rttrecord = []
re = 0
sendrecord = {}
datas = {}
timeout = 0.601
log = []
for i in range(1, 31):
    content = f"Packet {i}".ljust(74, '6').encode()
    datas[i] = content
while this <= 30:
    currentwindowsize = sum(len(datas[i]) for i in range(this, next) if not ackrecord[i - 1])
    while next <= 30 and (currentwindowsize + 80) <= 400:
        seq = next.to_bytes(4, byteorder='big')
        data = seq + b'\x06\x01' + datas[next]#构建数据包
        sock.sendto(data, (ip, port))
        sendrecord[next] = time.time()
        print(f"发送包 {next}: 内容大小 {80} 字节")
        next += 1
        currentwindowsize +=80
    try:
        sock.settimeout(timeout)
        ack, _ = sock.recvfrom(6)
        acknum = int.from_bytes(ack[:4], byteorder='big')
        rtt = getrtt(sendrecord.get(acknum, time.time()))
        rttrecord.append(rtt)
        print(f"收到 ACK {acknum}, RTT: {rtt:.2f} ms")
        if len(rttrecord) >= 5:
            avgrtt = (sum(rttrecord[-5:]) +timeout)/6
            timeout = avgrtt / 1000 + 0.05
            sock.settimeout(timeout)
        ackrecord[acknum - 1] = True
        log.append({
            "包编号": acknum,
            "RTT": round(rtt, 2),
            "发送时间": sendrecord.get(acknum),
            "是否重传": False
        })
        while this <= 30 and ackrecord[this - 1]:
            this += 1
    except socket.timeout:
        print(f"超时。接下来重传窗口 {this} ~ {next - 1}")
        re += 1
        for i in range(this, next):
            seq = i.to_bytes(4, byteorder='big')
            data = seq + b'\x06\x01' + datas[i]#构建数据包
            sock.sendto(data, (ip, port))
            sendrecord[i] = time.time()
            print(f"重发包 {i}")
            log.append({
                "包编号": i,
                "RTT": None,
                "发送时间": sendrecord.get(i),
                "是否重传": True
            })
sock.close()
print(f"所有数据包发送完成并收到确认，重传次数：{re} 次")
df = pd.DataFrame(log)
validrtt = df['RTT'].dropna()
droprate = df['是否重传'].sum() / 30
print("汇总统计如下：")
print(f"丢包率: {droprate:.2%}")
print(f"最大 RTT: {validrtt.max():.2f} ms")
print(f"最小 RTT: {validrtt.min():.2f} ms")
print(f"平均 RTT: {validrtt.mean():.2f} ms")
print(f"RTT 标准差: {validrtt.std():.2f} ms")
