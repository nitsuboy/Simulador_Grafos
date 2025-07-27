import json
import gerador_tabuleiro

def exportar_mapa_para_json(cidades_dict, arestas_tuples, nome_arquivo):
    """
    Extrai as estruturas de dados do gerador de tabuleiro (sem pesos nas arestas)
    e as converte para o formato JSON, calculando os pesos dinamicamente (supondo peso = população).
    """
    
    # Inicializa o dicionário que será convertido para JSON
    mapa_para_json = {
        "cidades": [],
        "arestas": []
    }

    # Converte o dicionário de cidades para uma lista de dicionários
    for cidade_id, info in cidades_dict.items():
        nova_cidade = {
            "id": cidade_id,
            "populacao": info["pop"]
        }
        mapa_para_json["cidades"].append(nova_cidade)

    # Converte a lista de tuplas de arestas, CALCULANDO O PESO NO PROCESSO
    for origem_id, destino_id in arestas_tuples:
        
        # Verifica se a cidade de origem existe no dicionário        
        if destino_id in cidades_dict:
            # Pega a população da cidade de destino
            populacao_destino = cidades_dict[destino_id]['pop']
            
            # Define o peso da aresta com base na população
            peso_calculado = populacao_destino

            # Cria a nova aresta com o peso calculado
            nova_aresta = {
                "de": origem_id,
                "para": destino_id,
                "peso": peso_calculado
            }
            mapa_para_json["arestas"].append(nova_aresta)
        else:
            # Trata o caso onde a cidade de destino não existe
            print(f"AVISO: A cidade de destino '{destino_id}' da aresta ('{origem_id}' -> '{destino_id}') não foi encontrada. Aresta ignorada.")
            
    # Salva o dicionário em um arquivo JSON
    with open(nome_arquivo, 'w', encoding='utf-8') as f:
        json.dump(mapa_para_json, f, indent=2, ensure_ascii=False)
    
    print(f"Mapa exportado com sucesso para {nome_arquivo}")

if __name__ == "__main__":
    # Gera o mapa usando o gerador_tabuleiro
    cidades_geradas, arestas_geradas = gerador_tabuleiro.gerar_grafo(jogadores=2, camadas=2)

    # Exporta o mapa gerado para um arquivo JSON
    exportar_mapa_para_json(cidades_geradas, arestas_geradas, "mapa.json")