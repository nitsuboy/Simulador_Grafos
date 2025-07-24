import random
import sys
import math

def rotate(origin, point, angle):
    """
    Rotate a point counterclockwise by a given angle around a given origin.

    The angle should be given in radians.
    """
    ox, oy = origin
    px, py = point

    qx = ox + math.cos(angle) * (px - ox) - math.sin(angle) * (py - oy)
    qy = oy + math.sin(angle) * (px - ox) + math.cos(angle) * (py - oy)
    return qx, qy

def adicionar_arestas_bidirecional(grafo, a, b, peso):
    grafo.setdefault(a, []).append((b, peso))
    grafo.setdefault(b, []).append((a, peso))

def gerar_grafo(camadas=None,seed=None,jogadores=2):
    
    #tratamento de argumentos
    if not seed:
        seed = random.randrange(sys.maxsize)
    random.seed(seed)
    print(seed)
    
    if not camadas:
        camadas = random.randint(2, 3)
    
    largura, altura = 800, 800
    raio = 25
    max_y = 200

    
    cidades = {
        "base_j1": {"pos": (raio, altura // 2), "pop": 100},
        "base_j2": {"pos": (largura - raio, altura // 2), "pop": 100},
    }

    nome_contador = 1
    camadas_esquerda = []
    camadas_direita = []

    # Geração das camadas à esquerda (entre base_j1 e meio)
    for i in range(camadas):
        camada = []
        n_cidades = random.randint(2, 4)
        
        x = raio + (i + 1) * ((largura // 2) // (camadas + 1))
        y_step = (altura - 2 * max_y) // (n_cidades + 1)
        
        for j in range(n_cidades):
            nome = f"c{nome_contador}"
            y = max_y + (j + 1) * y_step
            cidades[nome] = {
                "pos": (x, y),
                "pop": random.randint(30, 80)
            }
            camada.append(nome)
            nome_contador += 1
            
        camadas_esquerda.append(camada)

    # Espelhamento das camadas à direita
    for camada in camadas_esquerda:
        camada_espelhada = []
        for nome in camada:
            pos_x, pos_y = cidades[nome]["pos"]
            nome_espelhado = f"{nome}_r"
            cidades[nome_espelhado] = {
                "pos": (largura - pos_x, pos_y),
                "pop": cidades[nome]["pop"]  # manter mesma população
            }
            camada_espelhada.append(nome_espelhado)
        camadas_direita.append(camada_espelhada)
    # Geração das arestas
    arestas = []
    list_adj={}

    # base_j1 -> primeira camada
    arestas += [("base_j1", nome) for nome in camadas_esquerda[0]]
    arestas += [("base_j2", nome) for nome in camadas_direita[0]]
    print(arestas)
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

    # meio (ligação entre últimas camadas esquerda e direita)
    meio_esq = camadas_esquerda[-1]
    meio_dir = camadas_direita[-1]
    for a in meio_esq:
        b = random.choice(meio_dir)
        arestas.append((a, b))
    for b in meio_dir:
        a = random.choice(meio_esq)
        arestas.append((a, b))
        
    return cidades, arestas