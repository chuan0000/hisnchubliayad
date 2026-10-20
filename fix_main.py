with open("app/main.py", "r", encoding="utf-8") as f:
    text = f.read()

# Fix import
text = text.replace(
    "from app.routers import auth, blocks, evidence, health, team, upload, wishlist, crawler",
    "from app.routers import auth, blocks, evidence, health, team, upload"
)
text = text.replace(
    "app.include_router(wishlist.router)",
    "app.include_router(blocks.wishlist_router)"
)
text = text.replace(
    "app.include_router(crawler.router)",
    "app.include_router(blocks.crawler_router)"
)

with open("app/main.py", "w", encoding="utf-8") as f:
    f.write(text)

print("app/main.py fixed successfully!")
