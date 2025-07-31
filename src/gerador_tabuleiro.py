from collections import defaultdict
import random
import sys
import math
import json
import os

RAIO = 25
MAX_Y = 250

def rotate(origin, point, angle):
    """
    Rotaciona um ponto em torno de um ponto de origem.
    """
    ox, oy = origin
    px, py = point

    qx = ox + math.cos(angle) * (px - ox) - math.sin(angle) * (py - oy)
    qy = oy + math.sin(angle) * (px - ox) + math.cos(angle) * (py - oy)
    return [qx, qy]

class Grafo:
    
    def __init__(self):
        self.nos = {}
        self.arestas = []
        self.variaveis = {}
        self.conjunto_arestas = set()
        
            # Adiciona as arestas evitando repetições
    def adicionar_aresta(
        self,
        no_a:str, 
        no_b:str, 
        peso:int):
        """
        Adiciona uma aresta entre dois nós com um peso.
        """
        chave_aresta = tuple(sorted([no_a, no_b]))
        if chave_aresta not in self.conjunto_arestas:
            self.arestas.append((no_a, no_b, peso))
            self.conjunto_arestas.add(chave_aresta)

    def arestas_para_lista_adjacencia_nao_direcionado(self):
        """
        Converte as arestas do grafo para uma lista de adjacência não direcionada.
        """
        lista_adjacencia = defaultdict(list)
        for a, b, p in self.arestas:
            lista_adjacencia[a].append((b, p))
            lista_adjacencia[b].append((a, p))
        return dict(lista_adjacencia)

    def grafo_e_conexo(self):
        """
        Checa se o grafo é conexo usando BFS.
        lista_adjacencia: dict {cidade_id: [(vizinho_id, peso), ...]}
        Retorna True se conexo, False caso contrário.
        """
        
        lista_adjacencia = self.arestas_para_lista_adjacencia_nao_direcionado()
        
        if not lista_adjacencia:
            return True

        visitados = set()
        cidades = list(lista_adjacencia.keys())
        fila = [cidades[0]]

        while fila:
            atual = fila.pop(0)
            if atual not in visitados:
                visitados.add(atual)
                vizinhos = [v for v, _ in lista_adjacencia[atual]]
                for vizinho in vizinhos:
                    if vizinho not in visitados:
                        fila.append(vizinho)

        return len(visitados) == len(lista_adjacencia)

    def gerar_grafo(
        self,
        camadas: list[int] = None,
        seed: int = None,
        num_jogadores: int = 2,
        largura: int = 800,
        altura: int = 800,
    ):
        """
        Gera um grafo com base nos parâmetros fornecidos.
        """
        
        self.nos.clear()
        self.variaveis.clear()
        # Tratamento de argumentos
        if seed is None:
            seed = random.randrange(sys.maxsize)
        random.seed(seed)

        self.variaveis = {
            "seed": seed,
            "num_jogadores": num_jogadores,
            "camadas": camadas
        }
        
        if not camadas:
            camadas = []
            for _ in range(random.randrange(2, 4)):
                camadas.append(random.randrange(2, 5))

        # Conjunto contendo todos os nós
        contador_nomes = 1
        regioes_jogadores = []
        cidades_base = {}
        camadas_base = []
        tropas_disponiveis = 100  # Tropas iniciais na base

        

        """
        Geração de nós.
        """

        # Inicializa as bases dos jogadores
        for jogador in range(num_jogadores):
            self.nos[f"basej_{jogador}"] = {
                "pos": rotate((largura // 2, altura // 2), (RAIO, altura // 2), ((math.pi*2) / num_jogadores) * jogador),
                "pop": 100,
                "owner": jogador
            }

        # Balanceia as camadas para que a soma das populações seja igual e tenha ao menos uma conquistavel
        for camada_idx in range(len(camadas)):
            camada_atual = []
            num_cidades = camadas[camada_idx]

            x_pos = RAIO + (camada_idx + 1) * ((largura // 2) // (len(camadas) + 1))
            y_step = (altura - 2 * MAX_Y) // (num_cidades + 1)

            soma_populacao = (tropas_disponiveis * num_cidades) + camada_idx * 120
            conquista_minima = int(tropas_disponiveis * random.uniform(0.7, 0.9))

            restante_populacao = soma_populacao - conquista_minima
            cidades_restantes = num_cidades - 1

            if cidades_restantes <= 0:
                populacoes = [conquista_minima]
            else:
                base_populacao = restante_populacao // cidades_restantes
                sobra_populacao = restante_populacao % cidades_restantes
                populacoes = [base_populacao] * cidades_restantes
                for i in range(sobra_populacao):
                    populacoes[i % cidades_restantes] += 1
                populacoes.append(conquista_minima)

            populacoes = [round(pop * random.uniform(0.9, 1.1)) for pop in populacoes]

            tropas_disponiveis = sum(populacoes)
            
            for cidade_idx in range(num_cidades):
                nome_cidade = f"c{contador_nomes}"
                y_pos = MAX_Y + (cidade_idx + 1) * y_step
                cidades_base[nome_cidade] = {
                    "pos": [x_pos, y_pos],
                    "pop": populacoes[cidade_idx],
                    "owner": None
                }
                camada_atual.append(nome_cidade)
                contador_nomes += 1

            camadas_base.append(camada_atual)

        # Processo de espelhamento da camada base para criar simetria
        for jogador in range(num_jogadores):
            camadas_jogador = []
            for camada_base in camadas_base:
                camada_espelhada = []
                for nome_cidade in camada_base:
                    pos_x, pos_y = cidades_base[nome_cidade]["pos"]
                    nome_espelhado = f"{nome_cidade}_{jogador}"
                    self.nos[nome_espelhado] = {
                        "pos": rotate((largura // 2, altura // 2), (pos_x, pos_y), ((math.pi*2) / num_jogadores) * jogador),
                        "pop": cidades_base[nome_cidade]["pop"]
                    }
                    camada_espelhada.append(nome_espelhado)
                camadas_jogador.append(camada_espelhada)
            camadas_jogador.insert(0, [f"basej_{jogador}"])
            regioes_jogadores.append(camadas_jogador)

        """
        Geração de arestas entre as camadas.
        """
        
        # Conexão de camadas aleatoriamente
        """
        # Conectando a primeira camada com a base
        for jogador in range(num_jogadores):
            for camada_idx in range(1, len(regioes_jogadores[jogador])):
                camada_atual = regioes_jogadores[jogador][camada_idx]
                camada_anterior = regioes_jogadores[jogador][camada_idx - 1]
                ja_escolhidas = set()
                
                for cidade_idx, nome_cidade in enumerate(camada_atual):
                    conexoes = []
                    conexoes.extend(camada_anterior)
                    if cidade_idx + 1 < len(camada_atual) and camada_atual[cidade_idx + 1] not in ja_escolhidas:
                        conexoes.append(camada_atual[cidade_idx + 1])
                    if cidade_idx - 1 < 0 and camada_atual[cidade_idx - 1] not in ja_escolhidas:
                        conexoes.append(camada_atual[cidade_idx - 1])
                    
                    num_conexoes = random.randint(1, min(4,len(conexoes)))
                    conexoes_escolhidas = [camada_anterior[random.randint(0, len(camada_anterior) - 1)]]
                    conexoes_escolhidas.extend(random.sample(conexoes, num_conexoes-1))
                    peso_total = grafo_cidades[nome_cidade]["pop"]
                    peso_medio = peso_total // num_conexoes
                    pesos = []
                    
                    for i in range(num_conexoes):
                        if i == num_conexoes - 1:
                            # Ajustar o último peso para compensar
                            peso = peso_total - sum(pesos)
                        else:
                            peso = random.randint(peso_medio//75, peso_medio + peso_medio//25)
                        pesos.append(peso)
                    
                    for conexao, peso in zip(conexoes_escolhidas, pesos):
                        ja_escolhidas.add(tuple(sorted([nome_cidade, conexao])))
                        adicionar_aresta(nome_cidade, conexao, peso)
        
        """
        
        while True:
    
            self.arestas.clear()
            self.conjunto_arestas.clear()
            
            for camada_idx in range(1, len(regioes_jogadores[0])):
                    camada_atual = regioes_jogadores[0][camada_idx]
                    camada_anterior = regioes_jogadores[0][camada_idx - 1]
                    ja_escolhidas = set()
                    
                    for cidade_idx, nome_cidade in enumerate(camada_atual):
                        conexoes = []
                        conexoes.extend(camada_anterior)
                        
                        if cidade_idx + 1 < len(camada_atual):
                            par = tuple(sorted([nome_cidade, camada_atual[cidade_idx + 1]]))
                            if par not in ja_escolhidas:
                                conexoes.append(camada_atual[cidade_idx + 1])
                        if cidade_idx - 1 >= 0:
                            par = tuple(sorted([nome_cidade, camada_atual[cidade_idx - 1]]))
                            if par not in ja_escolhidas:
                                conexoes.append(camada_atual[cidade_idx - 1])
                        
                        num_conexoes = random.randint(1, min(4,len(conexoes)))
                        conexoes_escolhidas = [camada_anterior[random.randint(0, len(camada_anterior) - 1)]]
                        conexoes.remove(conexoes_escolhidas[0])  # Remove a conexão já escolhida
                        conexoes_escolhidas.extend(random.sample(conexoes, num_conexoes-1))
                        peso_total = self.nos[nome_cidade]["pop"]
                        peso_medio = peso_total // num_conexoes
                        pesos = []
                        
                        for i in range(len(conexoes_escolhidas)):
                            peso = 0
                            
                            if i == num_conexoes - 1:
                                peso = peso_total - sum(pesos)
                            else:
                                peso = random.randint(peso_medio//90, peso_medio + (peso_medio//10))
                            pesos.append(peso)
                        
                        for conexao, peso in zip(conexoes_escolhidas, pesos):
                            peso = max(0, peso)  # Garante que o peso não seja negativo
                            par = tuple(sorted([nome_cidade, conexao]))
                            if par not in ja_escolhidas and peso > 0:
                                ja_escolhidas.add(par)
                                self.adicionar_aresta(nome_cidade, conexao, peso)

            for aresta in self.arestas.copy():
                a, b, p = aresta
                for i in range(1,num_jogadores):
                    a_aux = a.split("_")[0] + f"_{i}"
                    b_aux = b.split("_")[0] + f"_{i}"
                    self.adicionar_aresta(a_aux, b_aux, p)

            # Liga as últimas camadas (meios) entre os jogadores
            ultima_camadas = [regioes_jogadores[j][-1] for j in range(num_jogadores)]

            # Precompute populations for all cities
            populacoes_cidades = {cidade: dados["pop"] for cidade, dados in self.nos.items()}

            for i in range(num_jogadores):
                for j in range(i + 1, num_jogadores):
                    camada_i = ultima_camadas[i]
                    camada_j = ultima_camadas[j]

                    # Define quantas conexões criar entre essas duas camadas
                    num_ligacoes = min(2, len(camada_i), len(camada_j))  # exemplo: 2 conexões por par

                    # Escolhe pares de cidades para conectar
                    pares = random.sample(
                        [(c1, c2) for c1 in camada_i for c2 in camada_j],
                        num_ligacoes
                    )

                    for c1, c2 in pares:
                        # Peso baseado nas populações médias das cidades conectadas
                        peso = max(populacoes_cidades[c1], populacoes_cidades[c2])
                        self.adicionar_aresta(c1, c2, peso)
            # Verifica se o grafo é conexo
            if self.grafo_e_conexo():
                break
            
        return self.nos, self.arestas




def exportar_mapa_para_json(grafo, nome_arquivo):
    """
    Extrai as estruturas de dados do gerador de tabuleiro (com pesos nas arestas)
    e as converte para o formato JSON, incluindo a lista de adjacência.
    """
    cidades_geradas = grafo.nos
    arestas_geradas = grafo.arestas
    lista_adjacencia = grafo.arestas_para_lista_adjacencia_nao_direcionado()
    mapa_para_json = {
        "configs": grafo.variaveis,
        "cidades": [],
        "arestas": [],
        "lista_adjacencia": []
    }
    for cidade_id, info in cidades_geradas.items():
        nova_cidade = {"id": cidade_id, "populacao": info["pop"]}
        mapa_para_json["cidades"].append(nova_cidade)
    for origem_id, destino_id, peso in arestas_geradas:
        nova_aresta = {"de": origem_id, "para": destino_id, "peso": peso}
        mapa_para_json["arestas"].append(nova_aresta)
    for cidade, vizinhos in lista_adjacencia.items():
        mapa_para_json["lista_adjacencia"].append({
            "cidade": cidade,
            "vizinhos": [{"id": v[0], "peso": v[1]} for v in vizinhos]
        })
        
    if os.path.exists(nome_arquivo):
        resposta = input(f"O arquivo '{nome_arquivo}' já existe. Deseja sobrescrever? (s/n): ").strip().lower()
        if resposta != 's':
            print("Exportação cancelada.")
            return
        
    with open(nome_arquivo, 'w', encoding='utf-8') as f:
        json.dump(mapa_para_json, f, indent=2, ensure_ascii=False)
    print(f"Mapa exportado com sucesso para {nome_arquivo}")

if __name__ == "__main__":
    # Gera o mapa
    if len(sys.argv) > 1:
        seed_para_teste = int(sys.argv[1])
    else:
        seed_para_teste = 12345
    
    grafo = Grafo()
    nos, arestas = grafo.gerar_grafo(seed=seed_para_teste, num_jogadores=2)
    print("Mapa gerado com sucesso.")
    print("variaveis:", grafo.variaveis)

    # Exporta o mapa gerado para um arquivo JSON
    exportar_mapa_para_json(grafo, "src\\mapa_debug.json")
