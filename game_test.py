import game
import time

x = game.Game()
for i in range(1000):
    if i % 100 == 0:
        x.buzz()
    time.sleep(0.1)
    print(x.gamestate())
