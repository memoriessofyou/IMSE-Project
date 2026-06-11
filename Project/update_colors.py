import re

def update_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    if "index.html" in filepath:
        # Update Tailwind config for softer off-white
        content = content.replace("'snow-white': '#fcfcfd'", "'snow-white': '#fdfbf7'")
        if "'card-white'" not in content:
            content = content.replace("colors: {", "colors: {\n                        'card-white': '#ffffff',")
        
        # Soften the body background
        content = content.replace("body { font-family: 'Inter', sans-serif; }", "body { font-family: 'Inter', sans-serif; background-color: #fdfbf7; }")
        content = content.replace('<body class="h-full text-slate-text antialiased">', '<body class="h-full text-slate-text antialiased bg-snow-white">')
        
        # Soften modal backdrop
        content = content.replace("background-color: rgba(30, 58, 95, 0.4);", "background-color: rgba(44, 75, 107, 0.3);")

    # Replace stark whites with the new card-white
    content = content.replace("bg-white", "bg-card-white")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

update_file("frontend/index.html")
update_file("frontend/app.js")
print("Colors updated successfully")