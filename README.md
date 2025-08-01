# Simulador de Conquista e Estratégia — Manual Oficial (v1.02)

*Última atualização: 1 de agosto de 2025, 00:30*

---

## 1. Visão Geral

Bem-vindo ao **Simulador de Conquista e Estratégia**, um jogo de guerra por turnos que exige domínio tanto militar quanto econômico-logístico. Os jogadores devem expandir seus impérios, gerenciar cadeias de suprimento e alimentar uma máquina de guerra capaz de converter população em poderio militar. A vitória depende de planejamento estratégico, com ordens que se desdobram ao longo de múltiplos turnos.

---

## 2. Condições de Vitória e Derrota

* **Vitória:**

  * Captura da Base inimiga.
  * Maior número de cidades controladas ao final do limite máximo de turnos (critério de desempate).

* **Derrota:**

  * Perda da Base para o inimigo.
  * Redução do número de tropas na Base para zero (a Base funciona como "pontos de vida" do jogador).

---

## 3. Estrutura do Turno

Cada turno é composto por três fases principais, executadas de forma sincronizada após o recebimento de ordens:

1. **Fase de Ordens:** Cada jogador envia comandos para suas Tropas e unidades de Transporte.
2. **Fase de Execução:** Todas as unidades executam simultaneamente um passo de suas ordens.
3. **Fase de Custo:** O custo de manutenção das rotas é calculado e debitado da Base.

> ⚠️ As ordens são **imutáveis**, salvo em casos excepcionais determinados pela engine (ex: recuo forçado por penalidade).

---

## 4. Controle Territorial e Suprimentos

Para manter o controle de uma cidade, duas condições devem ser atendidas **a cada turno**:

1. **Ocupação Militar:** Ao menos 1 Tropa deve permanecer na cidade. Caso contrário, ela se torna Neutra.
2. **Conexão Logística:** A cidade deve estar conectada à Base por uma rota contínua.

   * **Custo logístico:** `Peso da aresta / 100` tropas, descontadas da Base por turno.
   * **Isolamento:** Cidades isoladas da Base se tornam Neutras, e suas Tropas são perdidas.

---

## 5. Ações e Combate

### 5.1 Tropas

#### Tipos de Ataque

* **Contra Cidade Neutra:** A defesa equivale à **população** da cidade. Se `Força da Tropa ≥ População`, a cidade é conquistada.
* **Contra Cidade Inimiga:** A defesa corresponde à **força da Tropa inimiga** na cidade. O combate é direto (1v1) e o vencedor permanece com força reduzida.

#### Penalidade de 50%

A redução de 50% na força do atacante aplica-se **apenas** às situações:

* Ataque direto à **Base inimiga**.
* Tentativa de `Permanecer` em cidade inimiga **sem vitória prévia em combate**.

#### Comandos e Comportamentos

* `Atacar -> Permanecer`: Conquista e ocupa a cidade com a tropa sobrevivente.
* `Atacar` (modo incursão): A tropa retorna automaticamente à Base após o ataque.
* `Recuar`: Tropas estacionadas retornam à Base. Este comando **ignora restrições de peso** da aresta.

---

### 5.2 Transporte

* A principal função do Transporte é transferir **população** para a Base, para conversão em Tropas.
* Também pode reforçar cidades com população (sujeito a penalidades).
* **Falha em cidade Neutra:** Missão falha, 10% da carga é perdida e os 90% restantes retornam à Base e são convertidos.
* **Falha em cidade Inimiga:** Transporte é **destruído**, a carga é capturada pelo inimigo. A unidade retorna à Base após 1 turno de penalidade.

---

## 6. Integração com Inteligência Artificial (IA)

### Entrada de Dados para a IA

A cada turno, cada IA recebe:

* `estado_do_jogo`: Dicionário contendo o turno atual, dados dos jogadores, cidades, tropas em campo etc.
* `mapa`: Objeto da classe `Mapa` com acesso a `mapa.get_cidades()`,`mapa.get_arestas()`,`mapa.get_lista_adjacencia()`.

### Formato de Saída da IA

A IA deve retornar uma **string única** com as ordens do turno no formato abaixo:

```text
Novas Tropas:
# Formato: <id_da_tropa> <forca>: <rota>
j0_1 120: base_j0 -> c1_0 -> ataca c_meio
j0_2 50: base_j0 -> c2_0

Transporte:
# Formato: missao: COLETAR <qtd|MAX> DE <origem>, ENTREGAR EM <destino>
missao: COLETAR 50 DE c1_0, ENTREGAR EM base_j0
missao: COLETAR MAX DE c2_0, ENTREGAR EM c1_0
```

### Interpretação da Saída pela Engine

As ordens são traduzidas para filas de comandos internas:

* **Exemplo — Tropa:**

```python
tropa.fila_de_comandos = [
    {'tipo': 'MOVER', 'alvo': 'c1_0'},
    {'tipo': 'ATACAR', 'alvo': 'c_meio'},
    {'tipo': 'PERMANECER'}
]
```

* **Exemplo — Transporte:**

```python
transporte.fila_de_comandos = [
    {'tipo': 'COLETAR', 'alvo': 'c1_0', 'quantidade': 50},
    {'tipo': 'ENTREGAR', 'alvo': 'base_j0'}
]
```

---

## 7. Desenvolvendo sua IA

Para compatibilidade com o simulador, sua IA deve implementar a interface a seguir.

### Passo 1 — Criar o arquivo `ia_interface.py`

```python
from abc import ABC, abstractmethod

class IAInterface(ABC):
    """
    Interface que define a estrutura base para bots do simulador.
    """

    @abstractmethod
    def __init__(self, jogador_id):
        """Inicializa a IA com o ID do jogador."""
        self.jogador_id = jogador_id

    @abstractmethod
    def decidir_acoes(self, estado_do_jogo, mapa):
        """
        Método principal da IA. Deve retornar uma string com as ordens do turno.
        """
        pass
```

### Passo 2 — Criar o arquivo da IA

```python
# Exemplo: meu_bot.py
from ia_interface import IAInterface

class MeuBot(IAInterface):
    def __init__(self, jogador_id):
        super().__init__(jogador_id)
        self.contador_tropas = 0

    def decidir_acoes(self, estado_do_jogo, mapa):
        ordens_tropas = "Novas Tropas:\n"
        tropas_disponiveis = next(j for j in estado_do_jogo['jogadores'] if ['id'] == self.jogador_id)['tropas_na_base']

        if tropas_disponiveis >= 10:
            self.contador_tropas += 1
            id_tropa = f"{self.jogador_id}_{self.contador_tropas}"
            alvo = "c1_0"  # Exemplo simplificado
            ordens_tropas += f"{id_tropa} 10: base_j{self.jogador_id} -> ataca {alvo}\n"

        ordens_transporte = "Transporte:\n# Nenhuma ordem de transporte por enquanto"

        return ordens_tropas + "\n" + ordens_transporte
```

### Passo 3 — Registrar sua IA no Simulador

```python
# Em simulador.py
from meu_bot import MeuBot
from outro_bot import OutroBot

if __name__ == "__main__":
    competidores = {
        '0': MeuBot,
        '1': OutroBot
    }
```