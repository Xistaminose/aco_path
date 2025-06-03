#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Visualização de mapas para o projeto ACO Path Finding

import math
import numpy as np
import py5
import networkx as nx
import osmnx as ox
from scipy.spatial import distance
from collections import deque

# Configurações visuais
BACKGROUND_COLOR = (40, 42, 46)  # Cinza escuro pro fundo
STREET_COLOR = (70, 72, 76)      # Cinza um pouco mais escuro pras ruas
ORIGIN_COLOR = (50, 180, 220)    # Azul ciano para o ponto de origem
DEST_COLOR = (220, 50, 180)      # Rosa/roxo para o destino
BORDER_COLOR = (30, 32, 36)      # Cinza bem escuro para a borda circular
UI_TEXT_COLOR = (220, 220, 220)  # Cinza claro para o texto da UI

# Buffer ao redor dos pontos..
BUFFER_PERCENTAGE = 0.3

# Parâmetros de visualização
FADE_EDGE_START = 0.75  # Percentual do raio onde o fade começa
FADE_INTENSITY = 2.0    # Controla quão rápido as ruas somem
STREET_BUFFER_FACTOR = 1.8  # Quanto maior o buffer de ruas comparado à área visível

# Configurações de animação
pulse_counter = 0
BASE_POINT_SIZE = 10
PULSE_AMPLITUDE = 4
PULSE_SPEED = 0.08
PULSE_OFFSET = math.pi

# Monitoramento de desempenho
show_fps = True
fps_history = deque(maxlen=60)
fps_update_interval = 10

# Configurações dos agentes (formigas)
ANT_COLOR = (240, 240, 50)
ANT_SIZE = 6
ANT_SPEED = 120  # unidades de tela por segundo
NUM_ANTS = 15

# Estado da visualização
graph = None
nodes = {}
edge_data = []
visible_edges = []
origin_coords = None
dest_coords = None
scale_x = None
scale_y = None
min_x = None
min_y = None
max_x = None
max_y = None
center_x = None
center_y = None
circle_radius = None
circle_center_x = None
circle_center_y = None
is_initialized = False
street_buffer = None
streets_pg = None
streets_dirty = True
street_shapes = {}

# Lista de formigas e caminho precomputado em coordenadas de tela
ants = []
ant_path_screen = []


def calculate_view_boundaries(origin, destination, buffer_percentage=BUFFER_PERCENTAGE):
    # Calcula os limites da área de visualização baseados na origem e destino
    global min_x, min_y, max_x, max_y, center_x, center_y
    
    path_min_x = min(origin[0], destination[0])
    path_max_x = max(origin[0], destination[0])
    path_min_y = min(origin[1], destination[1])
    path_max_y = max(origin[1], destination[1])
    
    width_span = path_max_x - path_min_x
    height_span = path_max_y - path_min_y
    
    min_view_size = 1000  # metros
    
    if width_span < min_view_size:
        center_x = (path_min_x + path_max_x) / 2
        path_min_x = center_x - min_view_size / 2
        path_max_x = center_x + min_view_size / 2
        width_span = min_view_size
    
    if height_span < min_view_size:
        center_y = (path_min_y + path_max_y) / 2
        path_min_y = center_y - min_view_size / 2
        path_max_y = center_y + min_view_size / 2
        height_span = min_view_size
    
    buffer_x = width_span * buffer_percentage
    buffer_y = height_span * buffer_percentage
    
    min_x = path_min_x - buffer_x
    max_x = path_max_x + buffer_x
    min_y = path_min_y - buffer_y
    max_y = path_max_y + buffer_y
    
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    
    return min_x, min_y, max_x, max_y, center_x, center_y


def is_point_in_view_circle(x, y, center_x, center_y, radius):
    buffer_radius = radius * STREET_BUFFER_FACTOR
    dx = x - center_x
    dy = y - center_y
    return (dx**2 + dy**2) <= buffer_radius**2


def prepare_graph_data(graph_data):
    # Função complexa: extrai e filtra dados do grafo para visualização eficiente
    global nodes, edge_data, visible_edges
    
    nodes = {n: (data['x'], data['y']) for n, data in graph_data.nodes(data=True)}
    
    world_center_x = min_x + (max_x - min_x) / 2
    world_center_y = min_y + (max_y - min_y) / 2
    world_radius = min((max_x - min_x), (max_y - min_y)) / 2
    
    edge_data = []
    for u, v, data in graph_data.edges(data=True):
        if u in nodes and v in nodes:
            x1, y1 = nodes[u]
            x2, y2 = nodes[v]
            dist = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            edge_data.append((u, v, dist, x1, y1, x2, y2))
    
    visible_edges = []
    for u, v, dist, x1, y1, x2, y2 in edge_data:
        if (is_point_in_view_circle(x1, y1, world_center_x, world_center_y, world_radius) or
            is_point_in_view_circle(x2, y2, world_center_x, world_center_y, world_radius)):
            visible_edges.append((x1, y1, x2, y2))
    
    print(f"Total de arestas: {len(edge_data)}, Arestas visíveis: {len(visible_edges)}")


