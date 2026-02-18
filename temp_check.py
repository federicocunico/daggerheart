import json
from pathlib import Path

# Count files per category
cards_dir = Path("cards")
for cat in ["origine", "comunità"]:
    d = cards_dir / cat
    if d.exists():
        print(f"{cat}: {len(list(d.glob('*.json')))} cards")
        for f in sorted(d.glob("*.json"))[:5]:
            data = json.loads(f.read_text(encoding='utf-8'))
            print(f"  {f.stem}: nome='{data.get('nome','')}' id={data.get('id_carta','')}")

print()

# Domain subfolders and counts
domini_dir = cards_dir / "domini"
if domini_dir.exists():
    for subdir in sorted(domini_dir.iterdir()):
        if subdir.is_dir():
            jsons = list(subdir.glob("*.json"))
            print(f"  {subdir.name:<20}: {len(jsons)} cards")

# Check spell card names (pages 10+)
print("\n--- Spell/Ability card name samples ---")
sample_files = list((cards_dir / "domini").rglob("*.json"))
for f in sorted(sample_files)[50:60]:
    data = json.loads(f.read_text(encoding='utf-8'))
    if data.get('pagina', 0) >= 10:
        print(f"  {f.stem}: nome='{data.get('nome','')}' tipo={data.get('tipo_carta','')} id={data.get('id_carta','')}")

# Total count
all_json = list(cards_dir.rglob("*.json"))
print(f"\nTotal JSON files: {len(all_json)}")
