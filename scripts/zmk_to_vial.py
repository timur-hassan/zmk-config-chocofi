#!/usr/bin/env python3
"""
ZMK to Vial Converter
Converts ZMK keymap files to Vial .vil format.

Usage:
    python zmk_to_vial.py [--local PATH] [--output OUTPUT.vil]

By default, fetches from: https://github.com/timur-hassan/zmk-config-chocofi
"""

import json
import re
import sys
import argparse
from urllib.request import urlopen
from urllib.error import URLError
from dataclasses import dataclass, field
from typing import Optional

# =============================================================================
# ZMK to QMK Keycode Mapping
# =============================================================================

ZMK_TO_QMK = {
    # Letters
    "A": "KC_A", "B": "KC_B", "C": "KC_C", "D": "KC_D", "E": "KC_E",
    "F": "KC_F", "G": "KC_G", "H": "KC_H", "I": "KC_I", "J": "KC_J",
    "K": "KC_K", "L": "KC_L", "M": "KC_M", "N": "KC_N", "O": "KC_O",
    "P": "KC_P", "Q": "KC_Q", "R": "KC_R", "S": "KC_S", "T": "KC_T",
    "U": "KC_U", "V": "KC_V", "W": "KC_W", "X": "KC_X", "Y": "KC_Y",
    "Z": "KC_Z",

    # Numbers
    "N0": "KC_0", "N1": "KC_1", "N2": "KC_2", "N3": "KC_3", "N4": "KC_4",
    "N5": "KC_5", "N6": "KC_6", "N7": "KC_7", "N8": "KC_8", "N9": "KC_9",
    "NUMBER_0": "KC_0", "NUMBER_1": "KC_1", "NUMBER_2": "KC_2",
    "NUMBER_3": "KC_3", "NUMBER_4": "KC_4", "NUMBER_5": "KC_5",
    "NUMBER_6": "KC_6", "NUMBER_7": "KC_7", "NUMBER_8": "KC_8",
    "NUMBER_9": "KC_9",

    # Function keys
    "F1": "KC_F1", "F2": "KC_F2", "F3": "KC_F3", "F4": "KC_F4",
    "F5": "KC_F5", "F6": "KC_F6", "F7": "KC_F7", "F8": "KC_F8",
    "F9": "KC_F9", "F10": "KC_F10", "F11": "KC_F11", "F12": "KC_F12",

    # Modifiers
    "LEFT_CONTROL": "KC_LCTRL", "LCTRL": "KC_LCTRL", "LEFT_CTRL": "KC_LCTRL",
    "RIGHT_CONTROL": "KC_RCTRL", "RCTRL": "KC_RCTRL", "RIGHT_CTRL": "KC_RCTRL",
    "LEFT_SHIFT": "KC_LSHIFT", "LSHIFT": "KC_LSHIFT", "LSHFT": "KC_LSHIFT",
    "RIGHT_SHIFT": "KC_RSHIFT", "RSHIFT": "KC_RSHIFT", "RSHFT": "KC_RSHIFT",
    "LEFT_ALT": "KC_LALT", "LALT": "KC_LALT",
    "RIGHT_ALT": "KC_RALT", "RALT": "KC_RALT",
    "LEFT_GUI": "KC_LGUI", "LGUI": "KC_LGUI", "LEFT_WIN": "KC_LGUI", "LWIN": "KC_LGUI",
    "RIGHT_GUI": "KC_RGUI", "RGUI": "KC_RGUI", "RIGHT_WIN": "KC_RGUI", "RWIN": "KC_RGUI",

    # Navigation
    "UP": "KC_UP", "DOWN": "KC_DOWN", "LEFT": "KC_LEFT", "RIGHT": "KC_RIGHT",
    "HOME": "KC_HOME", "END": "KC_END",
    "PAGE_UP": "KC_PGUP", "PG_UP": "KC_PGUP", "PGUP": "KC_PGUP",
    "PAGE_DOWN": "KC_PGDN", "PG_DN": "KC_PGDN", "PGDN": "KC_PGDN",

    # Editing
    "BACKSPACE": "KC_BSPACE", "BSPC": "KC_BSPACE", "BKSP": "KC_BSPACE",
    "DELETE": "KC_DELETE", "DEL": "KC_DELETE",
    "INSERT": "KC_INSERT", "INS": "KC_INSERT",
    "ENTER": "KC_ENTER", "RETURN": "KC_ENTER", "RET": "KC_ENTER",
    "TAB": "KC_TAB",
    "ESCAPE": "KC_ESCAPE", "ESC": "KC_ESCAPE",
    "SPACE": "KC_SPACE", "SPC": "KC_SPACE",
    "CAPSLOCK": "KC_CAPSLOCK", "CAPS": "KC_CAPSLOCK",
    "PRINTSCREEN": "KC_PSCREEN", "PSCRN": "KC_PSCREEN", "PSCR": "KC_PSCREEN",

    # Punctuation and symbols
    "MINUS": "KC_MINUS", "PLUS": "KC_KP_PLUS",
    "EQUAL": "KC_EQUAL", "EQUALS": "KC_EQUAL",
    "UNDERSCORE": "LSFT(KC_MINUS)", "UNDER": "LSFT(KC_MINUS)",
    "LEFT_BRACKET": "KC_LBRACKET", "LBKT": "KC_LBRACKET", "LBRC": "KC_LBRACKET",
    "RIGHT_BRACKET": "KC_RBRACKET", "RBKT": "KC_RBRACKET", "RBRC": "KC_RBRACKET",
    "LEFT_BRACE": "LSFT(KC_LBRACKET)", "LBRC": "LSFT(KC_LBRACKET)",
    "RIGHT_BRACE": "LSFT(KC_RBRACKET)", "RBRC": "LSFT(KC_RBRACKET)",
    "LEFT_PARENTHESIS": "LSFT(KC_9)", "LPAR": "LSFT(KC_9)",
    "RIGHT_PARENTHESIS": "LSFT(KC_0)", "RPAR": "LSFT(KC_0)",
    "BACKSLASH": "KC_BSLASH", "BSLH": "KC_BSLASH",
    "SLASH": "KC_SLASH", "FSLH": "KC_SLASH",
    "SEMICOLON": "KC_SCOLON", "SEMI": "KC_SCOLON",
    "COLON": "LSFT(KC_SCOLON)",
    "APOSTROPHE": "KC_QUOTE", "APOS": "KC_QUOTE", "SQT": "KC_QUOTE",
    "SINGLE_QUOTE": "KC_QUOTE",
    "DOUBLE_QUOTES": "LSFT(KC_QUOTE)", "DQT": "LSFT(KC_QUOTE)",
    "COMMA": "KC_COMMA",
    "PERIOD": "KC_DOT", "DOT": "KC_DOT",
    "GRAVE": "KC_GRAVE", "GRV": "KC_GRAVE",
    "TILDE": "LSFT(KC_GRAVE)", "TILD": "LSFT(KC_GRAVE)",

    # Shifted symbols
    "EXCLAMATION": "LSFT(KC_1)", "EXCL": "LSFT(KC_1)",
    "AT_SIGN": "LSFT(KC_2)", "AT": "LSFT(KC_2)",
    "HASH": "LSFT(KC_3)", "POUND": "LSFT(KC_3)",
    "DOLLAR": "LSFT(KC_4)", "DLLR": "LSFT(KC_4)",
    "PERCENT": "LSFT(KC_5)", "PRCNT": "LSFT(KC_5)",
    "CARET": "LSFT(KC_6)", "CRRT": "LSFT(KC_6)",
    "AMPERSAND": "LSFT(KC_7)", "AMPS": "LSFT(KC_7)",
    "ASTERISK": "LSFT(KC_8)", "ASTRK": "LSFT(KC_8)", "STAR": "LSFT(KC_8)",
    "QUESTION": "LSFT(KC_SLASH)", "QMARK": "LSFT(KC_SLASH)",
    "PIPE": "LSFT(KC_BSLASH)",
    "LESS_THAN": "LSFT(KC_COMMA)", "LT": "LSFT(KC_COMMA)",
    "GREATER_THAN": "LSFT(KC_DOT)", "GT": "LSFT(KC_DOT)",

    # Keypad
    "KP_ASTERISK": "KC_KP_ASTERISK", "KP_MULTIPLY": "KC_KP_ASTERISK",
    "KP_PLUS": "KC_KP_PLUS", "KP_ADD": "KC_KP_PLUS",
    "KP_MINUS": "KC_KP_MINUS", "KP_SUBTRACT": "KC_KP_MINUS",
    "KP_SLASH": "KC_KP_SLASH", "KP_DIVIDE": "KC_KP_SLASH",

    # Media
    "K_PLAY_PAUSE": "KC_MEDIA_PLAY_PAUSE", "C_PP": "KC_MEDIA_PLAY_PAUSE",
    "K_STOP": "KC_MEDIA_STOP", "C_STOP": "KC_MEDIA_STOP",
    "K_NEXT": "KC_MEDIA_NEXT_TRACK", "C_NEXT": "KC_MEDIA_NEXT_TRACK",
    "K_PREV": "KC_MEDIA_PREV_TRACK", "C_PREV": "KC_MEDIA_PREV_TRACK",
    "K_VOL_UP": "KC_AUDIO_VOL_UP", "C_VOL_UP": "KC_AUDIO_VOL_UP",
    "K_VOL_DN": "KC_AUDIO_VOL_DOWN", "C_VOL_DN": "KC_AUDIO_VOL_DOWN",
    "K_MUTE": "KC_AUDIO_MUTE", "C_MUTE": "KC_AUDIO_MUTE",

    # Special
    "K_APPLICATION": "KC_APPLICATION", "K_APP": "KC_APPLICATION",
    "K_CMENU": "KC_APPLICATION",

    # ZMK-only features (no QMK equivalent - map to KC_NO)
    "BT_CLR": "KC_NO", "BT_CLR_ALL": "KC_NO",
    "BT_SEL": "KC_NO",  # Bluetooth select (handled specially in parser)
    "BT_PRV": "KC_NO", "BT_NXT": "KC_NO",
    "BT_DISC": "KC_NO",
    "OUT_TOG": "KC_NO", "OUT_USB": "KC_NO", "OUT_BLE": "KC_NO",
    "EP_ON": "KC_NO", "EP_OFF": "KC_NO", "EP_TOG": "KC_NO",
    "EXT_POWER": "KC_NO",
    "RGB_TOG": "KC_NO", "RGB_EFF": "KC_NO", "RGB_EFR": "KC_NO",
    "RGB_HUI": "KC_NO", "RGB_HUD": "KC_NO",
    "RGB_SAI": "KC_NO", "RGB_SAD": "KC_NO",
    "RGB_BRI": "KC_NO", "RGB_BRD": "KC_NO",
    "RGB_SPI": "KC_NO", "RGB_SPD": "KC_NO",
}

