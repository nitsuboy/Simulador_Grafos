import os
import json
import heapq
from collections import deque


class Cidade:
    """Representa uma cidade no mapa do jogo (apenas dados lógicos)."""

    def __init__(self, id, populacao: int):
        self.id = id
        self.populacao = populacao
        self.dono = None
        self.tropas_estacionadas = []


class Tropa:
    """Representa uma tropa no jogo."""

    def __init__(self, id, dono, forca: int, fila_de_comandos=None):
        self.id = id
        self.dono = dono
        self.forca = forca
        self.localizacao = dono.id_base
        self.fila_de_comandos = fila_de_comandos if fila_de_comandos is not None else []
        # Estados possíveis: 'ociosa', 'movendo', 'atacando', 'recuando', 'vitoriosa'
        self.estado = "ociosa"
        self.caminho_atual = []
        self.alvo_de_ataque = None  # Para guardar o alvo do comando ATACAR

    def __repr__(self):
        return f"{self.id}"


class Transporte:
    """Representa o transporte de um jogador, que serve para mover população entre cidades
    ou converter em tropas na base."""

    def __init__(self, dono):
        self.dono = dono
        self.localizacao = dono.id_base
        self.carga_populacao = 0
        self.fila_de_comandos = []
        # Estados: 'ocioso', 'indo_coletar', 'transportando', 'retornando', 'destruido'
        self.estado = "ocioso"
        self.quantidade_solicitada = 0  # Para saber quanto coletar
        self.caminho_atual = []
        self.timer_respawn = (
            0  # Para quando for destruído (nasce novamente na base após 1 turno)
        )


class Jogador:
    """Representa um jogador no jogo."""

    def __init__(self, id, id_base):
        self.id = id
        self.id_base = id_base
        self.tropas = []
        self.tropas_na_base = 500
        self.transporte = Transporte(self)  # Cada jogador tem um transporte associado


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
        self.lista_adjacencia = {}  # Para consultas rápidas de vizinhos

    def adicionar_cidade(self, cidade):
        """Adiciona uma cidade ao mapa."""
        if cidade.id in self.cidades:
            print(f"AVISO: Cidade {cidade.id} já existe no mapa. Ignorando.")
            return
        self.cidades[cidade.id] = cidade

    def adicionar_aresta(self, cidade1_id, cidade2_id, peso):
        """Adiciona uma aresta entre duas cidades."""
        chave = tuple(sorted((cidade1_id, cidade2_id)))
        if chave in self.arestas:
            print(f"AVISO: Aresta {chave} já existe. Ignorando.")
            return
        self.arestas[chave] = Aresta(cidade1_id, cidade2_id, peso)

    def get_aresta(self, cidade1_id, cidade2_id):
        """Retorna a aresta entre duas cidades, se existir."""
        chave = tuple(sorted((cidade1_id, cidade2_id)))
        return self.arestas.get(chave)

    def get_vizinhos(self, cidade_id):
        """Retorna uma lista de IDs de cidades vizinhas a uma cidade específica."""
        # Agora usa a lista de adjacência
        vizinhos = [vizinho for vizinho, _ in self.lista_adjacencia.get(cidade_id, [])]
        return vizinhos

    def encontrar_caminho(self, origem_id, destino_id, jogador_id=None):
        """
        Encontra um caminho seguro entre duas cidades considerando o dono.
        - Só atravessa cidades do jogador ou o destino final.
        - Usa BFS para retornar o menor caminho válido.
        """
        if origem_id not in self.cidades or destino_id not in self.cidades:
            print("Origem ou destino inválido.")
            return None

        if origem_id == destino_id:
            return [origem_id,origem_id]  # Retorna o próprio caminho se origem e destino forem iguais
        
        fila = deque([[origem_id]])  # fila guarda caminhos
        visitados = set([origem_id])

        while fila:
            caminho = fila.popleft()
            atual = caminho[-1]

            # Verifica se chegou ao destino
            if atual == destino_id:
                return caminho

            # Explora vizinhos não visitados
            for vizinho, _ in self.lista_adjacencia.get(atual, []):
                if jogador_id:
                    if (
                        self.cidades[vizinho].dono == jogador_id
                        or vizinho == destino_id
                    ):
                        if vizinho not in visitados:
                            visitados.add(vizinho)
                            fila.append(caminho + [vizinho])
                else:
                    if vizinho not in visitados:
                        visitados.add(vizinho)
                        fila.append(caminho + [vizinho])
        return None  # Nenhum caminho seguro encontrado


class MapaSomenteLeitura:
    def __init__(self, mapa: Mapa):
        self._mapa = mapa

    def get_vizinhos(self, cidade_id):
        return self._mapa.get_vizinhos(cidade_id)

    def get_cidades(self):
        return self._mapa.cidades

    def get_arestas(self):
        return self._mapa.arestas

    def get_lista_adjacencia(self):
        return self._mapa.lista_adjacencia

    def encontrar_caminho_bfs(self, inicio_id, fim_id):
        return self._mapa.encontrar_caminho(inicio_id, fim_id)


