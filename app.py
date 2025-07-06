from flask import Flask, jsonify, render_template, request
from game import Game, GamePhase

app = Flask(__name__)
game = Game()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/game_state')
def get_game_state():
    nodes = []
    for territory, (x, y) in game.board.positions.items():
        owner = game.territory_owner[territory]
        armies = game.armies[territory]
        
        nodes.append({
            "id": territory,
            "label": f"{territory}\n{armies}",
            "group": owner.name,
            "owner": owner.name,
            "x": x * 1.5, # Scaling factor for better spacing
            "y": y * 1.5  # Scaling factor for better spacing
        })


    edges = []
    for territory, neighbors in game.board.adjacency.items():
        for neighbor in neighbors:
            if territory < neighbor:
                edges.append({"from": territory, "to": neighbor})

    human_cards = [
        {"territory": card.territory, "card_type": card.card_type} 
        for card in game.human.cards
    ]

    state = {
        "nodes": nodes,
        "edges": edges,
        "phase": game.phase.value,
        "players": [p.name for p in game.players],
        "reinforcements": game.reinforcements,
        "winner": None,
        "current_player": game.players[game.current_player_index].name,
        "human_cards": human_cards,
        "conquest_move_details": game.conquest_move_details
    }
    
    if game.phase == GamePhase.GAME_OVER:
        winner_name = [p.name for p in game.players if p.has_territories(game)][0]
        state["winner"] = winner_name

    return jsonify(state)

@app.route('/api/deploy', methods=['POST'])
def deploy():
    data = request.json
    territory = data["territory"]
    armies = int(data["armies"])
    success = game.deploy(game.human, territory, armies)
    if success and game.reinforcements == 0:
        game.next_phase()
    return jsonify({"success": success})

@app.route('/api/attack', methods=['POST'])
def attack():
    data = request.json
    from_terr = data["from_terr"]
    to_terr = data["to_terr"]
    armies = int(data.get("armies", 1))
    result = game.attack(game.human, from_terr, to_terr, armies)
    return jsonify(result)

@app.route('/api/move_after_conquest', methods=['POST'])
def move_after_conquest():
    data = request.json
    num_armies = int(data['armies'])
    result = game.move_after_conquest(game.human, num_armies)
    return jsonify(result)

@app.route('/api/fortify', methods=['POST'])
def fortify():
    data = request.json
    from_terr = data["from_terr"]
    to_terr = data["to_terr"]
    armies = int(data["armies"])
    success = game.fortify(game.human, from_terr, to_terr, armies)
    return jsonify({"success": success})

@app.route('/api/next_phase', methods=['POST'])
def next_phase():
    if game.phase == GamePhase.ATTACK_MOVE:
        return jsonify({"success": False, "error": "Must move armies after conquest before ending phase."})
    game.next_phase()
    return jsonify({"success": True})

@app.route('/api/trade_in_cards', methods=['POST'])
def trade_in_cards():
    data = request.json
    card_indices = data.get("card_indices", [])
    result = game.trade_in_cards(game.human, card_indices)
    return jsonify(result)

@app.route('/api/restart', methods=['POST'])
def restart():
    game.restart()
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(debug=True, port=5001)
