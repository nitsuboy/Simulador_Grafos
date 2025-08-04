import pygame
import json
import os
import math

# --- Constantes e Configurações Iniciais ---
WIDTH, HEIGHT = 700, 700
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

class Map:
    def __init__(self, map_file='mapa_debug.json'):
        self.script_dir = os.path.dirname(__file__)
        self.map_file = os.path.join(self.script_dir, map_file)
        self.cities = {}
        self.edges = []
        self.animated_troops = [] # <-- Armazena as tropas animadas
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
        base_path = os.path.join(self.script_dir, '..', 'estados')
        print(f"Preparando animação para o turno {turn_number}...")
        self.animating = True
        # Caso especial: turno inicial
        if turn_number == -1:
            self._load_base_map()
            self.animated_troops = []
            return True

        # Caminhos dos arquivos
        path_prev_dc = os.path.join(base_path, f'estado_turno_{turn_number-1}_dc.json')
        path_ac = os.path.join(base_path, f'estado_turno_{turn_number}_ac.json')
        path_mc = os.path.join(base_path, f'estado_turno_{turn_number}_mc.json')
        path_dc = os.path.join(base_path, f'estado_turno_{turn_number}_dc.json')

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

        # Etapa 1: Atualiza cidades para AC e anima DC anterior -> AC
        for city_state in state_ac.get('mapa', {}).get('cidades', []):
            city_id = city_state['id']
            if city_id in self.cities:
                dono_value = city_state.get('dono')
                self.cities[city_id].owner = int(dono_value) if dono_value is not None else None
                self.cities[city_id].population = city_state.get('populacao')
        
        
        if state_prev_dc:  
            pass
            self._animar_tropas_distribuidas(state_prev_dc, state_ac, animation_duration)
        else:
            # Se não existe DC anterior (turno inicial), apenas prepara AC
            self._animar_tropas_distribuidas(state_ac, state_ac, animation_duration)

        # Armazena etapa 2 (AC -> DC) para disparar automática ao fim da 1ª
        self.pending_animation.append({
            "from": state_ac,
            "to": state_mc,
            "duration": animation_duration
        })
        self.pending_animation.append({
            "from": state_mc,
            "to": state_dc,
            "duration": animation_duration
        })
        

        return True


    def _trigger_next_animation(self):
        """Dispara AC -> DC automaticamente ao término da primeira animação."""
        if not hasattr(self, "pending_animation") or not self.pending_animation:
            return
        next_animation = self.pending_animation.pop(0)
        state_ac = next_animation["from"]
        state_dc = next_animation["to"]
        duration = next_animation["duration"]

        # Atualiza cidades para o estado final (DC)
        for city_state in state_dc.get('mapa', {}).get('cidades', []):
            city_id = city_state['id']
            if city_id in self.cities:
                dono_value = city_state.get('dono')
                self.cities[city_id].owner = int(dono_value) if dono_value is not None else None
                self.cities[city_id].population = city_state.get('populacao')
                
        self._animar_tropas_distribuidas(state_ac, state_dc, duration)
    
    def update_animation(self, dt):
        """Atualiza todas as tropas animadas."""
        if not self.animated_troops:
            return
        for troop in self.animated_troops:
            troop.update(dt)
        if all(t.animation_timer >= t.animation_duration for t in self.animated_troops):
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
class HUD:
    """Gerencia a Interface do Usuário (HUD), como contador de turno e legenda."""
    def __init__(self, player_names):
        self.player_names = player_names
        self.font = pygame.font.SysFont(None, 28)
        self.round_font = pygame.font.SysFont(None, 48)
        self.legend_font = pygame.font.SysFont(None, 20)

        self.left_arrow_rect = pygame.Rect(WIDTH - 280, 20, 50, 50)
        self.right_arrow_rect = pygame.Rect(WIDTH - 220, 20, 50, 50)

    def draw(self, surface, round_num):
        """Desenha todos os elementos do HUD."""
        self._draw_navigation_buttons(surface)
        self._draw_round_counter(surface, round_num)
        self._draw_legend(surface)

    def _draw_navigation_buttons(self, surface):
        pygame.draw.rect(surface, (0, 150, 0), self.left_arrow_rect)
        pygame.draw.rect(surface, WHITE, self.left_arrow_rect, 2)
        left_arrow_text = self.font.render("<", True, WHITE)
        surface.blit(left_arrow_text, left_arrow_text.get_rect(center=self.left_arrow_rect.center))

        pygame.draw.rect(surface, (0, 150, 0), self.right_arrow_rect)
        pygame.draw.rect(surface, WHITE, self.right_arrow_rect, 2)
        right_arrow_text = self.font.render(">", True, WHITE)
        surface.blit(right_arrow_text, right_arrow_text.get_rect(center=self.right_arrow_rect.center))

    def _draw_round_counter(self, surface, round_num):
        round_text = self.round_font.render(f"Turno: {round_num}", True, WHITE)
        surface.blit(round_text, (WIDTH - 220, 80))

    def _draw_legend(self, surface):
        legend_items = [
            (PLAYER_COLORS[0], f"Base {self.player_names[0]}"),
            (PLAYER_COLORS[1], f"Base {self.player_names[1]}"),
            (NEUTRAL_COLOR, "Cidade Neutra")
        ]
        x, y = 20, 20
        for color, description in legend_items:
            pygame.draw.circle(surface, color, (x + 10, y + 5), 10)
            text_surface = self.legend_font.render(description, True, BLACK)
            surface.blit(text_surface, (x + 30, y))
            y += 25
            
