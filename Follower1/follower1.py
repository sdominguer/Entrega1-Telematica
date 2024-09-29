import grpc
from concurrent import futures
import raft_pb2_grpc
import raft_pb2
import os

class FollowerService(raft_pb2_grpc.RaftServiceServicer):
    def __init__(self):
        self.term = 0
        self.log = []
        self.log_file = "follower1.txt"
        # Asegurar que el archivo follower1.txt existe
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w") as f:
                f.write("Registro de Writes - Follower1\n")

    def AppendEntries(self, request, context):
        if request.term < self.term:
            return raft_pb2.AppendEntriesResponse(term=self.term, success=False)
        
        # Registrar las entradas en el log
        self.log.extend(request.entries)
        with open(self.log_file, "a") as f:
            for entry in request.entries:
                f.write(f"Term {self.term}: {entry}\n")
        
        return raft_pb2.AppendEntriesResponse(term=self.term, success=True)

    def GetState(self, request, context):
        with open(self.log_file, "r") as f:
            state = f.read()
        return raft_pb2.GetStateResponse(state=state)

def serve():
    port = 50054
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    raft_pb2_grpc.add_RaftServiceServicer_to_server(FollowerService(), server)
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    print("Servidor de Follower 1 en ejecución en el puerto 50054...")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
