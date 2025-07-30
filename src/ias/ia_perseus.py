import random
from .ia_interface import IAInterface

class Perseus(IAInterface):
    """
    Uma IA de teste que toma decisões aleatórias e, propositalmente,
    tenta criar cenários de borda para testar a robustez da engine.
    """
    def __init__(self, jogador_id):
        super().__init__(jogador_id)
        self.contador_tropas = 0

    def decidir_acoes(self, estado_do_jogo, mapa):        
        bot_info = next((j for j in estado_do_jogo['jogadores'] if j['id'] == self.jogador_id), None)
        if not bot_info: return ""
        tropas_na_base = bot_info['tropas_na_base']
        minha_base_id = f"base_{self.jogador_id}"
        mapa_info = estado_do_jogo['mapa']
        lista_de_cidades = mapa_info['cidades']
        cidades_minhas = [c for c in lista_de_cidades if c['dono'] == self.jogador_id]
        cidades_neutras = [c for c in lista_de_cidades if c['dono'] is None]
        meu_transporte = next((t for t in estado_do_jogo['transportes'] if t['dono'] == self.jogador_id), None)
        minhas_tropas_em_campo = [t for t in estado_do_jogo['tropas_em_campo'] if t['dono'] == self.jogador_id]

        ordens_tropas_str = "Novas Tropas:\n"
        ordens_transporte_str = "Transporte:\n"

        # Com 10% de chance, tenta criar o cenário de "pedágio em cidade neutra"
        if meu_transporte and meu_transporte['estado'] == 'ocioso' and random.random() < 0.1:
            # Encontra uma cidade possuida que não seja a base, que tenha população e esteja no meio do caminho
            for cidade_origem in cidades_minhas:
                if "base" not in cidade_origem['id'] and cidade_origem['populacao'] > 0:
                    caminho_para_base = mapa.encontrar_caminho_bfs(cidade_origem['id'], minha_base_id)
                    if caminho_para_base and len(caminho_para_base) > 2:
                        cidade_pedagio_id = caminho_para_base[1] # A primeira cidade no caminho
                        
                        # Verifica se a cidade_pedagio é nossa e tem exatamente 1 tropa
                        tropas_na_cidade_pedagio = [t for t in minhas_tropas_em_campo if t['localizacao'] == cidade_pedagio_id]
                        if len(tropas_na_cidade_pedagio) == 1:
                            tropa_a_recuar = tropas_na_cidade_pedagio[0]
                            print(f"IA {self.jogador_id} INICIANDO TESTE DE PEDÁGIO NEUTRO!")
                            # Ação 1: Esvaziar a cidade de pedágio, transformando-a em neutra no futuro
                            ordens_tropas_str += f"{tropa_a_recuar['id']} 1: recua\n" # A força aqui é irrelevante
                            # Ação 2: Enviar o transporte em uma rota que passará pela cidade de pedágio
                            ordens_transporte_str += f"missao: COLETAR MAX DE {cidade_origem['id']}, ENTREGAR EM {minha_base_id}\n"
                            
                            # Retorna as ordens coordenadas e encerra a decisão deste turno
                            return ordens_tropas_str + "\n" + ordens_transporte_str        
        
        # Decisão de Tropa
        if random.random() < 0.5 and tropas_na_base >= 10:
            vizinhos_da_base = mapa.get_vizinhos(minha_base_id)
            alvos_validos = [c for c in cidades_neutras if c['id'] in vizinhos_da_base]
            if alvos_validos:
                self.contador_tropas += 1
                id_nova_tropa = f"{self.jogador_id}_{self.contador_tropas}"
                forca = random.randint(10, int(tropas_na_base / 2) + 1) if tropas_na_base >= 20 else 10
                alvo = random.choice(alvos_validos)
                ordens_tropas_str += f"{id_nova_tropa} {forca}: {minha_base_id} -> ataca {alvo['id']}\n"

        # Decisão de Transporte
        if meu_transporte and meu_transporte['estado'] == 'ocioso' and random.random() < 0.5:
            cidades_para_coleta = [c for c in cidades_minhas if "base" not in c['id'] and c['populacao'] > 0]
            if cidades_para_coleta:
                cidade_origem = random.choice(cidades_para_coleta)
                ordens_transporte_str += f"missao: COLETAR MAX DE {cidade_origem['id']}, ENTREGAR EM {minha_base_id}\n"

        return ordens_tropas_str + "\n" + ordens_transporte_str