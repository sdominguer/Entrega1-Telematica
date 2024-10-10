import grpc
import proxy_pb2_grpc
import proxy_pb2
import raft_pb2_grpc
import raft_pb2
import concurrent.futures as futures
import time

class ProxyService(proxy_pb2_grpc.ProxyServiceServicer):
    def __init__(self, leader_address, follower_addresses):
        self.leader_address = leader_address
        self.follower_addresses = follower_addresses
        self.leader_stub = None
        self.follower_stubs = []

        self.update_leader_stub()  # Establecer la conexión con el líder
        self.update_follower_stubs()  # Establecer la conexión con los followers

    def update_leader_stub(self):
        """Intentar conectar con el líder"""
        try:
            self.leader_channel = grpc.insecure_channel(self.leader_address)
            grpc.channel_ready_future(self.leader_channel).result(timeout=2)
            self.leader_stub = raft_pb2_grpc.RaftServiceStub(self.leader_channel)
            print(f"Conectado al líder en {self.leader_address}")
        except grpc.FutureTimeoutError:
            print("No se pudo conectar al líder.")
            self.leader_stub = None

    def update_follower_stubs(self):
        """Actualizar los stubs de los followers"""
        self.follower_channels = [grpc.insecure_channel(addr) for addr in self.follower_addresses]
        self.follower_stubs = [raft_pb2_grpc.RaftServiceStub(channel) for channel in self.follower_channels]

    def Write(self, request, context):
        """Redirigir escritura al líder"""
        if self.leader_stub is None:
            # Intentar reconectar si no hay un líder asignado
            self.update_leader_stub()

        if self.leader_stub:
            append_request = raft_pb2.AppendEntriesRequest(entries=[request.data])
            try:
                leader_response = self.leader_stub.AppendEntries(append_request)
                if leader_response.success:
                    return proxy_pb2.WriteResponse(success=True)
                else:
                    return proxy_pb2.WriteResponse(success=False)
            except grpc.RpcError as e:
                print(f"Error al escribir en el líder: {e}")
                return proxy_pb2.WriteResponse(success=False)
        else:
            print("No se pudo conectar al líder para realizar la escritura.")
            return proxy_pb2.WriteResponse(success=False)

    def Read(self, request, context):
        """Redirigir lectura a uno de los followers"""
        # Aquí puedes implementar balanceo de carga o seleccionar un follower al azar
        follower_stub = self.follower_stubs[0]
        try:
            response = follower_stub.GetState(raft_pb2.GetStateRequest())
            return proxy_pb2.ReadResponse(data=response.state)
        except grpc.RpcError as e:
            print(f"Error al leer de un follower: {e}")
            return proxy_pb2.ReadResponse(data="Error al leer de follower.")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    # Direcciones del líder y followers
    leader_address = 'localhost:50052'
    follower_addresses = ['localhost:50054', 'localhost:50055']
    
    proxy_service = ProxyService(leader_address, follower_addresses)
    proxy_pb2_grpc.add_ProxyServiceServicer_to_server(proxy_service, server)
    server.add_insecure_port('[::]:50051')
    print("Servidor de proxy en ejecución en el puerto 50051...")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
