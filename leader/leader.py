import grpc
from concurrent import futures
import raft_pb2_grpc
import raft_pb2
import os
import threading
import time

class LeaderService(raft_pb2_grpc.RaftServiceServicer):
    def __init__(self, follower_addresses):
        self.log = []
        self.last_id = 0  # Mantener un contador de IDs
        self.log_file = "leader.txt"
        self.follower_stubs = []
        self.heartbeat_interval = 2  # Enviar latidos cada 2 segundos

        # Establecer conexiones con los followers
        for addr in follower_addresses:
            channel = grpc.insecure_channel(addr)
            stub = raft_pb2_grpc.RaftServiceStub(channel)
            self.follower_stubs.append(stub)

        # Asegurar que el archivo leader.txt existe
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w") as f:
                f.write("ID\tEntrada\n")

        # Iniciar hilo para enviar latidos del corazón
        self.heartbeat_thread = threading.Thread(target=self.send_heartbeat)
        self.heartbeat_thread.daemon = True
        self.heartbeat_thread.start()

    def AppendEntries(self, request, context):
        # Registrar las entradas en el log con un ID único
        response_entries = []
        for entry in request.entries:
            self.last_id += 1
            log_entry = f"{self.last_id}\t{entry}\n"
            with open(self.log_file, "a") as f:
                f.write(log_entry)
            response_entries.append(f"ID {self.last_id}: {entry}")

        self.log.extend(response_entries)

        # Enviar las entradas a todos los followers
        append_request = raft_pb2.AppendEntriesRequest(entries=request.entries)
        for stub in self.follower_stubs:
            stub.AppendEntries(append_request)

        return raft_pb2.AppendEntriesResponse(success=True)

    def send_heartbeat(self):
        while True:
            heartbeat_request = raft_pb2.AppendEntriesRequest(entries=[])
            for stub in self.follower_stubs:
                stub.AppendEntries(heartbeat_request)  # Enviar latido de corazón
            print("Enviando latido del corazón a los followers.")
            time.sleep(self.heartbeat_interval)

def serve():
    port = 50052
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    # Direcciones de los followers
    follower_addresses = ['localhost:50054', 'localhost:50055']
    raft_pb2_grpc.add_RaftServiceServicer_to_server(LeaderService(follower_addresses), server)
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    print("Servidor de líder en ejecución en el puerto 50052...")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
