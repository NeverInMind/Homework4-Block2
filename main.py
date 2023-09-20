from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import pathlib
import mimetypes
import socket
import threading
import time
import datetime
import json

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
        run_client(UDP_IP, UDP_PORT, data)
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()
        # return data_dict

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
        while True:
            conn, addr = s.accept()
            print(f"Connected by {addr}")
            data = conn.recv(1024)
            print(f'From client: {data}')
            with open(".\storage\data.json", "r", encoding='utf-8') as f:
                old_data = json.load(f)
            with open(".\storage\data.json", "w", encoding='utf-8') as f:
                data_parse = urllib.parse.unquote_plus(data.decode())
                data_dict = {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}
                data_dict = {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"): data_dict}
                old_data.update(data_dict)
                json.dump(old_data, f)
            if not data:
                break
            conn.send(data.upper())
            conn.close()


def run_client(host, port, message):
    with socket.socket() as s:
        while True:
            try:
                s.connect((host, port))
                s.sendall(message)
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
    client = threading.Thread(target=run)
    server.start()
    client.start()