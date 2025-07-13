# Compiler configuration
build = "1.0.0"


# Libraries

import os, yaml
import platform
from pyfiglet import Figlet


# Variables
toinstall = []
hostname = platform.node()
username = os.getlogin()

class packs_manager:
    def find_pack_by_id(data, search_id):
        results = []
        def search(obj, path=None):
            if path is None: path = []
            if isinstance(obj, dict):
                for k, v in obj.items(): search(v, path + [k])
            elif isinstance(obj, list):
                entry = {}
                for item in obj:
                    if isinstance(item, dict): entry.update(item)
                if entry.get('id') == search_id: results.append({'path': path, 'info': entry})
                for item in obj: search(item, path)
        search(data); return results

    def pack_main(search_id):
        with open('packs.yml', 'r') as f: packs = yaml.safe_load(f)
        found = packs_manager.find_pack_by_id(packs, search_id)
        if not found: print('pack.result.none', search_id)
        else:
            for result in found:
                print(f"path: {'/'.join(result['path'])}")
                for k, v in result['info'].items(): print(f"{k}: {v}")

def main_runtime():
    print(Figlet(font='future').renderText(f"SuperBooter v{build}")); print("What do you want to install now, Master?")
    print("1. Display Managers\n2. Browsers\n3. Editors\n4. Games\n5. Visual Additons\n6. System Update\n7. Drivers")
    user_input = input(f"({hostname}@{username})> ")
    

if platform.system() == "Linux": main_runtime()