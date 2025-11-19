from time import sleep
from threading import Thread
def task1():
    for i in range(5):
        print("Task1", i)
        sleep(1)

def task2():
    for i in range(10):
        print("Task2", i)
        sleep(1)

tasks = [
    Thread(target=task1, daemon=False),
    Thread(target=task2, daemon=False),
]

# Start all tasks
for t in tasks:
    t.start()

print("Background tasks started.")

# Wait for ALL tasks to finish
for t in tasks:
    t.join()

print("All tasks finished. Exiting.")