def get_distance_fade_factor(distance_to_center, radius):
    relative_distance = distance_to_center / radius
    
    if relative_distance <= FADE_EDGE_START:
        return 1.0
    
    fade_amount = 1.0 - ((relative_distance - FADE_EDGE_START) / (1.0 - FADE_EDGE_START))
    return max(0.0, min(1.0, fade_amount ** FADE_INTENSITY))


def precompute_street_buffer():
    # Função complexa: pré-calcula buffer de ruas para otimizar renderização
    # Podemos melhorar isso no futuro com técnicas de LOD (Level of Detail)
    global street_buffer, streets_dirty, street_shapes
    
    if scale_x is None or scale_y is None or circle_center_x is None or circle_center_y is None:
        return
    
    print("Pré-calculando buffer de ruas...")
    
    street_buffer = {}
    street_shapes = {}
    
    translate_x = circle_center_x - (max_x - min_x) * scale_x / 2
    translate_y = circle_center_y - (max_y - min_y) * scale_y / 2
    
    filtered_edges = []
    max_distance = circle_radius * STREET_BUFFER_FACTOR
    
    for x1, y1, x2, y2 in visible_edges:
        sx1 = world_to_screen_x(x1)
        sy1 = world_to_screen_y(y1)
        sx2 = world_to_screen_x(x2)
        sy2 = world_to_screen_y(y2)
        
        abs_sx1 = sx1 + translate_x
        abs_sy1 = sy1 + translate_y
        abs_sx2 = sx2 + translate_x
        abs_sy2 = sy2 + translate_y
        
        dist1_to_center = math.sqrt((abs_sx1 - circle_center_x)**2 + (abs_sy1 - circle_center_y)**2)
        dist2_to_center = math.sqrt((abs_sx2 - circle_center_x)**2 + (abs_sy2 - circle_center_y)**2)
        
        if dist1_to_center <= max_distance or dist2_to_center <= max_distance:
            filtered_edges.append((x1, y1, x2, y2))
    
    visible_edges_count = len(filtered_edges)
    print(f"Arestas visíveis filtradas: {visible_edges_count} (reduzidas em {len(visible_edges) - visible_edges_count} segmentos)")
    
    for x1, y1, x2, y2 in filtered_edges:
        sx1 = world_to_screen_x(x1)
        sy1 = world_to_screen_y(y1)
        sx2 = world_to_screen_x(x2)
        sy2 = world_to_screen_y(y2)
        
        abs_sx1 = sx1 + translate_x
        abs_sy1 = sy1 + translate_y
        abs_sx2 = sx2 + translate_x
        abs_sy2 = sy2 + translate_y
        
        dist1_to_center = math.sqrt((abs_sx1 - circle_center_x)**2 + (abs_sy1 - circle_center_y)**2)
        dist2_to_center = math.sqrt((abs_sx2 - circle_center_x)**2 + (abs_sy2 - circle_center_y)**2)
        
        fade1 = get_distance_fade_factor(dist1_to_center, circle_radius)
        fade2 = get_distance_fade_factor(dist2_to_center, circle_radius)
        
        avg_fade = (fade1 + fade2) / 2
        
        if avg_fade > 0.01:
            opacity = int(avg_fade * 255)
            
            if opacity not in street_buffer:
                street_buffer[opacity] = []
            street_buffer[opacity].append((sx1, sy1, sx2, sy2))
    
    for opacity in street_buffer:
        segments = street_buffer[opacity]
        shape = py5.create_shape()
        shape.begin_shape(py5.LINES)
        shape.no_fill()
        shape.stroke(*STREET_COLOR, opacity)
        shape.stroke_weight(1.2)
        
        for sx1, sy1, sx2, sy2 in segments:
            shape.vertex(sx1, sy1)
            shape.vertex(sx2, sy2)
            
        shape.end_shape()
        street_shapes[opacity] = shape
    
    streets_dirty = True
    
    total_segments = sum(len(segments) for segments in street_buffer.values())
    print(f"Buffer de ruas pré-calculado com {total_segments} segmentos de rua visíveis")


