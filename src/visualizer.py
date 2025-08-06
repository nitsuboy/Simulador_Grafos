import pygame
import json
import os
import math
import re

# --- Constantes e Configurações Iniciais ---
WIDTH, HEIGHT = 1920, 1080
FPS = 60  # Aumentado para uma animação mais suave
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK_GREY = (30, 30, 30)

# --- Constantes de Cor ---
PLAYER_COLORS = [
    (0, 150, 255),  # Jogador 0 (Azul)
    (255, 150, 0),  # Jogador 1 (Laranja)
]
NEUTRAL_COLOR = (200, 200, 200)


# --- Funções Utilitárias ---
def draw_text_with_outline(surface, font, text, text_color, outline_color, pos, outline_width=1, alpha=255):
    text_surface = font.render(text, True, text_color)
    text_surface.set_alpha(alpha)  # Garante que o texto seja totalmente opaco
    outline_surface = font.render(text, True, outline_color)
    outline_surface.set_alpha(alpha)  # Garante que o contorno seja totalmente opaco
    text_rect = text_surface.get_rect(center=pos)

    for dx in range(-outline_width, outline_width + 1, outline_width):
        for dy in range(-outline_width, outline_width + 1, outline_width):
            if dx != 0 or dy != 0:
                outline_rect = outline_surface.get_rect(center=(pos[0] + dx, pos[1] + dy))
                surface.blit(outline_surface, outline_rect)
    surface.blit(text_surface, text_rect)

def lerp(v0, v1, t):
    """Interpolação linear entre dois valores."""
    return v0 + t * (v1 - v0)

def lerp_vector(v0, v1, t):
    """Interpolação linear entre dois vetores/tuplas."""
    return (lerp(v0[0], v1[0], t), lerp(v0[1], v1[1], t))

# --- Classes do Jogo ---

class AnimatedTroop:
    """Controla a animação de uma tropa individual."""
    def __init__(self, strength, owner_id, start_pos, end_pos, animation_duration,fade_out=False):
        self.strength = strength
        self.owner_id = owner_id
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.current_pos = start_pos
        self.animation_duration = animation_duration
        self.animation_timer = 0.0
        self.fade_out = fade_out  # Nova flag para desaparecer suavemente
        self.alpha = 255  # Opacidade inicial (255 = totalmente visível)

    def update(self, dt):
        """Atualiza o progresso da animação."""
        if self.animation_timer < self.animation_duration:
            self.animation_timer = min(self.animation_timer + dt, self.animation_duration)
            progress = self.animation_timer / self.animation_duration
            # Easing function (ease out) para uma animação mais suave no final
            t = 1 - (1 - progress) ** 3
            self.current_pos = lerp_vector(self.start_pos, self.end_pos, t)
            
            if self.fade_out:
                self.alpha = int(255 * (1 - progress))  # 255 → 0

    def draw(self, surface, font):
        """Desenha a tropa em sua posição animada atual."""
        temp_surface = pygame.Surface((100, 100), pygame.SRCALPHA)
        temp_surface = temp_surface.convert_alpha()
        
        color = PLAYER_COLORS[int(self.owner_id)]           
        faded_color = (*color, self.alpha)  # Adiciona transparência RGBA
        
        text_width, text_height = font.size(str(self.strength))
        radius = max(text_width, text_height) // 2 + 6

        pygame.draw.circle(temp_surface, faded_color, (50, 50), radius)
        pygame.draw.circle(temp_surface, (0, 0, 0, self.alpha), (50, 50), radius, 2)

        draw_text_with_outline(temp_surface, font, str(self.strength), WHITE, BLACK, (50, 50), 2,self.alpha)

        blit_pos = (self.current_pos[0] - 50, self.current_pos[1] - 50)
        surface.blit(temp_surface, blit_pos)

class City:
    def __init__(self, city_id, pos, population):
        self.id = city_id
        self.pos = pos
        self.population = population
        self.owner = None

        if 'basej_0' in self.id:
            self.owner = 0
        elif 'basej_1' in self.id:
            self.owner = 1

    def draw(self, surface, font):
        if self.owner is not None:
            color = PLAYER_COLORS[self.owner]
        else:
            color = NEUTRAL_COLOR

        self._draw_coin(surface, color, self.pos, 30, 8)
        
        pop_text = font.render(str(self.population), True, BLACK)
        pop_rect = pop_text.get_rect(center=self.pos)
        surface.blit(pop_text, pop_rect)

    def _draw_coin(self, surface, base_color, center, radius_x, height):
        radius_y = radius_x // 2 
        shadow_color = tuple(max(0, c - 50) for c in base_color)
        border_color = tuple(max(0, c - 80) for c in base_color)

        side_rect = pygame.Rect(center[0] - radius_x, center[1] - radius_y + height, 2 * radius_x, 2 * radius_y)
        pygame.draw.ellipse(surface, shadow_color, side_rect)
        pygame.draw.ellipse(surface, border_color, side_rect, 2)

        top_rect = pygame.Rect(center[0] - radius_x, center[1] - radius_y, 2 * radius_x, 2 * radius_y)
        pygame.draw.ellipse(surface, base_color, top_rect)
        pygame.draw.ellipse(surface, border_color, top_rect, 2)

