import pygame
import gerador_tabuleiro

# Inicializar Pygame
pygame.init()
WIDTH, HEIGHT = 800, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Visualizador de Grafo")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 24)

botao_rect = pygame.Rect(650, 20, 120, 30)

def desenhar_botao():
    pygame.draw.rect(screen, (180, 180, 180), botao_rect)
    pygame.draw.rect(screen, (0, 0, 0), botao_rect, 2)
    texto = font.render("Gerar Grafo", True, (0, 0, 0))
    screen.blit(texto, (botao_rect.x + 10, botao_rect.y + 5))

# Gerar grafo
cidades, arestas = gerador_tabuleiro.gerar_grafo(seed=8772254598625556543,jogadores=2,camadas=2)

# Loop principal
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if botao_rect.collidepoint(event.pos):
                cidades, arestas = gerador_tabuleiro.gerar_grafo(jogadores=4,camadas=2)

    screen.fill((255, 255, 255))

    # Desenhar arestas
    for a, b in arestas:
        pos_a = cidades[a]["pos"]
        pos_b = cidades[b]["pos"]
        pygame.draw.line(screen, (200, 200, 200), pos_a, pos_b, 2)

    # Desenhar cidades
    for nome, info in cidades.items():
        x, y = info["pos"]
        pop = info["pop"]
        cor = (0, 150, 255) if "base" in nome and "j0" in nome else \
              (255, 150, 0) if "base" in nome and "j1" in nome else \
              (0, 255, 150) if "base" in nome and "j2" in nome else \
              (150, 255, 0) if "base" in nome and "j3" in nome else \
              (255, 100, 100) if "base" in nome and "j4" in nome else (150, 150, 150)

        pygame.draw.circle(screen, cor, (x, y), 20)
        pygame.draw.circle(screen, (0, 0, 0), (x, y), 20, 2)

        texto_nome = font.render(nome, True, (0, 0, 0))
        texto_rect_nome = texto_nome.get_rect(center=(x, y-26))
        texto_pop = font.render(f"{pop}", True, (0,0,0))
        texto_rect_pop = texto_pop.get_rect(center=(x, y))
        screen.blit(texto_nome, texto_rect_nome)
        screen.blit(texto_pop, texto_rect_pop)

    desenhar_botao()

    pygame.display.flip()
    clock.tick(30)

pygame.quit()
