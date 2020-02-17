'''
@author Carter Koehn
@since 10/15/2019
Desc: 
This program contains the logic to make a checkers game work without double jumps or forced jumps.
It can use a computer generated random move, an inputted user move, or use MCTS (Which is what it does now)
It keeps track of the simulating and total times and of the average reward per board_state

-Can simulate random games of checkers independantly from MCTS at about 120 games per second
-Using MCTS without adding to or reading from the SQL db simulates at about 15 games per second
-However the SQL table is ugly and can only update games into the db at about 5 games per second
'''

#HyperParameters
numrollout = 250    #Number of rollouts performed
sqlUpdate_after_NGames = 2  #The sql speed database updates after these many games

#Set up
import pygame
import random as rand
import copy
from Testing_MCTS import MCTS
import SQLManipulator as sqlm

#Colors
black = (0,0,0)
grey = (120,120,120)
white = (255,255,255)
red = (255,0,0)
lightred = (255,120,120)
darkred = (128,0,0)
green = (0,255,0)
lightgreen = (120,200,120)
darkgreen = (0,128,0)
blue = (0,0,255)
lightblue = (120,120,255)
darkblue = (0,0,128)

#Variable Declaration
board = []
direc = {'upr':-7,'upl':-9,'dl':7,'dr':9}
options1 = [] #Moves team 1 can do
options2 = [] #Moves team 2 can do
avgRlist = [] #Maps the highest reward per state
winlist = [] #Keeps track of each win
pclock = pygame.time.Clock() #Keeps track of the total running time
simclock = pygame.time.Clock() #Keeps track of the time simulating games
BADGAME = pygame.USEREVENT + 1 #Pygame event for timer of games
totaltime = 0
square = None #Used in UserMove

#Classes
#Class Board_state is supposed to be an instance of the board that's hashable and can be ran through MCTS
class Board_State():
    def __init__(self, board):
        #These values are just initial values that don't matter in the functions
        self.board = board
        self.options1, self.options2 = CanMove(self.board)
        self.options = self.options1 + self.options2
        self.team = 1

    def find_children(self, board):
        children = set()
        #Update the options
        self.options1, self.options2 = CanMove(board)
        for option in self.options1:
            board_copy = copy.deepcopy(board)
            move(board_copy, option[0], option[1], option[2], option[3])
            children.add(Board_State(board_copy))
        return children

    def find_oppchildren(self,board):
        children = set()
        self.options1, self.options2 = CanMove(board)
        for option in self.options2:
            board_copy = copy.deepcopy(board)
            move(board_copy, option[0], option[1], option[2], option[3])
            children.add(Board_State(board_copy))
        return children


    def find_random_child(self, board):
        board_copy = copy.deepcopy(board)
        
        self.options1, self.options2 = CanMove(board)
        choice = rand.choice(self.options1)
        move(board_copy, choice[0], choice[1], choice[2], choice[3])

        if not self.is_terminal(board_copy):
            self.options1, self.options2 = CanMove(board_copy)
            choice2 = rand.choice(self.options2)        
            move(board_copy, choice2[0], choice2[1], choice2[2], choice2[3])

        return Board_State(board_copy)

    def is_terminal(self,board):
        self.options1,self.options2 = CanMove(board)
        if len(options1) == 0 or len(options2) == 0:
            return True
        else:
            return False

    def reward(self,board):
        if (-2 in board or -1 in board) and not (2 in board or 1 in board):
            return 0
        elif (2 in board or 1 in board) and not (-2 in board or -1 in board):
            return 1
        else:
            #Tie instances shouldn't really be a thing
            #Someone is winning
            #print("Tie Instance")
            return .5


