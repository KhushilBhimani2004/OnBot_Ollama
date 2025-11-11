import json

def save_bot_to_kb(bot_name, description, summary):
    entry = {
        "bot_name": bot_name,
        "description": description,
        "summary": summary
    }

    try:
        with open("knowledge_base.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        data = []

    data.append(entry)

    with open("knowledge_base.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
