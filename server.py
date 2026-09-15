"""AFZAL HEART CENTRE ECHO MANAGEMENT SYSTEM entry point."""
from http.server import ThreadingHTTPServer
from backend.config import HOST, PORT
from backend.handler import Handler
from backend.migrations import init


def main():
    init()
    print(f'Afzal Heart Centre Echo Management System: http://127.0.0.1:{PORT}', flush=True)
    with ThreadingHTTPServer((HOST, PORT), Handler) as server:
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print('Echo server stopped.')


if __name__ == '__main__':
    main()
