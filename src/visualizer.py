import pygame
import json
import sys

# GERADO PELO GEMINI 2.5 PRO

# --- Constantes de Configuração ---
WIDTH, HEIGHT = 800, 600
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
NEUTRAL_COLOR = (150, 150, 150)

# Dicionário de cores para cada jogador (fácil de expandir)
CORES_JOGADORES = {
    'j0': (0, 150, 255), # Azul
    'j1': (255, 150, 0), # Laranja
    'j2': (0, 255, 150), # Verde Água
    'j3': (150, 255, 0)  # Verde Limão
}

# --- Funções de Desenho (para organizar o código) ---

def carregar_estado_do_jogo(nome_arquivo):
    """Carrega os dados de um arquivo JSON de estado do jogo."""
    try:
        with open(nome_arquivo, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"ERRO: Arquivo '{nome_arquivo}' não encontrado. Crie um estado inicial.")
        sys.exit()
    except json.JSONDecodeError:
        print(f"ERRO: Arquivo '{nome_arquivo}' não é um JSON válido.")
        sys.exit()

def desenhar_mapa(superficie, mapa_data):
    """Desenha as arestas do mapa."""
    for aresta in mapa_data['arestas']:
        # Precisamos encontrar as posições das cidades conectadas pela aresta
        pos_de = None
        pos_para = None
        for cidade in mapa_data['cidades']:
            if cidade['id'] == aresta['de']:
                pos_de = cidade['pos']
            if cidade['id'] == aresta['para']:
                pos_para = cidade['pos']
        
        if pos_de and pos_para:
            pygame.draw.line(superficie, GRAY, pos_de, pos_para, 2)

def desenhar_cidades(superficie, mapa_data, jogadores_data, font):
    """Desenha as cidades, colorindo pelo dono e mostrando a população."""
    cidades_dict = {c['id']: c for c in mapa_data['cidades']}
    
    # Determina o dono de cada cidade
    donos_cidades = {}
    for jogador in jogadores_data:
        for cidade_id in jogador['cidades_possuidas']:
            donos_cidades[cidade_id] = jogador['id']

    for cidade_id, cidade in cidades_dict.items():
        pos = cidade['pos']
        pop = cidade['populacao']
        dono = donos_cidades.get(cidade_id) # Pega o dono, ou None se for neutra
        
        cor = CORES_JOGADORES.get(dono, NEUTRAL_COLOR)

        pygame.draw.circle(superficie, cor, pos, 25)
        pygame.draw.circle(superficie, BLACK, pos, 25, 2)
        
        # Desenha a população dentro do círculo
        texto_pop = font.render(str(pop), True, BLACK)
        rect_pop = texto_pop.get_rect(center=pos)
        superficie.blit(texto_pop, rect_pop)
        
        # Desenha o ID da cidade acima
        texto_id = font.render(cidade_id, True, BLACK)
        rect_id = texto_id.get_rect(center=(pos[0], pos[1] - 35))
        superficie.blit(texto_id, rect_id)

def desenhar_tropas(superficie, tropas_data, mapa_data, font):
    """Desenha as tropas em suas localizações."""
    cidades_dict = {c['id']: c for c in mapa_data['cidades']}

    for tropa in tropas_data:
        pos_cidade = cidades_dict[tropa['localizacao']]['pos']
        cor_dono = CORES_JOGADORES.get(tropa['dono'], BLACK)
        
        # Desenha um pequeno quadrado para representar a tropa, deslocado da cidade
        pos_tropa = (pos_cidade[0] + 20, pos_cidade[1] - 20)
        rect_tropa = pygame.Rect(pos_tropa[0], pos_tropa[1], 30, 20)
        pygame.draw.rect(superficie, cor_dono, rect_tropa)
        pygame.draw.rect(superficie, WHITE, rect_tropa, 1)
        
        # Escreve a força da tropa
        texto_forca = font.render(str(tropa['forca']), True, WHITE)
        rect_forca = texto_forca.get_rect(center=rect_tropa.center)
        superficie.blit(texto_forca, rect_forca)

def desenhar_hud(superficie, estado_jogo, font):
    """Desenha informações na tela, como o número do turno."""
    turno = estado_jogo.get('turno_atual', 0)
    texto_turno = font.render(f"Turno: {turno}", True, BLACK)
    superficie.blit(texto_turno, (10, 10))

# --- Função Principal ---

def main():
    """Função principal que roda o loop do visualizador."""
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Visualizador de Estratégia")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 22)
    font_hud = pygame.font.SysFont(None, 30)

    # Carrega o estado do jogo do arquivo.
    # Para um visualizador dinâmico, essa linha estaria DENTRO do loop principal,
    # procurando por novos arquivos de estado a cada segundo.
    estado_jogo = carregar_estado_do_jogo("src/estado_do_jogo.json")

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Preenche o fundo
        screen.fill(WHITE)

        # Extrai os dados do estado do jogo
        mapa_data = estado_jogo['mapa']
        jogadores_data = estado_jogo['jogadores']
        tropas_data = estado_jogo['tropas_em_campo']

        # Desenha os elementos em camadas
        desenhar_mapa(screen, mapa_data)
        desenhar_cidades(screen, mapa_data, jogadores_data, font)
        desenhar_tropas(screen, tropas_data, mapa_data, font)
        desenhar_hud(screen, estado_jogo, font_hud)

        # Atualiza a tela
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()

if __name__ == "__main__":
    main()