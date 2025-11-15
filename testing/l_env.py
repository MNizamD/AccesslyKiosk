import sys


GIT_OWNER = "MNizamD"
GIT_REPO = "AccesslyKiosk"
GIT_D_PATH = "testing/web_wall"

def get_cur_dir():
    from pathlib import Path
    return Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent

def get_app_dir():
    from pathlib import Path
    return Path("playground") / "web_wall"

def get_local_detail_dir():
    return get_app_dir() / "details.json"

def get_git_header():
    GITHUB_TOKEN = decrypt("0e081909110f361e08153250552c5f3f20543c30540a245a333b2831295b021d203e1555310610590f0c1c23311e592f5d57193706352b1a0b573803010e3c092d552e2f0d19213b26322e24212a3f2026365b34335b1a58282d3d5755", 'iamadmin')

    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

def encrypt(text: str, key: str) -> str:
    key_bytes = key.encode()
    text_bytes = text.encode()

    encrypted = bytes([b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(text_bytes)])
    return encrypted.hex()


def decrypt(hex_str: str, key: str) -> str:
    key_bytes = key.encode()
    encrypted = bytes.fromhex(hex_str)

    decrypted = bytes([b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(encrypted)])
    return decrypted.decode()

def encrypt_token():
    token = input("Token: ")
    key = input("Key: ")
    encrypted_token = encrypt(token, key)
    print(encrypted_token)

if __name__ == "__main__":
    encrypt_token()