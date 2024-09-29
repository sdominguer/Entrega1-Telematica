import grpc
import proxy_pb2_grpc
import proxy_pb2
import raft_pb2_grpc
import raft_pb2
import concurrent.futures as futures

class ProxyService(proxy_pb2_grpc.ProxyServiceServicer):
    def __init__(self, leader_address, follower_addresses):
        # Establecer comunicación con el líder para las escrituras
        self.leader_channel = grpc.insecure_channel(leader_address)
        self.leader_stub = raft_pb2_grpc.RaftServiceStub(self.leader_channel)

        # Establecer comunicación con los followers para las lecturas
        self.follower_channels = [grpc.insecure_channel(addr) for addr in follower_addresses]
        self.follower_stubs = [raft_pb2_grpc.RaftServiceStub(channel) for channel in self.follower_channels]

    def Write(self, request, context):
        # Enviar la solicitud de escritura al líder
        append_request = raft_pb2.AppendEntriesRequest(entries=[request.data])
        leader_response = self.leader_stub.AppendEntries(append_request)

        if leader_response.success:
            # Retornar éxito si el líder confirmó la escritura
            return proxy_pb2.WriteResponse(success=True)
        else:
            return proxy_pb2.WriteResponse(success=False)

    def Read(self, request, context):
        # Seleccionar uno de los followers para la lectura
        # Aquí puedes cambiar la lógica si deseas balanceo de carga o selección diferente
        follower_stub = self.follower_stubs[0]  # Seleccionar el primer follower
        response = follower_stub.GetState(raft_pb2.GetStateRequest())
        return proxy_pb2.ReadResponse(data=response.state)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    # Asigna la dirección del líder (para escribir) y los followers (para leer)
    proxy_service = ProxyService('localhost:50052', ['localhost:50054', 'localhost:50055'])
    proxy_pb2_grpc.add_ProxyServiceServicer_to_server(proxy_service, server)
    server.add_insecure_port('[::]:50051')
    print("Servidor de proxy en ejecución en el puerto 50051...")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
