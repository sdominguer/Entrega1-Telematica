import grpc
from concurrent import futures
import raft_pb2_grpc
import raft_pb2
import os

class LeaderService(raft_pb2_grpc.RaftServiceServicer):
    def __init__(self, follower_addresses):
        self.term = 0
        self.log = []
        self.last_id = 0  # Mantener un contador de IDs
        self.log_file = "leader.txt"
        self.follower_stubs = []

        # Establecer conexiones con los followers
        for addr in follower_addresses:
            channel = grpc.insecure_channel(addr)
            stub = raft_pb2_grpc.RaftServiceStub(channel)
            self.follower_stubs.append(stub)

        # Asegurar que el archivo leader.txt existe
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w") as f:
                f.write("ID\tTerm\tEntrada\n")

    def AppendEntries(self, request, context):
        if request.term < self.term:
            return raft_pb2.AppendEntriesResponse(term=self.term, success=False)
        
        # Registrar las entradas en el log con un ID único
        response_entries = []
        for entry in request.entries:
            self.last_id += 1
            log_entry = f"{self.last_id}\tTerm {self.term}\t{entry}\n"
            with open(self.log_file, "a") as f:
                f.write(log_entry)
            response_entries.append(f"ID {self.last_id}: {entry}")
        
        # Registrar las entradas recibidas
        self.log.extend(response_entries)

        # Enviar las entradas a todos los followers
        append_request = raft_pb2.AppendEntriesRequest(entries=request.entries, term=self.term)
        for stub in self.follower_stubs:
            stub.AppendEntries(append_request)

        return raft_pb2.AppendEntriesResponse(term=self.term, success=True)

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
