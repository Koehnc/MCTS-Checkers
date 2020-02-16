"""
A minimal implementation of Monte Carlo tree search (MCTS) in Python 3
Luke Harold Miles, July 2019, Public Domain Dedication
See also https://en.wikipedia.org/wiki/Monte_Carlo_tree_search
https://gist.github.com/qpwo/c538c6f73727e254fdc7fab81024f6e1

Edited by Carter Koehn October 2019 to fit into my Checkers Program
"""
from abc import ABC, abstractmethod
from collections import defaultdict
import math
import threading
import sqlite3
time_check = False

def r0():
    global time_check
    time_check = True
    print("Too long of a game")
    return 

class MCTS:
    "Monte Carlo tree searcher. First rollout the tree then choose a move."

    def __init__(self, exploration_weight=1):
        self.Q = defaultdict(int)  # total reward of each node
        self.N = defaultdict(int)  # total visit count for each node
        self.children = dict()  # children of each node
        self.exploration_weight = exploration_weight
        self.timer = threading.Timer(5.0, r0)
        self.connection = sqlite3.connect("MoveData.db")
        self.crsr = self.connection.cursor()

    def choose(self, node):
        "Choose the best successor of node. (Choose a move in the game)"
        if node.is_terminal(node.board):
            raise RuntimeError(f"choose called on terminal node {node}")

        if node not in self.children:
            print("It chose Random")
            return node.find_random_child(node.board)
        
        optionsNQ = []

        def score(n):
            if self.N[n] == 0:
                return float("-inf")  # avoid unseen moves
            
            #Pull nval from running db
            self.crsr.execute('SELECT n FROM data2 WHERE board="%s"' %(str(n.board)))
            nval = self.crsr.fetchall()[0][0]

            #Pull qval from running db
            self.crsr.execute('SELECT q FROM data2 WHERE board="%s"' %(str(n.board)))
            qval = self.crsr.fetchall()[0][0]

            #Add the nval from the big db
            self.crsr.execute('SELECT n FROM data WHERE board="%s"' %(str(n.board)))
            nval2 = self.crsr.fetchall()
            if len(nval2) > 0:
                nval += nval2[0][0]
                
            #Add the qval from thr big db
            self.crsr.execute('SELECT q FROM data WHERE board="%s"' %(str(n.board)))
            qval2 = self.crsr.fetchall()
            if len(qval2) > 0:
                qval += qval2[0][0]

            print(qval, " / ", nval, " = ", qval / nval) #Avg reward per state
            optionsNQ.append((nval,qval))

            return qval / nval
        #Chooses the node with the highest avg reward
        return max(self.children[node], key=score),optionsNQ

    def do_rollout(self, node):
        "Make the tree one layer better. (Train for one iteration.)"
        path = self._select(node)
        leaf = path[-1]
        self._expand(leaf)
        reward = self._simulate(leaf)
        self._backpropagate(path, reward)

    def _select(self, node):
        "Find an unexplored descendent of `node`"
        path = []
        while True:
            path.append(node)
            if node not in self.children or not self.children[node]:
                # node is either unexplored or terminal
                return path
            unexplored = self.children[node] - self.children.keys()
            if unexplored:
                n = unexplored.pop()
                path.append(n)
                return path
            node = self._uct_select(node)  # descend a layer deeper

    def _expand(self, node):
        "Update the `children` dict with the children of `node`"
        if node in self.children:
            return  # already expanded
        self.children[node] = node.find_children(node.board)
        for child in self.children[node]:
            self.children[child] = node.find_oppchildren(child.board)

    def _simulate(self, node):
        global time_check
        "Returns the reward for a random simulation (to completion) of `node`"
        invert_reward = True
        self.timer = threading.Timer(2.5,r0)
        self.timer.start()
        while True:
            if node.is_terminal(node.board):
                reward = node.reward(node.board)
                self.timer.cancel()
                return reward
                #return 1 - reward if invert_reward else reward
            if time_check:
                time_check = False
                return 0
            node = node.find_random_child(node.board)
            invert_reward = not invert_reward

    def _backpropagate(self, path, reward):
        "Send the reward back up to the ancestors of the leaf"
        for node in reversed(path):

            self.N[node] += 1
            if not node.is_terminal(node.board):
                reward = 1- reward  # 1 for me is 0 for my enemy, and vice versa
            self.Q[node] += reward

            self.crsr.execute('INSERT OR IGNORE INTO data2 VALUES ("%s", %d, %f, 0)' %(str(node.board), 0, 0))
            self.crsr.execute('update data2 set n= n + %d, q= q + %d where board like "%s"' %(1,reward,str(node.board)))
            self.connection.commit()

    def _uct_select(self, node):
        "Select a child of node, balancing exploration & exploitation"

        # All children of node should already be expanded:
        #assert all(n in self.children for n in self.children[node])

        log_N_vertex = math.log(self.N[node])
        #This is the log of the total visits in Node

        def uct(n):
            "Upper confidence bound for trees"
            if self.N[n] == 0:
                return 999
            return self.Q[n] / self.N[n] + self.exploration_weight * math.sqrt(
                log_N_vertex / self.N[n]
            )

        return max(self.children[node], key=uct)
    
    def close(self):
        self.connection.commit()
        self.connection.close()
