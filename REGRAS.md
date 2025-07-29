# Simulador de Conquista e Estratégia: Manual Oficial (v1.0)

*Última atualização: 29 de Julho de 2025, 18:33*

## 1\. Descrição Geral

Bem-vindo ao Simulador de Conquista e Estratégia\! Este é um jogo de guerra por turnos onde a vitória é forjada tanto pela força militar quanto pela supremacia econômica e logística. Os jogadores devem expandir seus impérios, gerenciar uma rede de suprimentos custosa e alimentar uma máquina de guerra que converte população em poderio militar. A estratégia está no planejamento de ordens que se desdobrarão ao longo de múltiplos turnos.

## 2\. Condições de Vitória e Derrota

  * **Vitória:** Ocorre quando:
      * Capturar a Base de um oponente.
      * Ser o jogador com mais cidades conquistadas ao fim do máximo de turnos (critério de desempate).
  * **Derrota:** Ocorre quando:
      * Sua Base é capturada.
      * O número de tropas na sua Base chega a zero (A Base funciona como os "Pontos de Vida" do jogador).

## 3\. A Estrutura do Turno

O turno funciona como um movimento anunciado no Xadrez: primeiro se declaram todas as ações, depois elas são executadas passo a passo, simultaneamente.

  * **Fase de Ordens:** Jogadores enviam ordens para suas Tropas e seu Transporte.
  * **Fase de Execução:** Todas as unidades no mapa executam um passo das ordens recebidas.
  * **Fase de Custo:** Os custos de manutenção das rotas são calculados e debitados da Base.

> Ordens são **imutáveis**, salvo exceções explícitas acionadas pela engine (ex: recuo forçado por uma penalidade).

## 4\. Posse e Suprimento

Para manter o controle de uma cidade, **duas condições** devem ser atendidas a cada turno:

1.  **Ocupação Militar:** Ao menos 1 Tropa deve estar estacionada na cidade. Se a última tropa sair, a cidade se torna Neutra.
2.  **Rede de Suprimentos:** A cidade deve ter um caminho contínuo até a sua Base.
      * **Custo:** `Peso da Aresta / 100` tropas, debitado da Base a cada turno.
      * **Isolamento:** Se uma cidade ficar isolada da Base (ex: um ponto de estrangulamento na rota é capturado), ela se torna Neutra e as tropas nela são perdidas.

## 5\. Ações e Combate

### 5.1. Tropas

#### Tipos de Ataque

  * **Atacando Cidade Neutra:** A defesa da cidade é igual à sua **População**. Se a `Força da Tropa >= População`, a cidade é conquistada.
  * **Atacando Cidade Inimiga:** A defesa é a **Força da Tropa inimiga** estacionada. O combate é direto (1v1). O vencedor sobrevive com sua força reduzida pela força total do exército derrotado.

#### Penalidade de 50%

A perda de 50% da força do atacante **NÃO** é uma regra de combate geral. Ela se aplica apenas a dois casos específicos e punitivos:

  * Ataque direto à **Base Inimiga**.
  * Tentar `Permanecer` em uma cidade inimiga guarnecida sem ter vencido um combate prévio.

#### Comandos e Comportamentos

  * **`Atacar -> Permanecer`:** Conquista e ocupa a cidade com a tropa sobrevivente.
  * **`Atacar` (Raid):** A tropa sobrevivente retorna automaticamente à Base após o ataque.
  * **`Recuar`:** Tropas estacionadas recebem ordem para retornar à Base. Este comando **IGNORA o custo de capacidade (`peso`)** da aresta.

### 5.2. Transporte

  * Sua função principal é levar População à Base para **conversão em Tropas**.
  * Pode também levar População a outra cidade para fortificá-la (sujeito a penalidades).
  * **Rota em Cidade Neutra:** A missão falha. O Transporte perde **10%** da sua carga para a cidade neutra e retorna à Base com os 90% restantes (que são convertidos).
  * **Rota em Cidade Inimiga:** O Transporte é **destruído**. A carga é capturada pelo inimigo. O Transporte reaparece na Base após 1 turno de penalidade.

## 6\. Comunicação com a IA

### Entrada para a IA

A cada turno, cada IA recebe um **dicionário Python** contendo o estado completo e atual do jogo, além do objeto `Mapa` para consultas.

  * `estado_do_jogo`: Dicionário com `turno_atual`, `jogadores`, `cidades`, `tropas_em_campo`, etc.
  * `mapa`: Objeto da classe `Mapa`, que permite usar métodos úteis como `mapa.encontrar_caminho_bfs()`.

