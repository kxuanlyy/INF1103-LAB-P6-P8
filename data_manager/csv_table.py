import csv
import logging
import os
import tempfile
from datetime import datetime
from typing import Iterable, Optional, Union

log = logging.getLogger("data_manager")


# --------------------------------------------------------------------------- #
# Base class: one CSV file held in memory
# --------------------------------------------------------------------------- #
class CsvTable:
    # A CSV file loaded into memory as a list of dict records (self.records).
    #
    # This base class handles what every table needs: reading the file (and
    # repairing it if it is missing or corrupt), saving it atomically, and the
    # add / replace / delete bookkeeping. Every change is saved straight away and
    # is undone in memory if the save fails, so memory and disk never disagree.
    # Subclasses set COLUMNS and add their own fields and searches.

    COLUMNS: list = []

    def __init__(self, path: str):
        self.path = path
        self.records: list = []

    # ---- file helpers ----------------------------------------------------- #
    def _write(self, rows: list) -> None:
        # Write atomically so a crash mid-save can't corrupt the file.
        folder = os.path.dirname(self.path) or "."
        os.makedirs(folder, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=folder, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self.COLUMNS)
                writer.writeheader()
                writer.writerows(rows)
            os.replace(tmp, self.path)
        except Exception:
            if os.path.exists(tmp):
                os.remove(tmp)
            raise

    def _create_empty(self) -> None:
        # Create a header-only CSV. If that isn't possible, carry on in memory.
        try:
            self._write([])
        except OSError as exc:
            log.error("Could not create %s (%s). Continuing with in-memory data only.", self.path, exc)

    def _quarantine(self) -> Optional[str]:
        # Move a corrupt file aside (never delete it). Returns the new path, or None.
        backup = f"{self.path}.corrupt-{datetime.now().strftime('%d%m%Y-%H%M%S')}"
        n = 1
        while os.path.exists(backup):
            n += 1
            backup = f"{self.path}.corrupt-{datetime.now().strftime('%d%m%Y-%H%M%S')}-{n}"
        try:
            os.replace(self.path, backup)
            return backup
        except OSError as exc:
            log.error("Could not move corrupt file %s aside (%s).", self.path, exc)
            return None

    def _read(self) -> list:
        # Read the CSV into a list of dicts, repairing missing/corrupt files.
        #
        # Always returns a list (possibly empty); only raises for problems that
        # aren't about the file's contents, such as a permissions error on read.

        # Missing or zero-byte file -> create a header-only CSV.
        if not os.path.exists(self.path) or os.path.getsize(self.path) == 0:
            log.warning("%s is missing or empty; creating a new one.", self.path)
            self._create_empty()
            return []

        try:
            with open(self.path, newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f, strict=True)
                header = reader.fieldnames or []
                absent = [c for c in self.COLUMNS if c not in header]
                if absent:
                    raise ValueError(f"required column(s) missing: {', '.join(absent)}")
                rows = []
                for row in reader:
                    clean = {c: (row.get(c) or "").strip() for c in self.COLUMNS}
                    if any(clean.values()):  # skip blank rows
                        rows.append(clean)
                return rows
        except (UnicodeDecodeError, csv.Error, ValueError) as exc:
            # UnicodeDecodeError is a ValueError subclass; listed for clarity.
            backup = self._quarantine()
            log.error("%s is corrupt (%s). %s Starting with an empty file.",
                      self.path, exc, f"Original saved as {backup}." if backup else "Original left in place.")
            self._create_empty()
            return []

    # ---- load / save ------------------------------------------------------ #
    def _clean(self, rows: list) -> list:
        # Hook: subclasses tidy freshly read rows here (default: leave as is).
        return rows

    def _rows_for_saving(self) -> list:
        # Hook: subclasses adjust records just before writing (default: as is).
        return self.records

    def load(self) -> None:
        # (Re)load the file from disk. self.records is replaced in place, so any
        # outside reference to the list stays valid.
        self.records[:] = self._clean(self._read())

    def save(self) -> None:
        self._write(self._rows_for_saving())

    # ---- change bookkeeping (saved immediately, undone if saving fails) ---- #
    def _check_index(self, index: int) -> None:
        # Raise IndexError unless `index` is a valid position in the table.
        if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < len(self.records):
            raise IndexError(f"No record at index {index!r}; there are {len(self.records)} record(s).")

    def _append_and_save(self, record: dict) -> dict:
        # Add a record and save. If saving fails (e.g. file locked or disk
        # full) the record is removed again so memory and disk stay in sync.
        self.records.append(record)
        try:
            self.save()
        except Exception as exc:
            self.records.pop()
            log.error("Could not save record, nothing was added: %s", exc)
            raise
        return record

    def _replace_and_save(self, index: int, record: dict) -> dict:
        # Swap in an updated record and save; restore the old one if saving fails.
        old = self.records[index]
        self.records[index] = record
        try:
            self.save()
        except Exception as exc:
            self.records[index] = old
            log.error("Could not save changes, record left unchanged: %s", exc)
            raise
        return record

    def _delete_and_save(self, index: int) -> dict:
        # Remove a record and save; put it back if saving fails.
        old = self.records.pop(index)
        try:
            self.save()
        except Exception as exc:
            self.records.insert(index, old)
            log.error("Could not save, nothing was deleted: %s", exc)
            raise
        return old

    def delete(self, index: int) -> dict:
        # Remove the record at `index`, save, and return the removed record.
        self._check_index(index)
        return self._delete_and_save(index)

    # ---- matching helpers shared by the searches -------------------------- #
    @staticmethod
    def _contains(haystack: str, needle: Optional[str]) -> bool:
        # Case-insensitive substring match. needle=None means 'no filter'.
        return needle is None or needle.lower() in haystack.lower()

    @staticmethod
    def _equals(value: str, wanted: Optional[str]) -> bool:
        # Case-insensitive exact match. wanted=None means 'no filter'.
        return wanted is None or value.lower() == wanted.lower()

    @staticmethod
    def _as_list(value: Union[str, Iterable[str], None]) -> list:
        if value is None:
            return []
        return [value] if isinstance(value, str) else list(value)
