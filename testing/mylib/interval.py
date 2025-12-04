from threading import Timer


class setInterval:
    def __init__(self, function, interval, *args, **kwargs):
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.timer = None
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self.timer = Timer(self.interval, self._run)
            self.timer.daemon = True  # ← This makes it stop when main program exits
            self.timer.start()
            self.is_running = True

    def stop(self):
        if self.timer:
            self.timer.cancel()
        self.is_running = False


# # Usage example
# def my_function(name):
#     print(f"Hello {name}! Time: {time.time()}")


# # Create interval that runs every 2 seconds
# interval = setInterval(my_function, 2, "Alice")

# # Let it run for 10 seconds
# time.sleep(10)

# # Stop the interval
# interval.stop()
# print("Interval stopped")
