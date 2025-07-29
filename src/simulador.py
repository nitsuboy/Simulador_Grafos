from engine import Jogo, Jogador, Tropa
import parser 

class Simulador:
    def __init__(self, mapa_json_path, jogadores_info):
        """
        Inicializa o simulador.
        """
        print("Inicializando o Simulador...")
        self.jogo = Jogo()
        self.jogo.carregar_mundo(mapa_json_path)
        
        # Cria os jogadores na engine
        for info in jogadores_info:
            jogador = Jogador(id=info['id'], id_base=info['base_id'])
            self.jogo.jogadores[jogador.id] = jogador
            if info['base_id'] in self.jogo.mapa.cidades:
                self.jogo.mapa.cidades[info['base_id']].dono = jogador.id
        
        print("Simulador inicializado. Jogadores e mapa carregados.")

    def _preparar_turno(self, todas_as_ordens):
        """Valida e injeta as ordens dos bots no estado do jogo."""
        print("\n--- Preparando o Turno: Validando e Injetando Ordens ---")
        for jogador_id, ordens in todas_as_ordens.items():
            jogador = self.jogo.jogadores[jogador_id]

            # Injeta ordens de novas tropas
            for ordem_tropa in ordens["novas_tropas"]:
                forca_desejada = ordem_tropa['forca']
                
                # Validação: O jogador tem tropas na base para criar esta unidade?
                if jogador.tropas_na_base >= forca_desejada:
                    jogador.tropas_na_base -= forca_desejada
                    nova_tropa = Tropa(
                        id=ordem_tropa['id'],
                        dono=jogador,
                        forca=forca_desejada,
                        fila_de_comandos=ordem_tropa['comandos']
                    )
                    jogador.tropas.append(nova_tropa)
                    print(f"Jogador {jogador_id}: Nova tropa {nova_tropa.id} (Força: {forca_desejada}) criada.")
                else:
                    print(f"AVISO: Jogador {jogador_id} não tem tropas suficientes na base para criar {ordem_tropa['id']}. Ordem ignorada.")

            # Injeta ordens do transporte
            if ordens["transporte"]:
                # Insere a ordem de transporte no jogador
                jogador.transporte.fila_de_comandos = ordens["transporte"]
                # A quantidade solicitada precisa ser guardada no objeto transporte
                comando_coleta = ordens["transporte"][0] 
                jogador.transporte.quantidade_solicitada = comando_coleta.get('quantidade', 'MAX')


    def run(self):
        """O loop principal que roda a simulação completa."""
        while True:
            # Verifica se o jogo deve terminar antes de solicitar novas ordens
            vencedor_check = self.jogo.verificar_vencedor()
            if vencedor_check or self.jogo.turno_atual >= self.jogo.turno_maximo:
                break

            # Gera o estado atual para os bots lerem
            self.jogo.gerar_estado_json(f"estado_turno_{self.jogo.turno_atual}.json")
            
            # Coleta as ordens de todos os jogadores
            todas_as_ordens = {}
            for jogador_id, jogador in self.jogo.jogadores.items():
                if jogador_id not in self.jogo.jogadores_derrotados:
                    # Em uma simulação real, aqui você chamaria o script do bot
                    print(f"Lendo ordens do jogador {jogador_id}...")
                    todas_as_ordens[jogador_id] = parser.parse_ordens_jogador(jogador_id)
            
            # Prepara o turno, validando e criando as unidades com base nas ordens
            self._preparar_turno(todas_as_ordens)

            # Processa o turno na engine
            self.jogo.processar_turno() 
        
        print("\nFim de jogo.")
        # Verifica se há um vencedor e anuncia o fim do jogo
        self.jogo.verificar_vencedor(anunciar_fim=True)


if __name__ == "__main__":
    # Parâmetros do jogo
    mapa_path = "mapa.json"
    jogadores_info = [
        {'id': 'j0', 'base_id': 'base_j0'},
        {'id': 'j1', 'base_id': 'base_j1'}
    ]

    # Cria e roda o simulador
    simulador = Simulador(mapa_json_path=mapa_path, jogadores_info=jogadores_info)
    simulador.run()