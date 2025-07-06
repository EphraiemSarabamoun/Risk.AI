"""Risk board representation.

This module defines the continents, territories and adjacency graph for the classic Risk board game. It provides a CLI to print or draw the board.
"""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Board:
    continents: Dict[str, List[str]] = field(default_factory=dict)
    adjacency: Dict[str, List[str]] = field(default_factory=dict)
    continent_bonuses: Dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self._init_continents()
        self._init_adjacency()
        self._init_positions()
        self._init_continent_bonuses()

    def _init_continents(self) -> None:
        self.continents = {
            "North America": [
                "Alaska",
                "Northwest Territory",
                "Greenland",
                "Alberta",
                "Ontario",
                "Quebec",
                "Western United States",
                "Eastern United States",
                "Central America",
            ],
            "South America": [
                "Venezuela",
                "Peru",
                "Brazil",
                "Argentina",
            ],
            "Europe": [
                "Iceland",
                "Scandinavia",
                "Ukraine",
                "Great Britain",
                "Northern Europe",
                "Western Europe",
                "Southern Europe",
            ],
            "Africa": [
                "North Africa",
                "Egypt",
                "East Africa",
                "Congo",
                "South Africa",
                "Madagascar",
            ],
            "Asia": [
                "Ural",
                "Siberia",
                "Yakutsk",
                "Kamchatka",
                "Irkutsk",
                "Mongolia",
                "Japan",
                "Afghanistan",
                "Middle East",
                "India",
                "Siam",
                "China",
            ],
            "Australia": [
                "Indonesia",
                "New Guinea",
                "Western Australia",
                "Eastern Australia",
            ],
        }

    def _init_adjacency(self) -> None:
        a = {
            "Alaska": ["Northwest Territory", "Alberta", "Kamchatka"],
            "Northwest Territory": [
                "Alaska",
                "Alberta",
                "Ontario",
                "Greenland",
            ],
            "Greenland": ["Northwest Territory", "Ontario", "Quebec", "Iceland"],
            "Alberta": [
                "Alaska",
                "Northwest Territory",
                "Ontario",
                "Western United States",
            ],
            "Ontario": [
                "Northwest Territory",
                "Greenland",
                "Quebec",
                "Eastern United States",
                "Western United States",
                "Alberta",
            ],
            "Quebec": ["Ontario", "Greenland", "Eastern United States"],
            "Western United States": [
                "Alberta",
                "Ontario",
                "Eastern United States",
                "Central America",
            ],
            "Eastern United States": [
                "Western United States",
                "Ontario",
                "Quebec",
                "Central America",
            ],
            "Central America": [
                "Western United States",
                "Eastern United States",
                "Venezuela",
            ],
            "Venezuela": ["Central America", "Brazil", "Peru"],
            "Peru": ["Venezuela", "Brazil", "Argentina"],
            "Brazil": ["Venezuela", "Peru", "Argentina", "North Africa"],
            "Argentina": ["Peru", "Brazil"],
            "Iceland": ["Greenland", "Great Britain", "Scandinavia"],
            "Scandinavia": ["Iceland", "Ukraine", "Northern Europe", "Great Britain"],
            "Ukraine": [
                "Scandinavia",
                "Northern Europe",
                "Ural",
                "Afghanistan",
                "Middle East",
                "Southern Europe",
            ],
            "Great Britain": ["Iceland", "Scandinavia", "Northern Europe", "Western Europe"],
            "Northern Europe": [
                "Great Britain",
                "Scandinavia",
                "Ukraine",
                "Southern Europe",
                "Western Europe",
            ],
            "Western Europe": ["Great Britain", "Northern Europe", "Southern Europe", "North Africa"],
            "Southern Europe": [
                "Western Europe",
                "Northern Europe",
                "Ukraine",
                "Middle East",
                "Egypt",
                "North Africa",
            ],
            "North Africa": [
                "Brazil",
                "Western Europe",
                "Southern Europe",
                "Egypt",
                "East Africa",
                "Congo",
            ],
            "Egypt": ["Southern Europe", "Middle East", "East Africa", "North Africa"],
            "East Africa": ["Egypt", "North Africa", "Congo", "South Africa", "Madagascar", "Middle East"],
            "Congo": ["North Africa", "East Africa", "South Africa"],
            "South Africa": ["Congo", "East Africa", "Madagascar"],
            "Madagascar": ["East Africa", "South Africa"],
            "Ural": ["Ukraine", "Siberia", "China", "Afghanistan"],
            "Siberia": ["Ural", "Yakutsk", "Irkutsk", "Mongolia", "China"],
            "Yakutsk": ["Siberia", "Kamchatka", "Irkutsk"],
            "Kamchatka": ["Yakutsk", "Irkutsk", "Mongolia", "Japan", "Alaska"],
            "Irkutsk": ["Siberia", "Yakutsk", "Kamchatka", "Mongolia"],
            "Mongolia": ["Siberia", "Irkutsk", "Kamchatka", "Japan", "China"],
            "Japan": ["Kamchatka", "Mongolia"],
            "Afghanistan": ["Ukraine", "Ural", "China", "Middle East", "India"],
            "Middle East": ["Ukraine", "Afghanistan", "India", "East Africa", "Egypt", "Southern Europe"],
            "India": ["Middle East", "Afghanistan", "China", "Siam"],
            "Siam": ["India", "China", "Indonesia"],
            "China": ["Ural", "Siberia", "Mongolia", "Siam", "India", "Afghanistan"],
            "Indonesia": ["Siam", "New Guinea", "Western Australia"],
            "New Guinea": ["Indonesia", "Western Australia", "Eastern Australia"],
            "Western Australia": ["Indonesia", "New Guinea", "Eastern Australia"],
            "Eastern Australia": ["New Guinea", "Western Australia"],
        }
        self.adjacency = a

    def _init_continent_bonuses(self) -> None:
        self.continent_bonuses = {
            "North America": 5,
            "South America": 2,
            "Europe": 5,
            "Africa": 3,
            "Asia": 7,
            "Australia": 2,
        }

    def _init_positions(self) -> None:
        self.positions = {
            # North America
            'Alaska': (10, 100),
            'Northwest Territory': (150, 100),
            'Greenland': (400, 80),
            'Alberta': (150, 200),
            'Ontario': (250, 200),
            'Quebec': (350, 200),
            'Western United States': (150, 300),
            'Eastern United States': (250, 300),
            'Central America': (150, 400),
            # South America
            'Venezuela': (200, 500),
            'Peru': (200, 600),
            'Brazil': (300, 550),
            'Argentina': (250, 700),
            # Europe
            'Iceland': (500, 150),
            'Scandinavia': (600, 150),
            'Great Britain': (500, 250),
            'Northern Europe': (600, 250),
            'Western Europe': (500, 350),
            'Southern Europe': (600, 350),
            'Ukraine': (700, 200),
            # Africa
            'North Africa': (550, 500),
            'Egypt': (650, 450),
            'East Africa': (700, 550),
            'Congo': (650, 650),
            'South Africa': (650, 750),
            'Madagascar': (780, 780),
            # Asia
            'Ural': (800, 200),
            'Siberia': (900, 150),
            'Yakutsk': (1000, 100),
            'Kamchatka': (1100, 100),
            'Irkutsk': (950, 250),
            'Mongolia': (1000, 320),
            'Japan': (1150, 280),
            'Afghanistan': (800, 300),
            'Middle East': (750, 400),
            'India': (850, 480),
            'Siam': (950, 500),
            'China': (900, 380),
            # Australia
            'Indonesia': (1000, 600),
            'New Guinea': (1100, 600),
            'Western Australia': (1000, 700),
            'Eastern Australia': (1100, 700),
        }

    def are_connected(self, terr1, terr2, player, territory_owner):
        """Check if two territories are connected by a path of territories owned by the player."""
        if terr1 not in self.adjacency or terr2 not in self.adjacency:
            return False

        q = [terr1]
        visited = {terr1}

        while q:
            current = q.pop(0)
            if current == terr2:
                return True
            
            for neighbor in self.adjacency[current]:
                if neighbor not in visited and territory_owner.get(neighbor) == player:
                    visited.add(neighbor)
                    q.append(neighbor)
        
        return False

    def are_connected(self, terr1: str, terr2: str, player: 'Player', territory_owner: Dict[str, 'Player']) -> bool:
        """Check if two territories are connected by a path of territories owned by the player."""
        if terr1 not in self.adjacency or terr2 not in self.adjacency:
            return False

        q = [terr1]
        visited = {terr1}

        while q:
            current = q.pop(0)
            if current == terr2:
                return True
            
            for neighbor in self.adjacency[current]:
                if neighbor not in visited and territory_owner.get(neighbor) == player:
                    visited.add(neighbor)
                    q.append(neighbor)
        
        return False

    def print_board(self) -> None:
        for continent, territories in self.continents.items():
            print(continent)
            for t in territories:
                neighbors = ", ".join(self.adjacency.get(t, []))
                print(f"  {t}: {neighbors}")
            print()

    def draw_board(self) -> None:
        """Display the board graph using networkx and matplotlib."""
        import networkx as nx
        import matplotlib.pyplot as plt

        G = nx.Graph()
        for t, neighbors in self.adjacency.items():
            for n in neighbors:
                if not G.has_edge(t, n):
                    G.add_edge(t, n)

        territory_to_continent = {}
        for continent, territories in self.continents.items():
            for terr in territories:
                territory_to_continent[terr] = continent

        cmap = plt.cm.get_cmap("tab10", len(self.continents))
        continents = list(self.continents.keys())
        node_colors = [cmap(continents.index(territory_to_continent[node])) for node in G.nodes]

        pos = nx.spring_layout(G, seed=42)
        plt.figure(figsize=(12, 8))
        nx.draw_networkx(G, pos, node_color=node_colors, with_labels=True, node_size=500, font_size=8)
        plt.axis("off")
        plt.show()


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Risk board CLI")
    parser.add_argument("--draw", action="store_true", help="Display the board graphically")
    args = parser.parse_args()

    board = Board()
    print(args.draw)
    board.draw_board()
    if args.draw:
        board.draw_board()
    else:
        board.print_board()


if __name__ == "__main__":
    main()
