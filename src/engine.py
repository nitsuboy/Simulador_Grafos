import json
import heapq
from collections import deque

class Cidade:
    """Representa uma cidade no mapa do jogo (apenas dados lógicos)."""
    def __init__(self, id, populacao):
        self.id = id
        self.populacao = populacao
        self.dono = None
        self.tropas_estacionadas = []

class Tropa:
    """Representa uma tropa no jogo."""
    def __init__(self, id, dono, forca, fila_de_comandos=None):
        self.id = id
        self.dono = dono
        self.forca = forca
        self.localizacao = dono.id_base
        self.fila_de_comandos = fila_de_comandos if fila_de_comandos is not None else []
        # Estados possíveis: 'ociosa', 'movendo', 'atacando', 'recuando', 'encurralada'
        self.estado = 'ociosa'
        self.caminho_atual = []
        self.alvo_de_ataque = None # Para guardar o alvo do comando ATACAR

class Jogador:
    """Representa um jogador no jogo."""
    def __init__(self, id, id_base):
        self.id = id
        self.id_base = id_base
        self.tropas = []
        self.tropas_na_base = 100

class Aresta:
    """Representa uma aresta lógica entre duas cidades."""
    def __init__(self, cidade1_id, cidade2_id, peso):
        self.cidades = (cidade1_id, cidade2_id)
        self.peso = peso

class Mapa:
    """Representa a estrutura lógica do mapa do jogo."""
    def __init__(self):
        self.cidades = {}
        self.arestas = {}

    def adicionar_cidade(self, cidade):
        """Adiciona uma cidade ao mapa."""
        self.cidades[cidade.id] = cidade

    def adicionar_aresta(self, cidade1_id, cidade2_id, peso):
        """Adiciona uma aresta entre duas cidades."""
        chave = tuple(sorted((cidade1_id, cidade2_id)))
        if chave not in self.arestas:
            self.arestas[chave] = Aresta(cidade1_id, cidade2_id, peso)

    def get_aresta(self, cidade1_id, cidade2_id):
        """Retorna a aresta entre duas cidades, se existir."""
        chave = tuple(sorted((cidade1_id, cidade2_id)))
        return self.arestas.get(chave)

    def get_vizinhos(self, cidade_id):
        """Retorna uma lista de IDs de cidades vizinhas a uma cidade específica."""
        vizinhos = []
        for cidades_na_aresta in self.arestas.keys():
            if cidade_id in cidades_na_aresta:
                vizinho = cidades_na_aresta[0] if cidades_na_aresta[1] == cidade_id else cidades_na_aresta[1]
                vizinhos.append(vizinho)
        return vizinhos
    
    def encontrar_caminho_bfs(self, inicio_id, fim_id):
        """Encontra o caminho mais curto entre duas cidades usando BFS."""
        if inicio_id == fim_id: return [inicio_id]
        fila = deque([[inicio_id]])
        visitados = {inicio_id}
        while fila:
            caminho = fila.popleft()
            ultimo_no = caminho[-1]
            if ultimo_no == fim_id: return caminho
            for vizinho in self.get_vizinhos(ultimo_no):
                if vizinho not in visitados:
                    visitados.add(vizinho)
                    novo_caminho = list(caminho)
                    novo_caminho.append(vizinho)
                    fila.append(novo_caminho)
        return None

