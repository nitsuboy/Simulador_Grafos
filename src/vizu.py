import pygame
import gerador_tabuleiro

# Inicializar Pygame
pygame.init()
WIDTH, HEIGHT = 800, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Visualizador de Grafo")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 28)  # Aumentei o tamanho da fonte

botao_rect = pygame.Rect(650, 20, 120, 30)

def desenhar_botao():
    pygame.draw.rect(screen, (180, 180, 180), botao_rect)
    pygame.draw.rect(screen, (0, 0, 0), botao_rect, 2)
    texto = font.render("Gerar Grafo", True, (0, 0, 0))
    screen.blit(texto, (botao_rect.x + 10, botao_rect.y + 5))

def desenhar_legenda():
    legenda_font = pygame.font.SysFont(None, 20)
    cores = [
        ((0, 150, 255), "Base Jogador 0"),
        ((255, 150, 0), "Base Jogador 1"),
        ((0, 255, 150), "Base Jogador 2"),
        ((150, 255, 0), "Base Jogador 3"),
        ((255, 100, 100), "Base Jogador 4"),
        ((150, 150, 150), "Cidade Normal")
    ]
    x, y = 20, 20
    for cor, descricao in cores:
        pygame.draw.circle(screen, cor, (x, y), 10)
        texto_legenda = legenda_font.render(descricao, True, (0, 0, 0))
        screen.blit(texto_legenda, (x + 20, y - 10))
        y += 25

# Gerar grafo
cidades, arestas, list_adj = gerador_tabuleiro.gerar_grafo(num_jogadores=3)

# Loop principal
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if botao_rect.collidepoint(event.pos):
                cidades, arestas, list_adj = gerador_tabuleiro.gerar_grafo(num_jogadores=3)

    screen.fill((255, 255, 255))

    # Desenhar arestas
    for a, b, p in arestas:
        pos_a = cidades[a]["pos"]
        pos_b = cidades[b]["pos"]

        # Ajustar a espessura da aresta com base no peso
        espessura = max(1, min(10, p // 10))  # Limita a espessura entre 1 e 10
        pygame.draw.line(screen, (100, 100, 100), pos_a, pos_b, espessura)

    # Desenhar cidades
    for nome, info in cidades.items():
        x, y = info["pos"]
        pop = info["pop"]
        cor = (0, 150, 255) if "basej" in nome and "0" in nome else \
              (255, 150, 0) if "basej" in nome and "1" in nome else \
              (0, 255, 150) if "basej" in nome and "2" in nome else \
              (150, 255, 0) if "basej" in nome and "3" in nome else \
              (255, 100, 100) if "basej" in nome and "4" in nome else (150, 150, 150)

        pygame.draw.circle(screen, cor, (x, y), 25)  # Aumentei o tamanho do círculo
        pygame.draw.circle(screen, (0, 0, 0), (x, y), 25, 2)
        
        texto_pop = font.render(f"{pop}", True, (0, 0, 0))
        texto_rect_pop = texto_pop.get_rect(center=(x, y))
        screen.blit(texto_pop, texto_rect_pop)

    desenhar_botao()
    desenhar_legenda()

    pygame.display.flip()
    clock.tick(30)

pygame.quit()