def create_streets_buffer():
    global streets_pg, streets_dirty
    
    if streets_pg is None:
        streets_pg = py5.create_graphics(py5.width, py5.height)
    
    if streets_dirty:
        print("Criando buffer de ruas...")
        
        streets_pg.begin_draw()
        streets_pg.background(0, 0, 0, 0)
        
        streets_pg.translate(circle_center_x - (max_x - min_x) * scale_x / 2, 
                           circle_center_y - (max_y - min_y) * scale_y / 2)
        
        sorted_opacities = sorted(street_shapes.keys())
        for opacity in sorted_opacities:
            streets_pg.shape(street_shapes[opacity], 0, 0)
        
        streets_pg.end_draw()
        
        streets_dirty = False
        print("Buffer de ruas criado")


def world_to_screen_x(x):
    return (x - min_x) * scale_x


def world_to_screen_y(y):
    return (max_y - y) * scale_y


def is_point_in_circle(x, y):
    dx = x - circle_center_x
    dy = y - circle_center_y
    return (dx**2 + dy**2) <= circle_radius**2


def calculate_distance_to_circle_edge(x, y):
    dx = x - circle_center_x
    dy = y - circle_center_y
    dist_to_center = math.sqrt(dx**2 + dy**2)
    
    dist_to_edge = circle_radius - dist_to_center
    
    normalized_dist = max(0, min(1, dist_to_edge / (circle_radius * 0.3)))

    return normalized_dist


class Ant:
    def __init__(self, path):
        self.segments = []
        self.lengths = []
        for i in range(len(path) - 1):
            x1, y1 = path[i]
            x2, y2 = path[i + 1]
            self.segments.append((x1, y1, x2, y2))
            self.lengths.append(math.hypot(x2 - x1, y2 - y1))
        self.total_length = sum(self.lengths)
        self.progress = 0.0

    def update(self, dt):
        if self.total_length == 0:
            return
        self.progress = (self.progress + ANT_SPEED * dt) % self.total_length

    def get_position(self):
        remaining = self.progress
        for (x1, y1, x2, y2), seg_len in zip(self.segments, self.lengths):
            if remaining <= seg_len:
                t = remaining / seg_len if seg_len else 0
                x = x1 + (x2 - x1) * t
                y = y1 + (y2 - y1) * t
                return x, y
            remaining -= seg_len
        return self.segments[-1][2], self.segments[-1][3]

    def draw(self):
        x, y = self.get_position()
        py5.no_stroke()
        py5.fill(*ANT_COLOR)
        py5.circle(x, y, ANT_SIZE)


def compute_shortest_path():
    if not nodes:
        return []
    try:
        orig_node = ox.distance.nearest_nodes(graph, origin_coords[0], origin_coords[1])
        dest_node = ox.distance.nearest_nodes(graph, dest_coords[0], dest_coords[1])
        path_nodes = nx.shortest_path(graph, orig_node, dest_node, weight="length")
        return [nodes[n] for n in path_nodes]
    except Exception as e:
        print(f"Erro ao calcular caminho: {e}")
        return []


def generate_ants(num=NUM_ANTS):
    global ants, ant_path_screen
    path = compute_shortest_path()
    ant_path_screen = [(world_to_screen_x(x), world_to_screen_y(y)) for x, y in path]
    ants = [Ant(ant_path_screen) for _ in range(num)]


def update_ants(dt):
    for ant in ants:
        ant.update(dt)


def draw_ants():
    for ant in ants:
        ant.draw()


def sketch_settings():
    py5.size(800, 800)
    py5.smooth(4)


def sketch_setup():
    global scale_x, scale_y, circle_radius, circle_center_x, circle_center_y
    
    py5.background(*BACKGROUND_COLOR)
    
    width_ratio = py5.width / (max_x - min_x)
    height_ratio = py5.height / (max_y - min_y)
    scale_factor = min(width_ratio, height_ratio) * 0.92  # Aumentei de 0.8 para mais zoom
    
    scale_x = scale_factor
    scale_y = scale_factor
    
    circle_radius = min(py5.width, py5.height) * 0.49
    circle_center_x = py5.width / 2
    circle_center_y = py5.height / 2
    
    precompute_street_buffer()
    
    try:
        py5.text_font(py5.create_font("DejaVu Sans", 14))
    except:
        print("Fontes disponíveis:", py5.PFont.list())
        py5.text_size(14)
    
    create_streets_buffer()

    generate_ants()

    py5.frame_rate(60)


