"""Simple Risk game simulation between a human and a bot."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List

from risk_board import Board


@dataclass
class TerritoryState:
    """Owner and army count for a territory."""

    owner: str
    armies: int = 1


@dataclass
class Game:
    """Minimal Risk game supporting a human vs bot."""

    board: Board = field(default_factory=Board)
    state: Dict[str, TerritoryState] = field(init=False)
    players: List[str] = field(default_factory=lambda: ["Human", "Bot"])

    def __post_init__(self) -> None:
        self._init_state()

    def _init_state(self) -> None:
        """Randomly assign territories between the players."""
        self.state = {
            t: TerritoryState(owner=None)
            for territories in self.board.continents.values()
            for t in territories
        }
        territories = list(self.state.keys())
        random.shuffle(territories)
        for idx, terr in enumerate(territories):
            self.state[terr].owner = self.players[idx % len(self.players)]

    def territories_of(self, player: str) -> List[str]:
        return [t for t, s in self.state.items() if s.owner == player]

    def print_state(self) -> None:
        score = {p: len(self.territories_of(p)) for p in self.players}
        print(f"Territories controlled: {score}")
        for continent, terrs in self.board.continents.items():
            print(continent)
            for t in terrs:
                s = self.state[t]
                print(f"  {t}: {s.owner}")
            print()

    def attack(self, attacker: str, src: str, dst: str) -> bool:
        if dst not in self.board.adjacency.get(src, []):
            print("Territories are not adjacent.")
            return False
        src_state = self.state[src]
        dst_state = self.state[dst]
        if src_state.owner != attacker or dst_state.owner == attacker:
            print("Invalid attack.")
            return False

        if random.random() < 0.5:
            print(f"{attacker} conquers {dst} from {dst_state.owner}.")
            dst_state.owner = attacker
        else:
            print(f"{attacker}'s attack on {dst} failed.")
        return True

    def play_human_turn(self) -> None:
        self.print_state()
        cmd = input("Enter attack as 'from to' or press Enter to skip: ").strip()
        if not cmd:
            return
        parts = cmd.split()
        if len(parts) != 2:
            print("Invalid input.")
            return
        self.attack("Human", parts[0], parts[1])

    def play_bot_turn(self) -> None:
        src_options = [
            t
            for t in self.territories_of("Bot")
            if any(self.state[n].owner != "Bot" for n in self.board.adjacency[t])
        ]
        if not src_options:
            return
        src = random.choice(src_options)
        targets = [n for n in self.board.adjacency[src] if self.state[n].owner != "Bot"]
        if not targets:
            return
        dst = random.choice(targets)
        print(f"Bot attacks from {src} to {dst}")
        self.attack("Bot", src, dst)

    def play(self) -> None:
        while True:
            if len(self.territories_of("Human")) == 0:
                print("Bot wins!")
                break
            if len(self.territories_of("Bot")) == 0:
                print("Human wins!")
                break
            self.play_human_turn()
            if len(self.territories_of("Bot")) == 0:
                print("Human wins!")
                break
            self.play_bot_turn()


def main() -> None:
    Game().play()


if __name__ == "__main__":
    main()
