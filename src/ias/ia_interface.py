from abc import ABC, abstractmethod

class IAInterface(ABC):
    """
    Classe base (Interface) que todas as IAs devem herdar.
    Ela define o "contrato" de como o Simulador vai interagir com um bot.
    """
    
    @abstractmethod
    def __init__(self, jogador_id):
        """Inicializa a IA com a identificação do jogador que ela controlará."""
        self.jogador_id = jogador_id

    @abstractmethod
    def decidir_acoes(self, estado_do_jogo, mapa_completo):
        """
        O método principal da IA. Recebe o estado atual do jogo e o mapa,
        e deve retornar um arquivo de texto com as ordens.
        """
        pass