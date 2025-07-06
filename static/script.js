document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const container = document.getElementById('mynetwork');
    const statusEl = document.getElementById('game-status');
    const actionBtn = document.getElementById('action-btn');
    const restartBtn = document.getElementById('restart-btn');
    const playerHandContainer = document.getElementById('player-hand-container');
    const tradeInBtn = document.getElementById('trade-in-btn');
    const botActionEl = document.getElementById('bot-action');
    const cardRulesEl = document.getElementById('card-rules');

    // Game state variables
    let network = null;
    let gameState = {};
    let selectedTerritory = null;
    let nodes, edges;
    let selectedCards = [];
    let isProcessingBotActions = false;
    let nextCardTradeInBonus = 4; // Initial trade-in bonus

    // Player colors
    const playerColors = {
        'Human': '#4169E1', // RoyalBlue
        'Bot': '#DC143C'   // Crimson
    };

    // Event listeners
    actionBtn.addEventListener('click', async () => {
        if (gameState.phase === 'ATTACK' || gameState.phase === 'FORTIFY') {
            console.log(`Ending phase ${gameState.phase}`);
            await apiPost('/api/next_phase', {});
        }
    });

    tradeInBtn.addEventListener('click', handleTradeIn);
    
    restartBtn.addEventListener('click', async () => {
        const confirmed = confirm('Are you sure you want to restart the game?');
        if (confirmed) {
            try {
                const response = await fetch('/api/restart', { method: 'POST' });
                if (response.ok) {
                    await fetchGameState();
                    alert('Game restarted!');
                }
            } catch (error) {
                console.error('Error restarting game:', error);
            }
        }
    });

    // API functions
    async function apiPost(url, data) {
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            
            if (!response.ok) {
                // Check content type to avoid parsing HTML as JSON
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('application/json')) {
                    const errorResult = await response.json();
                    throw new Error(errorResult.error || 'API request failed');
                } else {
                    throw new Error(`Server returned ${response.status}: ${response.statusText}`);
                }
            }
            
            // Safely parse JSON response
            try {
                const result = await response.json();
                
                if (url === '/api/attack' && result.success) {
                    let message = `Attack Results:\n` +
                                  `Attacker rolls: ${result.attack_rolls.join(', ')}\n` +
                                  `Defender rolls: ${result.defend_rolls.join(', ')}\n` +
                                  `Attacker lost: ${result.attack_losses} armies\n` +
                                  `Defender lost: ${result.defend_losses} armies`;
                    if (result.conquered) {
                        message += `\n\nYou conquered ${result.conquest_move_details.to_terr}!`;
                    }
                    alert(message);
                }

                await fetchGameState(); // Refresh state after every action
                return result;
            } catch (jsonError) {
                console.error('JSON parsing error:', jsonError);
                throw new Error('Failed to parse server response');
            }
        } catch (error) {
            console.error('API POST error:', error);
            alert(`Error: ${error.message}`);
            await fetchGameState(); // Refresh state even on error to sync up
            return null;
        }
    }

    async function fetchGameState() {
        try {
            const response = await fetch('/api/game_state');
            gameState = await response.json();
            drawBoard(gameState);
            updateStatus();
            console.log("Cards received:", gameState.human_cards);
            updatePlayerHand(gameState.human_cards);

            // Make sure player hand container is visible
            if (playerHandContainer) {
                playerHandContainer.style.display = 'block';
            }

            // Display card rules info
            updateCardRules();

            if (gameState.phase === 'ATTACK_MOVE' && gameState.current_player === 'Human' && gameState.conquest_move_details) {
                // Use a timeout to ensure the user sees the board update before the prompt
                setTimeout(handleAttackMove, 100); 
            }
            
            // Check if it's the bot's turn and start polling for bot actions
            if (gameState.current_player === 'Bot' && !isProcessingBotActions) {
                isProcessingBotActions = true;
                processBotActions();
            }
        } catch (error) {
            console.error('Error fetching game state:', error);
        }
    }

    async function handleAttackMove() {
        const details = gameState.conquest_move_details;
        if (!details) return;

        const { from_terr, to_terr, min_move, max_move } = details;
        
        let numArmiesStr = prompt(
            `You conquered ${to_terr} from ${from_terr}!\n` +
            `How many armies do you want to move into ${to_terr}?\n` +
            `(Minimum: ${min_move}, Maximum: ${max_move})`,
            max_move
        );

        if (numArmiesStr) {
            const numArmies = parseInt(numArmiesStr);
            if (numArmies >= min_move && numArmies <= max_move) {
                await apiPost('/api/move_after_conquest', { armies: numArmies });
            } else {
                alert(`Invalid number of armies. Please enter a number between ${min_move} and ${max_move}.`);
                setTimeout(handleAttackMove, 100); // Re-prompt
            }
        } else {
            // If the user cancels the prompt, default to moving the minimum
            alert(`You must move armies. Moving the minimum of ${min_move}.`);
            await apiPost('/api/move_after_conquest', { armies: min_move });
        }
    }

    function updateStatus() {
        if (gameState.winner) {
            statusEl.innerText = `Game Over! ${gameState.winner} wins!`;
            actionBtn.style.display = 'none';
            return;
        }

        let statusText = `Turn: ${gameState.current_player} | Phase: ${gameState.phase}`;
        if (gameState.phase === 'DEPLOY') {
            statusText += ` | Reinforcements: ${gameState.reinforcements}`;
        }
        statusEl.innerText = statusText;

        // Disable action button during bot's turn or ATTACK_MOVE phase
        if (gameState.current_player !== 'Human' || gameState.phase === 'ATTACK_MOVE') {
            actionBtn.style.display = 'none';
            return;
        }

        if (gameState.phase === 'ATTACK') {
            actionBtn.innerText = 'End Attack Phase';
            actionBtn.style.display = 'block';
        } else if (gameState.phase === 'FORTIFY') {
            actionBtn.innerText = 'End Turn';
            actionBtn.style.display = 'block';
        } else {
            actionBtn.style.display = 'none';
        }
    }

    function updatePlayerHand(cards) {
        const playerHandDiv = document.getElementById('player-hand');
        if (!playerHandDiv || !tradeInBtn) return;

        playerHandDiv.innerHTML = ''; // Clear only the card elements

        const updateTradeInButtonVisibility = () => {
            if (gameState.phase === 'DEPLOY' && gameState.current_player === 'Human' && selectedCards.length === 3) {
                tradeInBtn.style.display = 'block';
            } else {
                tradeInBtn.style.display = 'none';
            }
        };

        if (!cards || cards.length === 0) {
            playerHandDiv.innerHTML = '<p>No cards yet.</p>';
        } else {
            cards.forEach((card, index) => {
                const cardEl = document.createElement('div');
                cardEl.className = 'card';
                
                // Add visual styling based on card type
                if (card.card_type === null) {
                    cardEl.classList.add('wildcard');
                } else if (card.card_type === 'Infantry') {
                    cardEl.classList.add('infantry');
                } else if (card.card_type === 'Cavalry') {
                    cardEl.classList.add('cavalry');
                } else if (card.card_type === 'Artillery') {
                    cardEl.classList.add('artillery');
                }

                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.id = `card-${index}`;
                checkbox.dataset.cardIndex = index;
                if (selectedCards.includes(index)) {
                    checkbox.checked = true;
                }

                const label = document.createElement('label');
                label.htmlFor = `card-${index}`;
                const cardType = card.card_type === null ? 'Wildcard' : card.card_type;
                label.innerHTML = `<strong>${card.territory}</strong><br>(${cardType})`;

                cardEl.appendChild(checkbox);
                cardEl.appendChild(label);
                playerHandDiv.appendChild(cardEl);

                checkbox.addEventListener('change', () => {
                    const cardIndex = parseInt(checkbox.dataset.cardIndex);
                    if (checkbox.checked) {
                        if (!selectedCards.includes(cardIndex)) {
                            selectedCards.push(cardIndex);
                        }
                    } else {
                        selectedCards = selectedCards.filter(i => i !== cardIndex);
                    }
                    updateTradeInButtonVisibility();
                });
            });
        }
        updateTradeInButtonVisibility();
    }

    function drawBoard(data) {
        // Create a DataSet for nodes and edges
        nodes = new vis.DataSet(data.nodes);
        edges = new vis.DataSet(data.edges);

        const groups = {};
        data.players.forEach(player => {
            groups[player] = {
                color: { background: playerColors[player], border: playerColors[player] },
                font: { color: 'white' }
            };
        });

        const options = {
            nodes: {
                shape: 'box',
                size: 20,
                borderWidth: 2,
                shadow: true,
                font: {
                    size: 14,
                    color: '#000',
                    multi: true,
                    face: 'arial'
                }
            },
            edges: {
                width: 2,
                shadow: true
            },
            groups: groups,
            physics: {
                enabled: false
            },
            interaction: {
                dragNodes: false,
                dragView: true,
                zoomView: true
            }
        };

        if (!network) {
            network = new vis.Network(container, { nodes, edges }, options);
            network.on("click", handleNetworkClick);
        } else {
            network.setData({ nodes, edges });
        }
        
        // After an action, the selected territory might no longer be valid for another action.
        if (selectedTerritory) {
            const selectedNodeData = nodes.get(selectedTerritory);
            if (!selectedNodeData || parseInt(selectedNodeData.label.split('\n')[1]) <= 1) {
                selectedTerritory = null;
            }
        }
        
        highlightSelection();
    }

    function highlightSelection() {
        if (!nodes) return;
        const allNodeIds = nodes.getIds();
        const updates = [];

        allNodeIds.forEach(nodeId => {
            const node = nodes.get(nodeId);
            let borderWidth = 2;
            let borderColor = playerColors[node.owner];

            if (selectedTerritory) {
                const selectedNode = nodes.get(selectedTerritory);
                const neighborIds = network.getConnectedNodes(selectedTerritory);

                if (node.id === selectedTerritory) {
                    borderWidth = 4;
                } else if (gameState.phase === 'ATTACK' && selectedNode.owner === 'Human' && node.owner !== 'Human' && neighborIds.includes(node.id)) {
                    borderWidth = 3;
                    borderColor = '#FFFF00'; // Yellow for attackable neighbors
                } else if (gameState.phase === 'FORTIFY' && selectedNode.owner === 'Human' && node.owner === 'Human') {
                    borderWidth = 3;
                    borderColor = '#00FF00'; // Green for fortifiable neighbors
                }
            }
            updates.push({ id: node.id, borderWidth: borderWidth, color: { border: borderColor } });
        });
        nodes.update(updates);
    }

    async function handleNetworkClick(params) {
        // Disable clicks if not human's turn, game is over, or in ATTACK_MOVE phase
        if (gameState.current_player !== 'Human' || gameState.winner || gameState.phase === 'ATTACK_MOVE') {
            selectedTerritory = null;
            highlightSelection();
            return;
        }

        const clickedNodeId = params.nodes.length > 0 ? params.nodes[0] : null;

        if (!clickedNodeId) {
            selectedTerritory = null;
            highlightSelection();
            return;
        }

        const node = nodes.get(clickedNodeId);
        const nodeArmies = parseInt(node.label.split('\n')[1]);

        if (gameState.phase === 'DEPLOY') {
            if (node.owner === 'Human' && gameState.reinforcements > 0) {
                await apiPost('/api/deploy', { territory: clickedNodeId, armies: 1 });
            }
        } else if (gameState.phase === 'ATTACK') {
            if (!selectedTerritory) { // First click: select attacking territory
                if (node.owner === 'Human' && nodeArmies > 1) {
                    selectedTerritory = clickedNodeId;
                    console.log("Selected territory for attack:", clickedNodeId);
                }
            } else { // Second click: select target or deselect
                const selectedNode = nodes.get(selectedTerritory);
                if (clickedNodeId === selectedTerritory) {
                    selectedTerritory = null; // Deselect
                    console.log("Deselected territory");
                } else if (node.owner !== 'Human') { // Target is an enemy
                    const neighborIds = network.getConnectedNodes(selectedTerritory);
                    if (neighborIds.includes(clickedNodeId)) {
                        const maxArmies = parseInt(selectedNode.label.split('\n')[1]) - 1;
                        const numToSuggest = Math.min(3, maxArmies);
                        const numArmiesStr = prompt(`Attack ${clickedNodeId} from ${selectedTerritory} with how many armies? (1-${numToSuggest})`, numToSuggest);
                        
                        if (numArmiesStr) {
                            const numArmies = parseInt(numArmiesStr);
                            if (numArmies > 0 && numArmies <= maxArmies && numArmies <= 3) {
                                await apiPost('/api/attack', { from_terr: selectedTerritory, to_terr: clickedNodeId, armies: numArmies });
                            } else {
                                alert(`Invalid number of armies. You can attack with 1 to ${Math.min(maxArmies, 3)} armies.`);
                            }
                        }
                    } else {
                        selectedTerritory = null; // Clicked non-adjacent enemy, so deselect
                    }
                } else { // Target is friendly
                    if (nodeArmies > 1) {
                        selectedTerritory = clickedNodeId; // Select the new territory
                        console.log("Selected new territory for attack:", clickedNodeId);
                    } else {
                        selectedTerritory = null; // Deselect if new territory can't attack
                    }
                }
            }
        } else if (gameState.phase === 'FORTIFY') {
            if (!selectedTerritory) { // First click: select source territory
                if (node.owner === 'Human' && nodeArmies > 1) {
                    selectedTerritory = clickedNodeId;
                    console.log("Selected territory for fortify:", clickedNodeId);
                } else if (node.owner === 'Human') {
                    alert("You need at least 2 armies to fortify from a territory.");
                }
            } else { // Second click: select target or deselect
                if (selectedTerritory === clickedNodeId) {
                    selectedTerritory = null; // Deselect
                    console.log("Deselected territory");
                } else if (node.owner === 'Human') {
                    const fromArmies = parseInt(nodes.get(selectedTerritory).label.split('\n')[1]);
                    const maxMove = fromArmies - 1;
                    if (maxMove > 0) {
                        const numStr = prompt(`Move how many troops from ${selectedTerritory} to ${clickedNodeId}? (1-${maxMove})`, "1");
                        if (numStr) {
                            const num = parseInt(numStr);
                            if (num > 0 && num <= maxMove) {
                                console.log(`Attempting fortify: ${selectedTerritory} -> ${clickedNodeId} with ${num} armies`);
                                const result = await apiPost('/api/fortify', { from_terr: selectedTerritory, to_terr: clickedNodeId, armies: num });
                                if (result && !result.success) {
                                    alert("Fortification failed. Territories must be connected by a path of your own territories.");
                                    console.log("Fortify failed", result);
                                }
                            } else {
                                alert(`Invalid number. Must be between 1 and ${maxMove}.`);
                            }
                        }
                    } else {
                        alert("You must leave at least one army behind.");
                    }
                    selectedTerritory = null; // Reset after fortify attempt
                } else {
                    selectedTerritory = null; // Clicked an enemy, reset
                }
            }
        }
        highlightSelection();
    }

    async function handleTradeIn() {
        if (selectedCards.length !== 3) {
            alert("Please select exactly 3 cards to trade in.");
            return;
        }
        
        const result = await apiPost('/api/trade_in_cards', { card_indices: selectedCards });
        if (result && result.success) {
            alert(`Cards traded in successfully! You received ${result.bonus} reinforcements.
Next card set will be worth ${result.next_bonus} reinforcements.`);
            nextCardTradeInBonus = result.next_bonus;
            selectedCards = []; // Clear selection
            updateCardRules(); // Update the card rules display with new bonus value
        }
    }

    // Function to update card trade-in rules info
    function updateCardRules() {
        if (!cardRulesEl) return;
        
        cardRulesEl.innerHTML = `
            <h3>Card Trade-in Rules</h3>
            <p>Current trade-in bonus: <strong>${nextCardTradeInBonus} armies</strong></p>
            <p>Valid card sets:</p>
            <ul>
                <li>3 cards of the same type (Infantry, Cavalry, or Artillery)</li>
                <li>1 card of each type (1 Infantry + 1 Cavalry + 1 Artillery)</li>
                <li>Any set including Wildcards</li>
            </ul>
            <p>You receive a card when you conquer at least one territory during your turn.</p>
        `;
    }

    // Function to process bot actions one by one
    async function processBotActions() {
        if (botActionEl) botActionEl.style.display = 'block';
        
        try {
            // Execute the bot turn first
            console.log('Executing bot turn');
            try {
                const executeBotTurnResponse = await fetch('/api/execute_bot_turn', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                
                const executeBotResult = await executeBotTurnResponse.json();
                console.log('Bot turn execution result:', executeBotResult);
                
                if (!executeBotResult.success) {
                    console.error('Failed to execute bot turn:', executeBotResult.error);
                }
            } catch (error) {
                console.error('Error executing bot turn:', error);
            }
            
            // Now process bot actions
            while (gameState.current_player === 'Bot' && !gameState.winner) {
                // Fetch next bot action
                const response = await fetch('/api/bot_action');
                const result = await response.json();
                
                if (!result || !result.action) {
                    console.log('No more bot actions');
                    break;
                }
                
                const action = result.action;
                console.log('Bot action:', action);
                
                // Display the bot action
                if (botActionEl) {
                    botActionEl.innerHTML = `<strong>Bot Action:</strong> ${action.message}`;
                    botActionEl.classList.add('highlight');
                    
                    // Remove highlight after a moment
                    setTimeout(() => {
                        botActionEl.classList.remove('highlight');
                    }, 1000);
                }
                
                // Special handling for different action types
                if (action.type === 'game_over') {
                    alert('Game over! Bot has won!');
                    break;
                }
                
                // Wait before proceeding to next action (for visual effect)
                await new Promise(resolve => setTimeout(resolve, 1500));
                
                // Refresh game state after each action to see changes
                await fetchGameState();
            }
            
            // Final refresh after all actions
            await fetchGameState();
            
        } catch (error) {
            console.error('Error processing bot actions:', error);
        } finally {
            isProcessingBotActions = false;
            if (botActionEl) botActionEl.style.display = 'none';
        }
    }

    // Initialize the game
    fetchGameState();
});
