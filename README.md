# Simulador de Conquista e Estratégia: Manual Oficial

## 1. Descrição Geral

Bem-vindo ao Simulador de Conquista e Estratégia! Este é um jogo de guerra por turnos onde a vitória é forjada tanto pela força militar quanto pela supremacia econômica e logística. Os jogadores devem expandir seus impérios, gerenciar uma rede de suprimentos custosa e alimentar uma máquina de guerra que converte população em poderio militar. A estratégia está no planejamento de ordens que se desdobrarão ao longo de múltiplos turnos.

## 2. Condições de Vitória e Derrota

- **Vitória:** Ocorre quando:
  - Capturar a Base de um oponente.
  - Jogador com mais bases conquistadas ao fim do máximo de turnos
- **Derrota:** Ocorre quando:
  - Sua Base é capturada.
  - O número de tropas na sua Base chega a zero (Base = HP do jogador).

## 3. A Estrutura do Turno

O turno funciona como um movimento anunciado no Xadrez: primeiro se declaram todas as ações, depois elas são executadas simultaneamente.

- **Fase de Ordens:** Jogadores enviam ordens para Tropas e Transporte.
- **Fase de Execução:** Todas as unidades executam um passo das ordens anteriores.
- **Fase de Custo:** Os custos das rotas são calculados e debitados da Base.

> Ordens são **imutáveis**, salvo exceções explícitas como recuo forçado.

## 4. Posse e Suprimento

Para manter uma cidade:

- **Ocupação Militar:** Ao menos 1 Tropa deve estar estacionada.
- **Rede de Suprimentos:** Deve haver caminho contínuo até sua Base.
  - Custo: `Peso da Aresta / 100`, debitado da Base.
  - Se a cidade for isolada, ela se torna Neutra e tropas nela são perdidas.

## 5. Ações e Combate

### 5.1. Tropas

#### Tipos de Ataque

- **Cidade Neutra:** Defesa = População. Se Força da Tropa ≥ População, a cidade é conquistada.
- **Cidade Inimiga:** Defesa = Força da Tropa inimiga. Combate direto 1v1. Vencedor perde força equivalente à do derrotado.

#### Penalidade de 50%

Aplicável apenas a:

- Ataque direto à Base Inimiga.
- Tentar permanecer numa cidade inimiga guarnecida sem combate prévio.

#### Comportamentos

- **Atacar -> Permanecer:** Conquista e ocupa a cidade.
- **Atacar (Raid):** Retorna à Base após o ataque.
- **Recuar:** Tropas voltam à Base por ordem.

### 5.2. Transporte

- Transporta População à Base para conversão em Tropas.
- Pode levar População a outra cidade (sujeito a penalidades).
- **Falha em Cidade Neutra:** Perde 10% da carga, retorna à Base com 90%.
- **Falha em Cidade Inimiga:** Transporte destruído, carga capturada. Reaparece na Base após 1 turno.

## Entrada para a IA

Cada IA recebe:

- Estado das cidades (controle e população).
- Tropas próprias (posição e rota).
- Transporte (localização e carga).

## Formato de Saída Esperada da IA

```
Novas Tropas:
# Formato: <id_da_tropa> <forca_desejada>: <rota>
j0_1 120: base_j0 -> c1_0 -> ataca c_meio
j0_2 50: base_j0 -> c2_0

Transporte:
# Formato: rota: <passo> -> <acao_com_cidade> -> <acao_final_com_cidade>
rota: base_j0 -> coletar 50 em c1_0 -> entregar em base_j0
rota: base_j0 -> coletar MAX em c2_0 -> entregar em c1_0
rota: c1_0 -> entregar em c3_0 # Uma ordem simples de entrega da carga atual
```

## Como será interpretado pelo Parser
```
# Dicionário de uma tropa
tropa.fila_de_comandos = [
    {'tipo': 'MOVER', 'alvo': 'c1'},
    {'tipo': 'MOVER', 'alvo': 'c3'},
    {'tipo': 'ATACAR', 'alvo': 'c5'},
    {'tipo': 'PERMANECER'} 
]

# Dicionário do transporte
transporte.fila_de_comandos = [
    {'tipo': 'COLETAR', 'alvo': 'c3', 'quantidade': 50},
    {'tipo': 'ENTREGAR', 'alvo': 'c8'}
]
```