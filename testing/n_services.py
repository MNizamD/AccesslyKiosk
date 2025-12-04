import __fix1__
from sys import argv
import mylib.updater as update
import mylib.remote as remote
from mylib.interval import setInterval
from atexit import register as atexit_register
from time import sleep


def cleanup():
    """Cleanup function to stop all running intervals and threads"""
    if "updateInterval" in globals():
        updateInterval.stop()
    if "commandInterval" in globals():
        commandInterval.stop()
    # You can add other cleanup tasks here


# Register cleanup to run when script exits
atexit_register(cleanup)


def run_updater():
    updater = update.Updater(cmd=argv)
    updater.initiate_update()
    return setInterval(updater.initiate_update, 10)


def run_commander():
    commander = remote.Remote()
    commander.get_commands()
    return setInterval(commander.get_commands, commander.CMD_INTERVAL)
    # return setInterval(listenToServer, 1)


if __name__ == "__main__":
    try:
        # Start the interval (make sure your setInterval returns an object with stop() method)
        updateInterval = run_updater()

        # Start the thread as daemon so it stops when main thread exits
        commandInterval = run_commander()

        # Keep sleeping indefinitely instead of just 100 seconds
        while True:
            sleep(1)
    except KeyboardInterrupt:
        print("\nReceived interrupt, shutting down...")
    except Exception as e:
        print("[Service Error]:", e)
        cleanup()
    finally:
        cleanup()
        sleep(10)
