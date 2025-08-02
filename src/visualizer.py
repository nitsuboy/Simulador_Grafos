import pygame
import gerador_tabuleiro
import random
import json
import os

# Inicializar Pygame
pygame.init()
WIDTH, HEIGHT = 1920, 1080
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Visualizador de Grafo")

try:
    tile_image = pygame.image.load("./assets/ground.jpg")
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
    # Desenhar botões de navegação
    pygame.draw.rect(screen, (0, 150, 0), left_arrow_rect)
    pygame.draw.rect(screen, (255, 255, 255), left_arrow_rect, 2)
    left_arrow_text = font.render("<", True, (255, 255, 255))
    screen.blit(left_arrow_text, (left_arrow_rect.centerx - left_arrow_text.get_width() // 2, left_arrow_rect.centery - left_arrow_text.get_height() // 2))

    pygame.draw.rect(screen, (0, 150, 0), right_arrow_rect)
    pygame.draw.rect(screen, (255, 255, 255), right_arrow_rect, 2)
    right_arrow_text = font.render(">", True, (255, 255, 255))
    screen.blit(right_arrow_text, (right_arrow_rect.centerx - right_arrow_text.get_width() // 2, right_arrow_rect.centery - right_arrow_text.get_height() // 2))

    # Desenhar contador de rodada
    round_font = pygame.font.SysFont(None, 48)
    round_text = round_font.render(f"Turno: {round_num}", True, (255, 255, 255))
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

def carregar_mapa_do_json(caminho_json='mapa_debug.json'):
    script_dir = os.path.dirname(__file__)
    caminho_abs = os.path.join(script_dir, caminho_json)
    with open(caminho_abs, 'r', encoding='utf-8') as f:
        dados = json.load(f)
    
    cidades_carregadas = {c['id']: {'pop': c['populacao'], 'pos': tuple(map(int, c['pos'])), 'owner': None} for c in dados['cidades']}
    arestas_carregadas = [(a['de'], a['para'], a['peso']) for a in dados['arestas']]

    # Definir donos das bases
    for cid in cidades_carregadas:
        if 'basej_0' in cid:
            cidades_carregadas[cid]['owner'] = 0
        elif 'basej_1' in cid:
            cidades_carregadas[cid]['owner'] = 1
            
    return cidades_carregadas, arestas_carregadas


def draw_text_with_outline(surface, font, text, text_color, outline_color, pos, outline_width=1):
    text_surface = font.render(text, True, text_color)
    outline_surface = font.render(text, True, outline_color)
    
    # Desenha o contorno em várias posições
    for dx in [-outline_width, outline_width]:
        for dy in [-outline_width, outline_width]:
            surface.blit(outline_surface, (pos[0] - text_surface.get_width() // 2 + dx, pos[1] - text_surface.get_height() // 2 + dy))
    
    # Desenha o texto principal por cima
    surface.blit(text_surface, (pos[0] - text_surface.get_width() // 2, pos[1] - text_surface.get_height() // 2))

def carregar_estado_turno(turno):
    global game_data
    # Turno 0 é o mapa base, não carrega estado
    if turno == 0:
        game_data = {}
        for cid in cidades:
            if 'basej_0' in cid:
                cidades[cid]['owner'] = 0
            elif 'basej_1' in cid:
                cidades[cid]['owner'] = 1
            else:
                cidades[cid]['owner'] = None
        return True

    caminho_estado = os.path.join(os.path.dirname(__file__), '..', 'estados', f'estado_turno_{turno}.json')
    try:
        with open(caminho_estado, 'r', encoding='utf-8') as f:
            game_data = json.load(f)
        
        # Itera sobre as cidades no estado para definir o dono
        for cidade_estado in game_data.get('mapa', {}).get('cidades', []):
            cidade_id = cidade_estado['id']
            if cidade_id in cidades:
                dono = cidade_estado.get('dono')
                if dono is not None:
                    cidades[cidade_id]['owner'] = int(dono)
                else:
                    cidades[cidade_id]['owner'] = None
        return True
    except FileNotFoundError:
        print(f"Arquivo de estado para o turno {turno} não encontrado.")
        return False

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
left_arrow_rect = pygame.Rect(WIDTH - 280, 20, 50, 50)
right_arrow_rect = pygame.Rect(WIDTH - 220, 20, 50, 50)

# Variáveis de Jogo
round_counter = 0
max_turn = 9 # Baseado nos arquivos encontrados
cidades, arestas = {}, []

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
                    cidades, arestas = carregar_mapa_do_json()
                    # No turno 0, não carregamos um estado, apenas o mapa base.
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
                if left_arrow_rect.collidepoint(event.pos):
                    if round_counter > 0:
                        round_counter -= 1
                        carregar_estado_turno(round_counter)
                elif right_arrow_rect.collidepoint(event.pos):
                    if round_counter < max_turn:
                        round_counter += 1
                        carregar_estado_turno(round_counter)
                

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
                    
                    tropa_font = pygame.font.SysFont(None, 24)
                    text_color = (255, 255, 255)
                    outline_color = (0, 0, 0)

                    # Calcula a posição e a prende aos limites da tela
                    x_pos = pos_cidade[0] + 30
                    y_pos = pos_cidade[1] - 30

                    text_width, text_height = tropa_font.size(str(forca))
                    radius = max(text_width, text_height) // 2 + 4

                    x_pos = max(radius, min(WIDTH - radius, x_pos))
                    y_pos = max(radius, min(HEIGHT - radius, y_pos))
                    
                    pos_tropa = (x_pos, y_pos)

                    # Desenha o círculo da tropa
                    pygame.draw.circle(screen, cor_tropa, pos_tropa, radius)
                    pygame.draw.circle(screen, outline_color, pos_tropa, radius, 2)

                    # Desenha o texto com contorno
                    draw_text_with_outline(screen, tropa_font, str(forca), text_color, outline_color, pos_tropa, 2)

        # 4. Desenhar os pesos das arestas
        if arestas:
            for a, b, p in arestas:
                pos_a = cidades[a]["pos"]
                pos_b = cidades[b]["pos"]
                label_x = pos_a[0] * 0.8 + pos_b[0] * 0.2
                label_y = pos_a[1] * 0.8 + pos_b[1] * 0.2
                draw_text_with_outline(screen, peso_font, str(p), (255, 255, 255), (0, 0, 0), (label_x, label_y))

        desenhar_legenda(player_names)
        desenhar_hud(round_counter)

    pygame.display.flip()
    clock.tick(30)

pygame.quit()
