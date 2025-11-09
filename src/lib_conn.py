from typing import Any, Callable, Literal, Optional

def internet_ok(timeout: float = 2.0, test_http: Optional[str] = None) -> bool:
    """
    Checks if internet is usable.
    
    - timeout: seconds to wait for TCP connection
    - test_http: optional URL to test HTTP connectivity (like SQL API endpoint)
    """
    # 1️⃣ Check raw TCP to DNS (8.8.8.8:53)
    dns = "8.8.8.8"
    try:
        from socket import create_connection
        create_connection((dns, 53), timeout=timeout)
    except OSError:
        print(f"Unable to establish connection to {dns}")
        return False
    
    # 2️⃣ Optional: HTTP test (API, SQL endpoint, etc.)
    if test_http:
        from requests import head, RequestException
        try:
            r = head(test_http, timeout=timeout)
            return r.status_code < 500
        except RequestException:
            print("HTTP connection failed.")
            return False
    # If we reach here, TCP works, assume usable
    return True

def download(
        src: str,
        dst: str,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> bool:
    try:
        from requests import get
        with get(src, stream=True) as r:
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            downloaded = 0

            with open(dst, "wb") as f:
                for chunk in r.iter_content(8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        # Call progress callback if provided
                        if progress_callback:
                            progress_callback(downloaded * 100 / total)

        return True

    except Exception as e:
        print("[DOWNLOAD_ERR]:", e)
        return False
    
def fetch_database(
        select_: list[str],
        from_:Literal["lock_kiosk_status"],
        where_: Optional[str] = None
        ) -> list[dict[str, Any]] | None:
    if not internet_ok():
        return None
    
    # Connect with your Supabase Postgres URI
    from psycopg2 import connect, OperationalError
    try:
        conn = connect(
            "postgresql://postgres.wfnhabdtwcjebmyeglnt:qOe8OeQoGqOhQJia@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres",
            sslmode="require"
        )
        cur = conn.cursor()

        # Fetch all rows (assuming table has columns: key, value)
        # cur.execute(f"SELECT key, value FROM lock_kiosk_status WHERE deleted_at is NULL;")
        cur.execute(f"SELECT {', '.join(select_)} FROM {from_} {f'WHERE {where_}' if where_ != None else ''};")
        rows = cur.fetchall()

        col_names = [desc[0] for desc in (cur.description or [])]

        # ✅ Convert each row into a dict
        result = [dict(zip(col_names, row)) for row in rows]

        cur.close()
        conn.close()
        return result
    except OperationalError as e:
        from lib_tool import print_major_error
        print_major_error(title="[FETCH_DB_ERR]", msg=str(e))

if __name__ == "__main__":
    print(fetch_database(
        select_=["key", "value"],
        from_="lock_kiosk_status",
        where_="deleted_at is NULL"
    ))