# Modifier prefixes for ZMK
ZMK_MOD_MAP = {
    "LC": "LCTL", "LEFT_CONTROL": "LCTL", "LCTRL": "LCTL",
    "RC": "RCTL", "RIGHT_CONTROL": "RCTL", "RCTRL": "RCTL",
    "LS": "LSFT", "LEFT_SHIFT": "LSFT", "LSHIFT": "LSFT", "LSHFT": "LSFT",
    "RS": "RSFT", "RIGHT_SHIFT": "RSFT", "RSHIFT": "RSFT", "RSHFT": "RSFT",
    "LA": "LALT", "LEFT_ALT": "LALT",
    "RA": "RALT", "RIGHT_ALT": "RALT",
    "LG": "LGUI", "LEFT_GUI": "LGUI", "LWIN": "LGUI", "LCMD": "LGUI", "LMETA": "LGUI",
    "RG": "RGUI", "RIGHT_GUI": "RGUI", "RWIN": "RGUI", "RCMD": "RGUI", "RMETA": "RGUI",
}


# =============================================================================
# Data Structures
# =============================================================================

@dataclass
class TapDance:
    tap: str
    hold: str
    tapping_term: int = 140
    double_tap: str = "KC_NO"
    tap_hold: str = "KC_NO"


@dataclass
class Macro:
    actions: list  # List of ["tap"|"text"|"down"|"up", ...args]