class Jogo:
    """Classe principal da engine, gerencia a lógica e o estado do jogo."""

    def __init__(self):
        self.mapa = Mapa()
        self.mapa_somente_leitura = MapaSomenteLeitura(self.mapa)
        self.jogadores = {}
        self.turno_atual = 0
        self.turno_maximo = 100
        self.jogadores_derrotados = []  # Para guardar qualquer jogador derrotado

    def carregar_mundo(self, mapa_json):
        """Carrega a estrutura lógica do mundo a partir do JSON do gerador."""
        with open(mapa_json, "r") as f:
            dados_mapa = json.load(f)
            for cidade_data in dados_mapa.get("cidades", []):
                # A engine agora ignora a informação de 'pos'
                self.mapa.adicionar_cidade(
                    Cidade(cidade_data["id"], cidade_data["populacao"])
                )
            for aresta_data in dados_mapa.get("arestas", []):
                self.mapa.adicionar_aresta(
                    aresta_data["de"], aresta_data["para"], aresta_data["peso"]
                )
            for adj in dados_mapa["lista_adjacencia"]:
                cidade = adj["cidade"]
                vizinhos = [(v["id"], v["peso"]) for v in adj["vizinhos"]]
                self.mapa.lista_adjacencia[cidade] = vizinhos

    def gerar_estado_json(self, nome_arquivo, salvar_arquivo=True, diretorio="estados"):
        """
        Cria o dicionário com o estado completo do jogo e, opcionalmente, o salva.
        Retorna o dicionário de estado.
        """
        # Estrutura principal do JSON de estado
        estado_atual = {
            "turno_atual": self.turno_atual,
            "mapa": {"cidades": [], "arestas": []},
            "jogadores": [],
            "tropas_em_campo": [],
            "transportes": [],
        }

        # Serializa a estrutura do mapa e coleta informações das cidades possuídas
        cidades_possuidas_por_jogador = {j_id: [] for j_id in self.jogadores}

        for cidade in self.mapa.cidades.values():
            # Adiciona a cidade à lista do mapa no JSON
            estado_atual["mapa"]["cidades"].append(
                {
                    "id": cidade.id,
                    "populacao": cidade.populacao,
                    "dono": cidade.dono,
                    "tropas_estacionadas": [
                        {"id": tropa.id, "forca": tropa.forca}
                        for tropa in cidade.tropas_estacionadas
                    ],
                }
            )
            # Ao mesmo tempo, se a cidade tiver um dono, adiciona à lista de contagem
            if cidade.dono is not None and cidade.dono in cidades_possuidas_por_jogador:
                cidades_possuidas_por_jogador[cidade.dono].append(cidade.id)

        for aresta in self.mapa.arestas.values():
            estado_atual["mapa"]["arestas"].append(
                {
                    "de": aresta.cidades[0],
                    "para": aresta.cidades[1],
                    "peso": aresta.peso,
                }
            )

        # Serializa os jogadores e suas unidades
        for jogador in self.jogadores.values():
            # Adiciona as informações do jogador
            estado_atual["jogadores"].append(
                {
                    "id": jogador.id,
                    "tropas_na_base": jogador.tropas_na_base,
                    "cidades_possuidas": cidades_possuidas_por_jogador[jogador.id],
                }
            )

            # Adiciona as tropas em campo daquele jogador
            for tropa in jogador.tropas:
                estado_atual["tropas_em_campo"].append(
                    {
                        "id": tropa.id,
                        "dono": jogador.id,
                        "forca": tropa.forca,
                        "localizacao": tropa.localizacao,
                    }
                )

            # Adiciona o estado do transporte daquele jogador
            transporte = jogador.transporte
            estado_atual["transportes"].append(
                {
                    "dono": jogador.id,
                    "localizacao": transporte.localizacao,
                    "carga_populacao": transporte.carga_populacao,
                    "estado": transporte.estado,
                }
            )

        # Salva o arquivo, se solicitado
        if salvar_arquivo:
            os.makedirs(diretorio, exist_ok=True)
            caminho_completo = os.path.join(diretorio, nome_arquivo)
            with open(caminho_completo, "w", encoding="utf-8") as f:
                json.dump(estado_atual, f, indent=2)
            print(f"Arquivo de estado '{caminho_completo}' gerado com sucesso.")

        return estado_atual

    def verificar_vencedor(self, anunciar_fim=False):
        """
        Verifica as condições de fim de jogo.
        Retorna o ID do vencedor se houver um, "EMPATE" se for o caso, ou None se o jogo continua.
        """
        jogadores_ativos = [
            j for j in self.jogadores.values() if j.id not in self.jogadores_derrotados
        ]
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
                # Só conta a cidade se ela tiver um dono E se o ID dela NÃO contiver "base"
                if cidade.dono in contagem_cidades and "base" not in cidade.id:
                    contagem_cidades[cidade.dono] += 1

            # Soma total de cidades para verificar empate
            soma_total_de_cidades = sum(contagem_cidades.values())

            if soma_total_de_cidades == 0:
                motivo += "EMPATE! Ninguém possuía cidades (além das bases)."
            else:
                max_cidades = max(contagem_cidades.values())
                possiveis_vencedores = [
                    j_id
                    for j_id, count in contagem_cidades.items()
                    if count == max_cidades
                ]

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
        caminho_de_volta = self.mapa.encontrar_caminho(
            tropa.localizacao, tropa.dono.id_base, tropa.dono.id
        )

        if caminho_de_volta:
            # Se houver um caminho, define a nova rota de recuo
            tropa.caminho_atual = caminho_de_volta[
                1:
            ]  # Exclui a cidade atual do caminho
            tropa.estado = "recuando"
        else:
            # Se não houver caminho (tropa está isolada), ela fica encurralada e a cidade se torna neutra
            cidade_atual = self.mapa.cidades[tropa.localizacao]
            cidade_atual.dono = None
            for t in cidade_atual.tropas_estacionadas:
                if t.dono.id == tropa.dono.id:
                    tropa.dono.tropas.remove(t)
            cidade_atual.tropas_estacionadas.clear()  # Remove todas as tropas estacionadas
            
            print(
                f"ALERTA: A Tropa {tropa.id} ficou encurralada em {tropa.localizacao} e foi perdida."
            )

    def _calcular_mst_prim(self, jogador: Jogador):
        """
        Calcula a Árvore Geradora Mínima (MST) que conecta as cidades de um jogador,
        usando o Algoritmo de Prim. Retorna o custo total da manutenção e o
        conjunto de cidades que estão efetivamente conectadas à base.
        """

        # Copia todas as cidades do jogador, incluindo a base
        cidades_do_jogador = {
            c.id for c in self.mapa.cidades.values() if c.dono == jogador.id
        }
        cidades_do_jogador.add(jogador.id_base)

        if len(cidades_do_jogador) <= 1:
            return 0, cidades_do_jogador

        custo_total = 0
        cidades_conectadas = {jogador.id_base}
        fronteira = []

        push = heapq.heappush
        pop = heapq.heappop

        # Pré-carrega vizinhos e arestas iniciais pra evitar lookup desnecessário
        for vizinho_id in self.mapa.get_vizinhos(jogador.id_base):
            if vizinho_id in cidades_do_jogador:
                aresta = self.mapa.get_aresta(jogador.id_base, vizinho_id)
                if aresta:
                    push(fronteira, (aresta.peso, jogador.id_base, vizinho_id))

        while fronteira and len(cidades_conectadas) < len(cidades_do_jogador):
            peso, _, destino = pop(fronteira)

            if destino in cidades_conectadas:
                continue

            cidades_conectadas.add(destino)
            custo_total += peso

            for vizinho_id in self.mapa.get_vizinhos(destino):
                if (
                    vizinho_id in cidades_do_jogador
                    and vizinho_id not in cidades_conectadas
                ):
                    aresta = self.mapa.get_aresta(destino, vizinho_id)
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

            self.mapa.cidades[f"basej_{jogador.id}"].populacao = jogador.tropas_na_base  # Garante que a base é do jogador
            # Calcula a MST e verifica a conectividade
            cidades_sem_tropas = []

            cidades_possuidas_antes = {
                c.id for c in self.mapa.cidades.values() if c.dono == jogador.id
            }
            print(f"\njogador {jogador.id} possui as cidades: {cidades_possuidas_antes}")
            for cidade_id in cidades_possuidas_antes:
                tropas_estacionadas = self.mapa.cidades[cidade_id].tropas_estacionadas
                print(f"Cidade {cidade_id} do jogador {jogador.id} possui tropas estacionadas: {tropas_estacionadas}")
                # Se a cidade tiver tropas estacionadas, não é
                if tropas_estacionadas:
                    continue
                cidades_sem_tropas.append(cidade_id)
                for tropa in jogador.tropas:
                    if tropa.localizacao == cidade_id:
                        cidades_sem_tropas.remove(cidade_id)
                        break
            print(f"Cidades sem tropas do jogador {jogador.id}: {cidades_sem_tropas} etapa 0\n")
            if f"basej_{jogador.id}" in cidades_sem_tropas:
                cidades_sem_tropas.remove(f"basej_{jogador.id}")
            print(f"Cidades sem tropas do jogador {jogador.id}: {cidades_sem_tropas} etapa 1\n")
            for cidade_id in cidades_sem_tropas:
                self.mapa.cidades[cidade_id].dono = None  # Neutraliza a cidade
                cidades_possuidas_antes.remove(cidade_id)
            print(f"Cidades possuídas após neutralização: {cidades_possuidas_antes}\n")
            custo_total_manutencao, cidades_conectadas = self._calcular_mst_prim(
                jogador
            )

            print(
                f"Jogador {jogador.id}: Custo total de manutenção = {custo_total_manutencao} (Cidades conectadas: {cidades_conectadas})"
            )
            # Identifica e neutraliza cidades isoladas
            cidades_isoladas = cidades_possuidas_antes - cidades_conectadas
            for cidade_id in cidades_isoladas:
                cidade = self.mapa.cidades[cidade_id]
                print(
                    f"ALERTA: Cidade {cidade.id} do jogador {jogador.id} ficou isolada e se tornou neutra!"
                )
                cidade.dono = None
                # Tropas estacionadas são dadas como perdidas
                for tropa in cidade.tropas_estacionadas:
                    jogador.tropas.remove(
                        tropa
                    )  # Remove da lista geral de tropas para não contar mais
                cidade.tropas_estacionadas.clear()

            # Calcula o custo final e o debita da base
            custo_do_turno = custo_total_manutencao // 100
            print(
                f"Jogador {jogador.id}: Custo de manutenção do império = {custo_do_turno}"
            )
            jogador.tropas_na_base -= custo_do_turno

            # Verifica a condição de derrota por falência
            if jogador.tropas_na_base <= 0:
                print(
                    f"DERROTA: Jogador {jogador.id} foi à falência (tropas na base <= 0)!"
                )
                self.jogadores_derrotados.append(jogador.id)
                # Neutraliza todas as cidades do jogador derrotado
                for cidade_id in cidades_conectadas:  # Apenas as que ainda eram dele
                    self.mapa.cidades[cidade_id].dono = None
                # Remove todas as tropas do jogador
                jogador.tropas.clear()

    def _resolver_combate(self, cidade, lista_de_atacantes, eh_base=False):
        """Resolve o combate contra uma cidade ocupada por outro jogador ou uma base."""
        jogadores_atacantes = {}

        for tropa in lista_de_atacantes:
            if tropa.dono.id not in jogadores_atacantes:
                jogadores_atacantes[tropa.dono.id] = []
            jogadores_atacantes[tropa.dono.id].append(tropa)

        if not jogadores_atacantes:
            print(
                f"Nenhum atacante válido em {cidade.id}. Nenhum combate será realizado."
            )
            return

        ordenado = sorted(
            jogadores_atacantes.items(),
            key=lambda item: sum(t.forca for t in item[1]),
            reverse=True,
        )
        print(f"Jogadores atacantes ordenados por força total: {ordenado}")

        vitorioso = ordenado[0][0]  # O jogador com a maior força total
        tropas_perdidas = 0
        
        if len(ordenado) > 1:
            _, segunda_maior = ordenado[1]
            tropas_perdidas = sum(t.forca for t in segunda_maior)
            for _, tropas in ordenado[1:]:
                for tropa in tropas:
                    print(f"Tropa {tropa.id} do jogador {tropa.dono.id} foi destruída no combate!")
                    tropa.dono.tropas.remove(tropa)
                    if tropa in cidade.tropas_estacionadas:
                        cidade.tropas_estacionadas.remove(tropa)

        tropas_vitoriosas = ordenado[0][1]
        tropas_destruídas = []
        

        for t in tropas_vitoriosas:
            if t.forca - tropas_perdidas <= 0:
                print(f"Tropa {t.id} do jogador {t.dono.id} foi destruída no combate!")
                t.dono.tropas.remove(t)
                tropas_destruídas.append(t)
                if tropa in cidade.tropas_estacionadas:
                    cidade.tropas_estacionadas.remove(tropa)
            if t.forca - tropas_perdidas > 0:
                for y in t.dono.tropas:
                    if y.id == t.id:
                        y.forca -= tropas_perdidas
            tropas_perdidas -= t.forca
            if tropas_perdidas <= 0:
                break

        for tropa in tropas_destruídas:
            if tropa in tropas_vitoriosas:
                tropas_vitoriosas.remove(tropa)

        forca_restante = max(sum(t.forca for t in tropas_vitoriosas), 0)
        # A penalidade de 50% só se aplica ao atacar a base
        if eh_base:
            forca_restante *= 0.5
            print(f"Ataque à base! Força de ataque reduzida para {forca_restante}.")

        print(
            f"Combate em {cidade.id}: Ataque({forca_restante}) vs Defesa({cidade.populacao})"
        )

        if forca_restante >= cidade.populacao:  # Vitória do atacante

            # Se o ataque for contra a base inimiga, decreta a vitória DO jogador vencedor
            if eh_base:
                print(
                    f"Jogador {vitorioso} conquistou a base do jogador {cidade.dono}!"
                )
                jogador_derrotado = self.jogadores[cidade.dono]
                self.jogadores_derrotados.append(jogador_derrotado.id)
                self.jogadores.pop(cidade.dono, None)
            else:
                print(f"Vitória do jogador {vitorioso} em {cidade.id}!")

            cidade.dono = vitorioso
            for tropas in tropas_vitoriosas:
                tropas.estado = "vitoriosa"

        elif forca_restante == 0:  # Empate ou derrota do atacante
            print(f"Empate em {cidade.id}!, todos os atacantes foram destruídos.")
        else:  # Vitória do defensor
            print(f"Defensores de {cidade.id} venceram o ataque em {cidade.id}!")

            if len(tropas_vitoriosas) > 1:
                print(
                    f"Falha na conquista! A força das Tropas {tropas_vitoriosas} ({forca_restante}) é insuficiente para dominar {cidade.id}."
                )
                for tropa in tropas_vitoriosas:
                    self._iniciar_recuo_forcado(
                        tropa,
                        f"força insuficiente para conquistar a cidade {cidade.id}",
                    )
            else:
                print(
                    f"Falha na conquista! A força da Tropa {tropas_vitoriosas[0]} ({forca_restante}) é insuficiente para dominar {cidade.id}."
                )
                self._iniciar_recuo_forcado(
                    tropas_vitoriosas[0],
                    f"força insuficiente para conquistar a cidade {cidade.id}",
                )

    def _executar_fase_de_combates(self):
        """Coleta todos os ataques do turno e os resolve."""
        print("\n--- Fase de Resolução de Combates ---")
        ataques_por_cidade = {}
        
        # 0. reuni as tropas que estão reunindo na base
        for jogador in self.jogadores.values():
            for tropa in jogador.tropas:
                if tropa.estado == "reunindo":
                        jogador.tropas_na_base += tropa.forca
                        print(
                            f"Tropa {tropa.id} retornou à base e foi convertida em tropas na base (+{tropa.forca})."
                        )
                        jogador.tropas.remove(tropa)
        
        # 1. Coleta e agrupa todos os ataques
        for jogador in self.jogadores.values():
            for tropa in jogador.tropas:
                if tropa.estado == "atacando":
                    alvo_id = tropa.alvo_de_ataque
                    if alvo_id not in ataques_por_cidade:
                        ataques_por_cidade[alvo_id] = []
                    ataques_por_cidade[alvo_id].append(tropa)

        # 2. Resolve os combates cidade por cidade
        for cidade_id, lista_de_atacantes in ataques_por_cidade.items():
            cidade = self.mapa.cidades[cidade_id]

            if "base" in cidade.id:
                self._resolver_combate(cidade, lista_de_atacantes, eh_base=True)
            else:
                self._resolver_combate(cidade, lista_de_atacantes)

    def _executar_fase_pos_combate(self):
        """Processa as ações das tropas vitoriosas."""
        print("\n--- Fase de Pós-Combate ---")
        for jogador in self.jogadores.values():
            for tropa in list(jogador.tropas):
                if tropa.estado == "vitoriosa":
                    proximo_comando = (
                        tropa.fila_de_comandos[0] if tropa.fila_de_comandos else None
                    )

                    if proximo_comando and proximo_comando["tipo"] == "PERMANECER":
                        tropa.fila_de_comandos.pop(0)  # Consome o comando
                        cidade_conquistada = self.mapa.cidades[tropa.localizacao]
                        if tropa not in cidade_conquistada.tropas_estacionadas:
                            tropa.estado = "estacionada"
                            cidade_conquistada.tropas_estacionadas.append(tropa)
                            print(
                                f"Tropa {tropa.id} venceu e permaneceu em {tropa.localizacao}."
                            )
                        else:
                            print(
                                f"AVISO: Tropa {tropa.id} já está estacionada em {tropa.localizacao}."
                            )
                    else:
                        # Se não houver comando ou não for PERMANECER, a tropa recua (raid)
                        print(f"Tropa {tropa.id} venceu (raid) e iniciará o recuo.")
                        self._iniciar_recuo_forcado(tropa, "ataque 'raid' concluído")

    def _processar_movimento_tropas(self, jogador):
        """Processa os movimentos e comandos de todas as tropas de um jogador."""

        for tropa in list(jogador.tropas):

            # Lógica para tropas ociosas que têm novos comandos para executar
            if tropa.estado == "ociosa" and tropa.fila_de_comandos:
                if tropa.estado == "estacionada":
                    cidade_atual = self.mapa.cidades[tropa.localizacao]
                    if tropa in cidade_atual.tropas_estacionadas:
                        cidade_atual.tropas_estacionadas.remove(tropa)

                comando_atual = tropa.fila_de_comandos.pop(0)

                if comando_atual["tipo"] == "MOVER":
                    destino_final = comando_atual["alvo"]
                    print(
                        f"Tropa {tropa.id} iniciando movimento de {tropa.localizacao} para {destino_final}"
                    )
                    caminho = self.mapa.encontrar_caminho(
                        tropa.localizacao, destino_final
                    )
                    if caminho and len(caminho) > 1:
                        tropa.caminho_atual = caminho[1:]
                        tropa.estado = "movendo"
                    else:
                        tropa.fila_de_comandos.insert(0, comando_atual)
                        print(
                            f"AVISO: Tropa {tropa.id} não pôde iniciar movimento para {destino_final}."
                        )

                elif comando_atual["tipo"] == "ATACAR":
                    alvo_id = comando_atual["alvo"]
                    if alvo_id in self.mapa.get_vizinhos(tropa.localizacao):
                        tropa.estado = "atacando"
                        tropa.alvo_de_ataque = alvo_id
                        print(f"Tropa {tropa.id} está agora atacando {alvo_id}.")
                    else:
                        print(
                            f"ERRO: Tropa {tropa.id} tentou atacar {alvo_id} de {tropa.localizacao}, mas não é vizinho."
                        )

                elif comando_atual["tipo"] == "PERMANECER":
                    cidade_atual = self.mapa.cidades[tropa.localizacao]
                    if tropa not in cidade_atual.tropas_estacionadas:
                        tropa.estado = "estacionada"
                        cidade_atual.tropas_estacionadas.append(tropa)
                        print(
                            f"Tropa {tropa.id} agora está estacionada em {tropa.localizacao}."
                        )
                    else:
                        print(
                            f"AVISO: Tropa {tropa.id} já está estacionada em {tropa.localizacao}."
                        )

                elif comando_atual["tipo"] == "RECUAR":
                    print(
                        f"Tropa {tropa.id} iniciando recuo voluntário de {tropa.localizacao}."
                    )
                    self._iniciar_recuo_forcado(tropa, "ordem de recuo do jogador")

            elif tropa.estado == "estacionada" and tropa.fila_de_comandos:

                comando_atual = tropa.fila_de_comandos.pop(0)

                if comando_atual["tipo"] in ["MOVER", "ATACAR", "PERMANECER"]:
                    print(
                        f"AVISO: Tropa {tropa.id} está estacionada e não pode executar o comando {comando_atual['tipo']}."
                    )
                    tropa.fila_de_comandos = []  # Recoloca o comando na fila

                elif comando_atual["tipo"] == "RECUAR":
                    cidade_atual = self.mapa.cidades[tropa.localizacao]
                    if tropa in cidade_atual.tropas_estacionadas:
                        cidade_atual.tropas_estacionadas.remove(tropa)
                    print(
                        f"Tropa {tropa.id} iniciando recuo voluntário de {tropa.localizacao}."
                    )
                    self._iniciar_recuo_forcado(tropa, "ordem de recuo do jogador")

        tropas_por_destino = {}

        for tropa in list(jogador.tropas):  # Lista de todas as tropas do jogador
            aresta_destino = None
            
            if tropa.estado == "atacando":
                aresta_destino = self.mapa.get_aresta(
                    tropa.alvo_de_ataque, tropa.localizacao
                )  # Próximo passo planejado
            if tropa.caminho_atual and tropa.estado == "movendo":
                aresta_destino = self.mapa.get_aresta(
                    tropa.caminho_atual[0], tropa.localizacao
                )  # Próximo passo planejado
            
            if aresta_destino is not None:
                if aresta_destino not in tropas_por_destino:
                    tropas_por_destino[aresta_destino] = []
                tropas_por_destino[aresta_destino].append(tropa)

        for tropa in list(jogador.tropas):
            # Lógica de movimento para tropas que já estão em um caminho
            if tropa.estado in ["atacando"]:
                aresta = self.mapa.get_aresta(tropa.alvo_de_ataque, tropa.localizacao)
                tropas_no_mesmo_destino = tropas_por_destino[aresta]
                peso_total = sum(t.forca for t in tropas_no_mesmo_destino)
                if peso_total > aresta.peso:
                    self._iniciar_recuo_forcado(
                        tropa, f"muitas tropas indo de {tropa.localizacao} para {tropa.alvo_de_ataque}"
                    )
                else:
                    tropa.localizacao = tropa.alvo_de_ataque
            if tropa.estado in ["movendo", "recuando"]:
                if tropa.caminho_atual:
                    proximo_passo = tropa.caminho_atual.pop(0)

                    aresta = self.mapa.get_aresta(tropa.localizacao, proximo_passo)
                    cidade_destino = self.mapa.cidades[proximo_passo]

                    # Validações de movimento...
                    if (
                        tropa.estado == "movendo"
                        and cidade_destino.dono != jogador.id
                        and cidade_destino.id != jogador.id_base
                    ):
                        self._iniciar_recuo_forcado(
                            tropa, f"encontrou cidade inimiga/neutra em {proximo_passo}"
                        )
                        continue

                    if tropa.estado == "movendo" and not tropa.localizacao == proximo_passo:

                        tropas_no_mesmo_destino = tropas_por_destino[
                            self.mapa.get_aresta(tropa.localizacao, proximo_passo)
                        ]
                        peso_total = sum(t.forca for t in tropas_no_mesmo_destino)

                        if peso_total > aresta.peso:
                            self._iniciar_recuo_forcado(
                                tropa,
                                f"muitas tropas indo de {tropa.localizacao} para {proximo_passo}",
                            )
                            continue

                    tropa.localizacao = proximo_passo
                    print(
                        f"Tropa {tropa.id} ({tropa.estado}) moveu-se para {tropa.localizacao}"
                    )

                if not tropa.caminho_atual:
                    # Verifica se a tropa recuou para a base
                    if (
                        tropa.estado == "recuando"
                        and tropa.localizacao == jogador.id_base
                    ):
                        tropa.estado = "reunindo"
                    else:
                        tropa.estado = "ociosa"
                        print(f"Tropa {tropa.id} chegou ao seu destino.")
                        cidade_atual = self.mapa.cidades[tropa.localizacao]
                        if not tropa.fila_de_comandos:
                            if tropa not in cidade_atual.tropas_estacionadas:
                                tropa.estado = "estacionada"
                                cidade_atual.tropas_estacionadas.append(tropa)
                                print(
                                    f"Tropa {tropa.id} agora está estacionada em {tropa.localizacao}."
                                )
                            else:
                                print(
                                    f"AVISO: Tropa {tropa.id} já está estacionada em {tropa.localizacao}."
                                )

    def _processar_movimento_transporte(self, jogador):
        """Processa o movimento e os comandos do transporte de um jogador."""
        transporte = jogador.transporte

        if transporte.estado == "destruido":
            transporte.timer_respawn -= 1
            if transporte.timer_respawn <= 0:
                transporte.estado = "ocioso"
                transporte.localizacao = jogador.id_base
                print(f"Transporte do jogador {jogador.id} foi reconstruído na base.")
            return  # Pula o resto da lógica para este transporte

        if transporte.estado == "ocioso" and transporte.fila_de_comandos:
            if len(transporte.fila_de_comandos) >= 2:
                comando_coleta = transporte.fila_de_comandos[0]
                comando_entrega = transporte.fila_de_comandos[1]

                origem_coleta = comando_coleta["alvo"]
                destino_final = comando_entrega["alvo"]

                print(
                    f"Transporte de {jogador.id} iniciando missão: coletar em {origem_coleta} e levar para {destino_final}."
                )

                caminho = self.mapa.encontrar_caminho(
                    transporte.localizacao, origem_coleta, jogador_id=jogador.id
                )
                if caminho and len(caminho) > 1:
                    transporte.caminho_atual = caminho[1:]
                    transporte.estado = "indo_coletar"
                else:
                    print(
                        f"AVISO: Transporte não encontrou caminho para a coleta em {origem_coleta}."
                    )
                    transporte.fila_de_comandos.clear()

        if transporte.estado in ["indo_coletar", "transportando", "retornando"]:
            print(
                f"Processando transporte de {jogador.id} ({transporte.estado}) no caminho {transporte.caminho_atual}."
            )
            if transporte.caminho_atual:
                proximo_passo = transporte.caminho_atual.pop(0)

                cidade_destino = self.mapa.cidades[proximo_passo]
                if cidade_destino.dono != jogador.id:
                    if cidade_destino.dono is None:  # Neutra
                        perda = transporte.carga_populacao // 10
                        cidade_destino.populacao += perda
                        transporte.carga_populacao -= perda
                        print(
                            f"Transporte de {jogador.id} encontrou cidade neutra! Perdeu {perda} de população."
                        )
                        self._iniciar_retorno_transporte(
                            transporte, "encontrou cidade neutra"
                        )
                    else:  # Inimiga
                        cidade_destino.populacao += transporte.carga_populacao
                        transporte.carga_populacao = 0
                        transporte.estado = "destruido"
                        transporte.timer_respawn = 2
                        print(
                            f"Transporte de {jogador.id} DESTRUÍDO por cidade inimiga! Carga perdida."
                        )
                    return  # Interrompe o movimento

                transporte.localizacao = proximo_passo
                print(
                    f"Transporte de {jogador.id} ({transporte.estado}) moveu-se para {transporte.localizacao}"
                )

            if not transporte.caminho_atual:
                if transporte.estado == "indo_coletar":
                    cidade_origem = self.mapa.cidades[transporte.localizacao]

                    # Lógica para lidar com "MAX"
                    quantidade_a_coletar = 0
                    if transporte.quantidade_solicitada == "MAX":
                        quantidade_a_coletar = cidade_origem.populacao
                    else:
                        quantidade_a_coletar = transporte.quantidade_solicitada

                    quantidade_coletada = min(
                        cidade_origem.populacao, quantidade_a_coletar
                    )
                    transporte.carga_populacao += quantidade_coletada
                    cidade_origem.populacao -= quantidade_coletada
                    print(
                        f"Transporte coletou {quantidade_coletada} de população em {cidade_origem.id}."
                    )

                    # Se a coleta foi bem-sucedida, consome o comando de COLETAR
                    transporte.fila_de_comandos.pop(0)  # Consome o comando de COLETAR

                    if transporte.fila_de_comandos:  # Verifica se há um próximo comando
                        comando_entrega = transporte.fila_de_comandos[0]
                        # Pega o destino do comando de ENTREGAR (que agora é o primeiro)
                        destino_final = comando_entrega["alvo"]

                        caminho = self.mapa.encontrar_caminho(
                            transporte.localizacao, destino_final, jogador_id=jogador.id
                        )
                        if caminho and len(caminho) > 1:
                            transporte.caminho_atual = caminho[1:]
                            transporte.estado = "transportando"
                        else:
                            self._iniciar_retorno_transporte(
                                transporte, "não encontrou caminho para o destino"
                            )
                    else:
                        self._iniciar_retorno_transporte(
                            transporte, "missão de coleta concluída"
                        )

                elif transporte.estado == "transportando":
                    cidade_destino = self.mapa.cidades[transporte.localizacao]
                    print(
                        f"Transporte entregou {transporte.carga_populacao} de população em {cidade_destino.id}."
                    )

                    if "base" in cidade_destino.id:
                        jogador.tropas_na_base += transporte.carga_populacao
                        print(
                            f"Jogador {jogador.id} converteu população em tropas! Total na base: {jogador.tropas_na_base:.0f}"
                        )
                    else:
                        cidade_destino.populacao += transporte.carga_populacao

                    transporte.carga_populacao = 0
                    transporte.fila_de_comandos.pop(0)  # Consome o comando de ENTREGAR
                    transporte.estado = "ocioso"

                elif transporte.estado == "retornando":
                    transporte.estado = "ocioso"
                    print(f"Transporte de {jogador.id} retornou à base.")

    def _iniciar_retorno_transporte(self, transporte, motivo):
        """Função auxiliar para forçar o retorno do transporte à base."""
        print(
            f"Transporte de {transporte.dono.id} iniciando retorno à base. Motivo: {motivo}"
        )
        transporte.fila_de_comandos.clear()
        caminho_de_volta = self.mapa.encontrar_caminho(
            transporte.localizacao, transporte.dono.id_base
        )
        if caminho_de_volta and len(caminho_de_volta) > 1:
            transporte.caminho_atual = caminho_de_volta[1:]
            transporte.estado = "retornando"
        else:
            transporte.estado = (
                "ocioso"  # Se já estiver na base ou não houver caminho disponível
            )

    def _verificar_e_processar_fim_de_jogo(self):
        """
        Verifica se as condições de fim de jogo foram atingidas.
        Se sim, determina o vencedor ou o empate e retorna True.
        Se não, retorna False.
        """
        jogadores_ativos = [
            j for j in self.jogadores.values() if j.id not in self.jogadores_derrotados
        ]
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
                    possiveis_vencedores = [
                        j_id
                        for j_id, count in contagem_cidades.items()
                        if count == max_cidades
                    ]

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
            return True  # Sinaliza para o loop principal que o jogo acabou

        return False  # O jogo continua

    def processar_turno(self):
        print(f"\n--- Processando Turno {self.turno_atual} ---")

        self.gerar_estado_json(f"estado_turno_{self.turno_atual}_ac.json")
        
        # Etapa 1: Processamento de comandos de tropas e transportes
        for jogador in self.jogadores.values():
            if jogador.id in self.jogadores_derrotados:
                continue

            # Processa comandos de tropas
            self._processar_movimento_tropas(jogador)

            # Processa comandos de transporte
            self._processar_movimento_transporte(jogador)

        self.gerar_estado_json(f"estado_turno_{self.turno_atual}_mc.json")
        
        # Etapa 2: Resolução de combates
        if not self.jogadores_derrotados:  # Só executa se ainda houver jogadores ativos
            self._executar_fase_de_combates()

        # Etapa 3: Atualizações pós-combate
        if not self.jogadores_derrotados:  # Só executa se ainda houver jogadores ativos
            self._executar_fase_pos_combate()

        # Etapa 4: Cálculo de custos e suprimentos
        self._executar_fase_de_custo_e_suprimento()

        # Etapa 5: Verifica se o jogo terminou
        if self._verificar_e_processar_fim_de_jogo():
            return

        # Se ainda houver jogadores ativos, incrementa o turno e salva o estado atual
        self.gerar_estado_json(f"estado_turno_{self.turno_atual}_dc.json")
        self.turno_atual += 1
