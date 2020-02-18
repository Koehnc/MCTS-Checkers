# MCTS-Checkers
**Name:** Carter Koehn

**Since:** 2/17/2020

## Description
This repository encases my senior capstone project for Shenandoah Valley Governor's School. I had very little background information on machine learning and artificial intelligence, so I explored Q-learning, nueral networks, and monte-carlo tree searching. It started with a simple game of checkers played by two random agents. I kept track of the length of games and the win rate for each player. I then changed the state the game is played from; I started one agent with one less piece, which made it 5% more likely to loose. This proved that I could theoretically simulate from each possible board position and move to the highest performing state. Monte-Carlo tree search then expanded this simulation by selectively choosing specific nodes to expand. Once the learning began, instead of game lengths, I kept track of the predicted win rate from each state of the game. To make the code learn even more, I decided to implement a database(in SQL) that would keep track of already recorded board states. This essentially built a lookup tree.

### Monte-Carlo Tree Search
'Put image here'
Monte-Carlo Tree Search works by selecting a node, expanding it, simulating from it, and then back propogating the score.
>Easier said than done

Take an exampe from my checkers program: Initially it starts with one board state. The expand function then looks at every single option that is available, and it simulates a completely random game from each new state. The outcome of the simulated game is then backpropogated to the new moves, and then up to the initial node. The next time it selects a node, it uses a bandit function that balances reward and number of simulations from that node. Once selected, it expands that node and starts all over.

## How to Run
>Note to self

Make a new file that initializes the table and then runs it

## Performance
If the checkers game does not use any learning or any MCTS, it performs at ~120 games per second. Once MCTS is introduced, the rate is drastically decreased so much that it can only simulate games between 15 and 20 games per second. When the program updates the states and rewards into and SQL database, simulation drops to ~5 games per second, which makes one full game about 10-15 minutes to run.

### Future Goals
  * Change the SQL primary key to something other than a very large string
  * Some methods can be structured better to make the code shorter and more efficient
  * Needs more data
    * Needs to play itself instead of a random agent to narrow the searching tree
  * The game does not include double jumping
