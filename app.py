from flask import Flask, jsonify, render_template, request
from game import Game, GamePhase

app = Flask(__name__)
game = Game()

@app.route('/')
def index():
    return render_template('index.html')

# Mapping from risk_board.py names to the names in our coordinate file
territory_name_map = {
    "Northwest Territory": "Northwest Territories",
    "Western United States": "Western U.S.",
    "Eastern United States": "Eastern U.S.",
    "Central America": "Mexico",
    "Venezuela": "Colombia",
    "Argentina": "Chile",
    "North Africa": "Western Africa",
    "East Africa": "Ethiopia",
    "Congo": "Zaire",
    "Scandinavia": "Sweden",
    "Northern Europe": "Central Europe",
    "Ukraine": "Ukraine", # same
    "Great Britain": "Great Britain", # same
    "Southern Europe": "Southern Europe", # same
    "Ural": "Russia",
    "Siam": "Laos",
    "Mongolia": "Manchuria",
    "Afghanistan": "Pakistan",
    # Territories that need a new name/location from the classic board
    "Alberta": "British Columbia", 
    "Peru": "Peru", # same
    "Brazil": "Brazil", # same
    "Iceland": "Iceland", # same
    "Egypt": "Egypt", # same
    "South Africa": "South Africa", # same
    "Madagascar": "Madagascar", # same
    "Siberia": "Siberia", # same
    "Yakutsk": "Eastern Russia",
    "Kamchatka": "Kamchatka", # same
    "Irkutsk": "Irkutsk", # same
    "Japan": "Japan", # same
    "Middle East": "Middle East", # same
    "India": "India", # same
    "China": "China", # same
    "Indonesia": "Indonesia", # same
    "New Guinea": "New Guinea", # same
    "Western Australia": "Western Australia", # same
    "Eastern Australia": "Eastern Australia", # same
    "Alaska": "Alaska", # same
    "Greenland": "Greenland", # same
    "Ontario": "Ontario", # same
    "Quebec": "Quebec", # same
}

territory_coordinates = {
    "Alaska": {"x": 72, "y": 109},
    "Northwest Territories": {"x": 134, "y": 99},
    "Greenland": {"x": 219, "y": 88},
    "British Columbia": {"x": 126, "y": 144},
    "Ontario": {"x": 178, "y": 155},
    "Quebec": {"x": 234, "y": 163},
    "Western U.S.": {"x": 137, "y": 204},
    "Eastern U.S.": {"x": 192, "y": 210},
    "Mexico": {"x": 169, "y": 259},
    "Colombia": {"x": 215, "y": 297},
    "Brazil": {"x": 251, "y": 339},
    "Peru": {"x": 207, "y": 356},
    "Chile": {"x": 224, "y": 415},
    "South Africa": {"x": 378, "y": 389},
    "Zaire": {"x": 370, "y": 340},
    "Ethiopia": {"x": 403, "y": 318},
    "Western Africa": {"x": 332, "y": 294},
    "Egypt": {"x": 384, "y": 275},
    "Madagascar": {"x": 433, "y": 383},
    "Western Europe": {"x": 341, "y": 229},
    "Great Britain": {"x": 333, "y": 194},
    "Iceland": {"x": 302, "y": 152},
    "Sweden": {"x": 367, "y": 155},
    "Central Europe": {"x": 375, "y": 198},
    "Southern Europe": {"x": 392, "y": 215},
    "Ukraine": {"x": 425, "y": 175},
    "Middle East": {"x": 427, "y": 250},
    "Pakistan": {"x": 474, "y": 226},
    "Russia": {"x": 501, "y": 153},
    "India": {"x": 501, "y": 267},
    "Laos": {"x": 554, "y": 286},
    "China": {"x": 558, "y": 240},
    "Manchuria": {"x": 606, "y": 207},
    "Japan": {"x": 666, "y": 220},
    "Siberia": {"x": 566, "y": 145},
    "Irkutsk": {"x": 617, "y": 166},
    "Eastern Russia": {"x": 655, "y": 112},
    "Kamchatka": {"x": 703, "y": 149},
    "Indonesia": {"x": 604, "y": 328},
    "New Guinea": {"x": 671, "y": 331},
    "Western Australia": {"x": 636, "y": 389},
    "Eastern Australia": {"x": 679, "y": 388}
}

@app.route('/api/game_state')
def get_game_state():
    nodes = []
    for territory in game.board.adjacency.keys():
        mapped_name = territory_name_map.get(territory, territory)
        coords = territory_coordinates.get(mapped_name)
        owner = game.territory_owner[territory]
        armies = game.armies[territory]
        
        node = {
            "id": territory,
            "label": f"{territory}\n{armies}",
            "group": owner.name,
            "owner": owner.name
        }
        if coords:
            node['x'] = coords['x'] * 2
            node['y'] = coords['y'] * 2
        nodes.append(node)

    edges = []
    for territory, neighbors in game.board.adjacency.items():
        for neighbor in neighbors:
            if territory < neighbor:
                edges.append({"from": territory, "to": neighbor})

    winner = None
    if game.phase == GamePhase.GAME_OVER:
        winner = game.human.name if game.human.has_territories() else game.bot.name

    return jsonify({
        "nodes": nodes,
        "edges": edges,
        "phase": game.phase.value,
        "reinforcements": game.reinforcements,
        "players": [p.name for p in game.players],
        "winner": winner
    })

@app.route('/api/deploy', methods=['POST'])
def deploy():
    data = request.json
    success = game.deploy(game.human, data['territory'], data['armies'])
    if success and game.reinforcements == 0:
        game.next_phase()
    return jsonify({'success': success, 'phase': game.phase.value})

@app.route('/api/attack', methods=['POST'])
def attack():
    data = request.json
    result = game.attack(game.human, data['from_terr'], data['to_terr'])
    return jsonify(result)

@app.route('/api/fortify', methods=['POST'])
def fortify():
    data = request.json
    success = game.fortify(game.human, data['from_terr'], data['to_terr'], data['armies'])
    return jsonify({'success': success})


@app.route('/api/next_phase', methods=['POST'])
def next_phase():
    game.next_phase()
    return jsonify({'phase': game.phase.value, 'reinforcements': game.reinforcements})

@app.route('/api/restart', methods=['POST'])
def restart():
    game.restart()
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True, port=5001)