@dataclass
class Combo:
    keys: list  # List of key positions or keycodes
    result: str


@dataclass
class Behavior:
    name: str
    tapping_term: int = 200
    flavor: str = "tap-preferred"
    require_prior_idle: int = 0


@dataclass
class ZMKKeymap:
    layers: list = field(default_factory=list)
    behaviors: dict = field(default_factory=dict)
    macros: dict = field(default_factory=dict)
    combos: list = field(default_factory=list)


# =============================================================================
# Parser
# =============================================================================

class ZMKParser:
    def __init__(self, content: str):
        self.content = content
        self.keymap = ZMKKeymap()
        self.tap_dances: list[TapDance] = []
        self.td_map: dict[str, int] = {}  # Maps binding string to TD index

    def parse(self) -> ZMKKeymap:
        self._parse_behaviors()
        self._parse_macros()
        self._parse_combos()
        self._parse_layers()
        return self.keymap

    def _clean_content(self, text: str) -> str:
        """Remove C-style comments."""
        # Remove multi-line comments
        text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
        # Remove single-line comments
        text = re.sub(r'//.*$', '', text, flags=re.MULTILINE)
        return text

    def _parse_behaviors(self):
        """Extract custom behaviors (hold-tap configurations)."""
        # Look for behavior definitions like mt0: mt0 { ... }
        behavior_pattern = r'(\w+):\s*\1\s*\{([^}]+)\}'

        for match in re.finditer(behavior_pattern, self.content):
            name = match.group(1)
            body = match.group(2)

            behavior = Behavior(name=name)

            # Extract tapping-term-ms
            tt_match = re.search(r'tapping-term-ms\s*=\s*<(\d+)>', body)
            if tt_match:
                behavior.tapping_term = int(tt_match.group(1))

            # Extract flavor
            flavor_match = re.search(r'flavor\s*=\s*"([^"]+)"', body)
            if flavor_match:
                behavior.flavor = flavor_match.group(1)

            # Extract require-prior-idle-ms
            idle_match = re.search(r'require-prior-idle-ms\s*=\s*<(\d+)>', body)
            if idle_match:
                behavior.require_prior_idle = int(idle_match.group(1))

            self.keymap.behaviors[name] = behavior

        # Also check the default &mt configuration
        mt_config = re.search(r'&mt\s*\{([^}]+)\}', self.content)
        if mt_config:
            body = mt_config.group(1)
            behavior = Behavior(name="mt")

            tt_match = re.search(r'tapping-term-ms\s*=\s*<(\d+)>', body)
            if tt_match:
                behavior.tapping_term = int(tt_match.group(1))

            flavor_match = re.search(r'flavor\s*=\s*"([^"]+)"', body)
            if flavor_match:
                behavior.flavor = flavor_match.group(1)

            idle_match = re.search(r'require-prior-idle-ms\s*=\s*<(\d+)>', body)
            if idle_match:
                behavior.require_prior_idle = int(idle_match.group(1))

            self.keymap.behaviors["mt"] = behavior

    def _parse_macros(self):
        """Extract macro definitions."""
        # Pattern for ZMK macros
        macro_pattern = r'(\w+):\s*\1\s*\{[^}]*compatible\s*=\s*"zmk,behavior-macro"[^}]*bindings\s*=\s*<([^>]+)>'

        for match in re.finditer(macro_pattern, self.content, re.DOTALL):
            name = match.group(1)
            bindings_str = match.group(2)

            macro = Macro(actions=[])

            # Parse the bindings - split by &kp or other behaviors
            keys = re.findall(r'&kp\s+(\S+)', bindings_str)

            if keys:
                # Convert to text if it's just letters/numbers
                text = self._keys_to_text(keys)
                if text:
                    macro.actions.append(["text", text])
                else:
                    # Convert to tap sequence
                    qmk_keys = [self._zmk_key_to_qmk(k) for k in keys]
                    macro.actions.append(["tap"] + qmk_keys)

            self.keymap.macros[name] = macro

    def _keys_to_text(self, keys: list) -> Optional[str]:
        """Try to convert a list of ZMK keys to plain text."""
        text = ""
        text_chars = {
            'A': 'a', 'B': 'b', 'C': 'c', 'D': 'd', 'E': 'e', 'F': 'f',
            'G': 'g', 'H': 'h', 'I': 'i', 'J': 'j', 'K': 'k', 'L': 'l',
            'M': 'm', 'N': 'n', 'O': 'o', 'P': 'p', 'Q': 'q', 'R': 'r',
            'S': 's', 'T': 't', 'U': 'u', 'V': 'v', 'W': 'w', 'X': 'x',
            'Y': 'y', 'Z': 'z',
            'N0': '0', 'N1': '1', 'N2': '2', 'N3': '3', 'N4': '4',
            'N5': '5', 'N6': '6', 'N7': '7', 'N8': '8', 'N9': '9',
            'SPACE': ' ', 'SPC': ' ',
            'DOT': '.', 'PERIOD': '.',
            'COMMA': ',',
            'UNDER': '_', 'UNDERSCORE': '_', 'MINUS': '-',
            'PRCNT': '%', 'PERCENT': '%',
            'STAR': '*', 'ASTERISK': '*', 'ASTRK': '*',
        }

        for key in keys:
            # Handle shifted keys like LS(S)
            shift_match = re.match(r'LS\((\w+)\)', key)
            if shift_match:
                inner = shift_match.group(1)
                if inner in text_chars:
                    text += text_chars[inner].upper()
                    continue
                elif inner == 'MINUS':
                    text += '_'
                    continue

            if key in text_chars:
                text += text_chars[key]
            elif key == 'RET' or key == 'ENTER':
                text += '\n'
            elif key == 'NONE' or key == 'none':
                continue
            else:
                return None  # Can't convert to simple text

        return text if text else None

    def _parse_combos(self):
        """Extract combo definitions."""
        combo_pattern = r'\w+\s*\{[^}]*bindings\s*=\s*<([^>]+)>[^}]*key-positions\s*=\s*<([^>]+)>'

        for match in re.finditer(combo_pattern, self.content):
            binding = match.group(1).strip()
            positions = match.group(2).strip().split()

            combo = Combo(
                keys=[int(p) for p in positions if p.isdigit()],
                result=self._convert_binding(binding)
            )
            self.keymap.combos.append(combo)

    def _strip_comments(self, text: str) -> str:
        """Remove C-style comments from text."""
        # Remove multi-line comments /* ... */
        text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
        # Remove single-line comments // ...
        text = re.sub(r'//.*$', '', text, flags=re.MULTILINE)
        return text

    def _parse_layers(self):
        """Extract layer definitions."""
        # Strip comments first - they can contain { } characters that break parsing
        clean_content = self._strip_comments(self.content)

        # Find the keymap section
        keymap_start = clean_content.find('keymap {')
        if keymap_start == -1:
            print("Warning: Could not find keymap section")
            return

        # Find the matching closing brace by counting braces
        brace_count = 0
        keymap_end = keymap_start
        in_keymap = False

        for i, char in enumerate(clean_content[keymap_start:], keymap_start):
            if char == '{':
                brace_count += 1
                in_keymap = True
            elif char == '}':
                brace_count -= 1
                if in_keymap and brace_count == 0:
                    keymap_end = i + 1
                    break

        keymap_content = clean_content[keymap_start:keymap_end]

        # Now find layer blocks within keymap
        # Pattern: layer_name { bindings = <...>; };
        layer_pattern = r'(\w+(?:_layer)?)\s*\{[^{}]*bindings\s*=\s*<([\s\S]*?)>\s*;'

        for match in re.finditer(layer_pattern, keymap_content):
            layer_name = match.group(1)
            bindings_str = match.group(2)

            # Clean up layer name
            clean_name = layer_name.replace('_layer', '')

            # Parse bindings
            layer_keys = self._parse_bindings(bindings_str)

            # Only add if we got keys (filters out non-keymap bindings)
            if layer_keys:
                self.keymap.layers.append({
                    'name': clean_name,
                    'keys': layer_keys
                })

        print(f"  Layer names found: {[l['name'] for l in self.keymap.layers]}")

    def _parse_bindings(self, bindings_str: str) -> list:
        """Parse a bindings string into a list of QMK keycodes."""
        keys = []

        # Split on whitespace but handle multi-part bindings
        tokens = bindings_str.split()

        i = 0
        while i < len(tokens):
            token = tokens[i]

            if token.startswith('&'):
                # This is a behavior reference
                behavior = token[1:]  # Remove &

                if behavior in ('none', 'trans'):
                    keys.append("KC_NO" if behavior == 'none' else "KC_TRNS")
                    i += 1
                elif behavior == 'kp':
                    # Simple keypress: &kp KEY
                    if i + 1 < len(tokens):
                        key = tokens[i + 1]
                        keys.append(self._zmk_key_to_qmk(key))
                        i += 2
                    else:
                        i += 1
                elif behavior in ('mt', 'mt0', 'mti'):
                    # Mod-tap: &mt MOD KEY or &mt0 MOD KEY
                    if i + 2 < len(tokens):
                        hold_key = tokens[i + 1]
                        tap_key = tokens[i + 2]
                        keys.append(self._create_tap_dance(tap_key, hold_key, behavior))
                        i += 3
                    else:
                        i += 1
                elif behavior == 'lt':
                    # Layer-tap: &lt LAYER KEY
                    if i + 2 < len(tokens):
                        layer = tokens[i + 1]
                        tap_key = tokens[i + 2]
                        qmk_key = self._zmk_key_to_qmk(tap_key)
                        keys.append(f"LT{layer}({qmk_key})")
                        i += 3
                    else:
                        i += 1
                elif behavior == 'mo':
                    # Momentary layer: &mo LAYER
                    if i + 1 < len(tokens):
                        layer = tokens[i + 1]
                        keys.append(f"MO({layer})")
                        i += 2
                    else:
                        i += 1
                elif behavior == 'to':
                    # To layer: &to LAYER
                    if i + 1 < len(tokens):
                        layer = tokens[i + 1]
                        keys.append(f"TO({layer})")
                        i += 2
                    else:
                        i += 1
                elif behavior in self.keymap.macros:
                    # Macro reference
                    macro_idx = list(self.keymap.macros.keys()).index(behavior)
                    keys.append(f"M{macro_idx}")
                    i += 1
                elif behavior == 'bt':
                    # Bluetooth behavior: &bt BT_CLR or &bt BT_SEL 0
                    # ZMK-only, map to KC_NO
                    if i + 1 < len(tokens):
                        bt_cmd = tokens[i + 1]
                        if bt_cmd == 'BT_SEL' and i + 2 < len(tokens):
                            # &bt BT_SEL X - skip the index too
                            i += 3
                        else:
                            # &bt BT_CLR, etc.
                            i += 2
                    else:
                        i += 1
                    keys.append("KC_NO")
                else:
                    # Unknown behavior, try to handle as custom behavior with 2 args
                    if i + 2 < len(tokens) and not tokens[i + 1].startswith('&'):
                        hold_key = tokens[i + 1]
                        tap_key = tokens[i + 2]
                        keys.append(self._create_tap_dance(tap_key, hold_key, behavior))
                        i += 3
                    else:
                        keys.append("KC_NO")
                        i += 1
            else:
                i += 1

        return keys

    def _zmk_key_to_qmk(self, zmk_key: str) -> str:
        """Convert a ZMK keycode to QMK format."""
        # Handle modifier combinations like LC(X), LS(MINUS), LG(LS(K)), etc.
        # Use a more robust regex that handles nested parentheses
        mod_match = re.match(r'(\w+)\((.+)\)$', zmk_key)
        if mod_match:
            mod = mod_match.group(1)
            inner = mod_match.group(2)

            qmk_mod = ZMK_MOD_MAP.get(mod, mod)
            qmk_inner = self._zmk_key_to_qmk(inner)

            return f"{qmk_mod}({qmk_inner})"

        # Direct lookup
        if zmk_key in ZMK_TO_QMK:
            return ZMK_TO_QMK[zmk_key]

        # Try with KC_ prefix
        if zmk_key.startswith('KC_'):
            return zmk_key

        # Default: add KC_ prefix
        return f"KC_{zmk_key}"

    def _create_tap_dance(self, tap_key: str, hold_key: str, behavior: str = "mt") -> str:
        """Create a tap dance entry and return its reference."""
        qmk_tap = self._zmk_key_to_qmk(tap_key)
        qmk_hold = self._zmk_key_to_qmk(hold_key)

        # Get tapping term from behavior
        tapping_term = 140  # Default
        if behavior in self.keymap.behaviors:
            tapping_term = self.keymap.behaviors[behavior].tapping_term
        elif "mt" in self.keymap.behaviors:
            tapping_term = self.keymap.behaviors["mt"].tapping_term

        # Check if this tap dance already exists
        td_key = f"{qmk_tap}|{qmk_hold}"
        if td_key in self.td_map:
            return f"TD({self.td_map[td_key]})"

        # Create new tap dance
        td_idx = len(self.tap_dances)
        self.tap_dances.append(TapDance(
            tap=qmk_tap,
            hold=qmk_hold,
            tapping_term=tapping_term
        ))
        self.td_map[td_key] = td_idx

        return f"TD({td_idx})"

    def _convert_binding(self, binding: str) -> str:
        """Convert a single ZMK binding to QMK format."""
        binding = binding.strip()

        if binding.startswith('&mo'):
            layer = binding.split()[1] if len(binding.split()) > 1 else "0"
            return f"MO({layer})"
        elif binding.startswith('&to'):
            layer = binding.split()[1] if len(binding.split()) > 1 else "0"
            return f"TO({layer})"
        elif binding.startswith('&kp'):
            key = binding.split()[1] if len(binding.split()) > 1 else ""
            return self._zmk_key_to_qmk(key)
        elif binding.startswith('&trans'):
            return "KC_TRNS"
        elif binding.startswith('&none'):
            return "KC_NO"

        return "KC_NO"