#Class game includes the methods for the game.
class Game():
    def __init__(self,size):
        self.screen = pygame.display.set_mode((size,size))
        self.size = size / 8
        self.running = True

    #Init makes the background
    def init(self):
        self.screen.fill(grey)
        #BADGAME is just a game taking longer than 1000 milliseconds
        #pygame.time.set_timer(BADGAME, 60000) #This won't run visual slow games
        MakeBoard()

        #Makes the background board checkered
        for index in range(len(board)):
            if board[index] == 'null':
                pygame.draw.rect(self.screen, white, ((index % 8) * self.size, (index // 8) * self.size, self.size, self.size ))
        UpdateScreen()
        self.PieceUpdate()
        CanMove(board)

    #PieceUpdate updates the visuals of pieces according to list board
    def PieceUpdate(self):
        for index in range(len(board)):
            if board[index] == 1:
                pygame.draw.circle(self.screen,  lightblue, (int((index % 8) * self.size + self.size / 2), int((index // 8) * self.size + self.size / 2)), int(self.size / 2 - 5))
            elif board[index] == -1:
                pygame.draw.circle(self.screen,  lightred, (int((index % 8) * self.size + self.size / 2), int((index // 8) * self.size + self.size / 2)), int(self.size / 2 - 5))
            elif board[index] == 2:
                pygame.draw.circle(self.screen,  darkblue, (int((index % 8) * self.size + self.size / 2), int((index // 8) * self.size + self.size / 2)), int(self.size / 2 - 5))
            elif board[index] == -2:
                pygame.draw.circle(self.screen,  darkred, (int((index % 8) * self.size + self.size / 2), int((index // 8) * self.size + self.size / 2)), int(self.size / 2 - 5))
            elif board[index] == 0:
                pygame.draw.rect(self.screen, grey, ((index % 8) * self.size, (index // 8) * self.size, self.size, self.size ))
            else:
                continue

    #gameEvent is the pygame event handler.. Checks for BADGAME and QUIT
    def gameEvent(self):
        if pygame.event.get(pygame.QUIT): 
            #This updates at the beginning of the loop so it runs an extra time
            print("\nEnding\n")
            self.running = False
        for event in pygame.event.get():
            if event.type == BADGAME:
                print("BADGAME event handled\n")
                self.Restart()    
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    print("\nEnding\n")
                    self.running = False

    #Restarts the game
    def Restart(self):
        global board, winlist, avgRlist

        tietest = []

        for index in range(len(board)):
            if board[index] == 1 or board[index] == 2:
                tietest.append(1)
            if board[index] == -1 or board[index] == -2:
                tietest.append(-1)

        
        txtfile = open("MoveSets.txt", 'a')
        if 1 in tietest and not(1 in tietest and -1 in tietest):
            winlist.append(1)
            txtfile.write(str(avgRlist) + "\n")
        if -1 in tietest and not(1 in tietest and -1 in tietest):
            winlist.append(-1)
            txtfile.write(str(avgRlist) + "\n")
        txtfile.close()
        
        #if 1 in tietest and -1 in tietest:     #Tie logic: if the board has 1 and -1 then it's a tie
            #print("Tie")


        if len(winlist) % 1 == 0: #This throws error if it doesn't get to complete the first game lul
            PrintStats()
        
        avgRlist = []
        board = []
        self.init()


#Methods
#UpdateScreen = pygame.display.update()
def UpdateScreen():
    pygame.display.update()

#move is the checkers movement. Doesn't use logic, can't allow user rn
def move(board,index,dire,status,newstat):
    if newstat == 0:
        board[index] = 0
        board[index + dire] = status
    else:
        board[index] = 0
        board[index + dire] = 0
        board[index + dire * 2] = status

    CanMove(board)

#CompMove = randomly chooses move in options, uses move func
def CompMove(team):
    if team == 1:
        #choose = self.ScoreNodes(board,options1)
        choose = rand.choice(options1)
    elif team == -1:
        #choose = self.ScoreNodes(board,options2)
        #choose = sm.IntelliMove(options2,weights)
        choose = rand.choice(options2)
    else:
        return "No such team"

    move(board, choose[0],choose[1],choose[2],choose[3])

#MakeBoard = sets the board up in terms of 1, -1, 0, and null
def MakeBoard():
    global board
    for instances in range(0,64):
        board.append(0)

    for x in range(len(board)):
        #Every other square i na row, alternating which row starts w/ one, and not in the middle yet
        if (x + (x // 8)) % 2 == 0:
            board[x] = 0
        if (x + (x // 8)) % 2 == 0 and x < 24: #x < 24 is usual
            board[x] = 1
        if (x + (x // 8)) % 2 == 0 and x > 40: #x > 40 is usual
            board[x] = -1
        if (x + (x // 8)) % 2 == 1:
            board[x] = 'null'

#CanMove = returns true if an active square has atleast one movement
def CanMove(board):
    global options1, options2
    options1 = []
    options2 = []
    for index in range(len(board)):
        #For every square that isn't 0 or null
        if board[index] != 0 and board[index] != 'null':
            team = board[index]
            if (56 < index <= 63 and board[index] == 1) or (0 <= index < 8 and board[index] == -1):
                board[index] = 2 * board[index]
            #For every direction it can move
            for dire in direc:
                dire = direc[dire]
                newind = index + dire
                skipind = index + 2 * dire

                if (-1 < newind <= 63 and not ((board[newind] == team * -1 or board[newind] == team * -2 or board[newind] == team * -.5) and not -1 < skipind < 64)):
                    #Index of newind, if there's a faulty jump
                    if not(((board[newind] == team * -1 or board[newind] == team * -2 or board[newind] == team * -.5) and -1 < skipind < 64 and board[skipind] != 0) or board[newind] == team or board[newind] == team * 2 or board[newind] == team * .5 or (abs((index // 8)-(newind // 8)) != 1)) :
                        #Above checks- Faulty Skip Logic, the same teams piece in newind, and jumping more than one line 
                        if not (dire * team < 0 and not abs(board[index]) // 2 == 1):
                            #if it's not moving "Backwards" or it's a king
                            if board[index] > 0:
                                #Team 1
                                options1.append((index, dire, board[index], board[newind]))
                            elif board[index] < 0:
                                #Team 2
                                options2.append((index, dire, board[index], board[newind]))
    return options1, options2

#PrintStats = the print statements at the end
def PrintStats():
    global totaltime

    pclock.tick()
    totaltime += pclock.get_time() / 1000
    gamesran = len(winlist)
    if len(winlist) > 0:
        print()
        print("Game stats: " + str(gamesran) + " games ran in" + " %2d hours, %2d minutes, %2.2f seconds" %(totaltime//3600, (totaltime%3600)//60, totaltime%60) + ", avg time(s) per game = %2.2f" % (totaltime / gamesran))
        print("Team 1 wins: " + str(winlist.count(1)) + ", Percentage = %2.2f" % ((winlist.count(1)/len(winlist))*100))
        print("Team 2 wins: " + str(winlist.count(-1)) + ", Percentage = %2.2f" % ((winlist.count(-1)/len(winlist))*100))
        print()
    else:
        print()
        print("Game stats: " + str(gamesran) + " games ran in" + " %2d hours, %2d minutes, %2.2f seconds" %(totaltime//3600, (totaltime%3600)//60, totaltime%60))
        print()

    if len(winlist) % sqlUpdate_after_NGames == 0 and len(winlist) > 0:
        Updatesqldb()

#Updatesqldb = Stores and then clears the data, so it runs fast always. No need to restart
def Updatesqldb():
    sqlm.run()

#UserMove = Checks where the users cursor clicks to move that piece to the next square
def UserMove(game):
    global square
    screen = game.screen
    size = game.size

    while game.running:
        game.gameEvent()
        game.PieceUpdate()

        mouse = pygame.mouse.get_pos()
        mx = mouse[0] // 50
        my = mouse[1] // 50

        choices = []
        optionlist = []
        for option in options2:
            if option[0] == square:
                choice=(square + option[1] + option[1]*(abs(option[3]) % 2))
                choices.append(choice)
                optionlist.append(option)
                pygame.draw.rect(screen, (200,200,200,128), ((choice%8)*size, (choice//8)*size, size, size))

            click = pygame.mouse.get_pressed()
        
        #return t or f, if move successful t, break
        if click[0] == 1:
            square = (my * 8) + mx
            if square in choices:
                option = optionlist[choices.index(square)]
                square = None
                move(board,option[0],option[1],option[2],option[3])
                return

        if click[2] == 1:
            square = None
        
        UpdateScreen()

    #if square:
        #pygame.draw.rect(screen, (200,200,200,128), ((square%8)*size, (square//8)*size, size, size))

    #Side note, the allow logic just see if the move it's trying to do is in options
    #Just highlight all in options and click one of the options. Fact check if its bad square


def run():
    global board, totaltime
    game = Game(400)
    pygame.init()
    game.init()
    tree = MCTS()

    #pclock counts the entire game time
    pclock.tick()

    while (game.running):
        game.gameEvent()

        if len(options1) > 0:
            #MCTS in action
            CanMove(board)

            #By entering a specific board below, you can force the computer to choose a move at a given state
            #Because it makes the board equal to this choice instead of returning an option
            #[1, 'null',0,'null',0,'null',0,'null','null',0,'null',0,'null',0,'null',0,0,'null',0,'null',0,'null',0,'null','null',0,'null',-2,'null',0,'null',0,0,'null',0,'null',2,'null',0,'null','null',0,'null',0,'null',0,'null',0,0,'null',0,'null',0,'null',0,'null','null',0,'null',0,'null',0,'null',-1]
            #Above is a boardstate that you can plug into the board_state to see a correct move.
            board_state = Board_State(board)
            simclock.tick()

            for i in range(numrollout):
                tree.do_rollout(board_state)
                if i % 10 == 0:
                    print(i)
                    if i % 50 == 0 and i != 0:
                        simclock.tick()
                        simtime = 50 / (simclock.get_time() / 1000)
                        print("Simulation speed: %2.2f" %(simtime), "g/s")
            print()
            choice, optionsNQ = tree.choose(board_state) 
            board = (choice.board)

            def avgRmethod(o):
                return o[1] / o[0]
            bestavgR = max(optionsNQ, key=avgRmethod)
            avgRlist.append((int(bestavgR[1] / bestavgR[0] * 10000) / 10000))

            nsum = 0
            for option in optionsNQ:
                nsum += option[0]
            
            CanMove(board)

        
        if len(options2) > 0:
            #UserMove(game)
            CompMove(-1)

        if len(options1) <= 0 or len(options2) <= 0:
            game.Restart()

        pclock.tick()
        totaltime += pclock.get_time() / 1000
        print("Total visits: ", nsum, " / ", numrollout)
        print("Number of options: ", len(optionsNQ))
        print("Average Visits: " + "%2.2f" %(nsum/len(optionsNQ)))
        print("Running time:" + " %2d hours, %d minutes, %2.2f seconds" %(totaltime//3600, (totaltime%3600)//60, totaltime%60))
        print(avgRlist)

        game.PieceUpdate() #These two lines update the visual part
        UpdateScreen() #Removing them makes it run faster

        #pygame.time.wait(500) #This will not work with the game checking for games longer than a second

    pygame.quit()
    PrintStats()
    tree.close()

#run()  #It's now called in the ActiveRunner.py script

#CanMove() has to be updated after each and every move (So each next move is legit and not blind)
