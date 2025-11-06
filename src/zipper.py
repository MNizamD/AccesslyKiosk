from os import path as ospath, makedirs, remove, walk as oswalk
from variables import is_dir_safe


def extract_zip_dynamic(
    zip_path: str,
    extract_to: str,
    del_zip_later: bool = False,
    progress_callback: callable = None
):
    if (not is_dir_safe(zip_path)) or (not is_dir_safe(extract_to)):
        print("[ERROR]: Unsafe to extract zip at:", extract_to)
        return
    from zipfile import ZipFile
    from shutil import copyfileobj
    """
    Extracts a ZIP archive into a target folder.
    Optionally deletes the ZIP afterward and calls a progress callback.
    Returns a set of relative file and folder paths extracted.
    """
    makedirs(extract_to, exist_ok=True)
    extracted_paths = set()

    with ZipFile(zip_path, 'r') as zf:
        files = zf.infolist()
        total = len(files)

        for i, member in enumerate(files, 1):
            rel_path = member.filename.rstrip("/\\")
            if not rel_path:
                continue

            # ✅ Add file/folder + all parent directories
            parts = rel_path.split('/')
            for j in range(1, len(parts)):
                extracted_paths.add('/'.join(parts[:j]))
            extracted_paths.add(rel_path)

            safe_path = ospath.normpath(ospath.join(extract_to, member.filename))
            if not safe_path.startswith(ospath.abspath(extract_to)):
                raise Exception(f"Blocked unsafe extraction path: {member.filename}")

            if member.is_dir():
                makedirs(safe_path, exist_ok=True)
            else:
                makedirs(ospath.dirname(safe_path), exist_ok=True)
                with zf.open(member, 'r') as src, open(safe_path, 'wb') as dst:
                    copyfileobj(src, dst)

            percent = round(i / total * 100, 2)
            if progress_callback:
                progress_callback(percent)

    if del_zip_later:
        try:
            remove(zip_path)
            print(f"[-] Deleted zip: {zip_path}")
        except Exception as e:
            print(f"[!] Could not delete zip: {e}")

    print(f"[*] Extraction complete to: {extract_to}")
    return extracted_paths


def cleanup_extracted_files(
    extract_to: str,
    valid_paths: set,
    ignore_list: list[str] = None
):
    if not is_dir_safe(extract_to):
        print("[ERROR]: Unsafe to cleanup at:", extract_to)
        return
    from shutil import rmtree
    """
    Deletes any file/folder in extract_to that is NOT in valid_paths,
    except those in ignore_list.
    """
    if ignore_list is None:
        ignore_list = []

    ignore_set = {ospath.normpath(i).lower() for i in ignore_list}

    for root, dirs, files in oswalk(extract_to, topdown=False):
        for name in files + dirs:
            abs_path = ospath.join(root, name)
            rel_path = ospath.relpath(abs_path, extract_to)
            rel_path_norm = ospath.normpath(rel_path).lower().rstrip("/\\")

            # Skip ignored files/folders
            if any(rel_path_norm.startswith(ign) for ign in ignore_set):
                continue

            # If not part of ZIP contents, remove
            if rel_path not in valid_paths and rel_path.replace("\\", "/") not in valid_paths:
                try:
                    if ospath.isdir(abs_path):
                        rmtree(abs_path)
                        print(f"[-] Removed folder: {rel_path}")
                    else:
                        remove(abs_path)
                        print(f"[-] Removed file: {rel_path}")
                except Exception as e:
                    print(f"[!!] Could not remove {rel_path}: {e}")
