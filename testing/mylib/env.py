if __name__ == "__main__":
    import __fix2__
from typing import Optional
from pathlib import Path
from mylib.util import (
    is_user_exists,
    get_cur_user,
    get_cur_dir,
    launcher_name,
    services_name,
    PROJECT_NAME,
)


class EnvHelper:

    _instance = None  # singleton-style cache

    def __new__(cls, dir: Path, user: Optional[str] = None):
        # ✅ Lazy singleton — only one instance per project
        if (
            cls._instance is None
            or cls._instance.__user != user
            or cls._instance.__dir != dir
        ):
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, dir: Path, user: Optional[str] = None):
        if self._initialized:
            return  # skip re-init if already created

        user = user or get_cur_user()
        if not is_user_exists(user):
            raise ValueError(f"User '{user}' does not exist on this computer.")

        self.__user = user
        self.__dir = dir
        self._initialized = True

    def app_dir(self) -> Path:
        return self.__dir

    def web_dir(self) -> Path:
        return self.app_dir() / "web_wall"

    def local_detail_path(self) -> Path:
        return self.web_dir() / "details.json"

    def launcher_path(self) -> Path:
        return self.app_dir() / launcher_name()

    def services_path(self, temp: bool = False) -> Path:
        if temp:
            return self.temp_dir() / PROJECT_NAME / services_name()
        return self.app_dir() / services_name()

    def user(self):
        return self.__user

    def user_dir(self) -> Path:
        return Path(f"C:/Users/{self.__user}")

    def programdata(self) -> Path:
        from os import environ

        return Path(environ.get("PROGRAMDATA", r"C:\ProgramData"))

    def localappdata(self) -> Path:
        return self.user_dir() / "AppData" / "Local"

    def temp_dir(self):
        return self.localappdata() / "Temp"

    def set_user(self, new_user: str):
        """Switch the active user and reset cached folders."""

        if not is_user_exists(new_user):
            raise ValueError(f"User '{new_user}' does not exist on this computer.")
        self.__user = new_user
        print(f"[Env] Active user changed to: {self.__user}")


# ✅ Lazy global accessor (optional)
_env_cache: Optional[EnvHelper] = None


def get_env(dir: Path, user: Optional[str] = None) -> EnvHelper:
    """Return a lazily initialized global EnvHelper."""
    global _env_cache
    if _env_cache is None:
        _env_cache = EnvHelper(dir=dir, user=user)
    elif user and user != _env_cache.user():
        _env_cache.set_user(user)
    return _env_cache


if __name__ == "__main__":

    env = get_env(get_cur_dir())
    print(env.user)
    print(env.launcher_path())
    print(env.local_detail_path())
    print(env.services_path())
    print(env.app_dir())
    print(env.web_dir())
    print(env.temp_dir())
