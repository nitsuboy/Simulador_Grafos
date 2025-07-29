import pygame
import gerador_tabuleiro
import random
import json

# Inicializar Pygame
pygame.init()
WIDTH, HEIGHT = 1920, 1080
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Visualizador de Grafo")

try:
    tile_image = pygame.image.load("../assets/ground.jpg")
    tile_size = (200, 200)
    tile_image = pygame.transform.scale(tile_image, tile_size)
except pygame.error as e:
    print(f"Não foi possível carregar a imagem de fundo: {e}")
    tile_image = None
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 28)
peso_font = pygame.font.SysFont(None, 22)

botao_rect = pygame.Rect(650, 20, 120, 30)

def desenhar_moeda(surface, base_color, center, radius_x, height):
    radius_y = radius_x // 2 
    sombra_color = tuple(max(0, c - 50) for c in base_color)
    borda_color = tuple(max(0, c - 80) for c in base_color)

    rect_lateral = pygame.Rect(center[0] - radius_x, center[1] - radius_y + height, 2 * radius_x, 2 * radius_y)
    pygame.draw.ellipse(surface, sombra_color, rect_lateral)
    pygame.draw.ellipse(surface, borda_color, rect_lateral, 2)

    rect_topo = pygame.Rect(center[0] - radius_x, center[1] - radius_y, 2 * radius_x, 2 * radius_y)
    pygame.draw.ellipse(surface, base_color, rect_topo)
    pygame.draw.ellipse(surface, borda_color, rect_topo, 2)