# =============================================================================
# Vial Generator
# =============================================================================

class VialGenerator:
    def __init__(self, keymap: ZMKKeymap, parser: ZMKParser, template_vil: dict):
        self.keymap = keymap
        self.parser = parser
        self.template = template_vil

    def generate(self) -> dict:
        """Generate Vial .vil JSON structure."""
        vil = self.template.copy()

        # Update tap dances
        vil['tap_dance'] = self._generate_tap_dances()

        # Update macros
        vil['macro'] = self._generate_macros()

        # Update combos
        vil['combo'] = self._generate_combos()

        # Update layers
        vil['layout'] = self._generate_layout()

        # Update timing settings
        vil['settings'] = self._generate_settings()

        return vil

    def _generate_tap_dances(self) -> list:
        """Generate tap dance array for Vial."""
        tap_dances = []

        for td in self.parser.tap_dances:
            tap_dances.append([
                td.tap,
                td.hold,
                td.double_tap,
                td.tap_hold,
                td.tapping_term
            ])

        # Pad to 32 entries (Vial default)
        while len(tap_dances) < 32:
            tap_dances.append(["KC_NO", "KC_NO", "KC_NO", "KC_NO", 200])

        return tap_dances

    def _generate_macros(self) -> list:
        """Generate macro array for Vial."""
        macros = []

        for name, macro in self.keymap.macros.items():
            macros.append(macro.actions)

        # Pad to 16 entries (Vial default)
        while len(macros) < 16:
            macros.append([])

        return macros

    def _generate_combos(self) -> list:
        """Generate combo array for Vial."""
        combos = []

        # Vial combos are [key1, key2, key3, key4, result]
        # We need to map position-based combos to key-based
        for combo in self.keymap.combos:
            # For now, use KC_NO for unused key slots
            combo_entry = ["KC_NO", "KC_NO", "KC_NO", "KC_NO", combo.result]

            # This is tricky - Vial uses actual keycodes, not positions
            # We'd need to look up what keys are at those positions
            # For simplicity, we'll preserve the combo from template if available
            combos.append(combo_entry)

        # Pad to 32 entries
        while len(combos) < 32:
            combos.append(["KC_NO", "KC_NO", "KC_NO", "KC_NO", "KC_NO"])

        return combos

    def _generate_layout(self) -> list:
        """Generate layout array for Vial.

        ZMK Corne/Chocofi layout (42 keys in row-major order):
        Row 1: keys 0-5 (left) | keys 6-11 (right)
        Row 2: keys 12-17 (left) | keys 18-23 (right)
        Row 3: keys 24-29 (left) | keys 30-35 (right)
        Thumbs: keys 36-38 (left) | keys 39-41 (right)

        Vial layout structure (8 rows per layer):
        Row 0: left row 1 (keys 0-5)
        Row 1: left row 2 (keys 12-17)
        Row 2: left row 3 (keys 24-29)
        Row 3: left thumbs [-1,-1,-1, keys 36-38]
        Row 4: right row 1 (keys 6-11, REVERSED)
        Row 5: right row 2 (keys 18-23, REVERSED)
        Row 6: right row 3 (keys 30-35, REVERSED)
        Row 7: right thumbs [-1,-1,-1, keys 39-41, REVERSED]
        """
        layout = []

        for layer_idx, layer in enumerate(self.keymap.layers):
            keys = layer['keys']

            # Pad keys to 42 if needed
            while len(keys) < 42:
                keys.append("KC_NO")

            # Map ZMK keys to Vial row structure
            new_layer = [
                # Left half
                keys[0:6],                                    # Row 0: left row 1
                keys[12:18],                                  # Row 1: left row 2
                keys[24:30],                                  # Row 2: left row 3
                [-1, -1, -1] + keys[36:39],                   # Row 3: left thumbs
                # Right half (reversed)
                list(reversed(keys[6:12])),                   # Row 4: right row 1
                list(reversed(keys[18:24])),                  # Row 5: right row 2
                list(reversed(keys[30:36])),                  # Row 6: right row 3
                [-1, -1, -1] + list(reversed(keys[39:42])),   # Row 7: right thumbs
            ]

            layout.append(new_layer)

        # Pad with empty layers from template (Vial expects 10 layers)
        for i in range(len(layout), len(self.template['layout'])):
            layout.append(self.template['layout'][i])

        return layout

    def _generate_settings(self) -> dict:
        """Generate timing settings based on ZMK behaviors."""
        settings = self.template.get('settings', {}).copy()

        # Setting 4 is tapping term
        if 'mt' in self.keymap.behaviors:
            settings['4'] = self.keymap.behaviors['mt'].tapping_term
        elif 'mt0' in self.keymap.behaviors:
            settings['4'] = self.keymap.behaviors['mt0'].tapping_term

        # Setting 10 is quick tap term (require-prior-idle equivalent)
        if 'mt' in self.keymap.behaviors and self.keymap.behaviors['mt'].require_prior_idle:
            settings['10'] = self.keymap.behaviors['mt'].require_prior_idle

        return settings


