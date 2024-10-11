import socket
import threading
import sys


class Server:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.clients = {}
        self.clients_lock = threading.Lock()
        self.current_client_count = 0
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self):
        """Запуск сервера и начало прослушивания подключений."""
        with self.socket as server_socket:
            server_socket.bind((self.host, self.port))
            server_socket.listen()
            print(f"Сервер запущен на {self.host}:{self.port}")

            while True:
                conn, addr = server_socket.accept()
                threading.Thread(
                    target=self.client_handler, args=(conn, addr), daemon=True
                ).start()

    def client_handler(self, conn, addr):
        """Обработка подключения клиента."""
        with self.clients_lock:
            self.current_client_count += 1
            self.clients[conn] = addr
            self.display_client_count()

        try:
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                message = data.decode().strip()
                # Отправка полученного сообщения всем клиентам
                self.broadcast(message, exclude_conn=conn)
        except Exception as e:
            print(f"Ошибка с клиентом {addr}: {e}")
        finally:
            # подчищаем список клиентов, закрываем соединение
            with self.clients_lock:
                del self.clients[conn]
                self.current_client_count -= 1
                self.display_client_count()
            conn.close()

    def broadcast(self, message, exclude_conn=None):
        """Отправка сообщения всем подключённым клиентам, кроме исключённого."""
        with self.clients_lock:
            for client_conn in self.clients:
                if client_conn != exclude_conn:
                    try:
                        client_conn.sendall(message.encode())
                    except Exception as e:
                        print(
                            f"Не удалось отправить сообщение клиенту {self.clients[client_conn]}: {e}"
                        )

    def display_client_count(self):
        """Отображение количества подключённых клиентов при изменении."""
        print(f"Количество подключённых клиентов: {self.current_client_count}")


if __name__ == "__main__":
    # Можно передать хост и порт через аргументы командной строки
    host = "localhost"
    port = 12345

    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) >= 2:
        port = int(sys.argv[2])

    server = Server(host, port)
    server.start()
