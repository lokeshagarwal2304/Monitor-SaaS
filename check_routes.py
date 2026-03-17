from backend.main import app
print(f"Total routes: {len(app.routes)}")
for i, route in enumerate(app.routes):
    path = getattr(route, "path", "N/A")
    name = getattr(route, "name", "N/A")
    print(f"{i}: {path} ({name})")
