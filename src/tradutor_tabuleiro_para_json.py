import json
import gerador_tabuleiro
import pygame

def exportar_mapa_para_json(cidades_dict, arestas_tuples, nome_arquivo):
    """
    Extrai as estruturas de dados do gerador de tabuleiro (sem pesos nas arestas)
    e as converte para o formato JSON, calculando os pesos dinamicamente (supondo peso = população).
    """
    mapa_para_json = {"cidades": [], "arestas": []}
    for cidade_id, info in cidades_dict.items():
        nova_cidade = {"id": cidade_id, "populacao": info["pop"]}
        mapa_para_json["cidades"].append(nova_cidade)
    for origem_id, destino_id in arestas_tuples:
        if destino_id in cidades_dict:
            populacao_destino = cidades_dict[destino_id]['pop']
            peso_calculado = populacao_destino
            nova_aresta = {"de": origem_id, "para": destino_id, "peso": peso_calculado}
            mapa_para_json["arestas"].append(nova_aresta)
        else:
            print(f"AVISO: A cidade de destino '{destino_id}' da aresta ('{origem_id}' -> '{destino_id}') não foi encontrada. Aresta ignorada.")
    with open(nome_arquivo, 'w', encoding='utf-8') as f:
        json.dump(mapa_para_json, f, indent=2, ensure_ascii=False)
    print(f"Mapa exportado com sucesso para {nome_arquivo}")

def salvar_mapa_como_png(cidades_dict, arestas_tuples, nome_arquivo, width=800, height=800):
    """
    Usa a lógica de desenho do Pygame para renderizar o estado do mapa e salvá-lo
    como um arquivo de imagem PNG.
    """
    print(f"Gerando imagem de debug do mapa para {nome_arquivo}...")
    
    # 1. Inicializa o Pygame e a fonte
    pygame.init()
    font = pygame.font.SysFont(None, 24)

    # Cria uma superfície para desenhar o mapa
    superficie = pygame.Surface((width, height))
    
    # Fundo
    superficie.fill((255, 255, 255)) # Fundo branco

    # Desenhar arestas
    for a, b in arestas_tuples:
        pos_a = cidades_dict[a]["pos"]
        pos_b = cidades_dict[b]["pos"]
        pygame.draw.line(superficie, (200, 200, 200), pos_a, pos_b, 2)

    # Desenhar cidades
    for nome, info in cidades_dict.items():
        x, y = info["pos"]
        pop = info["pop"]
        # Cores das bases
        cor = (0, 150, 255) if "base" in nome and "j0" in nome else \
              (255, 150, 0) if "base" in nome and "j1" in nome else \
              (0, 255, 150) if "base" in nome and "j2" in nome else \
              (150, 255, 0) if "base" in nome and "j3" in nome else (150, 150, 150)

        pygame.draw.circle(superficie, cor, (x, y), 20)
        pygame.draw.circle(superficie, (0, 0, 0), (x, y), 20, 2)

        texto_nome = font.render(nome, True, (0, 0, 0))
        texto_rect_nome = texto_nome.get_rect(center=(x, y - 28))
        texto_pop = font.render(f"{pop}", True, (0, 0, 0))
        texto_rect_pop = texto_pop.get_rect(center=(x, y))
        superficie.blit(texto_nome, texto_rect_nome)
        superficie.blit(texto_pop, texto_rect_pop)

    # Salva o mapa desenhado como um arquivo PNG
    try:
        pygame.image.save(superficie, nome_arquivo)
        print(f"Imagem salva com sucesso em {nome_arquivo}")
    except pygame.error as e:
        print(f"Erro ao salvar a imagem: {e}")
        
    pygame.quit()


if __name__ == "__main__":
    # Gera o mapa
    seed_para_teste = 12345 
    cidades_geradas, arestas_geradas = gerador_tabuleiro.gerar_grafo(jogadores=2, camadas=2, seed=seed_para_teste)

    # Exporta o mapa gerado para um arquivo JSON
    exportar_mapa_para_json(cidades_geradas, arestas_geradas, "src\mapa.json")
    
    # Salva uma imagem de debug correspondente ao JSON gerado
    salvar_mapa_como_png(cidades_geradas, arestas_geradas, "src\mapa_debug.png")