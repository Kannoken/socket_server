import socket
import sys
import json
import threading
import time
import uuid


class Client:
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.client_id = str(uuid.uuid4())  # Генерация уникального ID для клиента
        self.increment = 0
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = True
        self.receive_lock = threading.Lock()

    def start(self):
        """Подключение к серверу и запуск потоков отправки и приёма сообщений."""
        self.socket.connect((self.server_ip, self.server_port))
        print(
            f"[Client {self.client_id}] Подключён к серверу {self.server_ip}:{self.server_port}"
        )

        # Запуск потоков
        send_thread = threading.Thread(target=self.send_messages, daemon=True)
        receive_thread = threading.Thread(target=self.receive_messages, daemon=True)

        send_thread.start()
        receive_thread.start()

        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print(f"[Client {self.client_id}] Отключение...")
            self.running = False
            self.socket.close()

    def send_messages(self):
        """Отправка сообщений на сервер каждую секунду."""
        while self.running:
            timestamp_ms = int(time.time() * 1000)
            message = {
                "id": self.client_id,
                "timestamp_ms": timestamp_ms,
                "increment": self.increment,
            }
            self.socket.sendall(json.dumps(message).encode())
            self.increment += 1
            time.sleep(1)

    def receive_messages(self):
        """Приём сообщений от сервера"""
        while self.running:
            data = self.socket.recv(1024)
            if not data:
                print(f"[Client {self.client_id}] Сервер отключил соединение.")
                self.running = False
                break

            message = data.decode().strip()
            try:
                message_json = json.loads(message)
                sender_id = message_json.get("id")
                sender_timestamp = message_json.get("timestamp_ms")
                sender_increment = message_json.get("increment")

                # отображаем только в случае отличия присланного id от client_id
                if sender_id != self.client_id:
                    current_timestamp_ms = int(time.time() * 1000)
                    timestamp_diff = current_timestamp_ms - sender_timestamp

                    # Условие отображения: таймстамп отличается от текущего
                    if timestamp_diff > 0:
                        sender_ip = self.socket.getpeername()[0]
                        print(
                            f"[Client {self.client_id}] Получено сообщение от Client {sender_id}: "
                            f"Разница таймстампа: {timestamp_diff}, инкремент: {sender_increment}, "
                            f"IP: {sender_ip}"
                        )
            except json.JSONDecodeError:
                print(
                    f"[Client {self.client_id}] Получено некорректное сообщение: {message}"
                )


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Использование: python client.py <server_ip> <server_port>")
        sys.exit(1)

    server_ip = sys.argv[1]
    server_port = int(sys.argv[2])

    client = Client(server_ip, server_port)
    client.start()
