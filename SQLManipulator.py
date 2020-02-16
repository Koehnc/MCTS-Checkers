'''
@author Carter Koehn
@since 11/19/2019
Desc: This file is used to edit the MoveData.db database
'''
import sqlite3 as sql
connection = sql.connect("MoveData.db")
crsr = connection.cursor()

#Clear_data removes all of the data from data2
def clear_data(crsr=crsr):
    #DELETE FROM <table> WHERE <condition>; No Where part = All rows
    crsr.execute("DELETE FROM data2")

#gameCount just returns the information in a readible format
def gameCount( data='data', crsr=crsr):
    crsr.execute("SELECT n from %s" %(data))
    games = crsr.fetchall()
    crsr.execute("SELECT q from %s" %(data))
    wins = crsr.fetchall()

    sumgame = 0
    sumwins = 0
    for i in range(len(games)):
        sumgame += games[i][0]
        sumwins += wins[i][0]
    print("Different Moves:", len(games),"\nTotal n:", sumgame, "\nTotal q:", sumwins, "\nAverage reward per visit: %.4f" %(sumwins/sumgame), "\nVisits per node: %2.2f" %(sumgame / len(games)))

#UpdateR updates the average reward per node (Column in table)
def updateR(crsr=crsr):
    crsr.execute("UPDATE data2 SET avgR = ROUND(CAST(q AS float) / CAST(n AS float), 3)")
    crsr.execute("UPDATE data SET avgR = ROUND(CAST(q AS float) / CAST(n AS float), 3)")

#addData takes the data from data2 and puts it into data
def addData(crsr=crsr):
    crsr.execute("SELECT board FROM data2")
    boards2 = crsr.fetchall()

    crsr.execute("SELECT board FROM data")
    boards = crsr.fetchall()

    for board in boards2:
        if boards2.index(board) % 500 == 0:
            print("Updating data: %2.2f%% Done" %(boards2.index(board) / len(boards2) * 100))
        crsr.execute('SELECT n FROM data2 WHERE board="%s"' %(board[0]))
        n = crsr.fetchall()
        crsr.execute('SELECT q FROM data2 WHERE board="%s"' %(board[0]))
        q = crsr.fetchall()
        if board in boards:
            crsr.execute('update data set n= n + %d, q= q + %d where board like "%s"' %(n[0][0],q[0][0],board[0]))
        else:
            crsr.execute('INSERT OR IGNORE INTO data VALUES ("%s", %d, %f, %f)' %(board[0], n[0][0], q[0][0], q[0][0]/n[0][0]))
    clear_data(crsr)

#Runs it all in an organized way
def run():
    connection = sql.connect("MoveData.db")
    crsr = connection.cursor()
    print("\nSQL data information:")

    gameCount('data', crsr)
    gameCount('data2', crsr)
    addData(crsr)
    updateR(crsr)
    print("\n")
    gameCount('data',crsr)

    connection.commit()
    connection.close()
    print("\nConnection Closed")


#crsr.execute("SELECT n FROM data ORDER BY n DESC LIMIT 10")
#print(crsr.fetchall())
#prints the top ten visits nodes, but the amount they've been visited
#Technically speaking these nodes should have the best decision made.


connection.commit()
connection.close()