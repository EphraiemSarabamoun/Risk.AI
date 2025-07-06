document.addEventListener('DOMContentLoaded', function() {
    const container = document.getElementById('mynetwork');
    const statusEl = document.getElementById('game-status');
    const actionBtn = document.getElementById('action-btn');
    const restartBtn = document.getElementById('restart-btn');

    let network = null;
    let gameState = {};
    let selectedTerritory = null;
    let nodes, edges;

    const playerColors = {
        'Human': '#4169E1',
        'Bot': '#DC143C'
    };

    function updateStatus() {
        if (gameState.winner) {
            statusEl.innerText = `Game Over! ${gameState.winner} wins!`;
            actionBtn.style.display = 'none';
            return;
        }

        let statusText = `Phase: ${gameState.phase}`;
        if (gameState.phase === 'DEPLOY') {
            statusText += ` - Reinforcements: ${gameState.reinforcements}`;
        }
        statusEl.innerText = statusText;

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

    function drawBoard(data) {
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
                shape: 'box', size: 20, borderWidth: 2, shadow: true,
                font: { size: 14, color: '#000', multi: true, face: 'arial' }
            },
            edges: { width: 2, shadow: true },
            groups: groups,
            physics: { enabled: false },
            interaction: { dragNodes: true, dragView: true, zoomView: true }
        };

        if (!network) {
            network = new vis.Network(container, { nodes, edges }, options);
            network.on("click", handleNetworkClick);
        } else {
            network.setData({ nodes, edges });
        }
        selectedTerritory = null;
        highlightSelection();
    }

    async function fetchGameState() {
        try {
            const response = await fetch('/api/game_state');
            gameState = await response.json();
            drawBoard(gameState);
            updateStatus();
        } catch (error) {
            console.error('Error fetching game state:', error);
        }
    }

    function highlightSelection() {
        const allNodes = nodes.get({ fields: ['id', 'owner'] });
        const updates = [];

        if (selectedTerritory) {
            const selectedNode = nodes.get(selectedTerritory);
            const neighborIds = network.getConnectedNodes(selectedTerritory);

            allNodes.forEach(node => {
                let borderWidth = 2;
                let color = playerColors[node.owner];

                if (node.id === selectedTerritory) {
                    borderWidth = 4;
                } else if (neighborIds.includes(node.id) && selectedNode.owner !== node.owner && gameState.phase === 'ATTACK') {
                    borderWidth = 3;
                    color = '#FFFF00'; // Yellow for attackable neighbors
                } else if (neighborIds.includes(node.id) && selectedNode.owner === node.owner && gameState.phase === 'FORTIFY') {
                    borderWidth = 3;
                    color = '#00FF00'; // Green for fortifiable neighbors
                }
                updates.push({ id: node.id, borderWidth: borderWidth, color: { border: color } });
            });
        } else {
            allNodes.forEach(node => {
                updates.push({ id: node.id, borderWidth: 2, color: { border: playerColors[node.owner] } });
            });
        }
        nodes.update(updates);
    }

    async function handleNetworkClick(params) {
        const clickedNodeId = params.nodes.length > 0 ? params.nodes[0] : null;

        if (!clickedNodeId) {
            selectedTerritory = null;
            highlightSelection();
            return;
        }

        const node = nodes.get(clickedNodeId);

        if (gameState.phase === 'DEPLOY') {
            if (node.owner === 'Human' && gameState.reinforcements > 0) {
                await apiPost('/api/deploy', { territory: clickedNodeId, armies: 1 });
            }
        } else if (gameState.phase === 'ATTACK') {
            if (!selectedTerritory && node.owner === 'Human' && node.label.split('\n')[1] > 1) {
                selectedTerritory = clickedNodeId;
            } else if (selectedTerritory) {
                if (selectedTerritory === clickedNodeId) {
                    selectedTerritory = null;
                } else if (node.owner !== 'Human') {
                    await apiPost('/api/attack', { from_terr: selectedTerritory, to_terr: clickedNodeId });
                    selectedTerritory = null;
                } else {
                    selectedTerritory = null;
                }
            }
        } else if (gameState.phase === 'FORTIFY') {
             if (!selectedTerritory && node.owner === 'Human') {
                selectedTerritory = clickedNodeId;
            } else if (selectedTerritory) {
                if (selectedTerritory === clickedNodeId) {
                    selectedTerritory = null;
                } else if (node.owner === 'Human') {
                    const num = parseInt(prompt(`Move troops from ${selectedTerritory} to ${clickedNodeId}?`, "1"));
                    if (num > 0) {
                        await apiPost('/api/fortify', { from_terr: selectedTerritory, to_terr: clickedNodeId, armies: num });
                    }
                    selectedTerritory = null;
                } else {
                    selectedTerritory = null;
                }
            }
        }
        highlightSelection();
    }

    async function apiPost(url, body) {
        try {
            await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });
            fetchGameState(); // Refresh state after every action
        } catch (error) {
            console.error(`Error posting to ${url}:`, error);
        }
    }

    actionBtn.addEventListener('click', () => apiPost('/api/next_phase', {}));
    restartBtn.addEventListener('click', () => apiPost('/api/restart', {}));

    fetchGameState();
});
