# ACO Path: Visualização de Mapas de Alta Performance com Python e py5

Este repositório contém o código fonte para a série de posts **"Visualização de Mapas de Alta Performance com Python e py5"** publicada em [xistaminose.com](https://xistaminose.com/posts/aco-blog-post-part1).

## Sobre o Projeto

Este projeto demonstra como criar uma visualização de mapas urbanos de alta performance utilizando Python, desafiando a noção de que Python não seria adequado para renderização gráfica em tempo real. O sistema permite:

- Visualizar mapas urbanos com milhares de segmentos de ruas a 60 FPS
- Destacar pontos de origem e destino com efeitos visuais
- Implementar técnicas avançadas de otimização para máxima performance

Este repositório implementa o código descrito na **Parte 1** da série, focando nas técnicas de visualização e otimização de desempenho. As próximas partes da série implementarão o algoritmo de colônia de formigas (ACO) para encontrar rotas otimizadas.

## Principais Otimizações

A visualização utiliza várias técnicas para atingir desempenho máximo:

- **Renderização em lote**: uso de PShape e vértices para reduzir chamadas de API gráficas
- **Buffers off-screen**: renderização em PGraphics para minimizar o retrabalho em cada frame
- **Filtragem inteligente**: remoção agressiva de elementos não visíveis antes da renderização
- **Cache eficiente**: armazenamento local de dados de mapas para carregamento rápido
- **Efeitos visuais otimizados**: desvanecimento suave nas bordas e efeitos de pulso

## Requisitos

```
python 3.8+
osmnx==1.3.0
networkx==3.1
shapely==2.0.1
py5==0.8.2
numpy==1.24.3
scipy==1.10.1
```

## Instalação

1. Clone este repositório:
   ```bash
   git clone https://github.com/seu-usuario/aco-path.git
   cd aco-path
   ```

2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

## Como Executar

Para executar a visualização com os parâmetros padrão (Uberaba, Brasil):

```bash
python -m aco_path.main
```

### Controles:

- **F**: Mostrar/ocultar contador de FPS
- **S**: Salvar screenshot do mapa atual
- **ESC**: Sair da visualização

## Estrutura do Projeto

```
aco_path/
├── __init__.py
├── main.py                # Ponto de entrada principal
├── map_utils.py           # Funções para carregar e processar mapas
├── map_visualization.py   # Funções de visualização com otimizações
└── cache/                 # Armazena dados para carregamento rápido
```

## Série de Blog Posts

Este projeto faz parte de uma série de posts sobre visualização de mapas e algoritmos de otimização:

- **Parte 1**: [Visualização de Mapas de Alta Performance com Python e py5](https://xistaminose.com/posts/aco-blog-post-part1)
- **Parte 2**: Implementação do Algoritmo ACO (em breve)
- **Parte 3**: Otimizações Avançadas (em breve)

## Licença

MIT

---

*"Este projeto demonstra como, com as técnicas certas de otimização e as bibliotecas adequadas, podemos superar as limitações de desempenho de Python e atingir resultados impressionantes."* 