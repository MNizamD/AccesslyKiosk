import __fix__
import mylib.updater as update
from threading import Thread


if __name__ == "__main__":
    try:
        t = Thread(target=update.run, daemon=False)
        t.start()
        t.join()
    except Exception as e:
        print(e)
