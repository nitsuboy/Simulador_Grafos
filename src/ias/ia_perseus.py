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
        Propositalmente inclui a chance de tentar ações "impossíveis" para
        testar a robustez da engine.
        """
        # Coleta de informações do estado do jogo
        bot_info = next((j for j in estado_do_jogo['jogadores'] if j['id'] == self.jogador_id), None)
        if not bot_info: return ""

        tropas_na_base = bot_info['tropas_na_base']
        minha_base_id = f"base_{self.jogador_id}"                 
        lista_de_cidades = estado_do_jogo['mapa']['cidades']
        
        # O resto do código agora usa a 'lista_de_cidades' que encontramos no lugar certo
        cidades_minhas = [c['id'] for c in lista_de_cidades if c['dono'] == self.jogador_id]
        cidades_neutras = [c for c in lista_de_cidades if c['dono'] is None]
        meu_transporte = next((t for t in estado_do_jogo['transportes'] if t['dono'] == self.jogador_id), None)

        # Preparação das Ordens
        ordens_tropas_str = "Novas Tropas:\n"
        ordens_transporte_str = "Transporte:\n"

        # Decisão de Tropa
        if random.random() < 0.5 and tropas_na_base >= 10 and cidades_neutras:
            self.contador_tropas += 1
            id_nova_tropa = f"{self.jogador_id}_{self.contador_tropas}"
            limite_superior_forca = max(10, int(tropas_na_base / 2) + 1)
            forca = random.randint(10, limite_superior_forca)
            alvo = random.choice(cidades_neutras)
            ordens_tropas_str += f"{id_nova_tropa} {forca}: {minha_base_id} -> ataca {alvo['id']}\n"

        # Decisão de Transporte
        if meu_transporte and meu_transporte['estado'] == 'ocioso' and random.random() < 0.5: # 50% de chance de usar o transporte
            
            cidades_para_coleta = []
                        
            # Com uma pequena chance, a IA vai tentar a ação "impossível" de coletar de uma cidade neutra.
            if cidades_neutras and random.random() < 0.2: # 20% de chance de tentar a ação de teste
                cidade_alvo_teste = random.choice(cidades_neutras)
                if cidade_alvo_teste['populacao'] > 0:
                    print(f"IA {self.jogador_id} está TENTANDO AÇÃO DE TESTE: coletar da cidade neutra {cidade_alvo_teste['id']}.")
                    cidades_para_coleta.append(cidade_alvo_teste['id'])
            
            # Lógica principal: sempre adiciona as cidades válidas à lista de possibilidades
            for cidade_id in cidades_minhas:
                if "base" not in cidade_id:
                    for c_info in estado_do_jogo['cidades']:
                        if c_info['id'] == cidade_id and c_info['populacao'] > 0:
                            cidades_para_coleta.append(cidade_id)
            
            if cidades_para_coleta:
                cidade_origem = random.choice(cidades_para_coleta)
                ordens_transporte_str += f"missao: COLETAR MAX DE {cidade_origem}, ENTREGAR EM {minha_base_id}\n"

        # Retorna as ordens da base
        return ordens_tropas_str + "\n" + ordens_transporte_str