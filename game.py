"""Simple Risk-like game between a human and a bot."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List

from risk_board import Board


@dataclass
class Player:
    name: str
    is_bot: bool = False
    territories: List[str] = field(default_factory=list)

    def has_territories(self) -> bool:
        return len(self.territories) > 0


class Game:
    def __init__(self) -> None:
        self.board = Board()
        self.territory_owner: Dict[str, Player] = {}
        self.armies: Dict[str, int] = {}
        self.human = Player("Human")
        self.bot = Player("Bot", is_bot=True)
        self.players = [self.human, self.bot]
        self._setup()

    def _setup(self) -> None:
        """Assign territories equally and place one army on each."""
        territories = [t for ts in self.board.continents.values() for t in ts]
        random.shuffle(territories)
        turn = 0
        for terr in territories:
            player = self.players[turn % 2]
            player.territories.append(terr)
            self.territory_owner[terr] = player
            self.armies[terr] = 1
            turn += 1

    def display_board(self) -> None:
        """Print current ownership and armies for all territories."""
        for terr in sorted(self.territory_owner.keys()):
            owner = self.territory_owner[terr].name[0]
            print(f"{terr:20} {owner} {self.armies[terr]}")

    def attack(self, attacker: Player, from_terr: str, to_terr: str) -> None:
        """Resolve an attack from one territory to another."""
        if self.armies[from_terr] < 2:
            print("Not enough armies to attack.")
            return
        if to_terr not in self.board.adjacency[from_terr]:
            print("Territories are not adjacent.")
            return
        if self.territory_owner[to_terr] == attacker:
            print("Cannot attack your own territory.")
            return

        attack_roll = random.randint(1, 6)
        defend_roll = random.randint(1, 6)
        print(f"Attack roll: {attack_roll} - Defend roll: {defend_roll}")
        if attack_roll > defend_roll:
            defender = self.territory_owner[to_terr]
            defender.territories.remove(to_terr)
            attacker.territories.append(to_terr)
            self.territory_owner[to_terr] = attacker
            self.armies[from_terr] -= 1
            self.armies[to_terr] = 1
            print(f"{attacker.name} captured {to_terr}!")
        else:
            self.armies[from_terr] -= 1
            print(f"{attacker.name} lost one army in the attack.")

    def bot_turn(self) -> None:
        """Simple bot that attacks randomly if possible."""
        random.shuffle(self.bot.territories)
        for terr in self.bot.territories:
            if self.armies[terr] < 2:
                continue
            targets = [t for t in self.board.adjacency[terr] if self.territory_owner[t] != self.bot]
            if targets:
                target = random.choice(targets)
                print(f"Bot attacks from {terr} to {target}")
                self.attack(self.bot, terr, target)
                return
        print("Bot passes.")

    def human_turn(self) -> bool:
        """Handle the human player's turn. Returns False if quitting."""
        while True:
            action = input("Enter command (attack from to / pass / quit): ").strip()
            if action == "pass":
                return True
            if action == "quit":
                return False
            parts = action.split()
            if len(parts) == 3 and parts[0] == "attack":
                _, from_terr, to_terr = parts
                if from_terr not in self.human.territories:
                    print("You do not own that territory.")
                    continue
                self.attack(self.human, from_terr, to_terr)
                return True
            print("Invalid command.")

    def play(self) -> None:
        """Main game loop."""
        turn = 0
        while self.human.has_territories() and self.bot.has_territories():
            current_player = self.players[turn % 2]
            print()
            print("Current board:")
            self.display_board()
            print(f"{current_player.name}'s turn")
            if current_player.is_bot:
                self.bot_turn()
            else:
                if not self.human_turn():
                    print("Quitting game.")
                    return
            turn += 1
        winner = self.human if self.human.has_territories() else self.bot
        print(f"{winner.name} wins!")


def main() -> None:
    game = Game()
    game.play()


if __name__ == "__main__":
    main()
