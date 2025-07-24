# Conquista e Sobrevivência

Jogo estratégico baseado em grafos onde dois jogadores competem utilizando suas próprias IAs.

## 🎯 Objetivo

Cada jogador deve conquistar e manter o maior número de cidades possíveis utilizando estratégias baseadas em algoritmos de grafos. O jogo termina quando:

- Um jogador perde sua base, ou
- O número máximo de rodadas é atingido.

## 🗺️ Estrutura do Tabuleiro

- Grafo simples e conexo com cidades (vértices) e estradas (arestas).
- Cada cidade tem uma população.
- Cada aresta tem uma capacidade máxima de tropas (não implementado na versão base).
- Os jogadores começam com uma base conectada à camada inicial.

> [!NOTE]  
> é necessario mais algumas regras de criação para fazer o jogo justo aos dois lados quando o tabuleiro for gerado:
> Simetria parcial, Controle populacional e de distância, Progressão estratégica

## 🔄 Turnos

O jogo é jogado por turnos. Cada turno representa o deslocamento de uma aresta e é processado da seguinte forma:

1. O jogo coleta as decisões das duas IAs.
2. Executa o movimento das tropas e transporte.
3. Atualiza o controle de cidades e rede de suprimentos.

## 🪖 Tropas

- Tropas são enviadas da base com uma **rota definida**.
- Só podem passar por cidades já conquistadas.
- Se entrarem em cidade inimiga:
  - Perdem 50% da força **antes** do combate.
- Se entrarem em cidade neutra:
  - Perdem 10% e **recuam automaticamente**.
- Tropas estacionadas só podem recuar.

## 🚚 Transporte de População

- Cada jogador possui **um único transporte**.
- Só pode atravessar cidades aliadas.
- Se entra em cidade neutra:
  - População foge para a cidade.
- Se entra em cidade inimiga:
  - Transporte é destruído e a população capturada.
- Movimento entre cidades leva 1 turno.

## 🔗 Rede de Suprimentos

Ao final de cada turno, o jogador deve decidir quais arestas manter. Cidades que perdem conexão com a base são **perdidas**.
> [!NOTE]  
> retornam ao neutro

## 🏆 Condições de Vitória

- **Vitória:** capturar a base inimiga.
- **Derrota:** perder a própria base.
- **Empate:** nenhuma base capturada até o final das rodadas.

> [!NOTE]  
> numero de cidades sobre o poder do jogador ao final pode ser contado como criterio de desempate

## 📥 Entrada para a IA

Cada IA recebe um dicionário com:
- Estado das cidades: quem controla e população.
- Tropas próprias: posição e rota.
- Transporte: localização e carga.
- Arestas ativas.

## 📤 Saída Esperada da IA

A IA deve retornar:

```python
{
  "novas_tropas": [
    # Exemplo:
    # {"rota": ["base", "c1", "c3"], "acao": "aguarda"},
    # {"rota": ["base", "c2", "c5"], "acao": "ataca"},
  ],
  "rota_transporte": [
    # Exemplo:
    # "base", "c3", "c7", "base"
  ],
  "manutencao": [
    # Exemplo:
    # ("c1", "c3"), ("c3", "c5")
  ]
}
