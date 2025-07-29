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
        # Estados possíveis: 'ociosa', 'movendo', 'atacando', 'recuando', 'encurralada', 'vitoriosa'
        self.estado = 'ociosa'
        self.caminho_atual = []
        self.alvo_de_ataque = None # Para guardar o alvo do comando ATACAR

class Transporte:
    """Representa o transporte de um jogador, que serve para mover população entre cidades
    ou converter em tropas na base."""
    def __init__(self, dono):
        self.dono = dono
        self.localizacao = dono.id_base
        self.carga_populacao = 0
        self.fila_de_comandos = []
        # Estados: 'ocioso', 'indo_coletar', 'transportando', 'retornando', 'destruido'
        self.estado = 'ocioso'
        self.caminho_atual = []
        self.timer_respawn = 0 # Para quando for destruído (nasce novamente na base após 1 turno)

class Jogador:
    """Representa um jogador no jogo."""
    def __init__(self, id, id_base):
        self.id = id
        self.id_base = id_base
        self.tropas = []
        self.tropas_na_base = 100
        self.transporte = Transporte(self) # Cada jogador tem um transporte associado

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

    def _resolver_combate_neutro(self, cidade, forca_total_atacante, tropa_lider):
        """Resolve o combate contra uma cidade neutra. As regras são diferentes de um combate normal."""
        defesa_total = cidade.populacao
        print(f"Tentativa de conquista em {cidade.id} (Neutra): Força da Tropa({forca_total_atacante}) vs População({defesa_total})")

        # Sucesso: A força do atacante deve ser maior ou igual à população.
        if forca_total_atacante >= defesa_total:
            print(f"Vitória! Jogador {tropa_lider.dono.id} conquistou {cidade.id}!")
            # A cidade assume novo dono
            cidade.dono = tropa_lider.dono.id

            # Muda o estado para tratar na Etapa 4
            tropa_lider.estado = 'vitoriosa'

        # Falha: A força do atacante é insuficiente.
        else:
            print(f"Falha na conquista! A força da Tropa {tropa_lider.id} ({forca_total_atacante}) é insuficiente para dominar {cidade.id}.")
            self._iniciar_recuo_forcado(tropa_lider, f"força insuficiente para conquistar a cidade neutra {cidade.id}")

    
    def _resolver_combate_jogador(self, cidade, forca_total_atacante, tropa_atacante_lider, eh_base=False):
        """Resolve o combate contra uma cidade ocupada por outro jogador ou uma base."""
        defensores = list(cidade.tropas_estacionadas)
        defesa_total = sum(t.forca for t in defensores)
        
        # A defesa da base inclui sua população
        if eh_base:
            defesa_total += cidade.populacao

        forca_ataque_efetiva = forca_total_atacante
        # A penalidade de 50% só se aplica ao atacar a base
        if eh_base:
            forca_ataque_efetiva *= 0.5
            print(f"Ataque à base! Força de ataque reduzida para {forca_ataque_efetiva}.")

        print(f"Combate em {cidade.id}: Ataque({forca_ataque_efetiva}) vs Defesa({defesa_total})")

        if forca_ataque_efetiva > defesa_total: # Vitória do atacante
            print(f"Vitória do jogador {tropa_atacante_lider.dono.id} em {cidade.id}!")
            # Remove todas as tropas defensoras
            for tropa_defensora in defensores:
                tropa_defensora.dono.tropas.remove(tropa_defensora)
            cidade.tropas_estacionadas.clear()
            
            cidade.dono = tropa_atacante_lider.dono.id
            tropa_atacante_lider.forca -= defesa_total # Atacante perde força igual à defesa
            tropa_atacante_lider.estado = 'vitoriosa'

        else: # Vitória do defensor
            print(f"Defensores de {cidade.dono} venceram o ataque em {cidade.id}!")
            # Remove a tropa atacante
            tropa_atacante_lider.dono.tropas.remove(tropa_atacante_lider)
            
            # Defensores perdem força
            dano_sofrido = forca_ataque_efetiva
            for tropa_defensora in defensores:
                if dano_sofrido <= 0: break
                perda = min(tropa_defensora.forca, dano_sofrido)
                tropa_defensora.forca -= perda
                dano_sofrido -= perda
            
            # Remove tropas defensoras que foram destruídas
            cidade.tropas_estacionadas[:] = [t for t in defensores if t.forca > 0]


    def _executar_fase_de_combates(self):
        """Coleta todos os ataques do turno e os resolve."""
        print("\n--- Fase de Resolução de Combates ---")
        ataques_por_cidade = {}

        # 1. Coleta e agrupa todos os ataques
        for jogador in self.jogadores.values():
            for tropa in jogador.tropas:
                if tropa.estado == 'atacando':
                    alvo_id = tropa.alvo_de_ataque
                    if alvo_id not in ataques_por_cidade:
                        ataques_por_cidade[alvo_id] = []
                    ataques_por_cidade[alvo_id].append(tropa)
        
        # 2. Resolve os combates cidade por cidade
        for cidade_id, lista_de_atacantes in ataques_por_cidade.items():
            cidade = self.mapa.cidades[cidade_id]
            forca_total_atacante = sum(t.forca for t in lista_de_atacantes)
            tropa_lider = lista_de_atacantes[0] # A primeira tropa lidera o ataque

            # Destrói as outras tropas atacantes (elas se fundem na tropa líder)
            for tropa in lista_de_atacantes[1:]:
                tropa.dono.tropas.remove(tropa)

            if cidade.dono is None:
                self._resolver_combate_neutro(cidade, forca_total_atacante, tropa_lider)
            elif "base" in cidade.id:
                 self._resolver_combate_jogador(cidade, forca_total_atacante, tropa_lider, eh_base=True)
            else:
                self._resolver_combate_jogador(cidade, forca_total_atacante, tropa_lider)

    def _executar_fase_pos_combate(self):
        """Processa as ações das tropas vitoriosas."""
        print("\n--- Fase de Pós-Combate ---")
        for jogador in self.jogadores.values():
            for tropa in list(jogador.tropas):
                if tropa.estado == 'vitoriosa':
                    proximo_comando = tropa.fila_de_comandos[0] if tropa.fila_de_comandos else None
                    
                    if proximo_comando and proximo_comando['tipo'] == 'PERMANECER':
                        tropa.fila_de_comandos.pop(0) # Consome o comando
                        tropa.estado = 'estacionada'
                        cidade_conquistada = self.mapa.cidades[tropa.localizacao]
                        cidade_conquistada.tropas_estacionadas.append(tropa)
                        print(f"Tropa {tropa.id} venceu e permaneceu em {tropa.localizacao}.")
                    else:
                        # Se não houver comando ou não for PERMANECER, a tropa recua (raid)
                        print(f"Tropa {tropa.id} venceu (raid) e iniciará o recuo.")
                        self._iniciar_recuo_forcado(tropa, "ataque 'raid' concluído")

    def _iniciar_retorno_transporte(self, transporte, motivo):
        """Função auxiliar para forçar o retorno do transporte à base."""
        print(f"Transporte de {transporte.dono.id} iniciando retorno à base. Motivo: {motivo}")
        transporte.fila_de_comandos.clear()
        caminho_de_volta = self.mapa.encontrar_caminho_bfs(transporte.localizacao, transporte.dono.id_base)
        if caminho_de_volta and len(caminho_de_volta) > 1:
            transporte.caminho_atual = caminho_de_volta[1:]
            transporte.estado = 'retornando'
        else:
            transporte.estado = 'ocioso' # Se já estiver na base ou não houver caminho disponível


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
        
            # Processamento dos transportes
            transporte = jogador.transporte
            
            # Checa se o transporte foi destruído e precisa respawnar
            if transporte.estado == 'destruido':
                transporte.timer_respawn -= 1
                if transporte.timer_respawn <= 0:
                    transporte.estado = 'ocioso'
                    transporte.localizacao = jogador.id_base
                    print(f"Transporte do jogador {jogador.id} foi reconstruído na base.")
                continue # Interrompe o processamento deste transporte se estiver destruído

            # Processa o movimento do transporte se ele estiver em um caminho
            if transporte.estado in ['indo_coletar', 'transportando', 'retornando']:
                if transporte.caminho_atual:
                    proximo_passo = transporte.caminho_atual.pop(0)
                    
                    # Validação da rota
                    cidade_destino = self.mapa.cidades[proximo_passo]
                    if cidade_destino.dono != jogador.id:# Rota hostil ou neutra, aplica penalidade
                        if cidade_destino.dono is None: # Cidade Neutra
                            perda = transporte.carga_populacao * 0.1
                            cidade_destino.populacao += perda
                            transporte.carga_populacao -= perda
                            print(f"Transporte de {jogador.id} encontrou cidade neutra! Perdeu {perda:.0f} de população.")
                            self._iniciar_retorno_transporte(transporte, "encontrou cidade neutra")
                        else: # Cidade Inimiga
                            cidade_destino.populacao += transporte.carga_populacao
                            transporte.carga_populacao = 0
                            transporte.estado = 'destruido'
                            transporte.timer_respawn = 2 # Leva 1 turno para reconstruir
                            print(f"Transporte de {jogador.id} DESTRUÍDO por cidade inimiga! Carga perdida.")
                        continue # Interrompe o movimento normal

                    transporte.localizacao = proximo_passo
                    print(f"Transporte de {jogador.id} ({transporte.estado}) moveu-se para {transporte.localizacao}")
                
                # Chegou ao destino do passo atual
                if not transporte.caminho_atual:
                    if transporte.estado == 'indo_coletar':
                        # Lógica de coleta
                        cidade_origem = self.mapa.cidades[transporte.localizacao]
                        quantidade_coletada = cidade_origem.populacao
                        transporte.carga_populacao += quantidade_coletada
                        cidade_origem.populacao = 0
                        print(f"Transporte coletou {quantidade_coletada} de população em {cidade_origem.id}.")
                        
                        # Calcula rota para o destino final
                        destino_final = transporte.fila_de_comandos[0]['destino']
                        caminho = self.mapa.encontrar_caminho_bfs(transporte.localizacao, destino_final)
                        if caminho and len(caminho) > 1:
                            transporte.caminho_atual = caminho[1:]
                            transporte.estado = 'transportando'
                        else:
                            self._iniciar_retorno_transporte(transporte, "não encontrou caminho para o destino")

                    elif transporte.estado == 'transportando':
                        # Lógica de entrega
                        cidade_destino = self.mapa.cidades[transporte.localizacao]
                        print(f"Transporte entregou {transporte.carga_populacao} de população em {cidade_destino.id}.")
                        
                        if "base" in cidade_destino.id: # Se o destino é a base, converte em tropas
                            jogador.tropas_na_base += transporte.carga_populacao
                            print(f"Jogador {jogador.id} converteu população em tropas! Total na base: {jogador.tropas_na_base:.0f}")
                        else: # Se for outra cidade, apenas aumenta a população
                            cidade_destino.populacao += transporte.carga_populacao
                        
                        transporte.carga_populacao = 0
                        transporte.fila_de_comandos.pop(0) # Remove o comando concluído
                        transporte.estado = 'ocioso'
                    
                    elif transporte.estado == 'retornando':
                        transporte.estado = 'ocioso'
                        print(f"Transporte de {jogador.id} retornou à base.")

            # Se o transporte está ocioso, pega um novo comando
            elif transporte.estado == 'ocioso' and transporte.fila_de_comandos:
                comando = transporte.fila_de_comandos[0] # Apenas lê, não remove ainda
                origem_coleta = comando['origem']

                print(f"Transporte de {jogador.id} iniciando missão: coletar em {origem_coleta} e levar para {comando['destino']}.")
                caminho = self.mapa.encontrar_caminho_bfs(transporte.localizacao, origem_coleta)
                if caminho and len(caminho) > 1:
                    transporte.caminho_atual = caminho[1:]
                    transporte.estado = 'indo_coletar'
                else:
                    print(f"AVISO: Transporte não encontrou caminho para a coleta em {origem_coleta}.")
                    transporte.fila_de_comandos.pop(0) # Descarta o comando impossível
        
        # Etapa 2: Cálculo de custos e suprimentos
        self._executar_fase_de_custo_e_suprimento()

        # Etapa 3: Resolução de combates
        if not self.jogadores_derrotados:  # Só executa se ainda houver jogadores ativos
            self._executar_fase_de_combates()

        # Etapa 4: Atualizações pós-combate
        if not self.jogadores_derrotados:  # Só executa se ainda houver jogadores ativos
            self._executar_fase_pos_combate()
        
        # Etapa 5: Verifica se o jogo terminou
        if self.turno_atual >= self.turno_maximo or len(self.jogadores) <= len(self.jogadores_derrotados):
            print("Fim do jogo! Jogadores restantes:")
            for jogador in self.jogadores.values():
                if jogador.id not in self.jogadores_derrotados:
                    print(f"Jogador {jogador.id} com {len(jogador.tropas)} tropas.")
            return

        # Se ainda houver jogadores ativos, incrementa o turno e salva o estado atual
        self.gerar_estado_json(f"estado_turno_{self.turno_atual}.json")
        self.turno_atual += 1
