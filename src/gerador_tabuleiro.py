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
    p = random.randrange(10,20)
    arestas.append((a, b, p))
    ja_conectados.add((a, b))

    total = 1

    # Conexões extras até o limite total
    while total < max_total:
        p = random.randrange(10,20)
        a = random.choice(camada1)
        b = random.choice(camada2)
        if (a, b) not in ja_conectados:
            arestas.append((a, b, p))
            ja_conectados.add((a, b))
            total += 1

def arestas_para_lista_adjacencia_nao_direcionado(arestas):
    grafo = defaultdict(list)
    for a, b, p in arestas:
        grafo[a].append((b, p))
        grafo[b].append((a, p))
    return dict(grafo)

def gerar_grafo(camadas=None,seed=None,jogadores=2,ilha_central=False):
    
    # Tratamento de argumentos
    # Geramento de seed ja que o random n disponibiliza a seed utilizada
    if not seed:
        seed = random.randrange(sys.maxsize)
    random.seed(seed)
    print(seed)
    
    if not camadas:
        camadas = []
        for i in range(random.randrange(2,4)):
            camadas.append(random.randrange(2,5))
    
    # Tamanho maximo de onde irão se encontrar os nos, detalhe de vizualização
    largura, altura = 800, 800
    raio = 25
    max_y = 250

    # Conjunto de nós para que serão espelhados
    cidades_base = {}
    camadas_base = []
    # Conjunto contendo todos os nós
    cidades = {}
    
    # Inicializa as bases dos jogadores
    for j in range(jogadores):
        cidades[f"base_j{j}"] = {
            "pos": rotate((largura // 2,altura // 2),(raio, altura // 2),(6.283185/jogadores)*j)
            , "pop": 100}

    
    nome_contador = 1
    #regiões espelhadas 
    regiao_jogadores = []

    # Processo de fazer as camadas nas quais o espelhamento vai se basear
    for i in range(len(camadas)):
        camada = []
        n_cidades = camadas[i]
        
        x = raio + (i + 1) * ((largura // 2) // (len(camadas) + 1))
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

    # Processo de espelhamento da camada base em as demais para ter uma simetria
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
    
    for j in range(jogadores):
        arestas += [(f'base_j{j}', nome, random.randint(1, 5) ) for nome in regiao_jogadores[j][0]]
    
    for j in range(jogadores):
        regioes = regiao_jogadores[j]
        for i in range(len(regioes) - 1):
            atual = regioes[i]
            prox = regioes[i + 1]
            check_arestas = []
            for a in atual:
                p = random.randrange(10,20)
                b = random.choice(prox)
                arestas.append((a, b, p))
                check_arestas.append((a, b))
            for b in prox:
                p = random.randrange(10,20)
                a = random.choice(atual)
                if (a, b) in check_arestas:
                    print("kek")
                else:
                    arestas.append((a, b, p))
                
    # meio (ligação entre últimas camadas esquerda e direita)
    for j in range(jogadores):
        camada_j = regiao_jogadores[j][-1]
        for jo in range(j + 1, jogadores):
            camada_jo = regiao_jogadores[jo][-1]
            conectar_camadas_limite_total(camada_j, camada_jo, arestas, max_total=2)
    
    return cidades, arestas, arestas_para_lista_adjacencia_nao_direcionado(arestas)