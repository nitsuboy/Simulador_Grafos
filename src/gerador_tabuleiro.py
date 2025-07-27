from collections import defaultdict
import random
import sys
import math

def rotate(origin, point, angle):
    ox, oy = origin
    px, py = point

    qx = ox + math.cos(angle) * (px - ox) - math.sin(angle) * (py - oy)
    qy = oy + math.sin(angle) * (px - ox) + math.cos(angle) * (py - oy)
    return [qx, qy]

def arestas_para_lista_adjacencia_nao_direcionado(arestas):
    grafo = defaultdict(list)
    for a, b, p in arestas:
        grafo[a].append((b, p))
        grafo[b].append((a, p))
    return dict(grafo)


def gerar_grafo(camadas=None, seed=None, jogadores=2, ilha_central=False,max_meio=2):

    # Tratamento de argumentos
    # Geramento de seed ja que o random n disponibiliza a seed utilizada
    if not seed:
        seed = random.randrange(sys.maxsize)
    random.seed(seed)
    print(seed)

    if not camadas:
        camadas = []
        for i in range(random.randrange(2, 4)):
            camadas.append(random.randrange(2, 5))

    # Tamanho maximo de onde irão se encontrar os nos, detalhe de vizualização
    largura, altura = 800, 800
    raio = 25
    max_y = 250

    # Conjunto contendo todos os nós
    cidades = {}

    # Inicializa as bases dos jogadores
    for j in range(jogadores):
        cidades[f"base_j{j}"] = {
            "pos": rotate((largura // 2, altura // 2), (raio, altura // 2), (6.283185/jogadores)*j),
            "pop": 100
        }

    nome_contador = 1
    # regiões espelhadas
    regiao_jogadores = []
    # Conjunto de nós para que serão espelhados
    cidades_base = {}
    camadas_base = []
    # Processo de fazer as camadas nas quais o espelhamento vai se basear
    tropas_disponiveis = 100  # Tropas iniciais na base
    
    for i in range(len(camadas)):
        camada = []
        n_cidades = camadas[i]

        x = raio + (i + 1) * ((largura // 2) // (len(camadas) + 1))
        y_step = (altura - 2 * max_y) // (n_cidades + 1)
        

        # Definir população total da camada (progressiva)
        soma_pop = (tropas_disponiveis * (n_cidades )) + i * 120  # ajustável

        # Definir população mínima de uma cidade que pode ser conquistada com as tropas atuais
        conquista_minima = int(tropas_disponiveis * random.uniform(0.7,0.9))

        # Distribuir população: 1 cidade com população <= conquista_minima, restante distribui o resto
        restante = soma_pop - conquista_minima
        restantes_cidades = n_cidades - 1
        
        if restantes_cidades <= 0:
            pops = [conquista_minima]
        else:
            base = restante // restantes_cidades
            sobra = restante % restantes_cidades
            pops = [base] * restantes_cidades
            for i in range(sobra):
                pops[i % restantes_cidades] += 1
            pops.append(conquista_minima)  # garante cidade acessível

        # Adiciona leve variação para não parecer artificial
        pops = [max(10, int(p * random.uniform(0.9, 1.1))) for p in pops]

        tropas_disponiveis = sum(pops)
        for j in range(n_cidades):
            nome = f"c{nome_contador}"
            y = max_y + (j + 1) * y_step
            cidades_base[nome] = {
                "pos": [x, y],
                "pop": pops[j]
            }
            camada.append(nome)
            nome_contador += 1

        camadas_base.append(camada)

    # Processo de espelhamento da camada base em as demais para ter uma simetria
    for j in range(jogadores):
        camadas_jogador = []
        for c in camadas_base:
            camada = []
            for nome in c:
                pos_x, pos_y = cidades_base[nome]["pos"]
                nome_espelhado = f"{nome}_{j}"
                cidades[nome_espelhado] = {
                    "pos": rotate((largura // 2, altura // 2), (pos_x, pos_y), (6.283185/jogadores)*j),
                    "pop": cidades_base[nome]["pop"]
                }
                camada.append(nome_espelhado)
            camadas_jogador.append(camada)
        regiao_jogadores.append(camadas_jogador)

    # Geração das arestas
    arestas = []
    arestas_set = set()

    def add_aresta(a, b, p):
        key = (a, b)
        if key not in arestas_set:
            arestas.append((a, b, p))
            arestas_set.add(key)

    for j in range(jogadores):
        for nome in regiao_jogadores[j][0]:
            add_aresta(f'base_j{j}', nome, random.randint(1, 5))

    for j in range(jogadores):
        regioes = regiao_jogadores[j]
        for i in range(len(regioes) - 1):
            atual = regioes[i]
            prox = regioes[i + 1]
            for a in atual:
                p = random.randrange(10,20)
                b = random.choice(prox)
                add_aresta(a, b, p)
            for b in prox:
                p = random.randrange(10,20)
                a = random.choice(atual)
                add_aresta(a, b, p)

    # meio (ligação entre últimas camadas esquerda e direita)
    for j in range(jogadores):
        camada_j = regiao_jogadores[j][-1]
        for jo in range(j + 1, jogadores):
            camada_jo = regiao_jogadores[jo][-1]
            # Adaptar conectar_camadas_limite_total para usar add_aresta
            ja_conectados = set()
            # Garante pelo menos uma conexão
            a = random.choice(camada_j)
            b = random.choice(camada_jo)
            p = random.randrange(10,20)
            add_aresta(a, b, p)
            ja_conectados.add((a, b))
            total = 1
            while total < max_meio:
                p = random.randrange(10,20)
                a = random.choice(camada_j)
                b = random.choice(camada_jo)
                if (a, b) not in ja_conectados:
                    add_aresta(a, b, p)
                    ja_conectados.add((a, b))
                    total += 1

    return cidades, arestas, arestas_para_lista_adjacencia_nao_direcionado(arestas)
