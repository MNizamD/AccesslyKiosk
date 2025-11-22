from webview import create_window, start as webview_start, Window
import sys
from pathlib import Path
from app_ext import message_box, MessageBoxIcon


def init_js_ready(window: Window):
    window.evaluate_js("fadeOutLoader()")


class LoginWall:
    def __init__(self, web_dir: str):
        self.web_dir = Path(web_dir)
        self.login_path = self.web_dir / "web" / "login" / "index.html"
        if not self.login_path.exists():
            print(self.login_path)
            raise FileNotFoundError("Login UI not found.")
        self._allow_close = False
        self._destruct = False
        self.api = Api(self)

    def block_close(self, window):
        """Prevent user from closing window unless allowed by code"""
        if self._allow_close or self.is_destructing():
            return True  # Allow Python to close
        print("User tried to close window! Blocked.")
        return False  # Block user attempts (Alt+F4)

    def run(self):
        dev_mode = True
        # Attach the close handler
        wall_window = create_window(
            "Access Wall",
            url=f"file://{str(self.login_path)}",
            width=400,
            height=400,
            fullscreen=(not dev_mode),
            frameless=True,
            on_top=True,
            js_api=self.api,
            confirm_close=False,  # Needed to intercept close events
        )
        if wall_window is None:
            raise Exception("Failed to start window")
        self.wall_window = wall_window
        self.wall_window.events.closing += self.block_close
        webview_start(debug=False)

    def is_destructing(self):
        return self._destruct


class Api:
    def __init__(self, parent: "LoginWall"):
        from socket import gethostname

        self._pc_name = gethostname()  # Get PC hostname
        self._parent = parent

    def get_pc_name(self):
        """Return the PC name to the frontend"""
        return self._pc_name

    def validate_login(self, user_id):
        if user_id == "destruct":
            self._parent._destruct = True
            self._parent.wall_window.destroy()

        elif user_id == "iamadmin":
            self._user = "Admin"
            self.open_session()

        else:
            message_box(
                "Student ID not found!", "Not Found", icon=MessageBoxIcon.WARNING
            )

    def open_session(self):
        print("Login successful!")
        self._parent._allow_close = True
        self.session_path = self._parent.web_dir / "web" / "session" / "index.html"
        if not self.session_path.exists():
            raise FileNotFoundError("Session UI not found.")

        session = Session(self)
        self._allow_close = False  # Allow Python to close
        session_window = create_window(
            title="Session",
            url=f"file://{str(self.session_path)}",
            background_color="#212529",
            width=300,
            height=200,
            js_api=session,
            resizable=False,
            # frameless=True
        )
        if session_window is None:
            raise Exception("Failed to start session window.")
        self.session_window = session_window
        self.session_window.events.closing += self.block_close
        self._parent.wall_window.destroy()  # Now it will close

    def block_close(self, window):
        """Prevent user from closing window unless allowed by code"""
        if self._allow_close:
            return True  # Allow Python to close
        print("User tried to close window! Blocked.")
        return False  # Block user attempts (Alt+F4)

    def show_message(self, *args, **kwargs):
        return message_box(*args, **kwargs)


class Session:
    def __init__(self, parent: Api) -> None:
        self._parent = parent

    def get_user(self):
        from json import dumps

        return dumps({"name": self._parent._user})

    def logout(self):
        self._parent._allow_close = True
        self._parent.session_window.destroy()

    def show_message(self, *args, **kwargs):
        return message_box(*args, **kwargs)


def run(path: str):
    try:
        while True:
            login = LoginWall(path)
            login.run()
            if login.is_destructing():
                break  #
            print("Loop")

    except Exception as e:
        print(e)


if __name__ == "__main__":
    run(
        str(
            Path(sys.executable).parent
            if getattr(sys, "frozen", False)
            else Path(__file__).parent
        )
    )
