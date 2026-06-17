from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import webbrowser


ROOT = Path(__file__).resolve().parents[1]
HOST = "127.0.0.1"
START_PORT = 3000


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        return


def create_server(start_port):
    handler = partial(QuietHandler, directory=str(ROOT))
    for port in range(start_port, start_port + 50):
        try:
            return port, ThreadingHTTPServer((HOST, port), handler)
        except OSError:
            continue
    raise RuntimeError("没有找到可用端口，请先关闭其他本地网站窗口后再试。")


def main():
    port, server = create_server(START_PORT)
    url = f"http://{HOST}:{port}/"

    print("Claire 个人网站已经在本地运行。")
    print(f"地址：{url}")
    print()
    print("浏览器会自动打开这个地址。")
    print("想关闭本地网站时，直接关闭这个黑色窗口，或按 Ctrl+C。")
    print()

    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n正在关闭 Claire 个人网站...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
