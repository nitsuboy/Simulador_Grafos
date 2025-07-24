import pygame
import random
import math
import gerador_tabuleiro

# ---- CONFIG ----
WIDTH, HEIGHT = 800, 800
NODE_RADIUS = 20
EDGE_LENGTH = 150
REPULSION_FORCE = 1000
ATTRACTION_FORCE = 0.005
WALL_REPULSION = 2000
FRICTION = 0.9

# ÁREA DE CONFINAMENTO
LIMIT_LEFT = 0
LIMIT_RIGHT = WIDTH - 0
LIMIT_TOP = 0
LIMIT_BOTTOM = HEIGHT - 0

# ---- NÓS E ARESTAS ----
nodes, edges = gerador_tabuleiro.gerar_grafo(seed=8772254598625556543,jogadores=4,camadas=2)

# Cada nó tem uma velocidade
velocities = {k: [0, 0] for k in nodes}

# ---- FUNÇÕES DE FORÇA ----
def apply_repulsion():
    for a in nodes:
        for b in nodes:
            if a == b:
                continue
            dx = nodes[a]["pos"][0] - nodes[b]["pos"][0]
            dy = nodes[a]["pos"][1] - nodes[b]["pos"][1]
            dist_sq = dx*dx + dy*dy + 0.01  # evitar divisão por zero
            force = REPULSION_FORCE / dist_sq
            angle = math.atan2(dy, dx)
            fx = math.cos(angle) * force
            fy = math.sin(angle) * force
            velocities[a][0] += fx
            velocities[a][1] += fy

def apply_attraction():
    for a, b in edges:
        dx = nodes[b]["pos"][0] - nodes[a]["pos"][0]
        dy = nodes[b]["pos"][1] - nodes[a]["pos"][1]
        distance = math.sqrt(dx*dx + dy*dy)
        force = (distance - EDGE_LENGTH) * ATTRACTION_FORCE
        angle = math.atan2(dy, dx)
        fx = math.cos(angle) * force
        fy = math.sin(angle) * force
        velocities[a][0] += fx
        velocities[a][1] += fy
        velocities[b][0] -= fx
        velocities[b][1] -= fy

def apply_wall_repulsion():
    for node, dados in nodes.items():
        x,y = dados["pos"]
        # Repulsão da parede esquerda
        if x - NODE_RADIUS < LIMIT_LEFT + 50:
            dist = max(x - LIMIT_LEFT, 1)
            velocities[node][0] += WALL_REPULSION / (dist ** 2)
        # Direita
        if x + NODE_RADIUS > LIMIT_RIGHT - 50:
            dist = max(LIMIT_RIGHT - x, 1)
            velocities[node][0] -= WALL_REPULSION / (dist ** 2)
        # Cima
        if y - NODE_RADIUS < LIMIT_TOP + 50:
            dist = max(y - LIMIT_TOP, 1)
            velocities[node][1] += WALL_REPULSION / (dist ** 2)
        # Baixo
        if y + NODE_RADIUS > LIMIT_BOTTOM - 50:
            dist = max(LIMIT_BOTTOM - y, 1)
            velocities[node][1] -= WALL_REPULSION / (dist ** 2)

# ---- INICIALIZAR PYGAME ----
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Grafo com layout automático (sem NetworkX)")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 24)

# ---- LOOP PRINCIPAL ----
running = True
while running:
    screen.fill((30, 30, 30))
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    apply_repulsion()
    apply_attraction()
    apply_wall_repulsion()

    # Atualizar posições com física básica
    for k in nodes:
        velocities[k][0] *= FRICTION
        velocities[k][1] *= FRICTION
        nodes[k]["pos"][0] += velocities[k][0]
        nodes[k]["pos"][1] += velocities[k][1]
        
        nodes[k]["pos"][0] = max(LIMIT_LEFT, min(nodes[k]["pos"][0], LIMIT_RIGHT))
        nodes[k]["pos"][1] = max(LIMIT_TOP, min(nodes[k]["pos"][1], LIMIT_BOTTOM))


    # Desenhar arestas
    for a, b in edges:
        pygame.draw.line(screen, (100, 100, 255), nodes[a]["pos"], nodes[b]["pos"], 2)

    # Desenhar nós
    for name, dados in nodes.items():
        x,y = dados["pos"]
        pygame.draw.circle(screen, (0, 200, 200), (int(x), int(y)), NODE_RADIUS)
        label = font.render(name, True, (0, 0, 0))
        screen.blit(label, (int(x) - 10, int(y) - 10))
    
    pygame.draw.rect(screen, (60, 60, 60), (LIMIT_LEFT, LIMIT_TOP, LIMIT_RIGHT - LIMIT_LEFT, LIMIT_BOTTOM - LIMIT_TOP), 2)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