### Formato de Saída Esperada da IA

A IA deve retornar uma **única string de texto** com suas ordens para o turno, seguindo o formato abaixo.

```text
Novas Tropas:
# Formato: <id_da_tropa> <forca_desejada>: <rota>
j0_1 120: base_j0 -> c1_0 -> ataca c_meio
j0_2 50: base_j0 -> c2_0

Transporte:
# Formato: missao: COLETAR <qtd|MAX> DE <origem>, ENTREGAR EM <destino>
missao: COLETAR 50 DE c1_0, ENTREGAR EM base_j0
missao: COLETAR MAX DE c2_0, ENTREGAR EM c1_0
```

### Como a Saída da IA será Interpretada pelo Parser

A engine traduzirá as ordens em texto para uma estrutura de dados interna (fila de comandos) para cada unidade.

  * **Dicionário de uma Tropa:**

    ```python
    tropa.fila_de_comandos = [
        {'tipo': 'MOVER', 'alvo': 'c1_0'},
        {'tipo': 'ATACAR', 'alvo': 'c_meio'},
        {'tipo': 'PERMANECER'} 
    ]
    ```

  * **Dicionário do Transporte:**

    ```python
    transporte.fila_de_comandos = [
        {'tipo': 'COLETAR', 'alvo': 'c1_0', 'quantidade': 50},
        {'tipo': 'ENTREGAR', 'alvo': 'base_j0'}
    ]
    ```

## 7\. Desenvolvendo sua IA

Para que sua IA seja compatível com o simulador, ela deve seguir um "contrato" simples, implementado através de uma classe base.

### Passo 1: Crie o Arquivo `ia_interface.py`

Este arquivo define a estrutura que toda IA deve ter.

```python
from abc import ABC, abstractmethod

class IAInterface(ABC):
    """
    Classe base (Interface) que todas as IAs devem herdar.
    Ela define o "contrato" de como o Simulador vai interagir com um bot.
    """
    
    @abstractmethod
    def __init__(self, jogador_id):
        """Inicializa a IA com a identificação do jogador que ela controlará."""
        self.jogador_id = jogador_id

    @abstractmethod
    def decidir_acoes(self, estado_do_jogo, mapa):
        """
        O método principal da IA. Recebe o estado atual do jogo e o mapa,
        e deve retornar uma string de texto com as ordens.
        """
        pass
```

### Passo 2: Crie o Arquivo da Sua IA

Crie um novo arquivo (ex: `meu_bot.py`) e crie sua classe herdando de `IAInterface`.

```python
# Em meu_bot.py
from ia_interface import IAInterface

class MeuBot(IAInterface):
    def __init__(self, jogador_id):
        super().__init__(jogador_id)
        # Você pode inicializar variáveis de estratégia aqui
        self.contador_tropas = 0

    def decidir_acoes(self, estado_do_jogo, mapa):
        """
        Esta é a função que você deve implementar com a lógica do seu bot.
        Analise o 'estado_do_jogo' e use as ferramentas do 'mapa' para tomar decisões.
        """
        # Exemplo de lógica simples:
        ordens_tropas = "Novas Tropas:\n"
        
        # Lógica para encontrar minhas informações no estado do jogo
        minhas_tropas_na_base = 0
        for jogador in estado_do_jogo['jogadores']:
            if jogador['id'] == self.jogador_id:
                minhas_tropas_na_base = jogador['tropas_na_base']
        
        # Se eu tiver recursos, crio uma tropa e a envio para a cidade neutra mais próxima
        if minhas_tropas_na_base >= 10:
            self.contador_tropas += 1
            id_nova_tropa = f"{self.jogador_id}_{self.contador_tropas}"
            # Lógica para encontrar um alvo (ex: a primeira cidade neutra)
            alvo = "c1_0" # Simplificação, aqui entraria sua lógica de alvo
            ordens_tropas += f"{id_nova_tropa} 10: base_{self.jogador_id} -> ataca {alvo}\n"

        ordens_transporte = "Transporte:\n# Nenhuma ordem de transporte por enquanto"
        
        # Retorna a string de ordens completa
        return ordens_tropas + "\n" + ordens_transporte
```

### Passo 3: Adicione sua IA ao Simulador

No arquivo `simulador.py` principal, importe sua classe e adicione-a ao dicionário de competidores.

```python
# Em simulador.py
# ... outros imports
from meu_bot import MeuBot
from outro_bot import OutroBot

if __name__ == "__main__":
    # ...
    competidores = {
        'j0': MeuBot,
        'j1': OutroBot 
    }
    # ...
```
