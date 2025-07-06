"""Simple Risk-like game engine."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Literal

from risk_board import Board


class GamePhase(Enum):
    DEPLOY = "DEPLOY"
    ATTACK = "ATTACK"
    ATTACK_MOVE = "ATTACK_MOVE"  # Post-conquest move
    FORTIFY = "FORTIFY"
    GAME_OVER = "GAME_OVER"


CardType = Literal["Infantry", "Cavalry", "Artillery", None]  # None represents a wildcard


@dataclass
class Card:
    territory: str
    card_type: CardType
    
    @staticmethod
    def is_valid_set(cards):
        """Check if the given cards form a valid set (3 of a kind or one of each kind)"""
        if len(cards) != 3:
            return False
            
        # Handle wildcards (None card_type)
        types = [c.card_type for c in cards if c.card_type is not None]
        wildcards = len(cards) - len(types)
        
        # If 3 wildcards or 2 wildcards + any card
        if wildcards >= 2:
            return True
            
        # If 1 wildcard + 2 matching cards or 2 different cards
        if wildcards == 1:
            return len(set(types)) == 1 or len(set(types)) == 2
            
        # No wildcards: must be 3 of same type or 1 of each type
        return len(set(types)) == 1 or len(set(types)) == 3


@dataclass
class Player:
    name: str
    is_bot: bool = False
    cards: List[Card] = field(default_factory=list)
    conquered_territory_this_turn: bool = False

    def get_territories(self, game: Game) -> List[str]:
        return [t for t, owner in game.territory_owner.items() if owner == self]

    def has_territories(self, game: Game) -> bool:
        return len(self.get_territories(game)) > 0


class Deck:
    def __init__(self, territories: List[str]):
        self.cards: List[Card] = []
        card_types: List[CardType] = ["Infantry", "Cavalry", "Artillery"]
        
        # Add one card per territory
        for i, territory in enumerate(territories):
            self.cards.append(Card(territory, card_types[i % 3]))
            
        # Add 2 wildcards
        self.cards.append(Card("Wildcard", None))
        self.cards.append(Card("Wildcard", None))
        
        self.shuffle()

    def shuffle(self):
        random.shuffle(self.cards)

    def draw(self) -> Card | None:
        if self.cards:
            return self.cards.pop(0)
        return None


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
        self.current_player_index = 0

        all_territories = list(self.board.adjacency.keys())
        self.deck = Deck(all_territories)
        self._setup(all_territories)

        self.phase = GamePhase.DEPLOY
        self.reinforcements = self._calculate_reinforcements(self.human)
        self.fortified_this_turn = False
        self.conquest_move_details: Dict | None = None
        self.card_trade_in_bonus = 4
        
        # Queue to store bot actions for sequential display in the frontend
        self.bot_actions = []

    def _setup(self, territories: List[str]) -> None:
        random.shuffle(territories)
        for i, terr in enumerate(territories):
            player = self.players[i % len(self.players)]
            self.territory_owner[terr] = player
            self.armies[terr] = 1

    def _calculate_reinforcements(self, player: Player) -> int:
        num_territories = len(player.get_territories(self))
        base = max(3, num_territories // 3)
        for continent, territories in self.board.continents.items():
            if all(self.territory_owner.get(t) == player for t in territories):
                base += self.board.continent_bonuses[continent]
        return base

    def deploy(self, player: Player, terr: str, num_armies: int) -> bool:
        current_player = self.players[self.current_player_index]
        if player != current_player or self.phase != GamePhase.DEPLOY:
            return False
        if self.territory_owner.get(terr) != player or num_armies > self.reinforcements:
            return False

        self.armies[terr] += num_armies
        self.reinforcements -= num_armies
        return True

    def attack(self, attacker: Player, from_terr: str, to_terr: str, num_attack_armies: int) -> Dict:
        current_player = self.players[self.current_player_index]
        if attacker != current_player or self.phase != GamePhase.ATTACK:
            return {"success": False, "error": "Not in attack phase or not your turn."}
        if self.territory_owner.get(from_terr) != attacker or self.territory_owner.get(to_terr) == attacker:
            return {"success": False, "error": "Invalid attack."}
        if to_terr not in self.board.adjacency[from_terr]:
            return {"success": False, "error": "Territories not adjacent."}

        from_terr_armies = self.armies[from_terr]
        if from_terr_armies <= num_attack_armies:
            return {"success": False, "error": "Not enough armies to attack."}
        if not (1 <= num_attack_armies <= 3):
            return {"success": False, "error": "Can only attack with 1, 2, or 3 armies."}

        defender = self.territory_owner[to_terr]
        num_defend_armies = min(2, self.armies[to_terr])

        attack_rolls = sorted([random.randint(1, 6) for _ in range(num_attack_armies)], reverse=True)
        defend_rolls = sorted([random.randint(1, 6) for _ in range(num_defend_armies)], reverse=True)

        attack_losses, defend_losses = 0, 0
        for a_roll, d_roll in zip(attack_rolls, defend_rolls):
            if a_roll > d_roll:
                defend_losses += 1
            else:
                attack_losses += 1

        self.armies[from_terr] -= attack_losses
        self.armies[to_terr] -= defend_losses

        conquered = self.armies[to_terr] <= 0
        result = {
            "success": True, "conquered": conquered, "attack_rolls": attack_rolls,
            "defend_rolls": defend_rolls, "attack_losses": attack_losses, "defend_losses": defend_losses
        }

        if conquered:
            self.territory_owner[to_terr] = attacker
            self.armies[to_terr] = 0
            attacker.conquered_territory_this_turn = True
            self.phase = GamePhase.ATTACK_MOVE
            self.conquest_move_details = {
                "from_terr": from_terr, "to_terr": to_terr,
                "min_move": num_attack_armies, "max_move": self.armies[from_terr] - 1
            }
            result["conquest_move_details"] = self.conquest_move_details
            self._check_game_over()

        return result

    def move_after_conquest(self, player: Player, num_move_armies: int) -> Dict:
        if player != self.players[self.current_player_index] or self.phase != GamePhase.ATTACK_MOVE:
            return {"success": False, "error": "Not in correct phase."}

        details = self.conquest_move_details
        if not details:
            return {"success": False, "error": "Internal error: No conquest details."}

        if not (details["min_move"] <= num_move_armies <= details["max_move"]):
            return {"success": False, "error": f"Invalid army number."}

        self.armies[details["from_terr"]] -= num_move_armies
        self.armies[details["to_terr"]] = num_move_armies

        self.phase = GamePhase.ATTACK
        self.conquest_move_details = None
        return {"success": True}

    def trade_in_cards(self, player: Player, card_indices: List[int]) -> Dict:
        if player != self.players[self.current_player_index] or self.phase != GamePhase.DEPLOY:
            return {"success": False, "error": "Can only trade cards during deploy phase."}
        if len(card_indices) != 3:
            return {"success": False, "error": "Must select 3 cards."}

        try:
            cards_to_trade = [player.cards[i] for i in card_indices]
        except IndexError:
            return {"success": False, "error": "Invalid card selection."}

        # Use improved card set validation
        is_set = Card.is_valid_set(cards_to_trade)

        if not is_set:
            return {"success": False, "error": "Not a valid set (need three of a kind, one of each kind, or sets with wildcards)."}

        # Calculate bonus troops
        current_bonus = self.card_trade_in_bonus
        self.reinforcements += current_bonus
        
        # Update the bonus for next time
        if self.card_trade_in_bonus < 12:
            self.card_trade_in_bonus += 2
        elif self.card_trade_in_bonus == 12:
            self.card_trade_in_bonus += 3
        else:
            self.card_trade_in_bonus += 5

        # Remove traded cards
        for i in sorted(card_indices, reverse=True):
            del player.cards[i]

        return {"success": True, "bonus": current_bonus, "next_bonus": self.card_trade_in_bonus}

    def fortify(self, player: Player, from_terr: str, to_terr: str, num_armies: int) -> bool:
        current_player = self.players[self.current_player_index]
        if player != current_player or self.phase != GamePhase.FORTIFY or self.fortified_this_turn:
            return False
        if self.territory_owner.get(from_terr) != player or self.territory_owner.get(to_terr) != player:
            return False
        if self.armies[from_terr] <= num_armies:
            return False
        if not self.board.are_connected(from_terr, to_terr, player, self.territory_owner):
            return False

        self.armies[from_terr] -= num_armies
        self.armies[to_terr] += num_armies
        self.fortified_this_turn = True
        return True

    def _check_game_over(self):
        if not self.bot.has_territories(self) or not self.human.has_territories(self):
            self.phase = GamePhase.GAME_OVER

    def run_bot_turn(self):
        print(f"Bot turn triggered! Current player: {self.players[self.current_player_index].name}, Phase: {self.phase}")
        
        # Clear previous bot actions
        self.bot_actions = []
        
        # Check if it's actually the bot's turn
        if self.players[self.current_player_index] != self.bot:
            print(f"ERROR: Not the bot's turn! Current player is {self.players[self.current_player_index].name}")
            return
            
        if self.phase == GamePhase.GAME_OVER:
            print("Game is over, bot turn skipped")
            return
            
        if self.phase != GamePhase.DEPLOY:
            print(f"ERROR: Bot turn called but phase is {self.phase} instead of DEPLOY")
            self.phase = GamePhase.DEPLOY  # Force correct phase
            
        # Check if bot has territories
        if not self.bot.has_territories(self):
            print("Bot has no territories, ending game")
            self.phase = GamePhase.GAME_OVER
            return
        
        # Start with a bot turn message
        self.bot_actions.append({
            "type": "turn_start",
            "message": "Bot begins turn"
        })
        
        print(f"Bot starting DEPLOY phase with {self.reinforcements} reinforcements")
        self._bot_deploy()
        
        print("Bot starting ATTACK phase")
        self.phase = GamePhase.ATTACK
        self._bot_attack()
        
        print("Bot starting FORTIFY phase")
        self.phase = GamePhase.FORTIFY
        self._bot_fortify()
        
        print("Bot ending turn")
        self.next_phase()

    def _bot_deploy(self):
        # Check for card trade-ins first
        if len(self.bot.cards) >= 5:
            from itertools import combinations
            for indices in combinations(range(len(self.bot.cards)), 3):
                cards = [self.bot.cards[i] for i in indices]
                if len({c.card_type for c in cards}) in [1, 3]:
                    card_names = [f"{c.territory} ({c.card_type})" for c in cards]
                    result = self.trade_in_cards(self.bot, list(indices))
                    if result.get("success"):
                        self.bot_actions.append({
                            "type": "trade_in",
                            "cards": card_names,
                            "bonus": result.get("bonus"),
                            "message": f"Bot traded in cards: {', '.join(card_names)} for {result.get('bonus')} reinforcements"
                        })
                    break

        # Calculate reinforcements and prepare for deployment
        self.reinforcements = self._calculate_reinforcements(self.bot)
        bot_territories = self.bot.get_territories(self)
        frontier = [t for t in bot_territories if self._is_frontier(t)]
        
        # Record reinforcement calculation
        self.bot_actions.append({
            "type": "reinforcement",
            "amount": self.reinforcements,
            "message": f"Bot received {self.reinforcements} reinforcements"
        })

        # Choose deployment territory
        if not frontier:
            if bot_territories:
                deploy_to = random.choice(bot_territories)
                self.deploy(self.bot, deploy_to, self.reinforcements)
                self.bot_actions.append({
                    "type": "deploy",
                    "territory": deploy_to,
                    "armies": self.reinforcements,
                    "message": f"Bot deployed {self.reinforcements} armies to {deploy_to}"
                })
            return

        # Deploy to strongest frontier territory
        deploy_to = max(frontier, key=lambda t: self.armies[t])
        self.deploy(self.bot, deploy_to, self.reinforcements)
        self.bot_actions.append({
            "type": "deploy",
            "territory": deploy_to,
            "armies": self.reinforcements,
            "message": f"Bot deployed {self.reinforcements} armies to {deploy_to}"
        })

    def _bot_attack(self):
        print("BOT ATTACK: --- Starting bot attack sequence ---")
        self.bot_actions.append({
            "type": "phase_change",
            "phase": "ATTACK",
            "message": "Bot begins attack phase"
        })

        max_attacks = 15  # Safety limit for number of attack loops
        for i in range(max_attacks):
            print(f"\nBOT ATTACK: Loop {i + 1}/{max_attacks}. Current phase: {self.phase}")

            if self.phase in [GamePhase.GAME_OVER, GamePhase.FORTIFY]:
                print(f"BOT ATTACK: Phase is now {self.phase}. Ending attack sequence.")
                break

            if self.phase == GamePhase.ATTACK_MOVE:
                print("BOT ATTACK: Handling mandatory move after conquest.")
                if self.conquest_move_details:
                    details = self.conquest_move_details
                    try:
                        # Bot will move all but one army from the attacking territory
                        armies_to_move = self.armies[details["from_terr"]] - 1
                        if armies_to_move > 0:
                            print(f"BOT ATTACK: Moving {armies_to_move} armies to new territory.")
                            self.move_after_conquest(self.bot, armies_to_move)
                        else:
                            # This case should ideally not happen if an attack was successful
                            print("BOT ATTACK: No armies to move. Switching back to ATTACK.")
                            self.phase = GamePhase.ATTACK
                    except Exception as e:
                        print(f"BOT ATTACK: Error during move_after_conquest: {e}. Forcing FORTIFY.")
                        self.phase = GamePhase.FORTIFY
                else:
                    print("BOT ATTACK: ERROR - In ATTACK_MOVE with no details. Forcing FORTIFY.")
                    self.phase = GamePhase.FORTIFY
                continue # Restart loop to re-evaluate the game state

            if self.phase != GamePhase.ATTACK:
                print(f"BOT ATTACK: Phase is {self.phase}, not ATTACK. Exiting.")
                break

            # Find all possible attacks the bot can make
            attacks = []
            bot_territories = self.bot.get_territories(self)
            for t in bot_territories:
                if self.armies.get(t, 0) > 1:  # Territory must have more than 1 army to attack
                    for n in self.board.adjacency.get(t, []):
                        if self.territory_owner.get(n) == self.human:
                            # Simple logic: attack if the bot has more armies
                            if self.armies[t] > self.armies.get(n, 0):
                                attacks.append((t, n))
            
            if not attacks:
                print("BOT ATTACK: No more viable attacks. Moving to FORTIFY.")
                self.phase = GamePhase.FORTIFY
                break # Exit the attack loop

            # Bot chooses the best attack (from its strongest territory)
            from_terr, to_terr = max(attacks, key=lambda att: self.armies[att[0]])
            num_attackers = min(3, self.armies[from_terr] - 1)
            
            if num_attackers <= 0:
                print(f"BOT ATTACK: Logic error, num_attackers is {num_attackers}. Skipping attack.")
                continue

            print(f"BOT ATTACK: Attacking {to_terr} from {from_terr} with {num_attackers} armies.")
            # The self.attack() method will handle dice rolls, army updates, and phase changes
            self.attack(self.bot, from_terr, to_terr, num_attackers)

        else:  # This 'else' belongs to the 'for' loop, runs if it completes without 'break'
            print("BOT ATTACK: Reached max attack loops.")

        # After the loop, if the phase is still ATTACK, it means the loop finished without finding attacks or hit its limit.
        if self.phase == GamePhase.ATTACK:
            print("BOT ATTACK: Loop finished. Forcing phase to FORTIFY.")
            self.phase = GamePhase.FORTIFY
            
        print(f"BOT ATTACK: --- Bot attack sequence complete. Final phase: {self.phase} ---")

    def _bot_fortify(self):
        print("Starting bot fortify sequence")
        
        # Add an action to show phase change
        self.bot_actions.append({
            "type": "phase_change",
            "phase": "FORTIFY",
            "message": "Bot begins fortify phase"
        })
        
        if self.phase != GamePhase.FORTIFY:
            print(f"ERROR: Bot fortify called but phase is {self.phase}")
            return
            
        bot_territories = self.bot.get_territories(self)
        print(f"Bot has {len(bot_territories)} territories for fortification")
        
        # Find territories that are not on the frontier (internal) with more than 1 army
        from_options = [t for t in bot_territories if self.armies[t] > 1 and not self._is_frontier(t)]
        # Find territories that are on the frontier and need reinforcement
        to_options = [t for t in bot_territories if self._is_frontier(t)]

        if not from_options:
            print("No source territories available for fortification")
            self.bot_actions.append({
                "type": "fortify_skip",
                "message": "Bot has no territories to fortify from (all territories are on the frontier)"
            })
            return
            
        if not to_options:
            print("No target territories available for fortification")
            self.bot_actions.append({
                "type": "fortify_skip",
                "message": "Bot has no frontier territories to fortify"
            })
            return

        # Choose the territory with the most armies as the source
        from_terr = max(from_options, key=lambda t: self.armies[t])
        print(f"Selected source territory for fortify: {from_terr} with {self.armies[from_terr]} armies")
        
        # Find the frontier territory with the fewest armies that is connected to the source
        best_to_terr = None
        min_armies = float('inf')

        for to_terr in to_options:
            # Check if territories are connected through bot-owned territories
            if self.board.are_connected(from_terr, to_terr, self.bot, self.territory_owner):
                if self.armies[to_terr] < min_armies:
                    min_armies = self.armies[to_terr]
                    best_to_terr = to_terr

        if best_to_terr:
            armies_to_move = self.armies[from_terr] - 1  # Leave one army behind
            print(f"Bot fortifying: Moving {armies_to_move} armies from {from_terr} to {best_to_terr}")
            
            # Log fortify intent
            self.bot_actions.append({
                "type": "fortify",
                "from_terr": from_terr,
                "to_terr": best_to_terr,
                "armies": armies_to_move,
                "message": f"Bot fortifies by moving {armies_to_move} armies from {from_terr} to {best_to_terr}"
            })
            
            success = self.fortify(self.bot, from_terr, best_to_terr, armies_to_move)
            if success:
                print(f"Fortification successful: {from_terr} now has {self.armies[from_terr]} armies, {best_to_terr} now has {self.armies[best_to_terr]} armies")
                self.bot_actions.append({
                    "type": "fortify_result",
                    "from_terr": from_terr,
                    "to_terr": best_to_terr,
                    "from_armies": self.armies[from_terr],
                    "to_armies": self.armies[best_to_terr],
                    "message": f"Fortification complete: {from_terr} now has {self.armies[from_terr]} armies, {best_to_terr} now has {self.armies[best_to_terr]} armies"
                })
            else:
                print("Fortification failed for some reason")
                self.bot_actions.append({
                    "type": "fortify_error",
                    "message": "Fortification failed due to an unexpected error"
                })
        else:
            print("No valid fortification path found between internal and frontier territories")
            self.bot_actions.append({
                "type": "fortify_skip",
                "message": "No valid path found to fortify between territories"
            })
            
        print("Bot fortify sequence complete")
        
        # Add an action to show turn end
        self.bot_actions.append({
            "type": "turn_end",
            "message": "Bot ends turn"
        })
        
    def _is_frontier(self, territory: str) -> bool:
        owner = self.territory_owner[territory]
        return any(self.territory_owner[n] != owner for n in self.board.adjacency[territory])

    def next_phase(self) -> None:
        current_player = self.players[self.current_player_index]
        print(f"next_phase called: Current player {current_player.name}, Current phase {self.phase}")
        
        if self.phase == GamePhase.DEPLOY:
            if self.reinforcements == 0:
                self.phase = GamePhase.ATTACK
                print(f"Transitioning to ATTACK phase")
        elif self.phase == GamePhase.ATTACK:
            self.phase = GamePhase.FORTIFY
            print(f"Transitioning to FORTIFY phase")
        elif self.phase == GamePhase.FORTIFY:
            if current_player.conquered_territory_this_turn:
                card = self.deck.draw()
                if card:
                    current_player.cards.append(card)
                    print(f"Player {current_player.name} received a card: {card.territory} ({card.card_type})")
            current_player.conquered_territory_this_turn = False

            self.current_player_index = (self.current_player_index + 1) % len(self.players)
            next_player = self.players[self.current_player_index]
            self.phase = GamePhase.DEPLOY
            self.reinforcements = self._calculate_reinforcements(next_player)
            self.fortified_this_turn = False
            print(f"Transitioning to DEPLOY phase for player {next_player.name} with {self.reinforcements} reinforcements")

            if next_player.is_bot:
                print(f"Bot turn detected - preparing bot actions")
                # Instead of calling run_bot_turn directly, we'll prepare bot actions
                # and let them be fetched via API
                self.prepare_bot_actions()

    def prepare_bot_actions(self):
        """Prepare bot actions queue without executing them"""
        print("Preparing bot actions for async execution")
        # Clear existing actions
        self.bot_actions = []
        
        # Add initial phase change action
        self.bot_actions.append({
            "type": "phase_change",
            "phase": "DEPLOY",
            "message": "Bot begins turn"
        })

    def run_bot_turn(self):
        print("Starting bot turn execution")
        
        # Check if it's actually the bot's turn
        if self.players[self.current_player_index] != self.bot:
            print(f"ERROR: Not the bot's turn! Current player is {self.players[self.current_player_index].name}")
            return
            
        if self.phase == GamePhase.GAME_OVER:
            print("Game is over, bot turn skipped")
            return
            
        if not self.bot.has_territories(self):
            print("Bot has no territories, ending game")
            self.phase = GamePhase.GAME_OVER
            return
        
        print(f"Bot is player {self.current_player_index}, starting actions")
        
        # Set up initial actions if not already done
        if not self.bot_actions:
            self.bot_actions.append({
                "type": "turn_start",
                "message": "Bot begins turn"
            })
        
        # Deploy phase
        print(f"Bot starting DEPLOY phase with {self.reinforcements} reinforcements")
        self._bot_deploy()
        
        # Attack phase
        if self.phase != GamePhase.GAME_OVER:
            print("Bot starting ATTACK phase")
            self.phase = GamePhase.ATTACK  # Explicitly set to ATTACK
            self._bot_attack()
            
        # Fortify phase
        if self.phase != GamePhase.GAME_OVER and self.phase != GamePhase.ATTACK_MOVE:
            print("Bot starting FORTIFY phase")
            self.phase = GamePhase.FORTIFY  # Explicitly set to FORTIFY
            self._bot_fortify()
            
        # Move to next player
        if self.phase != GamePhase.GAME_OVER:
            print("Bot turn complete, moving to next player")
            # Do not call next_phase here as that would trigger another bot turn
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
            next_player = self.players[self.current_player_index]
            self.phase = GamePhase.DEPLOY
            self.reinforcements = self._calculate_reinforcements(next_player)
            self.fortified_this_turn = False
            
            self.bot_actions.append({
                "type": "next_player",
                "player": next_player.name,
                "message": f"Next player: {next_player.name}"
            })
            
            print(f"Next player: {next_player.name}")
            
        print("Bot turn execution complete")
