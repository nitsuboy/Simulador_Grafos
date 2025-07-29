from engine import Jogo, Jogador, Tropa, Transporte 
import parser 
from ias.ia_interface import IAInterface
from ias.ia_perseus import Perseus # Exemplo de import de uma IA personalizada

class Simulador:
    def __init__(self, mapa_json_path, bots, turno_maximo=50):
        """
        Inicializa o simulador.
        :param mapa_json_path: Caminho para o arquivo JSON do mapa.
        :param bots: Dicionário mapeando ID de jogador para a CLASSE da IA.
                     Ex: {'j0': IADummy, 'j1': IABotOutro}
        """
        print("--- Inicializando o Simulador ---")
        self.jogo = Jogo()
        self.jogo.turno_maximo = turno_maximo  # Define o número máximo de turnos
        self.jogo.carregar_mundo(mapa_json_path)
        self.ias = {} # Dicionário para armazenar as instâncias das IAs
        
        # Cria os jogadores e instancia as IAs
        for i, (jogador_id, classe_ia) in enumerate(bots.items()):
            base_id = f"base_j{i}" 
            
            jogador = Jogador(id=jogador_id, id_base=base_id)
            self.jogo.jogadores[jogador_id] = jogador
            if base_id in self.jogo.mapa.cidades:
                self.jogo.mapa.cidades[base_id].dono = jogador.id
            
            self.ias[jogador_id] = classe_ia(jogador_id)
            print(f"Jogador '{jogador_id}' criado e controlado por '{classe_ia.__name__}'.")
        
        print("Simulador inicializado.")

    def _preparar_turno(self, todas_as_ordens):
        """Valida e injeta as ordens dos bots no estado do jogo."""
        for jogador_id, ordens in todas_as_ordens.items():
            jogador = self.jogo.jogadores[jogador_id]

            # Injeta ordens de novas tropas de forma segura
            for ordem_tropa in ordens.get("novas_tropas", []):
                forca_desejada = ordem_tropa['forca']
                if jogador.tropas_na_base >= forca_desejada:
                    jogador.tropas_na_base -= forca_desejada
                    nova_tropa = Tropa(
                        id=ordem_tropa['id'], dono=jogador,
                        forca=forca_desejada, fila_de_comandos=ordem_tropa['comandos']
                    )
                    jogador.tropas.append(nova_tropa)
                    print(f"Jogador {jogador_id}: Nova tropa {nova_tropa.id} (Força: {forca_desejada}) criada.")
                else:
                    print(f"AVISO: Jogador {jogador_id} com poucas tropas para criar {ordem_tropa['id']}. Ordem ignorada.")

            # Injeta ordens do transporte
            ordem_transporte = ordens.get("transporte")
            if ordem_transporte:
                jogador.transporte.fila_de_comandos = ordem_transporte
                comando_coleta = ordem_transporte[0] 
                jogador.transporte.quantidade_solicitada = comando_coleta.get('quantidade', 'MAX')

    def run(self):
        """Roda a simulação completa do jogo."""
        print("\n--- INICIANDO SIMULAÇÃO ---")
        while True:
            # Verifica se o jogo deve terminar antes de solicitar novas ordens
            vencedor = self.jogo.verificar_vencedor()
            if vencedor or self.jogo.turno_atual >= self.jogo.turno_maximo:
                break

            # Gera o estado do jogo (pode salvar, se necessário)
            estado_do_jogo_atual = self.jogo.gerar_estado_json(
                f"estado_turno_{self.jogo.turno_atual}.json", 
                salvar_arquivo=True # Mantenha True se desejar debugar estados intermediários
            )
            
            # Coleta as ordens de todos os jogadores
            ordens_parseadas = {}
            for jogador_id, ia_obj in self.ias.items():
                if jogador_id not in self.jogo.jogadores_derrotados:
                    print(f"--- Vez do Jogador {jogador_id} ({ia_obj.__class__.__name__}) ---")
                    ordens_em_texto = ia_obj.decidir_acoes(estado_do_jogo_atual, self.jogo.mapa)
                    # O parser traduz o comando que a IA retorna em um formato que o simulador entende
                    ordens_parseadas[jogador_id] = parser.parse_string_de_ordens(ordens_em_texto)

            self._preparar_turno(ordens_parseadas)
            self.jogo.processar_turno() 
        
        print("\n--- SIMULAÇÃO ENCERRADA ---")
        self.jogo.verificar_vencedor(anunciar_fim=True)


if __name__ == "__main__":
    # Parâmetros de inicialização do simulador
    mapa_path = "src\\mapa.json" 
    turno_maximo = 10  # Define o número máximo de turnos
    
    # Define as IAs competidoras
    bots = {
        'j0': Perseus,
        'j1': Perseus
    }

    # Inicia a simulação
    simulador = Simulador(mapa_json_path=mapa_path, bots=bots, turno_maximo=turno_maximo)
    simulador.run()