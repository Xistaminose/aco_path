#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Módulo de utilitários para obtenção e gerenciamento de dados de mapas

import os
import pickle
import time
from pathlib import Path
from datetime import datetime, timedelta

import osmnx as ox
from osmnx.projection import project_geometry
from shapely.geometry import Point

# Configurações de cache
CACHE_DIR = Path(__file__).parent / "cache"
CACHE_EXPIRY_DAYS = 30


def ensure_cache_dir():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def get_graph_cache_path(city_name):
    city_filename = "".join(c if c.isalnum() else "_" for c in city_name.lower())
    return CACHE_DIR / f"{city_filename}.graphml"


def get_coords_cache_path(origin, destination):
    locations = f"{origin}_{destination}"
    filename = "".join(c if c.isalnum() else "_" for c in locations.lower())
    return CACHE_DIR / f"{filename}_coords.pkl"


def is_cache_valid(cache_path, max_age_days=CACHE_EXPIRY_DAYS):
    if not cache_path.exists():
        return False
    
    cache_time = datetime.fromtimestamp(cache_path.stat().st_mtime)
    expiry_time = datetime.now() - timedelta(days=max_age_days)
    return cache_time > expiry_time


def load_or_create_graph(city_name):
    # Função complexa: carrega um grafo do cache ou baixa novo do OpenStreetMap
    # Potencial melhoria futura: otimizar para baixar apenas a área de interesse
    cache_path = get_graph_cache_path(city_name)
    ensure_cache_dir()
    
    if is_cache_valid(cache_path):
        print(f"Carregando mapa em cache para {city_name}...")
        start_time = time.time()
        graph = ox.load_graphml(str(cache_path))
        print(f"Mapa carregado em {time.time() - start_time:.2f} segundos")
    else:
        print(f"Baixando dados de {city_name} do OpenStreetMap...")
        start_time = time.time()
        
        graph = ox.graph_from_place(city_name, network_type="drive")
        
        try:
            graph = ox.simplify_graph(graph)
        except Exception as e:
            print(f"Nota: Simplificação do grafo ignorada ({str(e)})")
        
        ox.save_graphml(graph, str(cache_path))
        print(f"Mapa baixado e salvo em {time.time() - start_time:.2f} segundos")
    
    graph_proj = ox.project_graph(graph)
    return graph_proj


def geocode_locations(origin, destination):
    cache_path = get_coords_cache_path(origin, destination)
    ensure_cache_dir()
    
    if is_cache_valid(cache_path):
        print("Carregando coordenadas em cache...")
        with open(cache_path, 'rb') as f:
            return pickle.load(f)
    
    print("Geocodificando localizações...")
    start_time = time.time()
    
    orig_latlon = ox.geocode(origin)
    dest_latlon = ox.geocode(destination)
    
    # Cria objetos Point (longitude, latitude) para funções GIS
    orig_point = Point(orig_latlon[1], orig_latlon[0])
    dest_point = Point(dest_latlon[1], dest_latlon[0])
    
    with open(cache_path, 'wb') as f:
        pickle.dump((orig_latlon, dest_latlon, orig_point, dest_point), f)
    
    print(f"Geocodificação concluída em {time.time() - start_time:.2f} segundos")
    return orig_latlon, dest_latlon, orig_point, dest_point


def project_points(graph, orig_point, dest_point):
    orig_projected, _ = project_geometry(orig_point, to_crs=graph.graph['crs'])
    dest_projected, _ = project_geometry(dest_point, to_crs=graph.graph['crs'])
    
    origin_coords = (orig_projected.x, orig_projected.y)
    dest_coords = (dest_projected.x, dest_projected.y)
    
    return origin_coords, dest_coords


def load_city_map(city_name, origin, destination):
    # Função principal que coordena o carregamento do mapa e geocodificação
    graph = load_or_create_graph(city_name)
    
    orig_latlon, dest_latlon, orig_point, dest_point = geocode_locations(origin, destination)
    
    origin_coords, dest_coords = project_points(graph, orig_point, dest_point)
    
    print(f"Coordenadas de origem: {origin_coords}")
    print(f"Coordenadas de destino: {dest_coords}")
    
    return graph, origin_coords, dest_coords 