class Jogo:
    """Classe principal da engine, gerencia a lógica e o estado do jogo."""
    def __init__(self):
        self.mapa = Mapa()
        self.jogadores = {}
        self.turno_atual = 0
        self.turno_maximo = 100
        self.jogadores_derrotados = [] # Para guardar qualquer jogador derrotado

    def carregar_mundo(self, mapa_json):
        """Carrega a estrutura lógica do mundo a partir do JSON do gerador."""
        with open(mapa_json, 'r') as f:
            dados_mapa = json.load(f)
            for cidade_data in dados_mapa.get('cidades', []):
                # A engine agora ignora a informação de 'pos'
                self.mapa.adicionar_cidade(Cidade(cidade_data['id'], cidade_data['populacao']))
            for aresta_data in dados_mapa.get('arestas', []):
                self.mapa.adicionar_aresta(aresta_data['de'], aresta_data['para'], aresta_data['peso'])

    def gerar_estado_json(self, nome_arquivo):
        """Salva o estado dinâmico do jogo (sem dados de layout)."""
        estado_atual = {
            "turno_atual": self.turno_atual,
            "jogadores": [],
            "cidades": [],
            "tropas_em_campo": [],
            "transportes": []
        }

        # Serializa o estado dinâmico das cidades (dono, pop atual)
        for cidade in self.mapa.cidades.values():
            estado_atual["cidades"].append({
                "id": cidade.id,
                "dono": cidade.dono,
                "populacao": cidade.populacao
            })
        
        # Serializa jogadores e tropas
        for jogador in self.jogadores.values():
            estado_atual["jogadores"].append({
                "id": jogador.id,
                "tropas_na_base": jogador.tropas_na_base
            })
            for tropa in jogador.tropas:
                estado_atual["tropas_em_campo"].append({
                    "id": tropa.id,
                    "dono": jogador.id,
                    "forca": tropa.forca,
                    "localizacao": tropa.localizacao
                })

        with open(nome_arquivo, 'w', encoding='utf-8') as f:
            json.dump(estado_atual, f, indent=2)
        print(f"Arquivo de estado '{nome_arquivo}' gerado com sucesso.")

    def _iniciar_recuo_forcado(self, tropa, motivo):
        """
        Interrompe a ação atual de uma tropa e a força a recuar para a base.
        """
        print(f"RECIO FORÇADO para Tropa {tropa.id}! Motivo: {motivo}")

        # 1. Limpa todos os planos antigos da tropa
        tropa.fila_de_comandos.clear()
        tropa.caminho_atual.clear()
        
        # 2. Calcula o novo caminho de volta para a base
        caminho_de_volta = self.mapa.encontrar_caminho_bfs(tropa.localizacao, tropa.dono.id_base)

        if caminho_de_volta:
            # 3. Se houver um caminho, define a nova rota de recuo
            tropa.caminho_atual = caminho_de_volta[1:] # Exclui a cidade atual do caminho
            tropa.estado = 'recuando'
        else:
            # 4. Se não houver caminho (tropa está isolada), ela fica encurralada
            tropa.estado = 'encurralada'
            print(f"ALERTA: Tropa {tropa.id} está encurralada em {tropa.localizacao} e não pode recuar!")

    def _calcular_mst_prim(self, jogador):
        """
        Calcula a Árvore Geradora Mínima (MST) para as cidades de um jogador usando o Algoritmo de Prim.
        Retorna o custo total da manutenção e o conjunto de cidades conectadas.
        """
        cidades_do_jogador = {c.id for c in self.mapa.cidades.values() if c.dono == jogador.id}
        if not cidades_do_jogador:
            return 0, set()

        custo_total = 0
        cidades_conectadas = {jogador.id_base}
        
        # Fila de prioridade para guardar as arestas como (custo, cidade1, cidade2)
        fronteira = []

        # Começa a busca a partir da base
        no_atual = jogador.id_base
        
        while True:
            # Adiciona todas as arestas do nó atual à fronteira
            for vizinho_id in self.mapa.get_vizinhos(no_atual):
                aresta = self.mapa.get_aresta(no_atual, vizinho_id)
                if aresta:
                    # Adiciona à fila com o peso como prioridade
                    heapq.heappush(fronteira, (aresta.peso, no_atual, vizinho_id))

            # Encontra a próxima aresta mais barata que conecta a uma cidade nova
            aresta_mais_barata = None
            while fronteira:
                peso, de, para = heapq.heappop(fronteira)
                if para not in cidades_conectadas:
                    aresta_mais_barata = (peso, de, para)
                    break
            
            if aresta_mais_barata:
                peso, de, para = aresta_mais_barata
                custo_total += peso
                cidades_conectadas.add(para)
                no_atual = para
            else:
                # Se não há mais arestas para conectar novas cidades, paramos
                break
        
        return custo_total, cidades_conectadas

    def _executar_fase_de_custo_e_suprimento(self):
        """
        Verifica a conectividade do império de cada jogador e calcula os custos.
        """
        print("\n--- Fase de Custo e Suprimento ---")
        for jogador in self.jogadores.values():
            if jogador.id in self.jogadores_derrotados:
                continue

            # Calcula a MST e verifica a conectividade
            custo_total_manutencao, cidades_conectadas = self._calcular_mst_prim(jogador)
            
            cidades_possuidas_antes = {c.id for c in self.mapa.cidades.values() if c.dono == jogador.id}

            # Identifica e neutraliza cidades isoladas
            cidades_isoladas = cidades_possuidas_antes - cidades_conectadas
            for cidade_id in cidades_isoladas:
                cidade = self.mapa.cidades[cidade_id]
                print(f"ALERTA: Cidade {cidade.id} do jogador {jogador.id} ficou isolada e se tornou neutra!")
                cidade.dono = None
                # Tropas estacionadas são dadas como perdidas
                for tropa in cidade.tropas_estacionadas:
                    jogador.tropas.remove(tropa) # Remove da lista geral de tropas para não contar mais
                cidade.tropas_estacionadas.clear()

            # Calcula o custo final e o debita da base
            custo_do_turno = custo_total_manutencao / 100
            print(f"Jogador {jogador.id}: Custo de manutenção do império = {custo_do_turno:.2f}")
            jogador.tropas_na_base -= custo_do_turno

            # Verifica a condição de derrota por falência
            if jogador.tropas_na_base <= 0:
                print(f"DERROTA: Jogador {jogador.id} foi à falência (tropas na base <= 0)!")
                self.jogadores_derrotados.append(jogador.id)
                # Neutraliza todas as cidades do jogador derrotado
                for cidade_id in cidades_conectadas: # Apenas as que ainda eram dele
                     self.mapa.cidades[cidade_id].dono = None
                # Remove todas as tropas do jogador
                jogador.tropas.clear()

    def processar_turno(self):
        print(f"\n--- Processando Turno {self.turno_atual} ---")
        
        # Etapa 1: Processamento de Comandos e Movimentos
        for jogador_id, jogador in self.jogadores.items():
            # Iterar sobre uma cópia da lista é mais seguro se a lista for modificada
            for tropa in list(jogador.tropas): 
                
                # Lógica de movimento para tropas que já estão em um caminho
                if tropa.estado in ['movendo', 'recuando']:
                    if tropa.caminho_atual:
                        proximo_passo = tropa.caminho_atual.pop(0)
                        
                        aresta = self.mapa.get_aresta(tropa.localizacao, proximo_passo)
                        cidade_destino = self.mapa.cidades[proximo_passo]
                        
                        # Validações de movimento 
                        if tropa.estado == 'movendo' and cidade_destino.dono != jogador.id and cidade_destino.id != jogador.id_base:
                            self._iniciar_recuo_forcado(tropa, f"encontrou cidade inimiga/neutra em {proximo_passo}")
                            continue
                        
                        if tropa.estado == 'movendo' and tropa.forca > aresta.peso:
                            self._iniciar_recuo_forcado(tropa, f"é muito grande para a aresta para {proximo_passo}")
                            continue
                        
                        tropa.localizacao = proximo_passo
                        print(f"Tropa {tropa.id} ({tropa.estado}) moveu-se para {tropa.localizacao}")
                    
                    if not tropa.caminho_atual:
                        tropa.estado = 'ociosa'
                        print(f"Tropa {tropa.id} chegou ao seu destino.")
                        
                # Quando tropas ociosas que têm novos comandos para executar
                elif tropa.estado == 'ociosa' and tropa.fila_de_comandos:
                    comando_atual = tropa.fila_de_comandos.pop(0)

                    if comando_atual['tipo'] == 'MOVER':
                        destino_final = comando_atual['alvo']
                        print(f"Tropa {tropa.id} iniciando movimento de {tropa.localizacao} para {destino_final}")
                        caminho = self.mapa.encontrar_caminho_bfs(tropa.localizacao, destino_final)
                        if caminho and len(caminho) > 1:
                            tropa.caminho_atual = caminho[1:]
                            tropa.estado = 'movendo'
                        else:
                            tropa.fila_de_comandos.insert(0, comando_atual) # Devolve o comando para a fila
                            print(f"AVISO: Tropa {tropa.id} não pôde iniciar movimento para {destino_final}.")

                    elif comando_atual['tipo'] == 'ATACAR':
                        alvo_id = comando_atual['alvo']
                        # Validação: o alvo do ataque é vizinho da localização atual da tropa?
                        if alvo_id in self.mapa.get_vizinhos(tropa.localizacao):
                            tropa.estado = 'atacando'
                            tropa.alvo_de_ataque = alvo_id
                            print(f"Tropa {tropa.id} está agora atacando {alvo_id}. Combate será resolvido no final do turno.")
                        else:
                            print(f"ERRO: Tropa {tropa.id} tentou atacar {alvo_id} de {tropa.localizacao}, mas não é vizinho. Ordem ignorada.")
                    
                    elif comando_atual['tipo'] == 'PERMANECER':
                        tropa.estado = 'estacionada'
                        cidade_atual = self.mapa.cidades[tropa.localizacao]
                        cidade_atual.tropas_estacionadas.append(tropa)
                        jogador.tropas.remove(tropa) # Move da lista de tropas ativas para a guarnição
                        print(f"Tropa {tropa.id} agora está estacionada em {tropa.localizacao} como guarnição.")

                    elif comando_atual['tipo'] == 'RECUAR':
                        print(f"Tropa {tropa.id} iniciando recuo voluntário de {tropa.localizacao}.")
                        # A lógica é a mesma do recuo forçado, mas sem o motivo de penalidade
                        self._iniciar_recuo_forcado(tropa, "ordem de recuo do jogador")
        
        # Etapa 2: Cálculo de custos e suprimentos
        self._executar_fase_de_custo_e_suprimento()
        
        self.gerar_estado_json(f"estado_turno_{self.turno_atual}.json")
        self.turno_atual += 1
