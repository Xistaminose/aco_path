#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Ponto de entrada principal do meu projeto de visualização de rotas
# Por enquanto só visualiza o mapa, mas logo vou adicionar o algoritmo ACO!

import sys
import os

# Gambiarra para fazer os imports funcionarem direito
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from aco_path.map_utils import load_city_map
from aco_path.map_visualization import visualize_map

def main():
    print("=== ACO Path Visualization ===")
    
    # Por enquanto os parâmetros são fixos, depois vou implementar um CLI
    city = "Uberaba, Brazil"
    origin = "shopping uberaba, Uberaba, Brazil"
    destination = "prefeitura de uberaba, Uberaba, Brazil"
    
    print(f"City: {city}")
    print(f"Origin: {origin}")
    print(f"Destination: {destination}")
    
    # Carrega o mapa e as coordenadas
    graph, origin_coords, dest_coords = load_city_map(city, origin, destination)
    
    # Roda a visualização
    visualize_map(graph, origin_coords, dest_coords)
    
    print("Visualização concluída!")

if __name__ == "__main__":
    main() 