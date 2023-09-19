from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import pathlib
import mimetypes
import socket
import threading
import time

UDP_IP = '127.0.0.1'
UDP_PORT = 5000


class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/':
            self.send_html_file('index.html')
        elif pr_url.path == '/message': 
            self.send_html_file('message.html')
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file('error.html', 404)


    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        print(data)
        data_parse = urllib.parse.unquote_plus(data.decode())
        print(data_parse)
        data_dict = {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()
        return data_dict

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

def run_server(ip, port):
    with socket.socket() as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((ip, port))
        s.listen(1)
        conn, addr = s.accept()
        print(f"Connected by {addr}")
        with conn:
            while True:
                data = conn.recv(1024)
                print(f'From client: {data}')
                if not data:
                    break
                conn.send(data.upper())


def run_client(host, port):
    with socket.socket() as s:
        while True:
            try:
                s.connect((host, port))
                s.sendall(b'Hello, world')
                data = s.recv(1024)
                print(f'From server: {data}')
                break
            except ConnectionRefusedError:
                time.sleep(0.5)

def run(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = (UDP_IP, 3000)
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


if __name__ == '__main__':
    server = threading.Thread(target=run_server, args=(UDP_IP, UDP_PORT))
    client = threading.Thread(target=run_client, args=(UDP_IP, UDP_PORT))
    server.start()
    client.start()
    server.join()
    client.join()
    #run()
