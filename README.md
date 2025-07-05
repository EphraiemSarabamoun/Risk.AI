# Risk.AI
Risk playing Bot

## Risk Board

This repository includes a simple Python representation of the classic Risk board.
Run the following command to display the list of continents, territories and their
connections:

```bash
python risk_board.py
```

To see a graphical view, run:

```bash
python risk_board.py --draw
```

## Simple Game

A very small Risk-like simulation between a human and a bot is provided in
`game.py`. Launch it with:

```bash
python game.py
```

Follow the prompts to attack neighboring territories or pass your turn. The bot
will make random attacks when possible. The game ends when one player controls
all territories or you quit.