# =============================================================================
# Main
# =============================================================================

def fetch_from_github(repo: str = "timur-hassan/zmk-config-chocofi",
                      branch: str = "master",
                      keymap_path: str = "config/corne.keymap") -> str:
    """Fetch keymap file from GitHub."""
    raw_url = f"https://raw.githubusercontent.com/{repo}/{branch}/{keymap_path}"

    print(f"Fetching from: {raw_url}")

    try:
        with urlopen(raw_url) as response:
            return response.read().decode('utf-8')
    except URLError as e:
        print(f"Error fetching from GitHub: {e}")
        sys.exit(1)


def load_template_vil(path: Optional[str] = None) -> dict:
    """Load existing .vil file as template."""
    # Try specified path, then common locations
    paths_to_try = []
    if path:
        paths_to_try.append(path)
    paths_to_try.extend(["/tmp/vial.vil", "vial.vil", "template.vil"])

    for try_path in paths_to_try:
        try:
            with open(try_path, 'r') as f:
                print(f"Using template: {try_path}")
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            continue

    print("No template found, using built-in default structure")
    return get_default_template()


def get_default_template() -> dict:
    """Return a default Vial template structure."""
    return {
        "version": 1,
        "uid": 15126841831861545787,
        "layout": [[["KC_NO"] * 6 for _ in range(8)] for _ in range(10)],
        "encoder_layout": [[] for _ in range(10)],
        "layout_options": -1,
        "macro": [[] for _ in range(16)],
        "vial_protocol": 5,
        "via_protocol": 9,
        "tap_dance": [["KC_NO", "KC_NO", "KC_NO", "KC_NO", 200] for _ in range(32)],
        "combo": [["KC_NO", "KC_NO", "KC_NO", "KC_NO", "KC_NO"] for _ in range(32)],
        "key_override": [],
        "alt_repeat_key": [],
        "settings": {}
    }


