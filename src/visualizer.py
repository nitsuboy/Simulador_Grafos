import pygame
import json
import os
import math
import re

# --- Constantes e Configurações Iniciais ---
WIDTH, HEIGHT = 1920, 1080
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK_GREY = (30, 30, 30)
AUTO_PLAY_DELAY = 2.0  # <--- NOVO: Tempo em segundos entre os turnos no auto-play

# --- Constantes de Cor ---
PLAYER_COLORS = [
    (0, 150, 255),  # Jogador 0 (Azul)
    (255, 150, 0),  # Jogador 1 (Laranja)
]
NEUTRAL_COLOR = (200, 200, 200)

# --- Funções Utilitárias ---
def draw_text_with_outline(surface, font, text, text_color, outline_color, pos, outline_width=1, alpha=255):
    text_surface = font.render(text, True, text_color)
    text_surface.set_alpha(alpha)
    outline_surface = font.render(text, True, outline_color)
    outline_surface.set_alpha(alpha)
    text_rect = text_surface.get_rect(center=pos)

    for dx in range(-outline_width, outline_width + 1, outline_width):
        for dy in range(-outline_width, outline_width + 1, outline_width):
            if dx != 0 or dy != 0:
                outline_rect = outline_surface.get_rect(center=(pos[0] + dx, pos[1] + dy))
                surface.blit(outline_surface, outline_rect)
    surface.blit(text_surface, text_rect)

def lerp(v0, v1, t):
    return v0 + t * (v1 - v0)

def lerp_vector(v0, v1, t):
    return (lerp(v0[0], v1[0], t), lerp(v0[1], v1[1], t))

# <--- REVISÃO: Função movida para fora da classe Map por ser um utilitário geral.
def distribuir_tropas_em_circulo(city_pos, num_tropas, offset_radius=45):
    posicoes = []
    for i in range(num_tropas):
        angle = (2 * math.pi / num_tropas) * i
        x = city_pos[0] + offset_radius * math.cos(angle)
        y = city_pos[1] + offset_radius * math.sin(angle)
        posicoes.append((x, y))
    return posicoes

# --- Classes do Jogo ---