def sketch_draw():
    # Função principal de desenho - atualiza a cada frame
    global pulse_counter, fps_history
    
    current_fps = py5.get_frame_rate()
    fps_history.append(current_fps)
    dt = 1.0 / current_fps if current_fps > 0 else 0.016
    
    pulse_counter += PULSE_SPEED
    
    origin_pulse_effect = math.sin(pulse_counter) * PULSE_AMPLITUDE
    dest_pulse_effect = math.sin(pulse_counter + PULSE_OFFSET) * PULSE_AMPLITUDE
    
    py5.background(*BACKGROUND_COLOR)
    
    py5.no_stroke()
    py5.fill(*BACKGROUND_COLOR)
    py5.circle(circle_center_x, circle_center_y, circle_radius * 2)
    
    if streets_pg is not None:
        py5.image(streets_pg, 0, 0)
    
    py5.push_matrix()
    py5.translate(circle_center_x - (max_x - min_x) * scale_x / 2,
                 circle_center_y - (max_y - min_y) * scale_y / 2)
    
    if origin_coords and dest_coords:
        orig_x = world_to_screen_x(origin_coords[0])
        orig_y = world_to_screen_y(origin_coords[1])
        
        dest_x = world_to_screen_x(dest_coords[0])
        dest_y = world_to_screen_y(dest_coords[1])
        
        origin_point_size = BASE_POINT_SIZE + origin_pulse_effect
        dest_point_size = BASE_POINT_SIZE + dest_pulse_effect
        
        origin_glow_max_size = origin_point_size * 3
        dest_glow_max_size = dest_point_size * 3
        
        py5.no_stroke()
        for i in range(5, 0, -1):
            pulse_opacity = 150 // i + int(abs(origin_pulse_effect) * 3)
            current_size = (origin_glow_max_size / 5) * i + origin_pulse_effect
            py5.fill(*ORIGIN_COLOR, min(255, pulse_opacity))
            py5.circle(orig_x, orig_y, current_size)
        
        py5.fill(*ORIGIN_COLOR)
        py5.circle(orig_x, orig_y, origin_point_size)
        
        py5.no_stroke()
        for i in range(5, 0, -1):
            pulse_opacity = 150 // i + int(abs(dest_pulse_effect) * 3)
            current_size = (dest_glow_max_size / 5) * i + dest_pulse_effect
            py5.fill(*DEST_COLOR, min(255, pulse_opacity))
            py5.circle(dest_x, dest_y, current_size)
        
        py5.fill(*DEST_COLOR)
        py5.circle(dest_x, dest_y, dest_point_size)

    update_ants(dt)
    draw_ants()

    py5.pop_matrix()
    
    if show_fps:
        draw_fps_counter()


def draw_fps_counter():
    current_fps = py5.get_frame_rate()
    
    if len(fps_history) > 0:
        avg_fps = sum(fps_history) / len(fps_history)
        min_fps = min(fps_history)
        max_fps = max(fps_history)
    else:
        avg_fps = current_fps
        min_fps = current_fps
        max_fps = current_fps
    
    py5.fill(0, 0, 0, 150)
    py5.no_stroke()
    py5.rect(10, 10, 200, 70, 5)
    
    py5.fill(*UI_TEXT_COLOR)
    py5.text_align(py5.LEFT)
    py5.text(f"FPS: {current_fps:.1f}", 20, 30)
    py5.text(f"Média: {avg_fps:.1f} fps", 20, 50)
    py5.text(f"Min: {min_fps:.1f} | Max: {max_fps:.1f}", 20, 70)
    
    total_segments = sum(len(segments) for segments in street_buffer.values()) if street_buffer else 0
    py5.text(f"Ruas: {total_segments}", 20, 90)


def sketch_key_pressed():
    global show_fps
    
    if py5.key == 's':
        py5.save_frame("aco_map_####.png")
        print("Imagem salva!")
    elif py5.key == 'f':
        show_fps = not show_fps
        print(f"Contador de FPS {'ativado' if show_fps else 'desativado'}")
    elif py5.key == py5.ESC:
        py5.exit_sketch()


def visualize_map(graph_data, origin, destination):
    global graph, origin_coords, dest_coords, is_initialized
    
    graph = graph_data
    origin_coords = origin
    dest_coords = destination
    
    calculate_view_boundaries(origin, destination)
    
    prepare_graph_data(graph)
    
    is_initialized = True
    
    py5.run_sketch(sketch_functions={
        "settings": sketch_settings,
        "setup": sketch_setup,
        "draw": sketch_draw,
        "key_pressed": sketch_key_pressed
    }) 