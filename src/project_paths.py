"""Repository-relative defaults, independent of the current working directory."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEVELS = ROOT / 'data' / 'levels' / 'dolmenjord_levels.json'
SOLUTIONS = ROOT / 'data' / 'solutions' / 'solutions.json'
DOC = ROOT / 'doc'
LAYOUTS = DOC / 'layouts'
VALIDATION = DOC / 'validation_report.json'
