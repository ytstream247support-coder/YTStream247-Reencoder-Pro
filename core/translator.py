import json
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal
from helpers import resource_path

class Translator(QObject):
    languageChanged = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._strings = {}
        self.current_lang = "en"
        # Load default immediately
        self.load_language("en")

    def load_language(self, lang_code: str):
        """Loads the json file for the given language code."""
        # Use resource_path for PyInstaller compatibility
        lang_path = resource_path(f"assets/lang/{lang_code}.json")
        
        if not lang_path.exists():
            # Fallback to English if requested language not found
            if lang_code != "en":
                self.load_language("en")
            return

        try:
            with open(lang_path, "r", encoding="utf-8") as f:
                self._strings = json.load(f)
            self.current_lang = lang_code
            self.languageChanged.emit()
        except Exception as e:
            # Fallback to English on error
            if lang_code != "en":
                self.load_language("en")

    def t(self, key: str) -> str:
        """Returns the translated string or the key if missing."""
        return self._strings.get(key, key)

# Global Instance
tr = Translator()