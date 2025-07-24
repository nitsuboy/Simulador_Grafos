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

def adicionar_arestas_bidirecional(grafo, a, b, peso):
    grafo.setdefault(a, []).append((b, peso))
    grafo.setdefault(b, []).append((a, peso))

def conectar_camadas_limite_total(camada1, camada2, arestas, max_total=3):
    ja_conectados = set()

    # Garante pelo menos uma conexão
    a = random.choice(camada1)
    b = random.choice(camada2)
    arestas.append((a, b))
    ja_conectados.add((a, b))

    total = 1

    # Conexões extras até o limite total
    while total < max_total:
        a = random.choice(camada1)
        b = random.choice(camada2)
        if (a, b) not in ja_conectados:
            arestas.append((a, b))
            ja_conectados.add((a, b))
            total += 1

def arestas_para_lista_adjacencia_nao_direcionado(arestas):
    grafo = defaultdict(list)
    for a, b in arestas:
        grafo[a].append(b)
        grafo[b].append(a)
    return dict(grafo)

def gerar_grafo(camadas=None,seed=None,jogadores=3):
    
    #tratamento de argumentos
    if not seed:
        seed = random.randrange(sys.maxsize)
    random.seed(seed)
    print(seed)
    
    if not camadas:
        camadas = random.randint(2, 3)
    
    largura, altura = 800, 800
    raio = 25
    max_y = 250

    cidades_base = {}
    cidades = {}
    for j in range(jogadores):
        cidades[f"base_j{j}"] = {
            "pos": rotate((largura // 2,altura // 2),(raio, altura // 2),(6.283185/jogadores)*j)
            , "pop": 100}

    nome_contador = 1
    camadas_base = []
    regiao_jogadores = []

    # Geração das camadas base (entre base_j1 e meio)
    for i in range(camadas):
        camada = []
        n_cidades = random.randint(2, 4)
        
        x = raio + (i + 1) * ((largura // 2) // (camadas + 1))
        y_step = (altura - 2 * max_y) // (n_cidades + 1)
        
        for j in range(n_cidades):
            nome = f"c{nome_contador}"
            y = max_y + (j + 1) * y_step
            cidades_base[nome] = {
                "pos": [x, y],
                "pop": random.randint(30, 80)
            }
            camada.append(nome)
            nome_contador += 1
            
        camadas_base.append(camada)

    # Espelhamento da camada base em as demais para ter uma simetria
    for j in range(jogadores):
        camadas_jogador = []
        for c in camadas_base:
            camada = []
            for nome in c:
                pos_x, pos_y = cidades_base[nome]["pos"]
                nome_espelhado = f"{nome}_{j}"
                cidades[nome_espelhado] = {
                    "pos": rotate((largura // 2,altura // 2),(pos_x, pos_y),(6.283185/jogadores)*j),
                    "pop": cidades_base[nome]["pop"] 
                }
                camada.append(nome_espelhado)
            camadas_jogador.append(camada)
        regiao_jogadores.append(camadas_jogador)
    # Geração das arestas
    arestas = []
    list_adj={}
    # base_j1 -> primeira camada
    for j in range(jogadores):
        arestas += [(f'base_j{j}', nome) for nome in regiao_jogadores[j][0]]
    '''
    # entre camadas da esquerda
    for i in range(len(camadas_esquerda) - 1):
        atual = camadas_esquerda[i]
        prox = camadas_esquerda[i + 1]
        for a in atual:
            b = random.choice(prox)
            arestas.append((a, b))
        for b in prox:
            a = random.choice(atual)
            arestas.append((a, b))

    # entre camadas da direita (sentido inverso)
    for i in range(len(camadas_direita) - 1):
        atual = camadas_direita[i]
        prox = camadas_direita[i + 1]
        for a in atual:
            b = random.choice(prox)
            arestas.append((a, b))
        for b in prox:
            a = random.choice(atual)
            arestas.append((a, b))
    '''
    for j in range(jogadores):
        regioes = regiao_jogadores[j]
        for i in range(len(regioes) - 1):
            atual = regioes[i]
            prox = regioes[i + 1]
            for a in atual:
                b = random.choice(prox)
                arestas.append((a, b))
            for b in prox:
                a = random.choice(atual)
                arestas.append((a, b))
                
    # meio (ligação entre últimas camadas esquerda e direita)
    for j in range(jogadores):
        camada_j = regiao_jogadores[j][-1]
        for jo in range(j + 1, jogadores):
            camada_jo = regiao_jogadores[jo][-1]
            conectar_camadas_limite_total(camada_j, camada_jo, arestas, max_total=2)

    print(arestas)
    print(arestas_para_lista_adjacencia_nao_direcionado(arestas))
    
        
    return cidades, arestas