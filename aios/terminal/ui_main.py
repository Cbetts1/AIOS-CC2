"""AI-OS Terminal UI - Curses-based full terminal interface."""
import curses
import time
import threading
from datetime import datetime


class TerminalUI:
    def __init__(self, command_center=None):
        self._cc = command_center
        self._stdscr = None
        self._running = False
        self._console_lines = []
        self._selected_menu = 0
        self._input_buffer = ""
        self._status_msg = "Ready — type 'help' for a reference card"
        self._lock = threading.Lock()
        # Command history: list of previously submitted commands
        self._history: list = []
        self._history_pos: int = -1   # -1 = not browsing history
        self._menu_items = [
            ("1", "System Status"),
            ("2", "Layer Control"),
            ("3", "Engine Control"),
            ("4", "Virtual HW"),
            ("5", "Network"),
            ("6", "Security"),
            ("7", "Cloud"),
            ("8", "Cellular"),
            ("9", "Computer"),
            ("10", "AI Systems"),
            ("11", "Diagnostics"),
            ("12", "Maintenance"),
            ("13", "Legal"),
            ("14", "Docs"),
            ("15", "Logs"),
            ("16", "Shutdown"),
        ]

    def _init_colors(self) -> None:
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_CYAN, -1)       # cyan on default bg
        curses.init_pair(2, curses.COLOR_WHITE, -1)      # white
        curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_CYAN)  # selected menu
        curses.init_pair(4, curses.COLOR_GREEN, -1)      # status ok
        curses.init_pair(5, curses.COLOR_RED, -1)        # error
        curses.init_pair(6, curses.COLOR_YELLOW, -1)     # warning

    def draw_banner(self, scr, max_x: int) -> int:
        banner_lines = [
            " AI-OS COMMAND CENTER v2.0-CC2 ",
            " Operator: Chris  |  10.0.0.0/8  |  ONLINE ",
        ]
        scr.attron(curses.color_pair(1) | curses.A_BOLD)
        scr.addstr(0, 0, "=" * min(max_x - 1, 70))
        for i, line in enumerate(banner_lines):
            scr.addstr(i + 1, max(0, (max_x - len(line)) // 2), line[:max_x - 1])
        scr.addstr(len(banner_lines) + 1, 0, "=" * min(max_x - 1, 70))
        scr.attroff(curses.color_pair(1) | curses.A_BOLD)
        return len(banner_lines) + 2

    def draw_menu(self, scr, start_y: int, max_y: int) -> None:
        menu_width = 18
        scr.attron(curses.color_pair(1))
        scr.addstr(start_y, 0, "┌" + "─" * (menu_width - 2) + "┐")
        scr.addstr(start_y + 1, 0, "│  MAIN MENU      │")
        scr.addstr(start_y + 2, 0, "├" + "─" * (menu_width - 2) + "┤")
        scr.attroff(curses.color_pair(1))

        for i, (num, name) in enumerate(self._menu_items):
            row = start_y + 3 + i
            if row >= max_y - 2:
                break
            label = f"  {num:>2}. {name}"
            label = label[:menu_width - 2]
            if i == self._selected_menu:
                scr.attron(curses.color_pair(3) | curses.A_BOLD)
                scr.addstr(row, 0, label.ljust(menu_width - 1))
                scr.attroff(curses.color_pair(3) | curses.A_BOLD)
            else:
                scr.attron(curses.color_pair(2))
                scr.addstr(row, 0, label.ljust(menu_width - 1))
                scr.attroff(curses.color_pair(2))

        bottom_row = start_y + 3 + len(self._menu_items)
        if bottom_row < max_y - 2:
            scr.attron(curses.color_pair(1))
            scr.addstr(bottom_row, 0, "└" + "─" * (menu_width - 2) + "┘")
            scr.attroff(curses.color_pair(1))

    def draw_console(self, scr, start_y: int, start_x: int, max_y: int, max_x: int) -> None:
        console_h = max_y - start_y - 3
        console_w = max_x - start_x - 1
        scr.attron(curses.color_pair(1))
        scr.addstr(start_y, start_x, "┌─ CONSOLE " + "─" * max(0, console_w - 11) + "┐")
        scr.attroff(curses.color_pair(1))

        with self._lock:
            visible = self._console_lines[-(console_h):]

        for i, line in enumerate(visible):
            row = start_y + 1 + i
            if row >= max_y - 3:
                break
            display = line[:console_w - 1]
            scr.attron(curses.color_pair(2))
            try:
                scr.addstr(row, start_x + 1, display)
            except curses.error:
                pass
            scr.attroff(curses.color_pair(2))

        input_row = max_y - 3
        scr.attron(curses.color_pair(1))
        scr.addstr(input_row, start_x, "└" + "─" * max(0, console_w) + "┘")
        scr.attroff(curses.color_pair(1))

        prompt = f"  CMD> {self._input_buffer}"
        scr.attron(curses.color_pair(4) | curses.A_BOLD)
        try:
            scr.addstr(input_row + 1, start_x, prompt[:max_x - start_x - 1])
        except curses.error:
            pass
        scr.attroff(curses.color_pair(4) | curses.A_BOLD)

    def draw_status_bar(self, scr, max_y: int, max_x: int) -> None:
        now = datetime.now().strftime("%H:%M:%S")
        typing = bool(self._input_buffer)
        nav_hint = "UP/DOWN: history" if typing else "UP/DOWN: menu"
        bar = f" AI-OS | {now} | {self._status_msg} | {nav_hint} | ENTER: run | ?: help | q: quit "
        bar = bar[:max_x - 1]
        scr.attron(curses.color_pair(3) | curses.A_BOLD)
        try:
            scr.addstr(max_y - 1, 0, bar.ljust(max_x - 1))
        except curses.error:
            pass
        scr.attroff(curses.color_pair(3) | curses.A_BOLD)

    def render(self, scr) -> None:
        scr.erase()
        max_y, max_x = scr.getmaxyx()
        banner_end = self.draw_banner(scr, max_x)
        self.draw_menu(scr, banner_end, max_y)
        self.draw_console(scr, banner_end, 20, max_y, max_x)
        self.draw_status_bar(scr, max_y, max_x)
        scr.refresh()

    def handle_input(self, key: int) -> bool:
        if key == ord('q') or key == ord('Q'):
            # Only quit if no text is being typed
            if not self._input_buffer:
                return False
            self._input_buffer += chr(key)
        elif key == curses.KEY_UP:
            if self._input_buffer or self._history_pos >= 0:
                # Navigate command history upward
                if self._history:
                    if self._history_pos < 0:
                        # Start browsing from the most recent entry
                        self._history_pos = len(self._history) - 1
                    elif self._history_pos > 0:
                        self._history_pos -= 1
                    self._input_buffer = self._history[self._history_pos]
            else:
                # No text: navigate the menu up
                self._selected_menu = max(0, self._selected_menu - 1)
        elif key == curses.KEY_DOWN:
            if self._history_pos >= 0:
                # Navigate command history downward
                if self._history_pos < len(self._history) - 1:
                    self._history_pos += 1
                    self._input_buffer = self._history[self._history_pos]
                else:
                    # Past the end of history — clear input
                    self._history_pos = -1
                    self._input_buffer = ""
            elif not self._input_buffer:
                # No text: navigate the menu down
                self._selected_menu = min(len(self._menu_items) - 1, self._selected_menu + 1)
        elif key == curses.KEY_ENTER or key == 10 or key == 13:
            # If the user has typed something in the buffer, submit that
            if self._input_buffer and self._cc:
                cmd = self._input_buffer
                result = self._cc.handle_command(cmd)
                # Save to history (avoid duplicate consecutive entries)
                if not self._history or self._history[-1] != cmd:
                    self._history.append(cmd)
                    if len(self._history) > 100:
                        self._history = self._history[-100:]
                self._history_pos = -1
                with self._lock:
                    self._console_lines.append(f"> {cmd}")
                    for line in result.split("\n"):
                        self._console_lines.append(line)
                    if len(self._console_lines) > 300:
                        self._console_lines = self._console_lines[-150:]
                self._status_msg = f"CMD: {cmd}"
                self._input_buffer = ""
            else:
                # No typed input — execute the highlighted menu item
                num, name = self._menu_items[self._selected_menu]
                if self._cc:
                    result = self._cc.handle_command(num)
                    with self._lock:
                        for line in result.split("\n"):
                            self._console_lines.append(line)
                        if len(self._console_lines) > 300:
                            self._console_lines = self._console_lines[-150:]
                self._status_msg = f"Executed: {num}. {name}"
        elif key == curses.KEY_BACKSPACE or key == 127:
            self._input_buffer = self._input_buffer[:-1]
            self._history_pos = -1
        elif key == 27:  # Escape — clear input buffer / cancel history browsing
            self._input_buffer = ""
            self._history_pos = -1
        elif 32 <= key < 127:
            self._input_buffer += chr(key)
            self._history_pos = -1
        return True

    def _ticker(self) -> None:
        while self._running:
            if self._cc:
                hb = self._cc._heartbeat
                if hb:
                    beat = hb.last_beat()
                    count = beat.get("beat_count", 0)
                    with self._lock:
                        self._status_msg = f"HB#{count} | type 'help' for commands"
            time.sleep(5)

    def start(self) -> None:
        self._running = True
        ticker = threading.Thread(target=self._ticker, daemon=True)
        ticker.start()
        if self._cc:
            log = self._cc.get_console_log(limit=20)
            with self._lock:
                self._console_lines = [e["msg"] for e in log]
        try:
            curses.wrapper(self._curses_main)
        finally:
            self._running = False

    def _curses_main(self, stdscr) -> None:
        self._stdscr = stdscr
        self._init_colors()
        stdscr.nodelay(True)
        stdscr.keypad(True)
        curses.curs_set(0)
        last_render = 0
        while self._running:
            now = time.time()
            if now - last_render >= 0.1:
                self.render(stdscr)
                last_render = now
            try:
                key = stdscr.getch()
            except Exception:
                key = -1
            if key != -1:
                if not self.handle_input(key):
                    self._running = False
                    break
            time.sleep(0.02)
