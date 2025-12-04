if __name__ == "__main__":
    import __fix2__
from typing import Any, Literal
from mylib.conn import fetch_database, internet_ok
from time import sleep
from mylib.util import run_normally, run_elevated

ParseArgsType = dict[
    Literal["wait", "python", "sleep", "cmd", "elevated", "hidden"], Any
]


def parse_args(args: list) -> ParseArgsType:
    data: ParseArgsType = {
        "wait": False,
        "python": False,
        "sleep": 1,
        "cmd": "",
        "elevated": False,
        "hidden": False,
    }

    i = 0
    value_args = ["--sleep"]
    bool_args = ["--wait", "--python", "--elevated", "--hidden"]
    while i < len(args):
        arg = args[i].lower()
        if arg in value_args:
            if i + 1 < len(args) and not str(args[i + 1]).startswith("--"):
                data[arg[2:]] = args[i + 1]  # type: ignore
                i += 1
            else:
                raise Exception(f"[ERROR] Missing value for --{arg}")

        elif arg in bool_args:
            data[arg[2:]] = True
        else:
            data["cmd"] += f" {arg}"
        i += 1

    return data


class Remote:
    _instance = None  # singleton-style cache

    def __new__(cls):
        # ✅ Lazy singleton — only one instance per project
        if cls._instance is None:  # or cls._instance._cmd != cmd:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return  # skip re-init if already created
        # self._index = 0  # test index
        self._interval = 10
        self._initialized = True

    @property
    def CMD_INTERVAL(self):
        return self._interval

    def get_commands(self):
        # print(self._index)
        # self._index += 1
        if not internet_ok(quiet=True):
            print("[Remote]: No internet.")
            return
        self.__fetch_commands()

    def __fetch_commands(self):
        # cmd_lines = ["cmd --wait", "notepad"]
        from socket import gethostname

        cmd_lines = fetch_database(
            select_=["command"],
            from_="app_commands",
            where_=f"(target_pc = '{gethostname()}' or target_pc = 'all') AND deleted_at is null AND created_at >= (NOW() - INTERVAL '{self.CMD_INTERVAL * 1.5} seconds')",
        )
        if cmd_lines is None:
            print("[REMOTE_ERR]: Failed to fetch from database.")
            return

        print(cmd_lines)
        for cmd_line in cmd_lines:
            if "command" in cmd_line and isinstance(cmd_line["command"], str):
                line = cmd_line["command"]
                args = parse_args(line.split())
                if args["elevated"]:
                    run_elevated(
                        cmd=args["cmd"], wait=args["wait"], with_python=args["python"]
                    )
                else:
                    run_normally(
                        cmd=args["cmd"], wait=args["wait"], hidden=args["hidden"]
                    )
                # --dir C:\Users\Marohom\Documents\NizamLab\dist --user "Marohom"
                sleep(int(args["sleep"]))
            else:
                print(cmd_line)
                print("Command was not a string.")


def test():
    from sys import argv

    print(parse_args(argv[1:]))
    # print(input("GG:").split())


if __name__ == "__main__":
    remote = Remote()
    remote.get_commands()
