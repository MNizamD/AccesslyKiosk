from os import path as ospath, environ
from pathlib import Path

def get_cur_user() -> str:
    return environ.get("USERNAME", "Unknown")

def get_pc_name() -> str:
    from socket import gethostname
    return gethostname()
# ---------- FILE/DIR HELPERS ----------

def normalize_path(p: Path | str) -> str:
    return ospath.normpath(ospath.expandvars(ospath.expanduser(str(p)))).lower()

def move_up_dir(directory: str | Path, level: int = 1) -> Path:
    """
    Move up `level` directories from `directory`.
    """
    if not directory:
        return Path()
    
    path = Path(directory)
    for _ in range(level):
        path = path.parent
    return path.resolve()

def is_frozen(sys) -> bool:
    return getattr(sys, "frozen", False)


def get_run_dir() -> str:
    """Folder containing the running file or executable."""
    import sys
    if is_frozen(sys):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent

def is_user_exists(username: str) -> bool:
    """Check if a local Windows user exists."""
    from subprocess import run
    try:
        result = run(
            ["net", "user", username],
            capture_output=True,
            text=True,
            shell=True
        )
        # Return code 0 = user exists
        return result.returncode == 0
    except Exception as e:
        print(f"Error checking user: {e}")
        return False


def app_name(name: str) -> str:
    """
    Returns executable or .py filename depending on mode.
    Include prefix.
    """
    app_pref = 'nl'
    import sys
    normalize_name = f"{name}.exe" if is_frozen(sys) else f"{name}.py"
    return f"{app_pref}_{normalize_name}"

# ---------- BASIC INFO ----------

PROJECT_NAME = "NizamLab"
ONLY_USER = 'GVC'
SCHTASK_NAME = 'AccesslyKiosk'

# file names based on app_name
ACCESSLY_FILE_NAME = app_name("Accessly")
UPDATER_FILE_NAME = app_name("Updater")
UPDATER_COPY_FILE_NAME = app_name("Updater_Copy")
MAIN_FILE_NAME = app_name("Main")
CMD_FILE_NAME = app_name("cmd")

