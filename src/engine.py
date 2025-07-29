import os
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
        self.quantidade_solicitada = 0 # Para saber quanto coletar
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

    def gerar_estado_json(self, nome_arquivo, salvar_arquivo=True, diretorio="estados"):
        """
        Cria o dicionário com o estado do jogo e, opcionalmente, o salva em um arquivo
        dentro de um diretório específico.
        Retorna o dicionário de estado.
        """
        estado_atual = {
            "turno_atual": self.turno_atual,
            "mapa": {
                "cidades": [],
                "arestas": []
            },
            "jogadores": [],
            "tropas_em_campo": [],
            "transportes": []
        }

        # Serializa as cidades e arestas do mapa
        for cidade in self.mapa.cidades.values():
            estado_atual["mapa"]["cidades"].append({
                "id": cidade.id, "populacao": cidade.populacao,
                "pos": getattr(cidade, 'pos', [0, 0])
            })
        for aresta in self.mapa.arestas.values():
            estado_atual["mapa"]["arestas"].append({
                "de": aresta.cidades[0], "para": aresta.cidades[1], "peso": aresta.peso
            })
        
        cidades_possuidas_por_jogador = {j_id: [] for j_id in self.jogadores}
        for cidade in self.mapa.cidades.values():
            if cidade.dono in cidades_possuidas_por_jogador:
                cidades_possuidas_por_jogador[cidade.dono].append(cidade.id)
            
        for jogador in self.jogadores.values():
            estado_atual["jogadores"].append({
                "id": jogador.id, "tropas_na_base": jogador.tropas_na_base,
                "cidades_possuidas": cidades_possuidas_por_jogador.get(jogador.id, [])
            })
            for tropa in jogador.tropas:
                estado_atual["tropas_em_campo"].append({
                    "id": tropa.id, "dono": jogador.id, "forca": tropa.forca, "localizacao": tropa.localizacao
                })
            transporte = jogador.transporte
            estado_atual["transportes"].append({
                "dono": jogador.id, "localizacao": transporte.localizacao,
                "carga_populacao": transporte.carga_populacao, "estado": transporte.estado
            })

        # Salva o estado atual em um arquivo JSON, se solicitado
        if salvar_arquivo:
            os.makedirs(diretorio, exist_ok=True)
            
            # Constrói o caminho completo do arquivo
            caminho_completo = os.path.join(diretorio, nome_arquivo)
            
            # Salva o arquivo no caminho especificado
            with open(caminho_completo, 'w', encoding='utf-8') as f:
                json.dump(estado_atual, f, indent=2)
            print(f"Arquivo de estado '{caminho_completo}' gerado com sucesso.")

        return estado_atual
    
    def verificar_vencedor(self, anunciar_fim=False):
        """
        Verifica as condições de fim de jogo.
        Retorna o ID do vencedor se houver um, "EMPATE" se for o caso, ou None se o jogo continua.
        """
        jogadores_ativos = [j for j in self.jogadores.values() if j.id not in self.jogadores_derrotados]
        num_jogadores_ativos = len(jogadores_ativos)
        
        vencedor_final = None
        motivo = ""
        jogo_terminou = False

        if num_jogadores_ativos <= 1:
            jogo_terminou = True
            if num_jogadores_ativos == 1:
                vencedor_final = jogadores_ativos[0]
                motivo = f"Vitória por eliminação! Jogador {vencedor_final.id} foi o último restante."
            else:
                motivo = "EMPATE! Todos os jogadores foram eliminados."
                
        elif self.turno_atual >= self.turno_maximo:
            jogo_terminou = True
            motivo = "Fim de jogo por tempo! "
            
            contagem_cidades = {j.id: 0 for j in jogadores_ativos}
            for cidade in self.mapa.cidades.values():
                if cidade.dono in contagem_cidades:
                    contagem_cidades[cidade.dono] += 1
            
            if not contagem_cidades or max(contagem_cidades.values()) == 0:
                motivo += "EMPATE! Ninguém possuía cidades."
            else:
                max_cidades = max(contagem_cidades.values())
                possiveis_vencedores = [j_id for j_id, count in contagem_cidades.items() if count == max_cidades]
                
                if len(possiveis_vencedores) == 1:
                    vencedor_id = possiveis_vencedores[0]
                    vencedor_final = self.jogadores[vencedor_id]
                    motivo += f"Vitória por pontos! Jogador {vencedor_final.id} venceu com {max_cidades} cidades."
                else:
                    motivo += f"EMPATE! Os jogadores {possiveis_vencedores} terminaram com {max_cidades} cidades."

        if jogo_terminou and anunciar_fim:
            print(motivo)

        if vencedor_final:
            return vencedor_final.id
        elif jogo_terminou:
            return "EMPATE"
        else:
            return None

    def _iniciar_recuo_forcado(self, tropa, motivo):
        """
        Interrompe a ação atual de uma tropa e a força a recuar para a base.
        """
        print(f"RECUO FORÇADO para Tropa {tropa.id}! Motivo: {motivo}")

        # Limpa todos os planos antigos da tropa
        tropa.fila_de_comandos.clear()
        tropa.caminho_atual.clear()
        
        # Calcula o novo caminho de volta para a base
        caminho_de_volta = self.mapa.encontrar_caminho_bfs(tropa.localizacao, tropa.dono.id_base)

        if caminho_de_volta:
            # Se houver um caminho, define a nova rota de recuo
            tropa.caminho_atual = caminho_de_volta[1:] # Exclui a cidade atual do caminho
            tropa.estado = 'recuando'
        else:
            # Se não houver caminho (tropa está isolada), ela fica encurralada
            tropa.estado = 'encurralada'
            print(f"ALERTA: Tropa {tropa.id} está encurralada em {tropa.localizacao} e não pode recuar!")

    def _calcular_mst_prim(self, jogador):
        """
        Calcula a Árvore Geradora Mínima (MST) que conecta as cidades de um jogador,
        usando o Algoritmo de Prim. Retorna o custo total da manutenção e o 
        conjunto de cidades que estão efetivamente conectadas à base.
        """
        mapa = self.mapa
        jogador_id = jogador.id
        id_base = jogador.id_base

        # Copia todas as cidades do jogador, incluindo a base
        cidades_do_jogador = {c.id for c in mapa.cidades.values() if c.dono == jogador_id}
        cidades_do_jogador.add(id_base)

        if len(cidades_do_jogador) <= 1:
            return 0, cidades_do_jogador

        custo_total = 0
        cidades_conectadas = {id_base}
        fronteira = []

        push = heapq.heappush
        pop = heapq.heappop

        # Pré-carrega vizinhos e arestas iniciais pra evitar lookup desnecessário
        for vizinho_id in mapa.get_vizinhos(id_base):
            if vizinho_id in cidades_do_jogador:
                aresta = mapa.get_aresta(id_base, vizinho_id)
                if aresta:
                    push(fronteira, (aresta.peso, id_base, vizinho_id))

        while fronteira and len(cidades_conectadas) < len(cidades_do_jogador):
            peso, _, destino = pop(fronteira)

            if destino in cidades_conectadas:
                continue

            cidades_conectadas.add(destino)
            custo_total += peso

            for vizinho_id in mapa.get_vizinhos(destino):
                if vizinho_id in cidades_do_jogador and vizinho_id not in cidades_conectadas:
                    aresta = mapa.get_aresta(destino, vizinho_id)
                    if aresta:
                        push(fronteira, (aresta.peso, destino, vizinho_id))

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

    def _processar_movimento_tropas(self, jogador):
        """Processa os movimentos e comandos de todas as tropas de um jogador."""
        # Iterar sobre uma cópia da lista é mais seguro
        for tropa in list(jogador.tropas): 
            # Lógica de movimento para tropas que já estão em um caminho
            if tropa.estado in ['movendo', 'recuando']:
                if tropa.caminho_atual:
                    proximo_passo = tropa.caminho_atual.pop(0)
                    
                    aresta = self.mapa.get_aresta(tropa.localizacao, proximo_passo)
                    cidade_destino = self.mapa.cidades[proximo_passo]
                    
                    # Validações de movimento...
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
            
            # Lógica para tropas ociosas que têm novos comandos para executar
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
                        tropa.fila_de_comandos.insert(0, comando_atual)
                        print(f"AVISO: Tropa {tropa.id} não pôde iniciar movimento para {destino_final}.")

                elif comando_atual['tipo'] == 'ATACAR':
                    alvo_id = comando_atual['alvo']
                    if alvo_id in self.mapa.get_vizinhos(tropa.localizacao):
                        tropa.estado = 'atacando'
                        tropa.alvo_de_ataque = alvo_id
                        print(f"Tropa {tropa.id} está agora atacando {alvo_id}.")
                    else:
                        print(f"ERRO: Tropa {tropa.id} tentou atacar {alvo_id} de {tropa.localizacao}, mas não é vizinho.")
                
                elif comando_atual['tipo'] == 'PERMANECER':
                    tropa.estado = 'estacionada'
                    cidade_atual = self.mapa.cidades[tropa.localizacao]
                    cidade_atual.tropas_estacionadas.append(tropa)
                    jogador.tropas.remove(tropa)
                    print(f"Tropa {tropa.id} agora está estacionada em {tropa.localizacao}.")

                elif comando_atual['tipo'] == 'RECUAR':
                    print(f"Tropa {tropa.id} iniciando recuo voluntário de {tropa.localizacao}.")
                    self._iniciar_recuo_forcado(tropa, "ordem de recuo do jogador")

    def _processar_movimento_transporte(self, jogador):
        """Processa o movimento e os comandos do transporte de um jogador."""
        transporte = jogador.transporte
        
        if transporte.estado == 'destruido':
            transporte.timer_respawn -= 1
            if transporte.timer_respawn <= 0:
                transporte.estado = 'ocioso'
                transporte.localizacao = jogador.id_base
                print(f"Transporte do jogador {jogador.id} foi reconstruído na base.")
            return # Pula o resto da lógica para este transporte

        if transporte.estado in ['indo_coletar', 'transportando', 'retornando']:
            if transporte.caminho_atual:
                proximo_passo = transporte.caminho_atual.pop(0)
                
                cidade_destino = self.mapa.cidades[proximo_passo]
                if cidade_destino.dono != jogador.id:
                    if cidade_destino.dono is None: # Neutra
                        perda = transporte.carga_populacao * 0.1
                        cidade_destino.populacao += perda
                        transporte.carga_populacao -= perda
                        print(f"Transporte de {jogador.id} encontrou cidade neutra! Perdeu {perda:.0f} de população.")
                        self._iniciar_retorno_transporte(transporte, "encontrou cidade neutra")
                    else: # Inimiga
                        cidade_destino.populacao += transporte.carga_populacao
                        transporte.carga_populacao = 0
                        transporte.estado = 'destruido'
                        transporte.timer_respawn = 2
                        print(f"Transporte de {jogador.id} DESTRUÍDO por cidade inimiga! Carga perdida.")
                    return # Interrompe o movimento

                transporte.localizacao = proximo_passo
                print(f"Transporte de {jogador.id} ({transporte.estado}) moveu-se para {transporte.localizacao}")
            
            if not transporte.caminho_atual:
                if transporte.estado == 'indo_coletar':
                    cidade_origem = self.mapa.cidades[transporte.localizacao]
                    quantidade_coletada = min(cidade_origem.populacao, transporte.quantidade_solicitada)
                    transporte.carga_populacao += quantidade_coletada
                    cidade_origem.populacao -= quantidade_coletada
                    print(f"Transporte coletou {quantidade_coletada} de população em {cidade_origem.id}.")
                    
                    destino_final = transporte.fila_de_comandos[0]['destino']
                    caminho = self.mapa.encontrar_caminho_bfs(transporte.localizacao, destino_final)
                    if caminho and len(caminho) > 1:
                        transporte.caminho_atual = caminho[1:]
                        transporte.estado = 'transportando'
                    else:
                        self._iniciar_retorno_transporte(transporte, "não encontrou caminho para o destino")

                elif transporte.estado == 'transportando':
                    cidade_destino = self.mapa.cidades[transporte.localizacao]
                    print(f"Transporte entregou {transporte.carga_populacao} de população em {cidade_destino.id}.")
                    
                    if "base" in cidade_destino.id:
                        jogador.tropas_na_base += transporte.carga_populacao
                        print(f"Jogador {jogador.id} converteu população em tropas! Total na base: {jogador.tropas_na_base:.0f}")
                    else:
                        cidade_destino.populacao += transporte.carga_populacao
                    
                    transporte.carga_populacao = 0
                    transporte.fila_de_comandos.pop(0)
                    transporte.estado = 'ocioso'
                
                elif transporte.estado == 'retornando':
                    transporte.estado = 'ocioso'
                    print(f"Transporte de {jogador.id} retornou à base.")

        elif transporte.estado == 'ocioso' and transporte.fila_de_comandos:
            comando = transporte.fila_de_comandos[0]
            origem_coleta = comando['origem']

            print(f"Transporte de {jogador.id} iniciando missão: coletar em {origem_coleta} e levar para {comando['destino']}.")
            caminho = self.mapa.encontrar_caminho_bfs(transporte.localizacao, origem_coleta)
            if caminho and len(caminho) > 1:
                transporte.caminho_atual = caminho[1:]
                transporte.estado = 'indo_coletar'
            else:
                print(f"AVISO: Transporte não encontrou caminho para a coleta em {origem_coleta}.")
                transporte.fila_de_comandos.pop(0)

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

    def _verificar_e_processar_fim_de_jogo(self):
        """
        Verifica se as condições de fim de jogo foram atingidas.
        Se sim, determina o vencedor ou o empate e retorna True.
        Se não, retorna False.
        """
        jogadores_ativos = [j for j in self.jogadores.values() if j.id not in self.jogadores_derrotados]
        num_jogadores_ativos = len(jogadores_ativos)
        
        jogo_terminou = False
        motivo_fim_de_jogo = ""

        # Condição 1: Fim por tempo ou eliminação
        if self.turno_atual >= self.turno_maximo or num_jogadores_ativos <= 1:
            jogo_terminou = True
            
            # Sub-condição 1.1: Vitória por ser o último jogador restante
            if num_jogadores_ativos == 1:
                vencedor = jogadores_ativos[0]
                motivo_fim_de_jogo = f"Vitória por eliminação! Jogador {vencedor.id} foi o último restante."
            
            # Sub-condição 1.2: Fim por tempo, ativa o desempate por cidades
            elif self.turno_atual >= self.turno_maximo:
                motivo_fim_de_jogo = "Fim de jogo por tempo! "
                
                contagem_cidades = {j.id: 0 for j in jogadores_ativos}
                for cidade in self.mapa.cidades.values():
                    if cidade.dono in contagem_cidades:
                        contagem_cidades[cidade.dono] += 1
                
                if not contagem_cidades or max(contagem_cidades.values()) == 0:
                    motivo_fim_de_jogo += "EMPATE! Ninguém possuía cidades."
                else:
                    max_cidades = max(contagem_cidades.values())
                    possiveis_vencedores = [j_id for j_id, count in contagem_cidades.items() if count == max_cidades]
                    
                    if len(possiveis_vencedores) == 1:
                        vencedor_id = possiveis_vencedores[0]
                        motivo_fim_de_jogo += f"Vitória por pontos! Jogador {vencedor_id} venceu com {max_cidades} cidades."
                    else:
                        motivo_fim_de_jogo += f"EMPATE! Os jogadores {possiveis_vencedores} terminaram com {max_cidades} cidades."
            
            # Sub-condição 1.3: Empate por eliminação mútua
            else:
                motivo_fim_de_jogo = "EMPATE! Todos os jogadores foram eliminados."

        if jogo_terminou:
            print(motivo_fim_de_jogo)
            self.gerar_estado_json(f"estado_final_turno_{self.turno_atual}.json")
            return True # Sinaliza para o loop principal que o jogo acabou

        return False # O jogo continua


    def processar_turno(self):
        print(f"\n--- Processando Turno {self.turno_atual} ---")
        
        # Etapa 1: Processamento de comandos de tropas e transportes
        for jogador in self.jogadores.values():
            if jogador.id in self.jogadores_derrotados: continue
            
            # Processa comandos de tropas
            self._processar_movimento_tropas(jogador)

            # Processa comandos de transporte
            self._processar_movimento_transporte(jogador)

        # Etapa 2: Cálculo de custos e suprimentos
        self._executar_fase_de_custo_e_suprimento()

        # Etapa 3: Resolução de combates
        if not self.jogadores_derrotados:  # Só executa se ainda houver jogadores ativos
            self._executar_fase_de_combates()

        # Etapa 4: Atualizações pós-combate
        if not self.jogadores_derrotados:  # Só executa se ainda houver jogadores ativos
            self._executar_fase_pos_combate()
        
        # Etapa 5: Verifica se o jogo terminou
        if self._verificar_e_processar_fim_de_jogo():
                    return

        # Se ainda houver jogadores ativos, incrementa o turno e salva o estado atual
        self.gerar_estado_json(f"estado_turno_{self.turno_atual}.json")
        self.turno_atual += 1