class AnimatedTroop:
    def __init__(self, strength, owner_id, start_pos, end_pos, animation_duration,fade_out=False):
        self.strength = strength
        self.owner_id = owner_id
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.current_pos = start_pos
        self.animation_duration = animation_duration
        self.animation_timer = 0.0
        self.fade_out = fade_out
        self.alpha = 255

    def update(self, dt):
        if self.animation_timer < self.animation_duration:
            self.animation_timer = min(self.animation_timer + dt, self.animation_duration)
            progress = self.animation_timer / self.animation_duration
            t = 1 - (1 - progress) ** 3
            self.current_pos = lerp_vector(self.start_pos, self.end_pos, t)
            
            if self.fade_out:
                self.alpha = int(255 * (1 - progress))

    def draw(self, surface, font):
        temp_surface = pygame.Surface((100, 100), pygame.SRCALPHA)
        temp_surface = temp_surface.convert_alpha()
        
        color = PLAYER_COLORS[int(self.owner_id)]           
        faded_color = (*color, self.alpha)
        
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

        if 'basej_0' in self.id: self.owner = 0
        elif 'basej_1' in self.id: self.owner = 1

    def draw(self, surface, font):
        color = PLAYER_COLORS[self.owner] if self.owner is not None else NEUTRAL_COLOR
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
    # ... (Esta classe não foi modificada) ...
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
    # ... (Esta classe não foi modificada) ...
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
            final_positions = distribuir_tropas_em_circulo(city_pos, len(tropas))

            # Distribuir tropas com transição suave
            for i, (troop_id, troop_final) in enumerate(tropas):
                dono = troop_final["dono"]
                forca = troop_final["forca"]
                destino_pos = final_positions[i]

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
    
    def prepare_turn_animation(self, turn_number, animation_duration):
        """Anima DC do turno anterior -> AC do turno atual -> DC do turno atual."""
        self.animating = True

        if turn_number == -1: # <--- Lógica para estado inicial
            self._load_base_map()
            self.animated_troops = []
            self.animated_transports = []
            self.animating = False # Não há animação no estado -1
            return True

        # Caminhos dos arquivos
        path_prev_dc = os.path.join(self.base_path, f'estado_turno_{turn_number-1}_dc.json')
        path_ac = os.path.join(self.base_path, f'estado_turno_{turn_number}_ac.json')
        path_mc = os.path.join(self.base_path, f'estado_turno_{turn_number}_mc.json')
        path_dc = os.path.join(self.base_path, f'estado_turno_{turn_number}_dc.json')

        if not all(os.path.exists(p) for p in [path_ac, path_mc, path_dc]):
            print(f"Arquivos AC/MC/DC do turno {turn_number} não encontrados.")
            self.animating = False
            return False
        
        state_prev_dc = {} # Estado inicial vazio se for o turno 0
        if turn_number > 0:
            if not os.path.exists(path_prev_dc):
                print(f"Arquivo DC do turno anterior ({turn_number-1}) não encontrado.")
                self.animating = False
                return False
            with open(path_prev_dc, 'r', encoding='utf-8') as f:
                state_prev_dc = json.load(f)
        
        with open(path_ac, 'r', encoding='utf-8') as f: state_ac = json.load(f)
        with open(path_mc, 'r', encoding='utf-8') as f: state_mc = json.load(f)
        with open(path_dc, 'r', encoding='utf-8') as f: state_dc = json.load(f)

        self.pending_animation.clear()
        self.pending_animation.append((state_prev_dc, state_ac, animation_duration))
        self.pending_animation.append((state_ac, state_mc, animation_duration))
        self.pending_animation.append((state_mc, state_dc, animation_duration))
        
        self._trigger_next_animation()
        return True

    def _update_cities_from_state(self, state):
        for city_state in state.get('mapa', {}).get('cidades', []):
            city_id = city_state['id']
            if city_id in self.cities:
                dono_value = city_state.get('dono')
                self.cities[city_id].owner = int(dono_value) if dono_value is not None else None
                self.cities[city_id].population = city_state.get('populacao')

    def _trigger_next_animation(self):
        if not self.pending_animation:
            self.animating = False
            return
        
        state_from, state_to, duration = self.pending_animation.pop(0)
        self._update_cities_from_state(state_to)
        self._animar_tropas_distribuidas(state_from, state_to, duration)
        self._animar_transportes(state_from, state_to, duration)
    
    def update_animation(self, dt):
        if not self.animating: return

        for troop in self.animated_troops: troop.update(dt)
        for transport in self.animated_transports: transport.update(dt)

        all_troops_done = all(t.animation_timer >= t.animation_duration for t in self.animated_troops)
        all_transports_done = all(t.animation_timer >= t.animation_duration for t in self.animated_transports)

        if all_troops_done and all_transports_done:
            if self.pending_animation:
                self._trigger_next_animation()
            else:
                self.animating = False

    def draw(self, surface):
        self._draw_edges(surface)
        self._draw_cities(surface)
        self._draw_edge_weights(surface)
        for troop in self.animated_troops: troop.draw(surface, self.troop_font)
        for transport in self.animated_transports: transport.draw(surface, self.troop_font)

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

