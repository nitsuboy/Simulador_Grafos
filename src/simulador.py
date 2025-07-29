from engine import Jogo, Jogador, Tropa

# Gerado pelo Gemini 2.5 PRO

class Simulador:
    def __init__(self, mapa_json_path, jogadores_info):
        """
        Inicializa o simulador.
        :param mapa_json_path: Caminho para o arquivo JSON do mapa.
        :param jogadores_info: Lista de dicionários, ex: [{'id': 'j0', 'base_id': 'base_j0'}, ...]
        """
        print("Inicializando o Simulador...")
        self.jogo = Jogo()
        self.jogo.carregar_mundo(mapa_json_path)
        
        # Cria os jogadores na engine
        for info in jogadores_info:
            jogador = Jogador(id=info['id'], id_base=info['base_id'])
            self.jogo.jogadores[jogador.id] = jogador
            # Define o dono inicial da base
            if info['base_id'] in self.jogo.mapa.cidades:
                self.jogo.mapa.cidades[info['base_id']].dono = jogador.id
        
        print("Simulador inicializado. Jogadores e mapa carregados.")

    def _ler_e_parsear_ordens(self, jogador_id):
        """Lê e traduz o arquivo de ordens de um jogador."""
        ordens = {"novas_tropas": [], "transporte": None}
        nome_arquivo = f"ordens_{jogador_id}.txt"
        
        try:
            with open(nome_arquivo, 'r', encoding='utf-8') as f:
                secao_atual = None
                for linha in f:
                    linha = linha.strip()
                    if not linha or linha.startswith('#'): continue
                    
                    if "Novas Tropas:" in linha: secao_atual = "TROPAS"
                    elif "Transporte:" in linha: secao_atual = "TRANSPORTE"
                    else:
                        if secao_atual == "TROPAS":
                            partes = linha.split(':')
                            info_tropa, rota_str = partes[0], partes[1]
                            id_tropa = info_tropa.split()[1]
                            
                            comandos = []
                            for passo in rota_str.split('->'):
                                partes_passo = passo.strip().split()
                                comando = partes_passo[0]
                                if comando == 'ataca':
                                    comandos.append({'tipo': 'ATACAR', 'alvo': partes_passo[1]})
                                elif comando == 'permanece':
                                    comandos.append({'tipo': 'PERMANECER'})
                                elif comando == 'recua':
                                    comandos.append({'tipo': 'RECUAR'})
                                else:
                                    comandos.append({'tipo': 'MOVER', 'alvo': comando})

                            # TODO: Definir força da tropa pela entrada do bot
                            # Aqui, vamos assumir uma força padrão de 100 para simplificar
                            ordens["novas_tropas"].append({'id': id_tropa, 'forca': 100, 'comandos': comandos})

                        elif secao_atual == "TRANSPORTE":
                            partes = linha.split(':')
                            rota_str = partes[1].strip()
                            passos = [p.strip() for p in rota_str.split('->')]
                            if len(passos) >= 2:
                                # A ordem é ir de 'passos[1]' para 'passos[-1]'
                                # A quantidade é sempre o máximo da cidade de origem
                                ordens["transporte"] = {'origem': passos[1], 'destino': passos[-1], 'quantidade': 'MAX'}
        except FileNotFoundError:
            print(f"AVISO: Arquivo de ordens '{nome_arquivo}' não encontrado. O jogador {jogador_id} não fará nada.")
        
        return ordens

    def _preparar_turno(self, todas_as_ordens):
        """Valida e injeta as ordens dos bots no estado do jogo."""
        print("\n--- Preparando o Turno: Validando e Injetando Ordens ---")
        for jogador_id, ordens in todas_as_ordens.items():
            jogador = self.jogo.jogadores[jogador_id]

            # Injeta ordens de novas tropas
            for ordem_tropa in ordens["novas_tropas"]:
                # Validação: O jogador tem tropas na base para criar esta unidade?
                if jogador.tropas_na_base >= ordem_tropa['forca']:
                    jogador.tropas_na_base -= ordem_tropa['forca']
                    nova_tropa = Tropa(
                        id=ordem_tropa['id'],
                        dono=jogador,
                        forca=ordem_tropa['forca'],
                        fila_de_comandos=ordem_tropa['comandos']
                    )
                    jogador.tropas.append(nova_tropa)
                    print(f"Jogador {jogador_id}: Nova tropa {nova_tropa.id} criada. Tropas restantes na base: {jogador.tropas_na_base:.0f}")
                else:
                    print(f"AVISO: Jogador {jogador_id} não tem tropas suficientes na base para criar a tropa {ordem_tropa['id']}. Ordem ignorada.")

            # Injeta ordens do transporte
            if ordens["transporte"]:
                # Só pode haver uma ordem de transporte por vez
                jogador.transporte.fila_de_comandos = [ordens["transporte"]]


    def run(self):
        """O loop principal que roda a simulação completa."""
        while True:
            # Gera o estado atual para os bots lerem
            self.jogo.gerar_estado_json(f"estado_turno_{self.jogo.turno_atual}.json")
            
            # Coleta as ordens de todos os jogadores
            todas_as_ordens = {}
            for jogador_id in self.jogo.jogadores:
                if jogador_id not in self.jogo.jogadores_derrotados:
                    # TODO: Implementar uma função para ler ordens de bots
                    print(f"Aguardando ordens do jogador {jogador_id}...")
                    todas_as_ordens[jogador_id] = self._ler_e_parsear_ordens(jogador_id)
            
            # Prepara o turno, validando e criando as unidades com base nas ordens
            self._preparar_turno(todas_as_ordens)

            # Processa o turno na engine
            vencedor = self.jogo.processar_turno() # Retorna o id do vencedor ou None

            # 5. Verifica se o jogo acabou
            if vencedor:
                print(f"\nSIMULAÇÃO ENCERRADA. O VENCEDOR É O JOGADOR {vencedor}!")
                break
            
            if self.jogo.turno_atual >= self.jogo.turno_maximo:
                print("\nSIMULAÇÃO ENCERRADA POR LIMITE DE TURNOS.")
                break

if __name__ == "__main__":
    # Informações da partida
    mapa_path = "mapa.json" # O mapa gerado pelo gerador de tabuleiro
    jogadores_info = [
        {'id': 'j0', 'base_id': 'base_j0'},
        {'id': 'j1', 'base_id': 'base_j1'}
    ]

    # Cria e roda o simulador
    simulador = Simulador(mapa_json_path=mapa_path, jogadores_info=jogadores_info)
    simulador.run()