def desenhar_hud(round_num):
    # Desenhar botão de próxima rodada
    pygame.draw.rect(screen, (0, 150, 0), next_round_button_rect)
    pygame.draw.rect(screen, (255, 255, 255), next_round_button_rect, 2)
    next_round_text = font.render("Próxima Rodada", True, (255, 255, 255))
    screen.blit(next_round_text, (next_round_button_rect.centerx - next_round_text.get_width() // 2, next_round_button_rect.centery - next_round_text.get_height() // 2))

    # Desenhar contador de rodada
    round_font = pygame.font.SysFont(None, 48)
    round_text = round_font.render(f"Rodada: {round_num}", True, (255, 255, 255))
    screen.blit(round_text, (WIDTH - 220, 80))

def desenhar_legenda(nomes_jogadores):
    legenda_font = pygame.font.SysFont(None, 20)
    cores = [
        ((0, 150, 255), f"Base {nomes_jogadores[0]}"),
        ((255, 150, 0), f"Base {nomes_jogadores[1]}"),
        ((150, 150, 150), "Cidade Neutra")
    ]
    x, y = 20, 20
    for cor, descricao in cores:
        pygame.draw.circle(screen, cor, (x, y), 10)
        texto_legenda = legenda_font.render(descricao, True, (0, 0, 0))
        screen.blit(texto_legenda, (x + 20, y - 10))
        y += 25

game_data = {}

def gerar_estado_jogo_json(cidades_orig, arestas_orig, turno_atual):
    mapa_cidades =  [{ "id": nome, "populacao": info["pop"], "pos": info["pos"] } for nome, info in cidades_orig.items()]
    mapa_arestas = [{ "de": de, "para": para, "peso": peso } for de, para, peso in arestas_orig]

    cidades_nao_base = [c["id"] for c in mapa_cidades if "basej" not in c["id"]]
    cidades_disponiveis = list(cidades_nao_base)

    # Define cidades possuídas aleatoriamente
    cidades_j0 = [c["id"] for c in mapa_cidades if cidades_orig[c["id"]].get("owner") == 0]
    cidades_j1 = [c["id"] for c in mapa_cidades if cidades_orig[c["id"]].get("owner") == 1]
    if len(cidades_disponiveis) >= 2:
        dominadas_j0 = random.sample(cidades_disponiveis, k=min(2, len(cidades_disponiveis)))
        cidades_j0.extend(dominadas_j0)
        for c in dominadas_j0: cidades_disponiveis.remove(c)
    
    if len(cidades_disponiveis) >= 2:
        dominadas_j1 = random.sample(cidades_disponiveis, k=min(2, len(cidades_disponiveis)))
        cidades_j1.extend(dominadas_j1)

    # Gera tropas aleatórias em cidades possuídas (não na base)
    tropas_em_campo = []
    cidades_sem_base_j0 = [c for c in cidades_j0 if "basej" not in c]
    if cidades_sem_base_j0:
        cidade_tropa = random.choice(cidades_sem_base_j0)
        tropas_em_campo.append({"id": f"tropa_j0_{turno_atual}", "dono": 0, "forca": random.randint(20, 80), "localizacao": cidade_tropa})

    cidades_sem_base_j1 = [c for c in cidades_j1 if "basej" not in c]
    if cidades_sem_base_j1:
        cidade_tropa = random.choice(cidades_sem_base_j1)
        tropas_em_campo.append({"id": f"tropa_j1_{turno_atual}", "dono": 1, "forca": random.randint(20, 80), "localizacao": cidade_tropa})

    return {
        "turno_atual": turno_atual,
        "mapa": {"cidades": mapa_cidades, "arestas": mapa_arestas},
        "jogadores": [
            {"id": "j0", "cidades_possuidas": list(set(cidades_j0))},
            {"id": "j1", "cidades_possuidas": list(set(cidades_j1))}
        ],
        "tropas_em_campo": tropas_em_campo
    }

def call_new_status():
    global game_data
    if not cidades:
        return

    # Gera o novo estado do jogo em JSON falso, vai ser puxado a partir do motor
    game_data = gerar_estado_jogo_json(cidades, arestas, round_counter)

    # Reseta donos
    for nome in cidades:
        cidades[nome]['owner'] = None

    # Atualiza donos com base no JSON
    for jogador in game_data['jogadores']:
        player_id = int(jogador['id'].replace('j', ''))
        for cidade_id in jogador['cidades_possuidas']:
            if cidade_id in cidades:
                cidades[cidade_id]['owner'] = player_id

# Variáveis de estado do jogo
game_state = 'menu'

# Variáveis do Menu
player_names = ["Jogador 1", "Jogador 2"]
input_rects = [
    pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 - 50, 300, 40),
    pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 + 10, 300, 40)
]
active_input = None
start_button_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 80, 200, 50)
next_round_button_rect = pygame.Rect(WIDTH - 220, 20, 200, 50)

# Variáveis de Jogo
round_counter = 1

