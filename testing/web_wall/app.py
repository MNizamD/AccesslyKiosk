from webview import create_window, start as webview_start
import sys
from pathlib import Path
from app_ext import message_box, MessageBoxIcon

app_dir = ''

class LoginWall:
    def __init__(self):
        self.login_path = Path(app_dir) / "web" / "login" / "index.html"
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
        return False     # Block user attempts (Alt+F4)
    
    def run(self):
        dev_mode = False
        self.window = create_window(
            "Access Wall",
            url=f"file://{self.login_path}",
            width=400,
            height=400,
            fullscreen= (not dev_mode),
            frameless= True,
            on_top=True,
            js_api=self.api,
            confirm_close=False  # Needed to intercept close events
        )
        # Attach the close handler
        self.window.events.closing += self.block_close
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
            self._parent.window.destroy()

        elif user_id == "iamadmin":
            self._user = "Admin"
            self.open_session()
        
        else:
            message_box("Student ID not found!", "Not Found", icon=MessageBoxIcon.WARNING)
    

    def open_session(self):
        print("Login successful!")
        self._parent._allow_close = True
        self.session_path = Path(app_dir) / "web" / "session" / "index.html"
        if not self.session_path.exists():
            raise FileNotFoundError("Session UI not found.")

        session = Session(self)
        self._allow_close = False       # Allow Python to close
        self._window = create_window(
            title="Session",
            url=f"file://{self.session_path}",
            background_color='#212529',
            width=300,
            height=200,
            js_api=session,
            resizable=False,
            # frameless=True
        )
        self._window.events.closing += self.block_close
        self._parent.window.destroy()         # Now it will close
    
    def block_close(self, window):
        """Prevent user from closing window unless allowed by code"""
        if self._allow_close:
            return True  # Allow Python to close
        print("User tried to close window! Blocked.")
        return False     # Block user attempts (Alt+F4)
    
    def show_message(self, *args, **kwargs):
        return message_box(*args, **kwargs)

class Session():
    def __init__(self, parent: Api) -> None:
        self._parent = parent
    def get_user(self):
        from json import dumps 
        return dumps({
            "name": self._parent._user
        })
    def logout(self):
        self._parent._allow_close = True
        self._parent._window.destroy()

    def show_message(self, *args, **kwargs):
        return message_box(*args, **kwargs)

def run(path: Path | str):
    try:
        global app_dir
        app_dir = Path(path)
        login = LoginWall()
        while not login.is_destructing():
            login.run()
            print("Loop")
    except Exception as e:
        print(e)

if __name__ == "__main__":
    run(Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent)