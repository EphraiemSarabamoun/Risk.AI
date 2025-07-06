"""Simple Risk-like game engine."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List

from risk_board import Board


class GamePhase(Enum):
    DEPLOY = "DEPLOY"
    ATTACK = "ATTACK"
    FORTIFY = "FORTIFY"
    GAME_OVER = "GAME_OVER"


@dataclass
class Player:
    name: str
    is_bot: bool = False
    territories: List[str] = field(default_factory=list)

    def has_territories(self) -> bool:
        return len(self.territories) > 0


class Game:
    def restart(self):
        self.__init__()

    def __init__(self) -> None:
        self.board = Board()
        self.territory_owner: Dict[str, Player] = {}
        self.armies: Dict[str, int] = {}
        self.human = Player("Human")
        self.bot = Player("Bot", is_bot=True)
        self.players = [self.human, self.bot]
        
        self._setup()

        self.phase = GamePhase.DEPLOY
        self.reinforcements = self._calculate_reinforcements(self.human)
        self.turn_player = self.human
        self.fortified_this_turn = False

    def _setup(self) -> None:
        """Assign territories equally and place one army on each."""
        territories = list(self.board.adjacency.keys())
        random.shuffle(territories)
        turn = 0
        for terr in territories:
            player = self.players[turn % len(self.players)]
            player.territories.append(terr)
            self.territory_owner[terr] = player
            self.armies[terr] = 1
            turn += 1

    def _calculate_reinforcements(self, player: Player) -> int:
        """Calculate reinforcements based on territories and continents."""
        base = max(3, len(player.territories) // 3)
        # Add continent bonuses later
        return base

    def deploy(self, player: Player, terr: str, num_armies: int) -> bool:
        if player != self.turn_player or self.phase != GamePhase.DEPLOY:
            return False
        if terr not in player.territories or num_armies > self.reinforcements:
            return False
        
        self.armies[terr] += num_armies
        self.reinforcements -= num_armies
        return True

    def attack(self, attacker: Player, from_terr: str, to_terr: str) -> Dict:
        """Resolve an attack and return the result."""
        if attacker != self.turn_player or self.phase != GamePhase.ATTACK:
            return {"success": False, "error": "Not in attack phase."}
        if from_terr not in attacker.territories or to_terr in attacker.territories:
            return {"success": False, "error": "Invalid attack target."}
        if self.armies[from_terr] < 2:
            return {"success": False, "error": "Not enough armies."}
        if to_terr not in self.board.adjacency[from_terr]:
            return {"success": False, "error": "Territories not adjacent."}

        attack_roll = random.randint(1, 6)
        defend_roll = random.randint(1, 6)
        
        if attack_roll > defend_roll:
            defender = self.territory_owner[to_terr]
            defender.territories.remove(to_terr)
            attacker.territories.append(to_terr)
            self.territory_owner[to_terr] = attacker
            self.armies[to_terr] = self.armies[from_terr] - 1
            self.armies[from_terr] = 1
            self._check_game_over()
            return {"success": True, "conquered": True, "attack_roll": attack_roll, "defend_roll": defend_roll}
        else:
            self.armies[from_terr] -= 1
            return {"success": True, "conquered": False, "attack_roll": attack_roll, "defend_roll": defend_roll}

    def fortify(self, player: Player, from_terr: str, to_terr: str, num_armies: int) -> bool:
        if player != self.turn_player or self.phase != GamePhase.FORTIFY or self.fortified_this_turn:
            return False
    def fortify(self, player: Player, from_terr: str, to_terr: str, armies: int) -> dict:
        """Moves armies between two friendly territories."""
        if player != self.players[self.current_player_index] or self.game_phase != 'fortify':
            return {"success": False, "message": "Not the right player or phase to fortify."}
        if self.has_fortified_this_turn:
            return {"success": False, "message": "You can only fortify once per turn."}
        if from_terr not in player.territories or to_terr not in player.territories:
            return {"success": False, "message": "You must own both territories."}
        if self.armies[from_terr] <= armies:
            return {"success": False, "message": "Not enough armies to move (must leave at least 1)."}
        if armies <= 0:
            return {"success": False, "message": "Must move a positive number of armies."}
        # For simplicity, we'll allow fortification between any two owned territories.
        # A real game would require a path of friendly territories.

        self.armies[from_terr] -= armies
        self.armies[to_terr] += armies
        self.has_fortified_this_turn = True
        message = f"{player.name} fortified {to_terr} from {from_terr} with {armies} armies."
        self.turn_log.append(message)
        return {"success": True, "message": message}


    def next_phase(self) -> dict:
        """Transitions the game to the next phase or turn."""
        player = self.players[self.current_player_index]
        if self.game_phase == 'deploy':
            if self.reinforcements_to_deploy > 0:
                return {"success": False, "message": "You must deploy all your reinforcements."}
            self.game_phase = 'attack'
            message = f"Phase: Attack."
            self.turn_log.append(message)
            return {"success": True, "message": message}
        
        elif self.game_phase == 'attack':
            self.game_phase = 'fortify'
            message = f"Phase: Fortify."
            self.turn_log.append(message)
            return {"success": True, "message": message}
        
        elif self.game_phase == 'fortify':
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
            self.start_turn()
            return {"success": True, "message": "Turn ended."}
        
        return {"success": False, "message": "Invalid game state."}

    def bot_turn(self) -> None:
        """Simple bot that plays its turn."""
        bot = self.players[self.current_player_index]
        if not bot.is_bot: return

        # 1. Deploy
        while self.reinforcements_to_deploy > 0:
            terr_to_deploy = random.choice(bot.territories)
            self.deploy(bot, terr_to_deploy, 1)
        
        self.next_phase() # Move to attack phase

        # 2. Attack
        possible_attacks = []
        for terr in bot.territories:
            if self.armies[terr] > 1:
                for neighbor in self.board.adjacency[terr]:
                    if self.territory_owner[neighbor] != bot:
                        possible_attacks.append((terr, neighbor))
        
        if possible_attacks:
            from_terr, to_terr = random.choice(possible_attacks)
            self.attack(bot, from_terr, to_terr)

        self.next_phase() # Move to fortify phase
        self.next_phase() # End turn
