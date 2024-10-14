import grpc
from concurrent import futures
import raft_pb2_grpc
import raft_pb2
import os
import time
import threading
import random

class FollowerService(raft_pb2_grpc.RaftServiceServicer):
    def __init__(self, follower_id, peer_addresses):
        self.term = 0
        self.voted_for = None  # Seguir quién ha recibido el voto en la elección
        self.log = []
        self.log_file = f"follower{follower_id}.txt"
        self.is_leader = False
        self.leader_alive = True
        self.election_timeout = random.uniform(5, 10)  # Temporizador aleatorio más largo
        self.peer_stubs = []  # Otros followers para enviar solicitudes de votación
        self.peer_addresses = peer_addresses
        self.votes_received = 0

        # Establecer conexiones con otros followers
        for addr in self.peer_addresses:
            channel = grpc.insecure_channel(addr)
            stub = raft_pb2_grpc.RaftServiceStub(channel)
            self.peer_stubs.append(stub)

        # Asegurar que el archivo follower.txt existe
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w") as f:
                f.write(f"Registro de Writes - Follower{follower_id}\n")

        # Iniciar hilo para monitorear el líder
        self.heartbeat_thread = threading.Thread(target=self.monitor_leader)
        self.heartbeat_thread.daemon = True
        self.heartbeat_thread.start()

    def AppendEntries(self, request, context):
        """Recibe latidos del corazón del líder y reinicia el temporizador."""
        self.leader_alive = True
        self.voted_for = None  # Resetear la votación si se recibe latido
        print(f"Follower ha recibido latido del corazón del líder en el término {self.term}")
        # Replicar las entradas recibidas del líder
        with open(self.log_file, "a") as f:
            for entry in request.entries:
                f.write(f"{entry}\n")
        return raft_pb2.AppendEntriesResponse(success=True)

    def RequestVote(self, request, context):
        """Recibe solicitudes de voto de otros followers."""
        if self.voted_for is None or request.term > self.term:
            self.term = request.term
            self.voted_for = request.candidate_id
            print(f"Follower ha votado por el candidato {request.candidate_id} en el término {self.term}")
            return raft_pb2.RequestVoteResponse(term=self.term, vote_granted=True)
        else:
            print(f"Follower rechazó la solicitud de voto de {request.candidate_id} porque ya votó por {self.voted_for}")
            return raft_pb2.RequestVoteResponse(term=self.term, vote_granted=False)

    def monitor_leader(self):
        """Verifica si el líder sigue vivo o si debe iniciar una elección."""
        while True:
            time.sleep(self.election_timeout)  # Esperar el tiempo de latido antes de verificar
            if not self.leader_alive:
                print("No se detecta líder. Iniciando una elección...")
                self.start_election()
            else:
                self.leader_alive = False  # Reset del temporizador de latido

    def start_election(self):
        """Inicia una elección y solicita votos de otros followers."""
        self.term += 1  # Incrementa el término
        self.voted_for = None  # Reiniciar la votación
        self.votes_received = 1  # Se vota a sí mismo
        print(f"Iniciando proceso de elección en el término {self.term}")

        # Enviar solicitud de votos a otros followers
        for stub in self.peer_stubs:
            try:
                vote_request = raft_pb2.RequestVoteRequest(term=self.term, candidate_id="follower")
                response = stub.RequestVote(vote_request)
                if response.vote_granted:
                    self.votes_received += 1
                    print(f"Follower recibió un voto. Total de votos: {self.votes_received}")
            except grpc.RpcError as e:
                print(f"Error al solicitar votos: {e}")

        # Convertirse en líder si recibe la mayoría de votos
        if self.votes_received > len(self.peer_stubs) // 2:
            self.is_leader = True
            print(f"Follower se ha convertido en el nuevo líder en el término {self.term}")
            self.send_heartbeat()
        else:
            print(f"Follower no ha recibido suficientes votos en el término {self.term}")

    def send_heartbeat(self):
        """Envía latidos del corazón a los demás followers después de ser elegido líder."""
        while self.is_leader:
            # Si el líder original envía un latido, este follower debe volver a ser follower
            if self.leader_alive:
                print("El líder original ha regresado. Volviendo al estado de follower.")
                self.is_leader = False
                return  # Salir de la función para dejar de enviar latidos

            print("Enviando latido del corazón como líder.")
            heartbeat_request = raft_pb2.AppendEntriesRequest(entries=[])
            for stub in self.peer_stubs:
                try:
                    stub.AppendEntries(heartbeat_request)  # Enviar latido de corazón
                except grpc.RpcError as e:
                    print(f"Error al enviar latido del corazón: {e}")
            time.sleep(2)  # Enviar latidos cada 2 segundos



    def GetState(self, request, context):
        """Muestra el estado del follower."""
        with open(self.log_file, "r") as f:
            state = f.read()
        return raft_pb2.GetStateResponse(state=state)

def serve(follower_id, peer_addresses, port):
    """Configura y ejecuta el servidor follower."""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    raft_pb2_grpc.add_RaftServiceServicer_to_server(FollowerService(follower_id, peer_addresses), server)
    server.add_insecure_port(f'[::]:{port}')
    print(f"Servidor de Follower {follower_id} en ejecución en el puerto {port}...")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    # Configurar el follower con su ID, peers y puerto
    peer_addresses = ['localhost:50054']  # Cambia según los peers
    serve(follower_id=2, peer_addresses=peer_addresses, port=50055)
