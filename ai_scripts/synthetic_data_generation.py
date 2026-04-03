import json
import random
import os
from datetime import datetime, timedelta

# ----------------------------
# CONFIG
# ----------------------------
NUM_PRODUCTS = 777
OUTPUT_FILE = "toy_products_777.json"

categories = [
    "Action Figures", "Educational Toys", "Remote Control Toys",
    "Board Games", "Dolls & Accessories", "Puzzles",
    "Building Blocks", "Outdoor Toys", "Soft Toys", "STEM Kits"
]

brands = [
    "LEGO", "Hasbro", "Mattel", "Fisher-Price", "Hot Wheels",
    "Nerf", "Barbie", "Play-Doh", "Funskool", "Hamleys",
    "Giggles", "Little Tikes", "Melissa & Doug", "VTech", "Spin Master"
]

adjectives = ["Super", "Mega", "Ultimate", "Smart", "Creative", "Turbo", "Magic", "Mini", "Adventure"]

toy_names = ["Robot", "Car", "Doll", "Puzzle", "Blaster", "Kit", "Set", "Game", "Figure", "Blocks"]

# ----------------------------
# HELPERS
# ----------------------------
def random_date():
    start_date = datetime(2023, 1, 1)
    return (start_date + timedelta(days=random.randint(0, 900))).isoformat()

def generate_description(category, brand):
    age = random.randint(3, 10)

    if category == "Action Figures":
        return f"{random.randint(6,14)}-inch action figure by {brand} with movable joints and detailed design. Ideal for kids aged {age}+ for imaginative play."

    elif category == "Educational Toys":
        return f"Educational toy by {brand} designed to enhance cognitive and motor skills. Suitable for children aged {age}+."

    elif category == "Remote Control Toys":
        return f"Remote control toy by {brand} with {random.randint(20,50)}m range and rechargeable battery. Built for speed and durability."

    elif category == "Board Games":
        return f"Interactive board game by {brand} for {random.randint(2,6)} players. Encourages strategic thinking and family fun."

    elif category == "Dolls & Accessories":
        return f"Doll set by {brand} including accessories and outfits. Perfect for role-play and storytelling for ages {age}+."

    elif category == "Puzzles":
        return f"{random.randint(100,1000)}-piece puzzle by {brand} designed to improve focus and problem-solving skills."

    elif category == "Building Blocks":
        return f"Building block set by {brand} with {random.randint(50,500)} pieces. Encourages creativity and construction skills."

    elif category == "Outdoor Toys":
        return f"Outdoor play toy by {brand} made with durable materials. Ideal for active play and physical development."

    elif category == "Soft Toys":
        return f"Soft plush toy by {brand} made from child-safe fabric. Comfortable and suitable for ages {age}+."

    elif category == "STEM Kits":
        return f"STEM kit by {brand} with {random.randint(15,60)} components. Teaches basic science and engineering concepts."

    return f"High-quality toy by {brand}."

def generate_product(i):
    category = random.choice(categories)
    brand = random.choice(brands)

    name = f"{random.choice(adjectives)} {brand} {random.choice(toy_names)} {i}"

    price = round(random.uniform(199, 4999), 2)
    quantity = random.randint(0, 500)

    return {
        "name": name,
        "description": generate_description(category, brand),
        "brand": brand,
        "price": price,
        "quantity": quantity,
        "product_category": category,
        "created_at": random_date()
    }

# ----------------------------
# GENERATE DATASET
# ----------------------------
products = [generate_product(i) for i in range(1, NUM_PRODUCTS + 1)]

# ----------------------------
# SAVE FILE
# ----------------------------
# Save in current working directory
file_path = os.path.join(os.getcwd(), OUTPUT_FILE)

with open(file_path, "w", encoding="utf-8") as f:
    json.dump(products, f, indent=4)

print(f"✅ Dataset generated successfully!")
print(f"📁 File saved at: {file_path}")