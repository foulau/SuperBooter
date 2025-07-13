#!/usr/bin/env python3
# Compiler configuration
build = "1.0.0"
packs_list = 'https://raw.githubusercontent.com/foulau/SuperBooter/refs/heads/main/packs.yml'

# Libraries
import requests
import os, yaml
import platform
from pyfiglet import Figlet
import curses

class packs_manager:
    @staticmethod
    def load_raw():
        response = requests.get(packs_list)
        response.raise_for_status()
        return yaml.safe_load(response.text)

    @staticmethod
    def build_menu(data):
        """
        Recursively build menu structures from nested YAML dicts.
        Returns a list of items, each either:
          - {'name': str, 'id': int}
          - {'name': str, 'submenu': [ ... ]}
        """
        items = []
        # First entry may define display name
        title = None
        if isinstance(data, list) and data and isinstance(data[0], dict) and 'name' in data[0]:
            title = data[0]['name']
        # Iterate through dict keys
        for key, val in (data.items() if isinstance(data, dict) else []):
            if key == 'name': continue
            # val can be list or dict
            if isinstance(val, list):
                # Leaf items or nested submenus
                # Check if list contains leaf dicts with 'id'
                if all(isinstance(el, dict) and 'id' in el for el in val):
                    for pkg in val:
                        items.append({'name': pkg['name'], 'id': pkg['id']})
                else:
                    # Build nested submenu
                    submenu = packs_manager.build_menu(val)
                    display = val[0]['name'] if isinstance(val, list) and val and 'name' in val[0] else key.title()
                    items.append({'name': display, 'submenu': submenu})
        return items


def run_menu(menu_items, title, selected_ids=None, allow_toggle=False, custom_code=False):
    if selected_ids is None: selected_ids = set()
    result = {'back': True, 'selected_ids': selected_ids}

    def draw(stdscr):
        nonlocal result
        curses.curs_set(0)
        curses.use_default_colors()
        cursor = 0
        figlet = Figlet(font='future').renderText("SuperBooter").splitlines()
        while True:
            stdscr.clear()
            # Header
            for i, line in enumerate(figlet): stdscr.addstr(i, 0, line)
            offset = len(figlet) + 1
            stdscr.addstr(offset, 0, title, curses.A_BOLD)
            if selected_ids:
                stdscr.addstr(offset+1, 0, f"Selected: {len(selected_ids)}")
                offset += 1
            # Display entries
            for idx, it in enumerate(menu_items):
                if 'id' in it:
                    label = ('[X] ' if allow_toggle and it['id'] in selected_ids else '[ ] ' if allow_toggle else '') + it['name']
                else:
                    label = it['name']
                y = offset+2+idx
                try:
                    if idx == cursor:
                        stdscr.attron(curses.A_REVERSE)
                        stdscr.addstr(y, 2, label)
                        stdscr.attroff(curses.A_REVERSE)
                    else:
                        stdscr.addstr(y, 2, label)
                except curses.error:
                    pass
            # Extras: Install, Custom Code
            extra = len(menu_items)
            if custom_code:
                try:
                    stdscr.addstr(offset+2+extra, 2, '')
                    if cursor == extra:
                        stdscr.attron(curses.A_REVERSE); stdscr.addstr(offset+3+extra, 2, 'Install'); stdscr.attroff(curses.A_REVERSE)
                    else:
                        stdscr.addstr(offset+3+extra, 2, 'Install')
                    if cursor == extra+1:
                        stdscr.attron(curses.A_REVERSE); stdscr.addstr(offset+4+extra, 2, 'Custom Code'); stdscr.attroff(curses.A_REVERSE)
                    else:
                        stdscr.addstr(offset+4+extra, 2, 'Custom Code')
                except curses.error:
                    pass
            stdscr.refresh()
            k = stdscr.getch()
            max_cursor = len(menu_items) + (2 if custom_code else 0)
            if k in (curses.KEY_UP, curses.KEY_DOWN):
                cursor = (cursor + (1 if k==curses.KEY_DOWN else -1)) % max_cursor
            elif k == 10:
                # Handle select
                if cursor < len(menu_items):
                    sel = menu_items[cursor]
                    if 'submenu' in sel:
                        result = {'submenu': sel['submenu'], 'selected_ids': set(selected_ids)}
                        return
                    elif allow_toggle and 'id' in sel:
                        if sel['id'] in selected_ids: selected_ids.remove(sel['id'])
                        else: selected_ids.add(sel['id'])
                    elif 'id' in sel:
                        result = {'selected': sel, 'selected_ids': set(selected_ids)}; return
                else:
                    idx = cursor - len(menu_items)
                    if idx == 0:
                        result = {'install': True, 'selected_ids': set(selected_ids)}; return
                    elif idx == 1 and custom_code:
                        stdscr.clear(); stdscr.addstr(0,0,'Enter custom code:'); curses.echo(); code = stdscr.getstr(1,0,60).decode(); curses.noecho()
                        result = {'custom_code': code, 'selected_ids': set(selected_ids)}; return
            elif k in (127,8):
                result = {'back': True, 'selected_ids': set(selected_ids)}; return

    curses.wrapper(draw)
    return result


def main():
    raw = packs_manager.load_raw()
    # Build top-level menus
    categories = []
    for key, val in raw.items():
        name = val[0]['name'] if isinstance(val, list) and val and 'name' in val[0] else key.title()
        submenu = packs_manager.build_menu(val)
        categories.append({'name': name, 'submenu': submenu, 'key': key})

    selected_ids = set()
    stack = [{'items': categories, 'title': f"SuperBooter v{build} - Main Menu", 'allow_toggle': False, 'custom_code': True}]
    while stack:
        frame = stack.pop()
        res = run_menu(frame['items'], frame['title'], selected_ids, frame['allow_toggle'], frame['custom_code'])
        if 'submenu' in res:
            # push new frame
            stack.append({'items': res['submenu'], 'title': frame['items'][frame['last_cursor']]['name'], 'allow_toggle': frame['allow_toggle'], 'custom_code': False})
        elif 'install' in res:
            print(f"Installing IDs: {sorted(res['selected_ids'])}")
            selected_ids.clear()
        elif 'custom_code' in res:
            print(f"Custom code: {res['custom_code']}")
        elif 'id' in res.get('selected', {}):
            # leaf selection
            selected_ids.add(res['selected']['id'])
        elif res.get('back'):
            # go up
            continue

if __name__ == "__main__" and platform.system()=="Linux":
    main()
