#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
文件传输通信协议（命名为dj协议）设计：
1. 基于TCP协议；
2. 客户端连接服务器成功后，客户端不发送任何消息，服务器首先将一个文件的描述信息（定长包头，长度为215B），
   发送给客户端，接着发送文件数据给客户端，发完数据后断开连接
3. 文件描述信息结构为：文件名（200B，右边填充空格，UTF-8编码）+ 文件大小（15B，右边填充空格）+ MD5校验值(32B)

'''
import socket,time
import queue
import hashlib,os,json
from threading import Thread


server_ip = input('请输入服务器ip地址：')
# server_port = input('请输入服务器端口号：')
server_port = 9999
q = queue.Queue()

def conn(server_ip,server_port):
    sock = socket.socket()  
    #sock.bind(('0.0.0.0',1234))
    sock.connect((server_ip,int(server_port)))

    ##不断尝试连接服务器
    # while True:
    #     try:
    #         sock = socket.socket()   
    #        
    #         sock.connect(('127.0.0.1',9999))
    #     except:
    #         time.sleep(1)
    #     else:
    #         break
    return sock

def recv_error(sock):
    size = sock.recv(15)
    data1 = sock.recv(int(size.decode()))
    data1 = json.loads(data1.decode())
  
    return data1['error_code']

def reg_server(sock):
    '''1.首先校验用户名是否存在 2.注册服务器用户'''
    js_data = {
        "op":3,
        "args":{
            "uname":"flw"
        }
    }
    hearder = "{:<15}".format(len(json.dumps(js_data)))
    
    sock.send(hearder.encode())
    sock.send(json.dumps(js_data).encode())
    if recv_error(sock) == 1:
        return 2
    else:
        m = hashlib.md5()
        m.update(b'flw123')
        pwd = m.hexdigest()
        js_data1 = {
            "op":2,
            "args":{
                "uname":"flw123",
                "passwd":pwd.upper(),
                "phone":'13769267406',
                "email":'2814008690@qq.com'
            }
        }
        sock = conn(server_ip,server_port)
        hearder = "{:<15}".format(len(json.dumps(js_data1)))
        sock.send(hearder.encode())
        sock.send(json.dumps(js_data1).encode())

        return recv_error(sock)

def login_server(sock):
    """登录服务器"""
    m = hashlib.md5()
    m.update(b'flw123')
    pwd = m.hexdigest()
    js_data = {
        "op":1,
        "args":{
            "uname":"flw123",
            "passwd":pwd.upper()
        }
    }

    hearder = "{:<15}".format(len(json.dumps(js_data)))
    sock.send(hearder.encode())
    sock.send(json.dumps(js_data).encode())
    return recv_error(sock)

def recv_smg(sock,file_name,file_size):
    '''接受文件'''
    print("正在接收 %s " % file_name)
    size = 0
    file_size = int(file_size)
    while size < file_size:
        file_msg= sock.recv(file_size-size)
        size += len(file_msg)
        q.put(file_msg)
        
    print('%s 接受完毕....' % file_name)


def get_md5(save_path,name,md5):
    '''校验文件传输过程是否被破坏'''
 
    with open(os.path.join(save_path,os.path.split(name)[1]),'rb') as f :
        data = f.read()
     
    m = hashlib.md5()
    m.update(data)
    md5_value = m.hexdigest()
    # print(md5.lower())
    # print(md5_value.lower())

    if md5.lower() == md5_value.lower():
        print('%s 文件传输成功。。。' % name)
    else:
        print('%s 文件已损坏。。。' % name)


def write_msg(file_name,file_size,file_MD5):
    '''下载文件'''
    #while True:
    size1 = 0
    save_path =os.path.join(os.path.split(os.path.realpath(__file__))[0],os.path.split(file_name)[0])
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    with open(os.path.join(save_path,os.path.split(file_name)[1]),'wb+') as f:
        while True:
            if q.qsize() == 0:
                if (size1 == int(file_size)):
                    break
                pass
            else:
                sc = q.get()
                size1 += len(sc)
                f.write(sc)

    get_md5(save_path,file_name,file_MD5)
    print('%s 下载完毕....\n' % file_name) 
    


def main():
    while True:
        print("功能选择：\n")
        print("1. 新用户注册\t2. 登录服务器\t0.退出\n")
        flag = input("请选择：")
        if flag == '0':
            exit(0)
        elif flag == '1':
            sock = conn(server_ip,server_port)
            sc = reg_server(sock)
            if sc == 2:
                print("用户已存在\n")
            elif sc == 0:
                print('注册成功\n')
            elif sc == 1:
                print('注册失败\n')
            sock.close()
            input('任意键返回。。。\n')

        elif flag == '2':
            sock = conn(server_ip,server_port)
            if login_server(sock) == 0:
                while True:
                    ll = 0
                    sc=b''
                    while ll < 300:
                        sc += sock.recv(300-ll)
                        if not sc:
                            break
                        ll += len(sc)
                    file_name = sc.decode().rstrip()
                    
                    ll = 0
                    sc=b''
                    while ll < 15:
                        sc += sock.recv(15-ll)
                        if not sc:
                            break
                        ll += len(sc)
                    file_size = sc.decode().rstrip() 
                    
                    ll = 0
                    sc=b''
                    while ll < 32:
                        sc += sock.recv(32-ll)
                        if not sc:
                            break
                        ll += len(sc)
                    file_MD5 = sc.decode().rstrip()
                    print(file_name+'*'+file_size+'*'+file_MD5)

                    if file_size == '-1':
                            print("文件为空文件")       
                    else: 
                        if len(file_name) == 0 and len(file_size) == 0 and len(file_MD5) == 0:
                            print(len(file_name),len(file_size),len(file_MD5))
                            t = input("传输完成，任意键退出。。。\n")
                            sock.close()
                            exit(1)
                        elif len(file_name) != 0 and len(file_size) != 0 and len(file_MD5) != 0:
                            while True:
                                t1 = Thread(target=recv_smg,args=(sock,file_name,file_size))
                                t2 = Thread(target=write_msg,args=(file_name,file_size,file_MD5))
                                t1.start()
                                t2.start()
                                t1.join()
                                t2.join()
                                break
                        else:
                            print('传输异常。。。。。\n')
                            break
                       
                sock.close() 
            else:
                sock.close() 
                print("登录失败。。。\n")
        else :
            print('输入错误，请重新选择。。\n')


if __name__ == "__main__":
    main()
