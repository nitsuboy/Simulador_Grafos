import random
from .ia_interface import IAInterface # Não esqueça do . para importar corretamente

class Perseus(IAInterface):
    """
    Uma IA "Burra" que toma decisões aleatórias, mas válidas.
    Seu principal objetivo é testar a engine do jogo.
    """
    def __init__(self, jogador_id):
        super().__init__(jogador_id)
        self.contador_tropas = 0 # Garante que cada tropa tem um ID único

    def decidir_acoes(self, estado_do_jogo, mapa):
        """
        A lógica de decisão da IA.
        """
        # Coleta o estado do jogo e informações relevantes
        bot_info = next((j for j in estado_do_jogo['jogadores'] if j['id'] == self.jogador_id), None)
        if not bot_info: return ""

        tropas_na_base = bot_info['tropas_na_base']
        minha_base_id = f"base_{self.jogador_id}"
        
        mapa_info = estado_do_jogo['mapa']
        lista_de_cidades = mapa_info['cidades']
        
        cidades_minhas = [c['id'] for c in lista_de_cidades if c['dono'] == self.jogador_id]
        cidades_neutras = [c for c in lista_de_cidades if c['dono'] is None]
        meu_transporte = next((t for t in estado_do_jogo['transportes'] if t['dono'] == self.jogador_id), None)

        # Prepara as ordens de tropas e transporte
        ordens_tropas_str = "Novas Tropas:\n"
        ordens_transporte_str = "Transporte:\n"

        # Decisão de novas tropas
        if random.random() < 0.5 and tropas_na_base >= 10 and cidades_neutras:
            self.contador_tropas += 1
            id_nova_tropa = f"{self.jogador_id}_{self.contador_tropas}"
            forca = random.randint(10, int(tropas_na_base / 2) + 1) if tropas_na_base >= 20 else 10
            alvo = random.choice(cidades_neutras)
            ordens_tropas_str += f"{id_nova_tropa} {forca}: {minha_base_id} -> ataca {alvo['id']}\n"

        # --- Decisão de Transporte ---
        if meu_transporte and meu_transporte['estado'] == 'ocioso' and random.random() < 0.5:
            
            cidades_para_coleta = []
            
            # Lógica principal: sempre adiciona as cidades válidas à lista de possibilidades
            for cidade_id in cidades_minhas:
                if "base" not in cidade_id:                
                    for c_info in lista_de_cidades:
                        if c_info['id'] == cidade_id and c_info['populacao'] > 0:
                            cidades_para_coleta.append(cidade_id)
            
            if cidades_para_coleta:
                cidade_origem = random.choice(cidades_para_coleta)
                ordens_transporte_str += f"missao: COLETAR MAX DE {cidade_origem}, ENTREGAR EM {minha_base_id}\n"

        return ordens_tropas_str + "\n" + ordens_transporte_str