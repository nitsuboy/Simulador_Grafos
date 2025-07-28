import json
from collections import deque

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
    def __init__(self, id, dono, forca, fila_de_comandos=None):
        self.id = id
        self.dono = dono
        self.forca = forca
        self.localizacao = dono.id_base 
        self.fila_de_comandos = fila_de_comandos if fila_de_comandos is not None else []
        self.estado = 'Esperando'  # Estado da tropa: Esperando, Atacando, Movendo.
        self.caminho_atual = [] # Rota definida para movimentação

class Jogador:
    """Representa um jogador no jogo.
    Cada jogador tem um ID, uma lista de cidades sob seu controle, uma lista de tropas e um HP da base (tropas_na_base)."""
    def __init__(self, id, id_base):
        self.id = id
        self.id_base = id_base
        self.cidades_possuidas = [] 
        self.tropas = []
        self.tropas_na_base = 100 # HP da base do jogador

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
        self.cidades = (cidade1_id, cidade2_id)
        self.peso = peso    

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
        self.cidades = {} 
        self.arestas = {}

    def adicionar_cidade(self, cidade):
        """Adiciona uma cidade ao mapa."""
        self.cidades[cidade.id] = cidade

    def adicionar_aresta(self, cidade1_id, cidade2_id, peso):
        """Adiciona uma aresta entre duas cidades no mapa."""
        chave = tuple(sorted((cidade1_id, cidade2_id)))
        if chave not in self.arestas:
            self.arestas[chave] = Aresta(cidade1_id, cidade2_id, peso)

    def get_aresta(self, cidade1_id, cidade2_id):
        """Retorna o objeto Aresta entre duas cidades."""
        chave = tuple(sorted((cidade1_id, cidade2_id)))
        return self.arestas.get(chave)

    def get_vizinhos(self, cidade_id):
        """Retorna uma lista de IDs de cidades vizinhas."""
        vizinhos = []
        for cidades_na_aresta in self.arestas.keys():
            if cidade_id in cidades_na_aresta:
                vizinho = cidades_na_aresta[0] if cidades_na_aresta[1] == cidade_id else cidades_na_aresta[1]
                vizinhos.append(vizinho)
        return vizinhos
    
    def encontrar_caminho_bfs(self, inicio_id, fim_id):
        """Encontra o caminho mais curto entre duas cidades usando BFS."""
        if inicio_id == fim_id:
            return [inicio_id]
            
        fila = deque([[inicio_id]])
        visitados = {inicio_id}

        while fila:
            caminho = fila.popleft()
            ultimo_no = caminho[-1]

            if ultimo_no == fim_id:
                return caminho

            for vizinho in self.get_vizinhos(ultimo_no):
                if vizinho not in visitados:
                    visitados.add(vizinho)
                    novo_caminho = list(caminho)
                    novo_caminho.append(vizinho)
                    fila.append(novo_caminho)
        return None # Retorna None se não houver caminho

class Jogo:
    """Classe principal do jogo, que gerencia o estado do jogo, jogadores e o mapa."""
    def __init__(self):
        self.mapa = Mapa()
        self.jogadores = []
        self.turno_atual = 0
        self.turno_maximo = 100

    def carregar_mundo(self, mapa_json):
        """Carrega o tabuleiro a partir de um arquivo JSON gerado."""
        with open(mapa_json, 'r') as f:
            dados_mapa = json.load(f)
            for cidade_data in dados_mapa.get('cidades', []):
                self.mapa.adicionar_cidade(Cidade(**cidade_data))
            for aresta_data in dados_mapa.get('arestas', []):
                self.mapa.adicionar_aresta(Aresta(**aresta_data))

    def processar_turno(self):
        print(f"\n--- Processando Turno {self.turno_atual} ---")
        
        # Etapa 1: Processamento de Movimentos
        for jogador in self.jogadores:
            # Iteramos em todas as tropas do jogador
            for tropa in jogador.tropas:
                # Se a tropa está movendo, continuamos seu caminho
                if tropa.estado == 'movendo':
                    if tropa.caminho_atual:
                        proximo_passo = tropa.caminho_atual.pop(0)
                        
                        # Etapa de Validação
                        aresta = self.mapa.get_aresta(tropa.localizacao, proximo_passo)
                        cidade_destino = self.mapa.cidades[proximo_passo]
                        
                        # 1. A rota ainda pertence ao jogador?
                        if cidade_destino.dono != jogador.id and cidade_destino.id != jogador.base_id:
                            print(f"Tropa {tropa.id} encontrou cidade inimiga/neutra em {proximo_passo}! Recuo forçado.")
                            # TODO: Implementar lógica de recuo forçado (sobrescrever fila de comandos)
                            continue
                        
                        # 2. A tropa tem capacidade para passar?
                        if tropa.forca > aresta.peso:
                            print(f"Tropa {tropa.id} é muito grande para a aresta para {proximo_passo}! Recuo forçado.")
                            # TODO: Implementar lógica de recuo forçado
                            continue
                        
                        tropa.localizacao = proximo_passo
                        print(f"Tropa {tropa.id} moveu-se para {tropa.localizacao}")
                    
                    if not tropa.caminho_atual: # Se o caminho acabou
                        # Chegou ao destino do comando MOVER
                        tropa.estado = 'ociosa' 
                        print(f"Tropa {tropa.id} chegou ao destino.")
                        
                # Se a tropa está ociosa, pegamos um novo comando da fila
                elif tropa.estado == 'ociosa' and tropa.fila_de_comandos:
                    comando_atual = tropa.fila_de_comandos.pop(0)
                    
                    if comando_atual['tipo'] == 'MOVER':
                        destino_final = comando_atual['alvo']
                        print(f"Tropa {tropa.id} iniciando movimento de {tropa.localizacao} para {destino_final}")
                        
                        caminho = self.mapa.encontrar_caminho_bfs(tropa.localizacao, destino_final)
                        if caminho:
                            tropa.caminho_atual = caminho[1:] # Armazena o caminho, excluindo a cidade atual
                            tropa.estado = 'movendo'
                        else:
                            print(f"ERRO: Tropa {tropa.id} não encontrou caminho para {destino_final}")
        
        self.turno_atual += 1
