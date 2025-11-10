def fix():
    # Only adjust when this module is imported (not run directly)
    # Add /src/lib/ to sys.path so `from env import ...` still works
    from sys import path as syspath
    from os import path as ospath, listdir
    current_dir = ospath.dirname(__file__)
    if current_dir not in syspath:
        syspath.append(current_dir)
        
    # Add immediate subdirectories
    for sub in listdir(current_dir):
        sub_path = ospath.join(current_dir, sub)
        if ospath.isdir(sub_path) and sub_path not in syspath:
            syspath.append(sub_path)

fix()