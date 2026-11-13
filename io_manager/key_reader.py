import os
import sys

try:
    import msvcrt                      # Windows
except ImportError:
    msvcrt = None
    import select
    import termios
    import tty


class KeyReader:
    # Reads single key presses from the terminal, without waiting for Enter.

    ESCAPE_WAIT = 0.05   # seconds to wait to tell a lone Esc from an arrow-key sequence

    @staticmethod
    def is_interactive() -> bool:
        # False when input or output is piped or redirected (no live keys possible).
        return sys.stdin.isatty() and sys.stdout.isatty()

    def __enter__(self):
        if msvcrt:
            os.system("")              # switches on ANSI escape codes in Windows terminals
        else:
            self._fd = sys.stdin.fileno()
            self._saved = termios.tcgetattr(self._fd)
            tty.setcbreak(self._fd)    # key-by-key input, Ctrl+C still works
        return self

    def __exit__(self, *exc_info):
        if not msvcrt:
            termios.tcsetattr(self._fd, termios.TCSADRAIN, self._saved)
        return False

    def pending(self, timeout: float = 0) -> bool:
        if msvcrt:
            return msvcrt.kbhit()
        return bool(select.select([self._fd], [], [], timeout)[0])

    #reading
    def read_key(self) -> str:
        return self._read_key_windows() if msvcrt else self._read_key_posix()

    def _read_key_windows(self) -> str:
        ch = msvcrt.getwch()
        if ch in ("\x00", "\xe0"):     # arrow / function keys come as two characters
            msvcrt.getwch()
            return "OTHER"
        if ch == "\x03":
            raise KeyboardInterrupt
        return self._name_for(ch)

    def _read_key_posix(self) -> str:
        first = os.read(self._fd, 1)
        if not first:
            raise EOFError("Input closed.")
        if first == b"\x1b":
            return self._read_escape()
        # A character outside ASCII arrives as several bytes; collect them all
        lead = first[0]
        extra = 3 if lead >= 0xF0 else 2 if lead >= 0xE0 else 1 if lead >= 0xC0 else 0
        data = first
        for _ in range(extra):
            data += os.read(self._fd, 1)
        return self._name_for(data.decode("utf-8", errors="replace"))

    def _read_escape(self) -> str:
        # A lone Esc press has nothing after it; arrow keys etc. send "ESC [ A" and so on
        if not self.pending(self.ESCAPE_WAIT):
            return "ESC"
        os.read(self._fd, 1)           # the "[" or "O"
        while self.pending(self.ESCAPE_WAIT):
            final = os.read(self._fd, 1)[0]
            if 0x40 <= final <= 0x7E:  # last byte of the sequence
                break
        return "OTHER"

    @staticmethod
    def _name_for(ch: str) -> str:
        if ch in ("\r", "\n"):
            return "ENTER"
        if ch in ("\x7f", "\x08"):
            return "BACKSPACE"
        if ch == "\x1b":
            return "ESC"
        if ch == "\x15":
            return "CTRL_U"
        if len(ch) == 1 and ch < " ":
            return "OTHER"
        return ch
