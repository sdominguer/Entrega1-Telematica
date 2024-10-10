import grpc
from concurrent import futures
import raft_pb2
import raft_pb2_grpc

# follower.py

class RaftFollower(raft_pb2_grpc.RaftServiceServicer):
    def __init__(self):
        self.data_store = ""

    def Replicate(self, request, context):
        self.data_store = request.data
        print(f"Seguidor replicando: {self.data_store}")
        return raft_pb2.ReplicateResponse(success=True)

    def Read(self, request, context):
        return raft_pb2.ReadResponse(data=self.data_store)


# Código para iniciar el servidor
def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    raft_pb2_grpc.add_RaftServiceServicer_to_server(RaftFollower(), server)
    server.add_insecure_port('[::]:50054')
    server.start()
    print("Servidor de follower en ejecución en el puerto 50054...")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()

