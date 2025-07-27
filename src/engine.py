import json

class Cidade:
    """Representa uma cidade no mapa do jogo.
    Cada cidade tem um ID, uma população, um dono (jogador) e uma lista de tropas estacionadas."""
    def __init__(self, id, populacao):
        self.id = id
        self.populacao = populacao
        self.dono = None
        self.tropas_estacionadas = []

class Tropa:
    """Representa uma tropa no jogo.
    Cada tropa tem um ID, um dono (jogador), uma força e uma localização."""
    def __init__(self, id, dono, forca, comando=None):
        self.id = id
        self.dono = dono
        self.forca = forca
        self.localizacao = 'base' # Começa na base
        self.fila_de_comandos = comando
        self.estado = 'Esperando'

class Jogador:
    """Representa um jogador no jogo.
    Cada jogador tem um ID, uma lista de cidades sob seu controle, uma lista de tropas e um HP da base (tropas_na_base)."""
    def __init__(self, id, id_base):
        self.id = id
        self
        self.cidades = []
        self.tropas = []
        self.tropas_na_base = 100  # HP da base do jogador

    def adicionar_cidade(self, cidade):
        """Adiciona uma cidade ao jogador e define o dono da cidade como o ID do jogador."""
        self.cidades.append(cidade)
        cidade.dono = self.id

    def adicionar_tropa(self, tropa):
        """Adiciona uma tropa ao jogador e define o dono da tropa como o ID do jogador."""
        self.tropas.append(tropa)
        tropa.dono = self.id

    def remover_tropa(self, tropa):
        """Remove uma tropa do jogador e redefine o dono da tropa como None."""
        if tropa in self.tropas:
            self.tropas.remove(tropa)
            tropa.dono = None

class Aresta:
    """Representa uma aresta entre duas cidades no mapa do jogo.
    Cada aresta tem uma cidade de origem, uma cidade de destino e um peso (capacidade de tráfego)."""
    def __init__(self, cidade1_id, cidade2_id, peso):
        self.origem = cidade1_id
        self.destino = cidade2_id
        self.peso = peso # Capacidade de Tráfego

class Transporte:
    """Representa um transporte de tropas entre cidades.
    Cada transporte tem um dono (jogador), uma localização (cidade) e uma carga de população."""
    def __init__(self, dono):
        self.dono = dono
        self.localizacao = dono.id_base
        self.carga_populacao = 0
        self.fila_de_comandos = []
        self.estado = 'Esperando'

    def adicionar_comando(self, comando=None):
        """Adiciona um comando à fila de comandos do transporte."""
        self.fila_de_comandos.append(comando)

class Mapa:
    """Representa o mapa do jogo, contendo cidades e arestas."""
    def __init__(self):
        self.cidades = {} # Um dicionário para acesso rápido por ID
        self.arestas = []

    def adicionar_cidade(self, cidade):
        """Adiciona uma cidade ao mapa."""
        self.cidades[cidade.id] = cidade

    def adicionar_aresta(self, origem_id, destino_id, peso):
        """Adiciona uma aresta entre duas cidades no mapa."""
        origem = self.cidades.get(origem_id)
        destino = self.cidades.get(destino_id)
        if origem and destino:
            aresta = Aresta(origem, destino, peso)
            self.arestas.append(aresta)

    def get_vizinhos(self, cidade_id):
        """Retorna uma lista de cidades vizinhas a uma cidade específica."""
        vizinhos = []
        for aresta in self.arestas:
            if aresta.origem.id == cidade_id:
                vizinhos.append(aresta.destino)
            elif aresta.destino.id == cidade_id:
                vizinhos.append(aresta.origem)
        return vizinhos

class Jogo:
    """Classe principal do jogo, que gerencia o estado do jogo, jogadores e o mapa."""
    def __init__(self):
        self.mapa = Mapa()
        self.jogadores = []
        self.turno_atual = 0
        self.turno_maximo = 100

    def carregar_mundo(self, mapa_json):
        """Carrega o mapa do jogo a partir de um arquivo JSON."""
        with open(mapa_json, 'r') as f:
            dados_mapa = json.load(f)
            # Processa os dados do mapa e os adiciona ao objeto Mapa
            for cidade in dados_mapa.get('cidades', []):
                nova_cidade = Cidade(**cidade)
                self.mapa.adicionar_cidade(nova_cidade)
            for aresta in dados_mapa.get('arestas', []):
                self.mapa.adicionar_aresta(**aresta)

    def processar_turno(self, ordem_jogadores):
        # TODO: Instanciar tropas e novos comandos para o turno atual (Preparação do Turno)
        # NOTE: Essa preparação pode depender do estado atual do jogo ou de eventos aleatórios
        
        # Etapa 1: Processamento de Comandos
        for jogador in self.jogadores:
            for tropa in list(jogador.tropas_ativas): 
                if not tropa.fila_de_comandos:
                    # TODO: Implementar lógica para decidir o que fazer quando a tropa não tem comandos
                    # FIXME: Tropas sem comandos ficam inativas indefinidamente, até que recebam comando para RECUAR
                    continue

                comando_atual = tropa.fila_de_comandos[0]

                if comando_atual['tipo'] == 'MOVER':
                    # TODO: Implementar movimentação da tropa passo a passo até o alvo
                    # NOTE: Assumindo que o caminho já está definido na fila_de_comandos
                    proximo_passo = tropa.fila_de_comandos.pop(0)['alvo']
                    tropa.localizacao = proximo_passo  # Simplificação para o MVP
                    # FIXME: Falta validação se o movimento é possível ou permitido

                elif comando_atual['tipo'] == 'ATACAR':
                    # TODO: Marcar tropa como pronta para atacar e armazenar o alvo
                    tropa.estado = 'ATACANDO'
                    tropa.alvo_de_ataque = comando_atual['alvo']
                    tropa.fila_de_comandos.pop(0)
                    # NOTE: A resolução do ataque ocorre apenas na próxima etapa

                # TODO: Adicionar lógica para outros comandos como PERMANECER, RECUAR
                # FIXME: Outros tipos de comando ainda não são tratados

        # TODO: Calcular custos de manutenção e debitar recursos (Etapa 2)
        # FIXME: Ausência de penalidades pode gerar tropas "infinitas"
        
        # Etapa 3: Resolução de Combates
        for cidade in self.mapa.cidades.values():
            atacantes_nesta_cidade = []
            for jogador in self.jogadores:
                for tropa in jogador.tropas_ativas:
                    if tropa.estado == 'ATACANDO' and tropa.alvo_de_ataque == cidade.id:
                        atacantes_nesta_cidade.append(tropa)

            if atacantes_nesta_cidade:
                # TODO: Resolver combate para esta cidade
                # NOTE: Esse método deve lidar com vitórias, derrotas e consequências
                self.resolver_combate(cidade, atacantes_nesta_cidade)
        
        # Etapa 4: Atualizações de Estado Pós-combate
        # TODO: Processar atualizações de estado pós-combate (Etapa 4)
        # NOTE: Atualizações como permanência na cidade conquistada ou retirada

