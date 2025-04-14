import socket
import gzip
import urllib.parse

# 服务器配置 - 请修改为您的内网服务器地址和端口
SERVER_HOST = '43.136.171.182'  # 替换为您的服务器IP
SERVER_PORT = 80               # 替换为您的服务器端口
LOGIN_PATH = '/login'          # 替换为登录路径

def send_gzip_transfer_encoded_post():
    # 创建表单数据
    form_data = urllib.parse.urlencode({
        'httpd_username': 'ruhao',     # 替换为您要测试的用户名
        'httpd_password': 'ruhao',  # 替换为您要测试的密码
        'login': 'Login'
    }).encode()
    
    # 使用gzip压缩表单数据
    # compressed_data = gzip.compress(form_data)
    compressed_data = form_data
    
    # 构建HTTP请求头
    request = (
        f'POST {LOGIN_PATH} HTTP/1.1\r\n'
        f'Host: {SERVER_HOST}\r\n'
        f'Content-Type: application/x-www-form-urlencoded\r\n'
        # f'Content-Encoding: gzip\r\n'
        f'Connection: close\r\n'
        f'\r\n'
    ).encode()
    
    # 将请求头和压缩后的数据组合
    full_request = request + compressed_data
    
    # 创建socket连接
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # 连接服务器
        print(f"连接到 {SERVER_HOST}:{SERVER_PORT}...")
        sock.connect((SERVER_HOST, SERVER_PORT))
        
        # 发送请求
        print("发送请求...")
        sock.sendall(full_request)
        
        # 接收响应
        print("接收响应...")
        response = b''
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk
            
        # 解析并打印响应
        try:
            headers, body = response.split(b'\r\n\r\n', 1)
            print("\n---- 响应头 ----")
            print(headers.decode('utf-8'))
            print("\n---- 响应体 ----")
            print(body.decode('utf-8', errors='replace'))
        except:
            print("\n---- 完整响应 ----")
            print(response.decode('utf-8', errors='replace'))
            
    except Exception as e:
        print(f"发生错误: {e}")
    finally:
        sock.close()
        print("连接已关闭")

if __name__ == "__main__":
    send_gzip_transfer_encoded_post()