class Menu:
    """Gerencia a tela de menu inicial."""
    def __init__(self):
        self.font = pygame.font.SysFont(None, 40)
        self.title_font = pygame.font.SysFont(None, 72)
        self.player_names = ["Jogador 1", "Jogador 2"]
        self.input_rects = [
            pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 - 50, 300, 40),
            pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 + 10, 300, 40)
        ]
        self.start_button_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 80, 200, 50)
        self.active_input = None

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.start_button_rect.collidepoint(event.pos):
                return "start_game"
            
            self.active_input = None
            for i, rect in enumerate(self.input_rects):
                if rect.collidepoint(event.pos):
                    self.active_input = i
                    break
        
        if event.type == pygame.KEYDOWN and self.active_input is not None:
            if event.key == pygame.K_BACKSPACE:
                self.player_names[self.active_input] = self.player_names[self.active_input][:-1]
            else:
                self.player_names[self.active_input] += event.unicode
        return None

    def draw(self, surface):
        surface.fill(DARK_GREY)
        
        title_text = self.title_font.render("Conquista e Sobrevivência", True, WHITE)
        surface.blit(title_text, title_text.get_rect(center=(WIDTH // 2, HEIGHT // 4)))

        for i, rect in enumerate(self.input_rects):
            pygame.draw.rect(surface, (200, 200, 200), rect)
            color = (0, 100, 200) if self.active_input == i else BLACK
            pygame.draw.rect(surface, color, rect, 2)
            text_surface = self.font.render(self.player_names[i], True, BLACK)
            surface.blit(text_surface, (rect.x + 10, rect.y + 5))

        pygame.draw.rect(surface, (0, 200, 0), self.start_button_rect)
        start_text = self.font.render("Iniciar", True, WHITE)
        surface.blit(start_text, start_text.get_rect(center=self.start_button_rect.center))

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT),pygame.RESIZABLE)
        pygame.display.set_caption("Visualizador de Grafo Animado")
        self.clock = pygame.time.Clock()
        self.running = True
        self.game_state = 'menu' # 'menu', 'game', 'animating'
        self.round_counter = 0
        self.max_turn = 9

        self.animation_duration = 0.5 # em segundos
        self.animation_timer = 0.0

        self.tile_image = self._load_background_tile()
        self.menu = Menu()
        self.map = None
        self.hud = None

    def _load_background_tile(self):
        try:
            image = pygame.image.load("./assets/ground.jpg").convert()
            return pygame.transform.scale(image, (200, 200))
        except pygame.error as e:
            print(f"Não foi possível carregar a imagem de fundo: {e}")
            return None

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

            if self.game_state == 'animating':
                continue # Bloqueia input durante a animação

            if self.game_state == 'menu':
                action = self.menu.handle_event(event)
                if action == 'start_game':
                    self.start_game()
            
            elif self.game_state == 'game':
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.hud.left_arrow_rect.collidepoint(event.pos): self.change_turn(-1)
                    elif self.hud.right_arrow_rect.collidepoint(event.pos): self.change_turn(1)

    def update(self, dt):
        if self.game_state == 'animating':
            self.animation_timer += dt
            self.map.update_animation(dt)
            if not self.map.animating:
                self.game_state = 'game'

    def start_game(self):
        self.game_state = 'game'
        self.map = Map()
        self.hud = HUD(self.menu.player_names)
        self.change_turn(0, initial_load=True)

    def change_turn(self, direction, initial_load=False):
        if self.game_state != 'game': return
            
        new_turn = self.round_counter + direction if not initial_load else 0
        
        if -1 <= new_turn <= self.max_turn:
            self.round_counter = new_turn
            self.game_state = 'animating'
            self.map.prepare_turn_animation(new_turn, self.animation_duration)

    def draw(self):
        self._draw_background()
        if self.game_state == 'menu':
            self.menu.draw(self.screen)
        else:
            if self.map: self.map.draw(self.screen)
            if self.hud: self.hud.draw(self.screen, self.round_counter)
        
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