class AnimatedTransport:
    """Representa a animação de um transporte."""
    def __init__(self, payload, owner, start_pos, end_pos, duration, fade_out=False):
        self.payload = payload
        self.owner = owner
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.current_pos = start_pos
        self.animation_duration = duration
        self.animation_timer = 0.0
        self.fade_out = fade_out
        self.alpha = 255

    def update(self, dt):
        if self.animation_timer < self.animation_duration:
            self.animation_timer = min(self.animation_timer + dt, self.animation_duration)
            progress = self.animation_timer / self.animation_duration
            t = 1 - (1 - progress) ** 3  # Easing out cúbico
            self.current_pos = lerp_vector(self.start_pos, self.end_pos, t)
            
            if self.fade_out:
                self.alpha = int(255 * (1 - progress))

    def draw(self, surface, font):
        if self.alpha == 0:
            return

        if self.owner is not None and self.owner < len(PLAYER_COLORS):
            color = PLAYER_COLORS[self.owner]
        else:
            color = NEUTRAL_COLOR
        shadow_color = tuple(max(0, c - 50) for c in color)
        border_color = tuple(max(0, c - 80) for c in color)
        
        size = 30  # Tamanho do quadrado
        rect = pygame.Rect(self.current_pos[0] - size / 2, self.current_pos[1] - size / 2, size, size)

        # Lógica para desenhar com transparência (fade-out)
        if self.fade_out:
            transport_surface = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.rect(transport_surface, (*shadow_color, self.alpha), (2, 2, size, size))
            pygame.draw.rect(transport_surface, (*color, self.alpha), (0, 0, size, size))
            pygame.draw.rect(transport_surface, (*border_color, self.alpha), (0, 0, size, size), 2)
            
            if self.payload > 0:
                text = font.render(str(self.payload), True, (*BLACK, self.alpha))
                text_rect = text.get_rect(center=(size / 2, size / 2))
                transport_surface.blit(text, text_rect)
            
            surface.blit(transport_surface, rect.topleft)
        else:
            pygame.draw.rect(surface, shadow_color, rect.move(2, 2))
            pygame.draw.rect(surface, color, rect)
            pygame.draw.rect(surface, border_color, rect, 2)
            
            if self.payload > 0:
                text = font.render(str(self.payload), True, BLACK)
                text_rect = text.get_rect(center=rect.center)
                surface.blit(text, text_rect)