def main():
    parser = argparse.ArgumentParser(
        description="Convert ZMK keymap to Vial .vil format"
    )
    parser.add_argument(
        '--local', '-l',
        help="Path to local .keymap file (default: fetch from GitHub)"
    )
    parser.add_argument(
        '--output', '-o',
        default="zmk-converted.vil",
        help="Output .vil file path (default: zmk-converted.vil)"
    )
    parser.add_argument(
        '--template', '-t',
        default=None,
        help="Template .vil file for structure (default: auto-detect or use built-in)"
    )
    parser.add_argument(
        '--branch', '-b',
        default="master",
        help="GitHub branch to fetch from (default: master)"
    )
    parser.add_argument(
        '--repo', '-r',
        default="timur-hassan/zmk-config-chocofi",
        help="GitHub repo to fetch from (default: timur-hassan/zmk-config-chocofi)"
    )

    args = parser.parse_args()

    # Fetch or load keymap
    if args.local:
        print(f"Loading local file: {args.local}")
        with open(args.local, 'r') as f:
            keymap_content = f.read()
    else:
        keymap_content = fetch_from_github(
            repo=args.repo,
            branch=args.branch
        )

    # Load template
    template = load_template_vil(args.template)

    # Parse ZMK keymap
    print("Parsing ZMK keymap...")
    zmk_parser = ZMKParser(keymap_content)
    keymap = zmk_parser.parse()

    print(f"  Found {len(keymap.layers)} layers")
    print(f"  Found {len(keymap.behaviors)} custom behaviors")
    print(f"  Found {len(keymap.macros)} macros")
    print(f"  Found {len(keymap.combos)} combos")
    print(f"  Created {len(zmk_parser.tap_dances)} tap dances")

    # Generate Vial output
    print("Generating Vial .vil file...")
    generator = VialGenerator(keymap, zmk_parser, template)
    vil_data = generator.generate()

    # Write output
    with open(args.output, 'w') as f:
        json.dump(vil_data, f, separators=(',', ':'))

    print(f"Output written to: {args.output}")
    print("\nTo use: Load the .vil file in Vial via File -> Load saved layout")


if __name__ == "__main__":
    main()