class LogPanel:
    # ... (Esta classe não foi modificada) ...
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
    def __init__(self, selected_characters):
        self.font = pygame.font.SysFont(None, 24)
        self.round_font = pygame.font.SysFont(None, 48)
        self.log_font = pygame.font.SysFont('Consolas', 14)

        self.player_portraits = []
        self.player_names = []
        if selected_characters:
            for char in selected_characters:
                self.player_portraits.append(pygame.transform.scale(char.image, (80, 80)))
                self.player_names.append(char.name)

        log_panel_width = WIDTH // 2 - 40
        self.log_panel = LogPanel(20, HEIGHT - 270, log_panel_width, 250, self.log_font)
        self.current_hud_round = -1

        self.left_arrow_rect = None
        self.right_arrow_rect = None
        self.autoplay_button_rect = None # <--- NOVO

    def handle_event(self, event):
        self.log_panel.handle_event(event)

    def draw(self, surface, round_num, log_entries, is_auto_playing): # <--- NOVO: Parâmetro is_auto_playing
        self._draw_player_portraits(surface)

        if round_num >= 0:
            turn_text_str = f"Turno: {round_num}"
        else:
            turn_text_str = "Simulação não iniciada" # <--- NOVO: Texto para turno -1
        
        text_pos = (surface.get_width() / 2, 45)
        draw_text_with_outline(surface, self.round_font, turn_text_str, WHITE, BLACK, text_pos, 2)
        
        turn_text_surf = self.round_font.render(turn_text_str, True, WHITE)
        text_rect = turn_text_surf.get_rect(center=text_pos)
        
        button_y = text_rect.centery
        self.left_arrow_rect = pygame.Rect(text_rect.left - 70, button_y - text_rect.height // 2, 50, text_rect.height)
        self.right_arrow_rect = pygame.Rect(text_rect.right + 20, button_y - text_rect.height // 2, 50, text_rect.height)
        # <--- NOVO: Posição do botão de auto-play
        self.autoplay_button_rect = pygame.Rect(self.right_arrow_rect.right + 10, button_y - text_rect.height // 2, 50, text_rect.height)

        self._draw_navigation_buttons(surface, self.left_arrow_rect, self.right_arrow_rect, self.autoplay_button_rect, is_auto_playing)
        
        if round_num != self.current_hud_round:
            self.log_panel.set_logs(log_entries)
            self.current_hud_round = round_num
        
        self.log_panel.draw(surface)

    def _draw_navigation_buttons(self, surface, left_rect, right_rect, autoplay_rect, is_auto_playing): # <--- NOVO
        # Botões de seta
        pygame.draw.rect(surface, (0, 150, 0), left_rect, border_radius=5)
        pygame.draw.rect(surface, WHITE, left_rect, 2, border_radius=5)
        left_arrow_text = self.font.render("<", True, WHITE)
        surface.blit(left_arrow_text, left_arrow_text.get_rect(center=left_rect.center))

        pygame.draw.rect(surface, (0, 150, 0), right_rect, border_radius=5)
        pygame.draw.rect(surface, WHITE, right_rect, 2, border_radius=5)
        right_arrow_text = self.font.render(">", True, WHITE)
        surface.blit(right_arrow_text, right_arrow_text.get_rect(center=right_rect.center))

        # <--- NOVO: Botão de auto-play
        autoplay_color = (0, 100, 200) if is_auto_playing else (150, 0, 0)
        pygame.draw.rect(surface, autoplay_color, autoplay_rect, border_radius=5)
        pygame.draw.rect(surface, WHITE, autoplay_rect, 2, border_radius=5)
        
        if is_auto_playing: # Ícone de Pause
            pause_w, pause_h = 5, 20
            pygame.draw.rect(surface, WHITE, (autoplay_rect.centerx - 8, autoplay_rect.centery - 10, pause_w, pause_h))
            pygame.draw.rect(surface, WHITE, (autoplay_rect.centerx + 3, autoplay_rect.centery - 10, pause_w, pause_h))
        else: # Ícone de Play
            pygame.draw.polygon(surface, WHITE, [
                (autoplay_rect.centerx - 8, autoplay_rect.centery - 10),
                (autoplay_rect.centerx - 8, autoplay_rect.centery + 10),
                (autoplay_rect.centerx + 10, autoplay_rect.centery)
            ])

    def _draw_player_portraits(self, surface):
        if len(self.player_portraits) > 0:
            p1_portrait, p1_name = self.player_portraits[0], self.player_names[0]
            p1_rect = p1_portrait.get_rect(topleft=(20, 20))
            surface.blit(p1_portrait, p1_rect)
            pygame.draw.rect(surface, PLAYER_COLORS[0], p1_rect, 3)
            draw_text_with_outline(surface, self.font, p1_name, WHITE, BLACK, (p1_rect.centerx, p1_rect.bottom + 15), 1)

        if len(self.player_portraits) > 1:
            p2_portrait, p2_name = self.player_portraits[1], self.player_names[1]
            p2_rect = p2_portrait.get_rect(topright=(WIDTH - 20, 20))
            surface.blit(p2_portrait, p2_rect)
            pygame.draw.rect(surface, PLAYER_COLORS[1], p2_rect, 3)
            draw_text_with_outline(surface, self.font, p2_name, WHITE, BLACK, (p2_rect.centerx, p2_rect.bottom + 15), 1)

class Character:
    # ... (Esta classe não foi modificada) ...
    def __init__(self, name, image_path, pos, size):
        self.name = name
        self.image = pygame.image.load(image_path)
        self.image = pygame.transform.scale(self.image, (size, size))
        self.rect = self.image.get_rect(center=pos)

class Menu:
    # ... (Esta classe não foi modificada) ...
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
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT)) # Removido RESIZABLE por simplicidade
        pygame.display.set_caption("Visualizador de Batalha")
        self.clock = pygame.time.Clock()
        self.running = True
        self.game_state = 'menu'
        
        self.base_path = os.path.join(os.path.dirname(__file__), '..', 'estados')
        self.current_round = -1 # <--- NOVO: Inicia no turno -1
        self.max_round = self._get_max_round()
        self.log_content = self._load_log_file()
        self.end_of_simulation = False

        self.animation_duration = 0.5
        
        # <--- NOVO: Atributos de Auto-Play
        self.auto_play_enabled = False
        self.auto_play_timer = 0.0

        self.tile_image = self._load_background_tile()
        self.menu = Menu()
        self.map = None
        self.hud = None
        self.restart_button_rect = pygame.Rect(self.screen.get_rect().centerx - 150, self.screen.get_rect().centery + 50, 300, 50)

    def _load_background_tile(self):
        try:
            image = pygame.image.load("./assets/ground.jpg").convert()
            return pygame.transform.scale(image, (200, 200))
        except pygame.error:
            return None

    def _get_max_round(self):
        if not os.path.exists(self.base_path): return 0
        max_round = -1
        pattern = re.compile(r'estado_turno_(\d+)_.*\.json')
        for filename in os.listdir(self.base_path):
            match = pattern.match(filename)
            if match:
                round_num = int(match.group(1))
                if round_num > max_round: max_round = round_num
        return max_round if max_round != -1 else 0

    def _load_log_file(self):
        log_path = os.path.join(self.base_path, 'log.log')
        try:
            with open(log_path, 'r', encoding='utf-8') as f: return f.read()
        except FileNotFoundError: return ""

    def _parse_log_for_turn(self, turn_number):
        if not self.log_content: return ["Log não disponível."]
        pattern = re.compile(r'(--- Preparando Turno ---.*?)(?=\n--- Preparando Turno ---|\Z)', re.DOTALL)
        turn_blocks = pattern.findall(self.log_content)
        processing_marker = f'--- Processando Turno {turn_number} ---'
        for block in turn_blocks:
            if processing_marker in block:
                lines = block.strip().split('\n')
                return [line.strip() for line in lines if line.strip()]
        return [f"Nenhum evento registrado para o turno {turn_number}."]

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self.handle_events()
            self.update(dt)
            self.draw()
        pygame.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            if self.hud: self.hud.handle_event(event)

            if self.game_state == 'menu':
                self.menu.handle_event(event)
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if all(self.menu.selected_players) and self.menu.start_button_rect.collidepoint(event.pos):
                        self.start_game()

            elif self.game_state == 'game':
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.hud.log_panel.rect.collidepoint(event.pos): continue
                    
                    if self.hud.left_arrow_rect and self.hud.left_arrow_rect.collidepoint(event.pos):
                        self.auto_play_timer = 0.0 # Reseta timer ao usar controle manual
                        self.change_turn(-1)
                    elif self.hud.right_arrow_rect and self.hud.right_arrow_rect.collidepoint(event.pos):
                        self.auto_play_timer = 0.0 # Reseta timer
                        self.change_turn(1)
                    elif self.hud.autoplay_button_rect and self.hud.autoplay_button_rect.collidepoint(event.pos):
                        self.auto_play_enabled = not self.auto_play_enabled
                        self.auto_play_timer = 0.0 # Reseta timer ao ligar/desligar

            elif self.game_state == 'end':
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.restart_button_rect.collidepoint(event.pos):
                        self.restart_game()

    def update(self, dt):
        if self.game_state == 'animating':
            if not self.map.animating: self.game_state = 'game'
            else: self.map.update_animation(dt)
        
        # <--- NOVO: Lógica do Auto-Play
        if self.auto_play_enabled and self.game_state == 'game':
            self.auto_play_timer += dt
            if self.auto_play_timer >= AUTO_PLAY_DELAY:
                self.auto_play_timer = 0.0
                self.change_turn(1)

    def start_game(self):
        self.game_state = 'game'
        self.map = Map()
        
        selected_chars = []
        if self.menu.selected_players:
            for name in self.menu.selected_players:
                for char in self.menu.characters:
                    if char.name == name:
                        selected_chars.append(char)
                        break
        self.hud = HUD(selected_chars)
        # <--- NOVO: Inicia no turno -1, que apenas carrega o mapa base sem animação.
        self.map.prepare_turn_animation(self.current_round, self.animation_duration)

    def restart_game(self):
        self.current_round = -1
        self.end_of_simulation = False
        self.auto_play_enabled = False # Desliga o auto-play ao reiniciar
        self.auto_play_timer = 0.0
        self.game_state = 'game'
        self.map.prepare_turn_animation(self.current_round, self.animation_duration)

    def change_turn(self, direction):
        if self.game_state != 'game': return # Só muda de turno se não estiver animando
        
        new_turn = self.current_round + direction
        if new_turn > self.max_round:
            self.end_of_simulation = True
            self.auto_play_enabled = False # Para o auto-play no fim
            return
        if new_turn < -1: return

        self.end_of_simulation = False
        self.current_round = new_turn
        
        if self.current_round >= 0:
             self.game_state = 'animating'
             self.map.prepare_turn_animation(self.current_round, self.animation_duration)
        else: # Se voltou para -1, apenas reseta o mapa sem animação
            self.map.prepare_turn_animation(-1, self.animation_duration)


    def draw(self):
        self._draw_background()
        if self.game_state == 'menu':
            self.menu.draw(self.screen)
        else:
            if self.map: self.map.draw(self.screen)
            if self.hud:
                log_entries = self._parse_log_for_turn(self.current_round)
                self.hud.draw(self.screen, self.current_round, log_entries, self.auto_play_enabled)

        if self.end_of_simulation and self.game_state != 'menu':
            self._draw_end_message()
        
        pygame.display.flip()
    
    def _draw_end_message(self):
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        end_font = pygame.font.SysFont(None, 80)
        draw_text_with_outline(
            self.screen, end_font, "Fim da Simulação",
            WHITE, BLACK, (self.screen.get_rect().centerx, self.screen.get_rect().centery - 40), 2
        )

        button_font = pygame.font.SysFont(None, 40)
        pygame.draw.rect(self.screen, PLAYER_COLORS[0], self.restart_button_rect, border_radius=10)
        pygame.draw.rect(self.screen, WHITE, self.restart_button_rect, 2, border_radius=10)
        
        # <--- REVISÃO: Corrigido o bug na chamada da função.
        draw_text_with_outline(
            self.screen, button_font, "Retornar ao Início",
            WHITE, BLACK, self.restart_button_rect.center, 1
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