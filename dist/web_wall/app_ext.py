from ctypes import windll, c_int, c_wchar_p
from enum import IntEnum, IntFlag
from typing import Literal


# ─────────────────────────────────────────────────────────────
# Define Enums for clarity and type-safety
# ─────────────────────────────────────────────────────────────


class MessageBoxButtons(IntFlag):
    OK = 0x00000000
    OK_CANCEL = 0x00000001
    ABORT_RETRY_IGNORE = 0x00000002
    YES_NO_CANCEL = 0x00000003
    YES_NO = 0x00000004
    RETRY_CANCEL = 0x00000005
    CANCEL_TRY_CONTINUE = 0x00000006


class MessageBoxIcon(IntFlag):
    NONE = 0x00000000
    ERROR = 0x00000010
    QUESTION = 0x00000020
    WARNING = 0x00000030
    INFORMATION = 0x00000040


class MessageBoxResult(IntEnum):
    OK = 1
    CANCEL = 2
    ABORT = 3
    RETRY = 4
    IGNORE = 5
    YES = 6
    NO = 7
    TRY_AGAIN = 10
    CONTINUE = 11


# ─────────────────────────────────────────────────────────────
# MessageBox function
# ─────────────────────────────────────────────────────────────
MB_TOPMOST = 0x00040000  # makes message box always on top


def message_box(
    text: str,
    title: str = "Message",
    buttons: MessageBoxButtons = MessageBoxButtons.OK,
    icon: MessageBoxIcon = MessageBoxIcon.NONE,
) -> MessageBoxResult:
    """Show a native Windows MessageBox and return the user's choice."""
    flags = buttons | icon
    flags |= MB_TOPMOST

    result = windll.user32.MessageBoxW(
        0, c_wchar_p(text), c_wchar_p(title), c_int(flags)
    )
    return MessageBoxResult(result)


def get_details_json(dir_path) -> dict[Literal["version", "updated"], str] | None:
    from pathlib import Path

    path = Path(dir_path) / "details.json"
    details = {}
    from json import load

    try:
        if not path.exists():
            raise FileNotFoundError(f"Missing details: {path}")
        with open(path, "r", encoding="utf-8") as f:
            details = load(f)

        if any((key not in details) for key in ["version", "updated"]):
            raise Exception("Invalid detail json.")

        return details

    except Exception as e:
        print("[GET_DETAILS_JSON_ERR]:", e)
        return None


# ─────────────────────────────────────────────────────────────
# Example Usage
# ─────────────────────────────────────────────────────────────
def test_msg():
    result = message_box(
        "Do you want to continue?",
        "Confirm Action",
        buttons=MessageBoxButtons.YES_NO_CANCEL,
        icon=MessageBoxIcon.QUESTION,
    )

    if result == MessageBoxResult.YES:
        message_box("You pressed YES!", "Result", icon=MessageBoxIcon.INFORMATION)
    elif result == MessageBoxResult.NO:
        message_box("You pressed NO!", "Result", icon=MessageBoxIcon.WARNING)
    elif result == MessageBoxResult.CANCEL:
        message_box("Cancelled.", "Result", icon=MessageBoxIcon.ERROR)


if __name__ == "__main__":
    from sys import argv

    print(get_details_json(argv[0]))