class Map:
    def __init__(self, map_file='mapa_debug.json'):
        self.base_path = os.path.join(os.path.dirname(__file__), '..', 'estados')
        self.map_file = os.path.join(os.path.dirname(__file__), map_file)
        self.cities = {}
        self.edges = []
        self.animated_troops = []
        self.animated_transports = [] # <-- Armazena os transportes animados
        self._load_base_map()
        self.pending_animation = []  # Para armazenar animações pendentes
        self.animating = False
        
        self.city_font = pygame.font.SysFont(None, 28)
        self.edge_font = pygame.font.SysFont(None, 22)
        self.troop_font = pygame.font.SysFont(None, 24)

    def _load_base_map(self):
        with open(self.map_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.cities = {c['id']: City(c['id'], tuple(map(int, c['pos'])), c['populacao']) for c in data['cidades']}
        self.edges = [(a['de'], a['para'], a['peso']) for a in data['arestas']]
    def distribuir_tropas_em_circulo(city_pos, num_tropas, offset_radius=45):
        """Retorna posições em círculo ao redor de uma cidade."""
        posicoes = []
        for i in range(num_tropas):
            angle = (2 * math.pi / num_tropas) * i
            x = city_pos[0] + offset_radius * math.cos(angle)
            y = city_pos[1] + offset_radius * math.sin(angle)
            posicoes.append((x, y))
        return posicoes
    
    def _animar_transportes(self, state_origem, state_destino, animation_duration):
        """Compara os estados de transporte e cria as animações necessárias."""
        self.animated_transports.clear()
        transports_origem = {t['dono']: t for t in state_origem.get('transportes', [])}
        transports_destino = {t['dono']: t for t in state_destino.get('transportes', [])}

        for dono, transport_destino in transports_destino.items():
            transport_origem = transports_origem.get(dono)
            if not transport_origem:
                continue # Transporte novo, sem animação de movimento

            # Se a localização mudou, cria uma animação de movimento
            if transport_origem['localizacao'] != transport_destino['localizacao']:
                start_pos = self.cities[transport_origem['localizacao']].pos
                end_pos = self.cities[transport_destino['localizacao']].pos
                payload = transport_destino['carga_populacao']
                owner = int(transport_destino['dono'])
                
                # Animação de destruição
                fade_out = (transport_destino['estado'] == 'destruido')

                anim_transport = AnimatedTransport(payload, owner, start_pos, end_pos, animation_duration, fade_out=fade_out)
                self.animated_transports.append(anim_transport)


    def _animar_tropas_distribuidas(self, state_origem, state_destino, animation_duration):
        """Anima tropas entre dois estados e distribui elas em círculo com rotação suave."""
        
        # Salva última posição visual (antes da atualização)
        ultimas_posicoes = {getattr(t, "id", None): t.current_pos for t in getattr(self, 'animated_troops', []) if hasattr(t, "id")}

        if not state_origem.get("tropas_em_campo", []):
            print("Nenhuma tropa em campo para animar.")
            return
        
        self.animated_troops = []
        tropas_origem = {t["id"]: t for t in state_origem.get("tropas_em_campo", [])}
        tropas_destino = {t["id"]: t for t in state_destino.get("tropas_em_campo", [])}

        # Agrupar tropas destino por cidade
        tropas_por_cidade = {}
        for troop_id, troop_final in tropas_destino.items():
            cidade_id = troop_final["localizacao"]
            tropas_por_cidade.setdefault(cidade_id, []).append((troop_id, troop_final))

        for cidade_id, tropas in tropas_por_cidade.items():
            if cidade_id not in self.cities:
                continue

            city_pos = self.cities[cidade_id].pos
            num_tropas = len(tropas)
            radius = 45

            # Calcula posições finais em círculo
            posicoes_finais = [
                (
                    city_pos[0] + radius * math.cos((2 * math.pi / num_tropas) * i),
                    city_pos[1] + radius * math.sin((2 * math.pi / num_tropas) * i),
                )
                for i in range(num_tropas)
            ]

            # Distribuir tropas com transição suave
            for i, (troop_id, troop_final) in enumerate(tropas):
                dono = troop_final["dono"]
                forca = troop_final["forca"]
                destino_pos = posicoes_finais[i]

                # Origem: usa última posição visual, ou posição anterior, ou surge direto
                if troop_id in ultimas_posicoes:
                    origem_pos = ultimas_posicoes[troop_id]  # Rotação suave de posição
                elif troop_id in tropas_origem:
                    origem_id = tropas_origem[troop_id]["localizacao"]
                    origem_pos = self.cities[origem_id].pos if origem_id in self.cities else destino_pos
                else:
                    origem_pos = destino_pos  # tropa nova aparece direto na posição final

                # Cria AnimatedTroop com ID armazenado (para rastrear depois)
                troop = AnimatedTroop(forca, dono, origem_pos, destino_pos, animation_duration)
                troop.id = troop_id
                self.animated_troops.append(troop)

        # Tropas que sumiram: fade-out no local atual
        for troop_id, troop_inicio in tropas_origem.items():
            if troop_id not in tropas_destino:
                origem_pos = ultimas_posicoes.get(troop_id)
                if origem_pos is None:
                    origem_id = troop_inicio["localizacao"]
                    origem_pos = self.cities[origem_id].pos if origem_id in self.cities else (0, 0)
                troop = AnimatedTroop(troop_inicio["forca"], troop_inicio["dono"], origem_pos, origem_pos, animation_duration,fade_out=True)
                troop.id = troop_id
                self.animated_troops.append(troop)
    
    def _animar_tropas(self, state_origem, state_destino, animation_duration):
        """Anima tropas entre dois estados JSON."""
        self.animated_troops = []
        tropas_origem = {t["id"]: t for t in state_origem.get("tropas_em_campo", [])}
        tropas_destino = {t["id"]: t for t in state_destino.get("tropas_em_campo", [])}

        # Tropas que se movem ou permanecem
        for troop_id, troop_final in tropas_destino.items():
            dono, forca = troop_final["dono"], troop_final["forca"]
            destino_id = troop_final["localizacao"]
            destino_pos = self.cities[destino_id].pos if destino_id in self.cities else (0, 0)

            if troop_id in tropas_origem:
                origem_id = tropas_origem[troop_id]["localizacao"]
                origem_pos = self.cities[origem_id].pos if origem_id in self.cities else destino_pos
            else:
                origem_pos = destino_pos  # tropa nova aparece no destino

            self.animated_troops.append(
                AnimatedTroop(forca, dono, origem_pos, destino_pos, animation_duration)
            )

        # Tropas que sumiram (fade out)
        for troop_id, troop_inicio in tropas_origem.items():
            if troop_id not in tropas_destino:
                origem_id = troop_inicio["localizacao"]
                origem_pos = self.cities[origem_id].pos if origem_id in self.cities else (0, 0)
                self.animated_troops.append(
                    AnimatedTroop(troop_inicio["forca"], troop_inicio["dono"], origem_pos, origem_pos, animation_duration)
                )
    
    def prepare_turn_animation(self, turn_number, animation_duration):
        """Anima DC do turno anterior -> AC do turno atual -> DC do turno atual."""
        print(f"Preparando animação para o turno {turn_number}...")
        self.animating = True
        # Caso especial: turno inicial
        if turn_number == -1:
            self._load_base_map()
            self.animated_troops = []
            return True

        # Caminhos dos arquivos
        path_prev_dc = os.path.join(self.base_path, f'estado_turno_{turn_number-1}_dc.json')
        path_ac = os.path.join(self.base_path, f'estado_turno_{turn_number}_ac.json')
        path_mc = os.path.join(self.base_path, f'estado_turno_{turn_number}_mc.json')
        path_dc = os.path.join(self.base_path, f'estado_turno_{turn_number}_dc.json')

        # Verifica se existem os arquivos necessários
        if not os.path.exists(path_ac) or not os.path.exists(path_dc) or not os.path.exists(path_mc):
            print(f"Arquivos AC/DC do turno {turn_number} não encontrados.")
            self.animating = False
            return False
        if turn_number > 0 and not os.path.exists(path_prev_dc):
            print(f"Arquivo DC do turno anterior ({turn_number-1}) não encontrado.")
            return False
        # Carrega os estados
        with open(path_ac, 'r', encoding='utf-8') as f:
            state_ac = json.load(f)
        with open(path_mc, 'r', encoding='utf-8') as f:
            state_mc = json.load(f)
        with open(path_dc, 'r', encoding='utf-8') as f:
            state_dc = json.load(f)
        state_prev_dc = None
        if turn_number > 0:
            with open(path_prev_dc, 'r', encoding='utf-8') as f:
                state_prev_dc = json.load(f)

        # Etapa 1: Animação do final do turno anterior (prev_dc) para o início deste (ac)
        state_start = state_prev_dc if state_prev_dc else state_ac
        self._update_cities_from_state(state_ac) # Atualiza mapa para o estado de destino (ac)
        self._animar_tropas_distribuidas(state_start, state_ac, animation_duration)
        self._animar_transportes(state_start, state_ac, animation_duration)

        # Armazena etapa 2 (AC -> DC) para disparar automática ao fim da 1ª
        # Armazena etapas seguintes para disparar automaticamente
        self.pending_animation.append((state_ac, state_mc, animation_duration))
        self.pending_animation.append((state_mc, state_dc, animation_duration))
        

        return True


    def _update_cities_from_state(self, state):
        """Atualiza o dono e a população das cidades com base em um estado."""
        for city_state in state.get('mapa', {}).get('cidades', []):
            city_id = city_state['id']
            if city_id in self.cities:
                dono_value = city_state.get('dono')
                self.cities[city_id].owner = int(dono_value) if dono_value is not None else None
                self.cities[city_id].population = city_state.get('populacao')

    def _trigger_next_animation(self):
        """Dispara a próxima animação da fila."""
        if not hasattr(self, "pending_animation") or not self.pending_animation:
            return
        
        state_from, state_to, duration = self.pending_animation.pop(0)

        # Atualiza o mapa para o estado de destino ANTES de criar a animação
        self._update_cities_from_state(state_to)
        self._animar_tropas_distribuidas(state_from, state_to, duration)
        self._animar_transportes(state_from, state_to, duration)
    
    def update_animation(self, dt):
        """Atualiza todas as unidades animadas (tropas e transportes)."""
        if not self.animated_troops and not self.animated_transports:
            return

        for troop in self.animated_troops:
            troop.update(dt)
        
        for transport in self.animated_transports:
            transport.update(dt)

        all_troops_done = all(t.animation_timer >= t.animation_duration for t in self.animated_troops)
        all_transports_done = all(t.animation_timer >= t.animation_duration for t in self.animated_transports)

        if all_troops_done and all_transports_done:
            if hasattr(self, "pending_animation") and self.pending_animation:
                print("Disparando animação pendente AC -> DC.")
                self._trigger_next_animation()
            else:
                print("Todas as animações concluídas.")
                self.animating = False

    def draw(self, surface):
        """Desenha todos os componentes estáticos e as tropas animadas."""
        self._draw_edges(surface)
        self._draw_cities(surface)
        self._draw_edge_weights(surface)

        # Desenha as tropas em suas posições atuais de animação
        for troop in self.animated_troops:
            troop.draw(surface, self.troop_font)

        for transport in self.animated_transports:
            transport.draw(surface, self.troop_font)

    def _draw_edges(self, surface):
        for a, b, weight in self.edges:
            if a in self.cities and b in self.cities:
                pygame.draw.line(surface, (131, 111, 98), self.cities[a].pos, self.cities[b].pos, max(1, min(10, weight // 10)))

    def _draw_cities(self, surface):
        for city in self.cities.values():
            city.draw(surface, self.city_font)

    def _draw_edge_weights(self, surface):
        for a, b, weight in self.edges:
            if a in self.cities and b in self.cities:
                pos_a, pos_b = self.cities[a].pos, self.cities[b].pos
                label_pos = (pos_a[0] * 0.8 + pos_b[0] * 0.2, pos_a[1] * 0.8 + pos_b[1] * 0.2)
                draw_text_with_outline(surface, self.edge_font, str(weight), WHITE, BLACK, label_pos)

# ... (As classes HUD e Menu permanecem as mesmas) ...
class LogPanel:
    """Gerencia a exibição de um painel com mensagens de log e botões de rolagem."""
    def __init__(self, x, y, width, height, font):
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.title_font = pygame.font.SysFont(None, 24)
        self.log_messages = []
        self.scroll_y = 0
        self.content_height = 0
        self.scroll_step = 30  # Píxeis para rolar por clique

        # Define os retângulos dos botões
        self.up_button_rect = pygame.Rect(self.rect.right - 28, self.rect.top + 5, 22, 22)
        self.down_button_rect = pygame.Rect(self.rect.right - 28, self.rect.top + 32, 22, 22)

    def set_logs(self, messages):
        self.log_messages = messages
        self.content_height = len(self.log_messages) * (self.font.get_height() + 3)
        self.scroll_y = 0

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            content_area_height = self.rect.height - 45 # 35 para margem superior, 10 para inferior
            max_scroll = max(0, self.content_height - content_area_height)

            if self.up_button_rect.collidepoint(event.pos):
                self.scroll_y -= self.scroll_step
                self.scroll_y = max(0, self.scroll_y)
            elif self.down_button_rect.collidepoint(event.pos):
                self.scroll_y += self.scroll_step
                self.scroll_y = min(max_scroll, self.scroll_y)

    def draw(self, surface):
        # 1. Desenha o fundo e a borda
        bg_surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        bg_surface.fill((30, 30, 30, 210))
        surface.blit(bg_surface, self.rect.topleft)
        pygame.draw.rect(surface, WHITE, self.rect, 1, border_radius=3)

        # 2. Desenha o título
        title_surf = self.title_font.render("Log de Eventos do Turno", True, WHITE)
        surface.blit(title_surf, (self.rect.x + 10, self.rect.y + 8))

        # 3. Prepara a área de conteúdo rolável
        content_area = self.rect.inflate(-40, -45) # Reduz a área para margens e botões
        content_area.top = self.rect.top + 35
        # A superfície de conteúdo deve ter a altura total dos logs
        content_surface_height = max(content_area.height, self.content_height)
        content_surface = pygame.Surface((content_area.width, content_surface_height), pygame.SRCALPHA)
        content_surface.fill((0, 0, 0, 0)) # Garante que a superfície esteja limpa
        y_offset = 0
        for msg in self.log_messages:
            msg_surf = self.font.render(msg.strip(), True, (220, 220, 220))
            content_surface.blit(msg_surf, (0, y_offset))
            y_offset += self.font.get_height() + 3

        # 5. Blit a parte visível do conteúdo
        # A área de origem (terceiro argumento) deve usar a altura da área visível
        visible_rect = pygame.Rect(0, self.scroll_y, content_area.width, content_area.height)
        surface.blit(content_surface, content_area.topleft, visible_rect)

        # 6. Desenha os botões de rolagem
        self._draw_scroll_buttons(surface)

    def _draw_scroll_buttons(self, surface):
        # Botão para Cima
        pygame.draw.rect(surface, (80, 80, 80), self.up_button_rect, border_radius=3)
        pygame.draw.polygon(surface, WHITE, [
            (self.up_button_rect.centerx, self.up_button_rect.top + 6),
            (self.up_button_rect.left + 6, self.up_button_rect.bottom - 6),
            (self.up_button_rect.right - 6, self.up_button_rect.bottom - 6)
        ])

        # Botão para Baixo
        pygame.draw.rect(surface, (80, 80, 80), self.down_button_rect, border_radius=3)
        pygame.draw.polygon(surface, WHITE, [
            (self.down_button_rect.centerx, self.down_button_rect.bottom - 6),
            (self.down_button_rect.left + 6, self.down_button_rect.top + 6),
            (self.down_button_rect.right - 6, self.down_button_rect.top + 6)
        ])

class HUD:
    """Gerencia a Interface do Usuário (HUD), como contador de turno e retratos dos jogadores."""
    def __init__(self, selected_characters):
        # Fontes
        self.font = pygame.font.SysFont(None, 24)
        self.round_font = pygame.font.SysFont(None, 48)
        self.log_font = pygame.font.SysFont('Consolas', 14)

        # Prepara dados dos jogadores
        self.player_portraits = []
        self.player_names = []
        if selected_characters:
            for char in selected_characters:
                portrait = pygame.transform.scale(char.image, (80, 80)) # Retrato menor para o HUD
                self.player_portraits.append(portrait)
                self.player_names.append(char.name)

        # Painel de Log
        log_panel_width = WIDTH // 2 - 40
        log_panel_height = 250
        self.log_panel = LogPanel(20, HEIGHT - log_panel_height - 20, log_panel_width, log_panel_height, self.log_font)
        self.current_hud_round = -1

        # Botões de Navegação
        self.left_arrow_rect = None
        self.right_arrow_rect = None

    def handle_event(self, event):
        """Processa um evento e o passa para os subcomponentes, como o LogPanel."""
        self.log_panel.handle_event(event)

    def draw(self, surface, round_num, log_entries):
        """Desenha todos os elementos do HUD."""
        # 1. Desenha os retratos dos jogadores
        self._draw_player_portraits(surface)

        # 2. Desenha o contador de turno e botões de navegação
        turn_text_str = f"Turno: {round_num}"
        text_pos = (surface.get_width() / 2, 45) # Centralizado no topo
        draw_text_with_outline(surface, self.round_font, turn_text_str, WHITE, BLACK, text_pos, 2)
        
        turn_text_surf = self.round_font.render(turn_text_str, True, WHITE)
        text_rect = turn_text_surf.get_rect(center=text_pos)
        
        button_y = text_rect.centery
        self.left_arrow_rect = pygame.Rect(text_rect.left - 70, button_y - text_rect.height // 2, 50, text_rect.height)
        self.right_arrow_rect = pygame.Rect(text_rect.right + 20, button_y - text_rect.height // 2, 50, text_rect.height)

        self._draw_navigation_buttons(surface, self.left_arrow_rect, self.right_arrow_rect)
        
        # 3. Desenha o painel de log
        if round_num != self.current_hud_round:
            self.log_panel.set_logs(log_entries)
            self.current_hud_round = round_num
        
        self.log_panel.draw(surface)

    def _draw_navigation_buttons(self, surface, left_rect, right_rect):
        # Botão Esquerdo
        pygame.draw.rect(surface, (0, 150, 0), left_rect, border_radius=5)
        pygame.draw.rect(surface, WHITE, left_rect, 2, border_radius=5)
        left_arrow_text = self.font.render("<", True, WHITE)
        surface.blit(left_arrow_text, left_arrow_text.get_rect(center=left_rect.center))

        # Botão Direito
        pygame.draw.rect(surface, (0, 150, 0), right_rect, border_radius=5)
        pygame.draw.rect(surface, WHITE, right_rect, 2, border_radius=5)
        right_arrow_text = self.font.render(">", True, WHITE)
        surface.blit(right_arrow_text, right_arrow_text.get_rect(center=right_rect.center))



    def _draw_player_portraits(self, surface):
        # Jogador 1 (esquerda)
        if len(self.player_portraits) > 0:
            p1_portrait = self.player_portraits[0]
            p1_rect = p1_portrait.get_rect(topleft=(20, 20))
            surface.blit(p1_portrait, p1_rect)
            pygame.draw.rect(surface, (0, 100, 200), p1_rect, 3) # Borda P1
            draw_text_with_outline(surface, self.font, self.player_names[0], WHITE, BLACK, (p1_rect.centerx, p1_rect.bottom + 15), 1)

        # Jogador 2 (direita)
        if len(self.player_portraits) > 1:
            p2_portrait = self.player_portraits[1]
            p2_rect = p2_portrait.get_rect(topright=(WIDTH - 20, 20))
            surface.blit(p2_portrait, p2_rect)
            pygame.draw.rect(surface, (200, 0, 0), p2_rect, 3) # Borda P2
            draw_text_with_outline(surface, self.font, self.player_names[1], WHITE, BLACK, (p2_rect.centerx, p2_rect.bottom + 15), 1)
            
class Character:
    """Armazena dados para um personagem selecionável."""
    def __init__(self, name, image_path, pos, size):
        self.name = name
        self.image = pygame.image.load(image_path)
        self.image = pygame.transform.scale(self.image, (size, size))
        self.rect = self.image.get_rect(center=pos)

class Menu:
    """Gerencia a tela de seleção de personagens no estilo de jogos de luta."""
    def __init__(self):
        self.font = pygame.font.SysFont(None, 32)
        self.title_font = pygame.font.SysFont(None, 72)
        self.characters = []
        self.selected_players = [None, None] # Armazena os nomes dos personagens selecionados
        self.current_selection = 0 # 0 para P1, 1 para P2
        self.start_button_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT - 100, 200, 50)
        self.background_image = self._load_background()

        self._load_characters()

    def _load_background(self):
        try:
            image_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'fundo_menu.png')
            image = pygame.image.load(image_path).convert()
            return pygame.transform.scale(image, (WIDTH, HEIGHT))
        except pygame.error as e:
            print(f"Não foi possível carregar a imagem de fundo do menu: {e}")
            return None

    def _load_characters(self):
        teams_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'teams')
        if not os.path.exists(teams_path):
            return

        character_files = [f for f in os.listdir(teams_path) if f.endswith(('.png', '.jpg'))]
        total_chars = len(character_files)
        if total_chars == 0:
            return

        # Lógica de layout dinâmico
        max_grid_height = HEIGHT - 300 # Deixa espaço para título e botão
        max_grid_width = WIDTH - 100

        # Determina o número de colunas e o tamanho do retrato
        if total_chars <= 5:
            grid_cols = total_chars
            portrait_size = 150
        elif total_chars <= 12:
            grid_cols = (total_chars + 1) // 2
            portrait_size = 120
        else: # Para 13 ou mais, usa uma grade mais densa
            grid_cols = (total_chars + 2) // 3
            portrait_size = 100

        grid_rows = (total_chars + grid_cols - 1) // grid_cols

        # Ajusta o tamanho se a grade for muito alta ou larga
        spacing_x = portrait_size * 1.2 # Aumentado para mais espaço horizontal
        spacing_y = portrait_size * 1.6 # Aumentado para evitar sobreposição de nomes
        grid_width = grid_cols * spacing_x
        grid_height = grid_rows * spacing_y

        if grid_height > max_grid_height or grid_width > max_grid_width:
            scale_factor = min(max_grid_height / grid_height, max_grid_width / grid_width)
            portrait_size = int(portrait_size * scale_factor)
            spacing_x = portrait_size * 1.15
            spacing_y = portrait_size * 1.3

        # Calcula a posição inicial para centralizar a grade
        grid_width = (grid_cols - 1) * spacing_x
        grid_height = (grid_rows - 1) * spacing_y
        start_x = (WIDTH - grid_width) / 2
        start_y = (HEIGHT - grid_height) / 2

        for i, filename in enumerate(character_files):
            name = os.path.splitext(filename)[0].replace('_', ' ')
            image_path = os.path.join(teams_path, filename)
            
            col = i % grid_cols
            row = i // grid_cols
            
            pos_x = start_x + col * spacing_x
            pos_y = start_y + row * spacing_y
            
            self.characters.append(Character(name, image_path, (pos_x, pos_y), portrait_size))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for char in self.characters:
                if char.rect.collidepoint(event.pos):
                    # Caso 1: O personagem clicado já está selecionado pelo jogador atual.
                    if char.name == self.selected_players[self.current_selection]:
                        self.selected_players[self.current_selection] = None # Desseleciona
                        break

                    # Caso 2: O personagem clicado já foi pego pelo OUTRO jogador.
                    other_player_idx = 1 - self.current_selection
                    if char.name == self.selected_players[other_player_idx]:
                        break # Impede a seleção

                    # Caso 3: Seleção normal ou troca de personagem.
                    self.selected_players[self.current_selection] = char.name
                    # Avança para o próximo jogador (ou volta para o primeiro se o segundo já escolheu)
                    if self.selected_players[other_player_idx] is not None:
                        self.current_selection = other_player_idx
                    else:
                        self.current_selection = 1 - self.current_selection
                    break

    def draw(self, surface):
        if self.background_image:
            surface.blit(self.background_image, (0, 0))
        else:
            surface.fill(DARK_GREY)
        title_text = self.title_font.render("Selecione seu Time", True, WHITE)
        surface.blit(title_text, title_text.get_rect(center=(WIDTH // 2, 80)))

        # Desenha os personagens
        for char in self.characters:
            surface.blit(char.image, char.rect)
            pygame.draw.rect(surface, WHITE, char.rect, 2) # Borda branca
            
            name_text = self.font.render(char.name, True, WHITE)
            surface.blit(name_text, name_text.get_rect(center=(char.rect.centerx, char.rect.bottom + 20)))

        # Desenha os indicadores P1 e P2
        player_indicator_font = pygame.font.SysFont(None, 50)
        for i, player_name in enumerate(self.selected_players):
            if player_name:
                for char in self.characters:
                    if char.name == player_name:
                        draw_text_with_outline(
                            surface, player_indicator_font, f"P{i+1}", (255, 215, 0), BLACK, 
                            char.rect.center, 2
                        )
                        break

        # Desenha o botão de iniciar quando ambos os jogadores forem selecionados
        if all(self.selected_players):
            pygame.draw.rect(surface, (0, 200, 0), self.start_button_rect, border_radius=10)
            start_text = self.font.render("Iniciar Batalha", True, WHITE)
            surface.blit(start_text, start_text.get_rect(center=self.start_button_rect.center))

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT),pygame.RESIZABLE)
        pygame.display.set_caption("Visualizador de Grafo Animado")
        self.clock = pygame.time.Clock()
        self.running = True
        self.game_state = 'menu' # 'menu', 'game', 'animating'
        
        self.base_path = os.path.join(os.path.dirname(__file__), '..', 'estados')
        self.current_round = 0
        self.max_round = self._get_max_round()
        self.log_content = self._load_log_file()
        self.end_of_simulation = False

        self.animation_duration = 0.5 # em segundos
        self.animation_timer = 0.0

        self.tile_image = self._load_background_tile()
        self.menu = Menu()
        self.map = None
        self.hud = None
        self.restart_button_rect = pygame.Rect(self.screen.get_rect().centerx - 150, self.screen.get_rect().centery + 50, 300, 50)


    def _load_background_tile(self):
        try:
            image = pygame.image.load("./assets/ground.jpg").convert()
            return pygame.transform.scale(image, (200, 200))
        except pygame.error as e:
            print(f"Não foi possível carregar a imagem de fundo: {e}")
            return None

    def _get_max_round(self):
        """Verifica a pasta de estados e retorna o número máximo de turno."""
        if not os.path.exists(self.base_path):
            return 0
        
        max_round = -1
        pattern = re.compile(r'estado_turno_(\d+)_.*\.json')
        
        for filename in os.listdir(self.base_path):
            match = pattern.match(filename)
            if match:
                round_num = int(match.group(1))
                if round_num > max_round:
                    max_round = round_num
                    
        return max_round if max_round != -1 else 0

    def _load_log_file(self):
        """Carrega o conteúdo do arquivo de log em memória."""
        log_path = os.path.join(self.base_path, 'log.log')
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"Arquivo de log não encontrado em {log_path}")
            return ""

    def _parse_log_for_turn(self, turn_number):
        """Extrai as linhas de log para um turno específico."""
        if not self.log_content:
            return ["Log não disponível."]

        # Expressão para encontrar todos os blocos de turno completos.
        # Um bloco começa com '--- Preparando Turno ---' e vai até o próximo, ou até o fim do arquivo.
        pattern = re.compile(r'(--- Preparando Turno ---.*?)(?=\n--- Preparando Turno ---|\Z)', re.DOTALL)
        
        # Encontra todos os blocos que correspondem a um ciclo de turno
        turn_blocks = pattern.findall(self.log_content)

        # Procura pelo bloco que contém o processamento do turno correto
        processing_marker = f'--- Processando Turno {turn_number} ---'
        for block in turn_blocks:
            if processing_marker in block:
                # Encontrou o bloco correto, agora limpa e retorna as linhas
                lines = block.strip().split('\n')
                return [line.strip() for line in lines if line.strip()]

        # Se nenhum bloco foi encontrado para o turno
        return [f"Nenhum evento registrado para o turno {turn_number}."]

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0 # Delta time em segundos

            self.handle_events()
            self.update(dt)
            self.draw()
        pygame.quit()
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            # O HUD e seus componentes (LogPanel) devem sempre receber eventos para a UI responder.
            if self.hud:
                self.hud.handle_event(event)

            # Lógica de eventos específica para cada estado do jogo
            if self.game_state == 'menu':
                # Passa o evento para o menu lidar com a seleção
                self.menu.handle_event(event)
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # Verifica se o botão de iniciar foi clicado APÓS ambos os jogadores serem selecionados
                    if all(self.menu.selected_players) and self.menu.start_button_rect.collidepoint(event.pos):
                        self.start_game()

            elif self.game_state == 'game':
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # Se o clique foi no painel de log, o evento já foi tratado. Não faz mais nada.
                    if self.hud and self.hud.log_panel and self.hud.log_panel.rect.collidepoint(event.pos):
                        continue

                    # Se não foi no painel, verifica os botões de turno.
                    if self.hud.left_arrow_rect and self.hud.left_arrow_rect.collidepoint(event.pos):
                        self.change_turn(-1)
                    elif self.hud.right_arrow_rect and self.hud.right_arrow_rect.collidepoint(event.pos):
                        self.change_turn(1)

            elif self.game_state == 'end':
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.restart_button_rect.collidepoint(event.pos):
                        self.restart_game()

    def update(self, dt):
        if self.game_state == 'animating':
            self.animation_timer += dt
            self.map.update_animation(dt)
            if not self.map.animating:
                self.game_state = 'game'

    def start_game(self):
        self.game_state = 'game'
        self.map = Map()
        
        # Encontra os objetos Character completos para passar ao HUD
        selected_chars = []
        if self.menu.selected_players:
            for name in self.menu.selected_players:
                for char in self.menu.characters:
                    if char.name == name:
                        selected_chars.append(char)
                        break
        self.hud = HUD(selected_chars)
        # Inicia no turno 0, sem direção
        self.map.prepare_turn_animation(self.current_round, self.animation_duration)

    def restart_game(self):
        """Reseta a simulação para o primeiro turno."""
        print("Reiniciando a simulação.")
        self.current_round = 0
        self.end_of_simulation = False
        self.game_state = 'animating'
        self.map.prepare_turn_animation(self.current_round, self.animation_duration)

    def change_turn(self, direction):
        new_turn = self.current_round + direction

        if new_turn > self.max_round:
            self.end_of_simulation = True
            print("Chegou ao final da simulação.")
            return

        if new_turn < 0:
            # Impede de ir para um turno negativo
            return

        # Se chegou aqui, o turno é válido
        self.end_of_simulation = False
        self.current_round = new_turn
        self.game_state = 'animating' # Bloqueia novos cliques de turno
        self.map.prepare_turn_animation(self.current_round, self.animation_duration)

    def draw(self):
        self._draw_background()
        if self.game_state == 'menu':
            self.menu.draw(self.screen)
        else:
            if self.map: self.map.draw(self.screen)
            if self.hud:
                log_entries = self._parse_log_for_turn(self.current_round)
                self.hud.draw(self.screen, self.current_round, log_entries)

        if self.end_of_simulation:
            self._draw_end_message()
        
        pygame.display.flip()
    
    def _rescale_positions(self,height, width):
        scale_x = width / 1920
        scale_y = height / 1080

        # Reescalar cidades
        for city in self.map.cities.values():
            city.pos = (int(city.pos[0] * scale_x), int(city.pos[1] * scale_y))

        # Reescalar fontes da HUD e do mapa
        self.map.city_font = pygame.font.SysFont(None, int(28 * scale_y))
        self.map.edge_font = pygame.font.SysFont(None, int(22 * scale_y))
        self.map.troop_font = pygame.font.SysFont(None, int(24 * scale_y))
        self.hud.font = pygame.font.SysFont(None, int(28 * scale_y))
        self.hud.round_font = pygame.font.SysFont(None, int(48 * scale_y))
        self.hud.legend_font = pygame.font.SysFont(None, int(20 * scale_y))
    
    def _draw_end_message(self):
        """Desenha a mensagem de fim de simulação."""
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # Sobreposição escura semitransparente
        self.screen.blit(overlay, (0, 0))

        end_font = pygame.font.SysFont(None, 80)
        draw_text_with_outline(
            self.screen, end_font, "Fim da Simulação",
            WHITE, BLACK, (self.screen.get_rect().centerx, self.screen.get_rect().centery - 40), 2
        )

        # Desenha o botão de reiniciar
        button_font = pygame.font.SysFont(None, 40)
        pygame.draw.rect(self.screen, PLAYER_COLORS[0], self.restart_button_rect, border_radius=10)
        pygame.draw.rect(self.screen, WHITE, self.restart_button_rect, 2, border_radius=10)
        self.draw_text_with_outline(
            "Retornar ao Início",
            self.restart_button_rect.center,
            button_font, WHITE, BLACK, 1
        )

    def _draw_background(self):
        if self.tile_image:
            tile_w, tile_h = self.tile_image.get_size()
            for y in range(0, HEIGHT, tile_h):
                for x in range(0, WIDTH, tile_w):
                    self.screen.blit(self.tile_image, (x, y))
        else:
            self.screen.fill(WHITE)

if __name__ == "__main__":
    game = Game()
    game.run()