"""Risk board representation.

This module defines the continents, territories and adjacency graph for the classic Risk board game. It provides a CLI to print or draw the board.
"""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Board:
    continents: Dict[str, List[str]] = field(default_factory=dict)
    adjacency: Dict[str, List[str]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self._init_continents()
        self._init_adjacency()

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