class EnvHelper:
    
    _instance = None  # singleton-style cache

    def __new__(cls, user: str | None = None):
        # ✅ Lazy singleton — only one instance per project
        if cls._instance is None or cls._instance.PROJECT_NAME != PROJECT_NAME:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, user: str | None = None):
        if self._initialized:
            return  # skip re-init if already created
        
        # Determine user first (either provided or current)
        user = user or get_cur_user()
        if not is_user_exists(user):
            raise ValueError(f"User '{user}' does not exist on this computer.")
        
        self.user = user
        self._initialized = True

    # ---------- Lazy Properties ----------
    @property
    def user_profile(self) -> Path:
        return Path(f"C:/Users/{self.user}")

    @property
    def localappdata(self) -> Path:
        return self.user_profile / "AppData" / "Local"

    @property
    def temp(self) -> Path:
        return self.localappdata / "Temp"

    @property
    def localdata_dir(self) -> Path:
        return self.localappdata / PROJECT_NAME
    
    @property
    def programdata(self) -> Path:
        return Path(environ.get("PROGRAMDATA", r"C:\ProgramData"))

    @property
    def windir(self) -> Path:
        return Path(environ.get("WINDIR", r"C:\Windows"))
    
    # ---------- DIRECTORY STRUCTURE ----------

    @property
    def base_dir(self) -> Path:
        """The parent of the run directory (usually project root)."""
        return self.programdata / PROJECT_NAME

    @property
    def app_dir(self) -> Path:
        """Where the app source or executables reside (typically 'src')."""
        return self.base_dir / "src"

    # ---------- SAFETY CHECK ----------
    def is_dir_safe(self, path: Path | str) -> bool:
        normalized = normalize_path(str(path))

        unsafe_dirs = [
            str(self.windir).lower(),
            "%localappdata%",
            "%programdata%",
            f"C:\\Users\\{self.user}",
            r"c:\windows",
            r"c:\program files",
            r"c:\program files (x86)",
            r"c:\users\default",
            r"c:\users\public\desktop",
            r"c:\$recycle.bin",
            r"c:\system volume information",
        ]

        exemptions = [
            rf"%programdata%\{PROJECT_NAME}",
            str(self.temp / PROJECT_NAME),
            str(self.localappdata / PROJECT_NAME),
        ]

        norm_unsafe = [normalize_path(u) for u in unsafe_dirs]
        norm_exempt = [normalize_path(e) for e in exemptions]

        for ex in norm_exempt:
            if normalized.startswith(ex):
                return True
        for unsafe in norm_unsafe:
            if normalized.startswith(unsafe):
                print(f"[BLOCKED]: {normalized}")
                return False

        drive, _ = ospath.splitdrive(normalized)
        if normalized.strip("\\/") == drive.strip("\\/").lower():
            print(f"[BLOCKED]: {normalized}")
            return False
        return True
    
    def path(self, path: Path | str, strict = False) -> Path:
        path = normalize_path(path)  # normalize
        if not self.is_dir_safe(path):
            raise ValueError(f"Unsafe directory or invalid path: {path}")
        
        if strict and not path.exists():
            raise FileNotFoundError(f"Path does not exist: {path}")

        return path

    # ---------- PATH ACCESSORS ----------

    @property
    def data_dir(self) -> Path | None:
        data_dir = self.localdata_dir / "data"
        if not self.is_dir_safe(data_dir):
            return None
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir

    @property
    def cache_dir(self) -> Path | None:
        cache_dir = self.localdata_dir / "cache"
        if not self.is_dir_safe(cache_dir):
            return None
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir

    @property
    def temp_dir(self) -> Path | None:
        temp_dir = self.temp / PROJECT_NAME
        if not self.is_dir_safe(temp_dir):
            return None
        temp_dir.mkdir(parents=True, exist_ok=True)
        return temp_dir

    
    # ---------- Switch user dynamically ----------
    def get_user(self):
        return self.user

    def set_user(self, new_user: str):
        """Switch the active user and reset cached folders."""
        if not is_user_exists(new_user):
            raise ValueError(f"User '{new_user}' does not exist on this computer.")
        self.user = new_user
        print(f"[Env] Active user changed to: {self.user}")

    # ---------- FILE PATHS ----------
    @property
    def student_csv(self) -> Path:
        return self.data_dir / "Students.csv"

    @property
    def log_file(self) -> Path:
        return self.data_dir / "StudentLogs.csv"

    @property
    def flag_destruct_file(self) -> Path:
        return self.temp_dir / "STOP_LAUNCHER.flag"

    @property
    def flag_idle_file(self) -> Path:
        return self.temp_dir / "IDLE.flag"

    @property
    def cache_file(self) -> Path:
        return self.cache_dir / "lock_kiosk_status.json"

    @property
    def details_file(self) -> Path:
        return self.app_dir / "details.json"

    @property
    def script_accessly(self) -> Path:
        return self.app_dir / ACCESSLY_FILE_NAME
        
    @property
    def script_main(self) -> Path:
        return self.app_dir / MAIN_FILE_NAME
    
    @property
    def script_updater(self) -> Path:
        return self.app_dir / UPDATER_FILE_NAME
    
    @property
    def script_updater_copy(self) -> Path:
        return self.app_dir / UPDATER_COPY_FILE_NAME
    
    @property
    def script_cmd(self) -> Path:
        return self.app_dir / CMD_FILE_NAME
    
    def all_app_processes(self, exclude: list[str] = [], dir: bool = False) -> list[str]:
        # Preselect list once (avoid recomputing conditionally twice)
        if dir:
            apps = (
                self.script_accessly,
                self.script_main,
                self.script_updater,
                self.script_updater_copy,
            )
        else:
            apps = (
                ACCESSLY_FILE_NAME,
                UPDATER_FILE_NAME,
                UPDATER_COPY_FILE_NAME,
                MAIN_FILE_NAME,
            )

        # Fast return if no excludes
        if not exclude:
            return list(apps)

        # Normalize once
        excludes = tuple(e.lower() for e in exclude)

        result = []
        for app in apps:
            app_lower = app.lower()
            if not any(ex in app_lower for ex in excludes):
                result.append(app)

        return result



# ✅ Lazy global accessor (optional)
_env_cache: EnvHelper | None = None


def get_env(user: str | None = None) -> EnvHelper:
    """Return a lazily initialized global EnvHelper."""
    global _env_cache
    if _env_cache is None:
        _env_cache = EnvHelper(user)
    elif user and user != _env_cache.user:
        _env_cache.set_user(user)
    return _env_cache

def parse_env(env) -> EnvHelper:
    if env is None:
        raise ValueError("No environment supplied")
    if not isinstance(env, EnvHelper):
        raise TypeError(f"Expected EnvHelper instance, got {type(env).__name__}")
    return env

# ---------- DEMO ----------
if __name__ == "__main__":
    env = get_env(user=ONLY_USER)

    print("User:", env.user)
    print("PC Name:", get_pc_name())
    print("User Profile:", env.user_profile)
    print("LocalAppData:", env.localappdata)
    print("LocalAppDir:", env.localdata_dir)
    print("Programdata:", env.programdata)
    print("Temp:", env.temp)
    print("Temp Dir:", env.temp_dir)
    print("Data Dir:", env.data_dir)
    print("Cache Dir:", env.cache_dir)
    print("Run dir:", get_run_dir())
    print("Base dir:", env.base_dir)
    print("App dir:", env.app_dir)
    print("Flag IDLE:", env.flag_idle_file)
    print("Flag DESTRUCT:", env.flag_destruct_file)
    print("Cache:", env.cache_file)
    print("Details:", env.details_file)
    print("All Processes:", env.all_app_processes(dir=True))