# Loop principal
running = True
while running:
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            running = False

    if game_state == 'menu':
        # Lógica de eventos do menu
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_button_rect.collidepoint(event.pos):
                    game_state = 'game'
                    cidades, arestas, list_adj = gerador_tabuleiro.gerar_grafo(num_jogadores=len(player_names), largura=WIDTH, altura=HEIGHT)
                else:
                    # Ativar a caixa de texto clicada
                    clicked_on_input = False
                    for i, rect in enumerate(input_rects):
                        if rect.collidepoint(event.pos):
                            active_input = i
                            clicked_on_input = True
                            break
                    # Desativar se clicar fora
                    if not clicked_on_input:
                        active_input = None

            if event.type == pygame.KEYDOWN and active_input is not None:
                if event.key == pygame.K_BACKSPACE:
                    player_names[active_input] = player_names[active_input][:-1]
                else:
                    player_names[active_input] += event.unicode

        # Desenhar o menu
        screen.fill((30, 30, 30)) # Fundo escuro para o menu
        title_font = pygame.font.SysFont(None, 72)
        title_text = title_font.render("Conquista e Sobrevivência", True, (255, 255, 255))
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, HEIGHT // 4))

        for i, rect in enumerate(input_rects):
            pygame.draw.rect(screen, (200, 200, 200), rect)
            pygame.draw.rect(screen, (0, 0, 0), rect, 2)
            text_surface = font.render(player_names[i], True, (0, 0, 0))
            screen.blit(text_surface, (rect.x + 10, rect.y + 5))

        pygame.draw.rect(screen, (0, 200, 0), start_button_rect)
        start_text = font.render("Iniciar", True, (255, 255, 255))
        screen.blit(start_text, (start_button_rect.centerx - start_text.get_width() // 2, start_button_rect.centery - start_text.get_height() // 2))

    elif game_state == 'game':
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if next_round_button_rect.collidepoint(event.pos):
                    round_counter += 1
                    call_new_status()
                elif botao_rect.collidepoint(event.pos):
                    cidades, arestas, list_adj = gerador_tabuleiro.gerar_grafo(num_jogadores=len(player_names), largura=WIDTH, altura=HEIGHT)

        if tile_image:
            tile_width, tile_height = tile_image.get_size()
            for y in range(0, HEIGHT, tile_height):
                for x in range(0, WIDTH, tile_width):
                    screen.blit(tile_image, (x, y))
        else:
            screen.fill((255, 255, 255))

        # 1. Desenhar as linhas das arestas
        if arestas:
            for a, b, p in arestas:
                pos_a = cidades[a]["pos"]
                pos_b = cidades[b]["pos"]
                espessura = max(1, min(10, p // 10))
                pygame.draw.line(screen, (131,111,98), pos_a, pos_b, espessura)

        # 2. Desenhar as cidades (moedas e população)
        if cidades:
            for nome, info in cidades.items():
                x, y = info["pos"]
                pop = info["pop"]
                owner = info.get("owner")
                if owner == 0:
                    cor = (0, 150, 255)  # Azul para Jogador 0
                elif owner == 1:
                    cor = (255, 150, 0)  # Laranja para Jogador 1
                else:
                    cor = (200, 200, 200) # Cinza para Neutra
                desenhar_moeda(screen, cor, (x, y), 30, 8)
                texto_pop = font.render(f"{pop}", True, (0, 0, 0))
                texto_rect_pop = texto_pop.get_rect(center=(x, y))
                screen.blit(texto_pop, texto_rect_pop)

        # 3. Desenhar tropas em campo
        if game_data and 'tropas_em_campo' in game_data:
            for tropa in game_data['tropas_em_campo']:
                cidade_id = tropa['localizacao']
                if cidade_id in cidades:
                    pos_cidade = cidades[cidade_id]['pos']
                    forca = tropa['forca']
                    dono_id = tropa['dono']
                    cor_tropa = (0, 100, 200) if dono_id == 0 else (200, 100, 0)
                    
                    tropa_font = pygame.font.SysFont(None, 26)
                    texto_tropa = tropa_font.render(str(forca), True, cor_tropa)
                    texto_rect_tropa = texto_tropa.get_rect(center=(pos_cidade[0] + 25, pos_cidade[1] - 25))
                    pygame.draw.circle(screen, cor_tropa, texto_rect_tropa.center, 12, 2) # Círculo em volta
                    screen.blit(texto_tropa, texto_rect_tropa)

        # 4. Desenhar os pesos das arestas
        if arestas:
            for a, b, p in arestas:
                pos_a = cidades[a]["pos"]
                pos_b = cidades[b]["pos"]
                label_x = pos_a[0] * 0.8 + pos_b[0] * 0.2
                label_y = pos_a[1] * 0.8 + pos_b[1] * 0.2
                peso_texto = peso_font.render(str(p), True, (0, 0, 0))
                texto_rect = peso_texto.get_rect(center=(label_x, label_y))
                screen.blit(peso_texto, texto_rect)

        desenhar_legenda(player_names)
        desenhar_hud(round_counter)

    pygame.display.flip()
    clock.tick(30)

pygame.quit()
