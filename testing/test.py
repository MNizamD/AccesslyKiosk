from typing import Any, Literal


app: dict[Literal["name", "age"], Any] = {"name": "test"}

print(bool(app["age"]))
