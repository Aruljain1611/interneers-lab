import requests

CATEGORY_API_URL = "http://127.0.0.1:8000/inventory/categories/"

def run_seed():
    core_categories = [
        {
            "title": "Uncategorized", 
            "description": "Default system category for products missing a classification."
        },
        {
            "title": "Electronics", 
            "description": "Computers, phones, and digital accessories."
        },
        {
            "title": "Apparel", 
            "description": "Clothing, shoes, and wearables."
        },
        {
            "title": "Home & Kitchen", 
            "description": "Furniture, decor, and cooking supplies."
        }
    ]

    seeded_count = 0
    for cat_data in core_categories:
        title = cat_data["title"]
        try:
            create_response = requests.post(CATEGORY_API_URL, json=cat_data)
            
            if create_response.status_code == 201:
                print(f"✅ Created: '{title}'")
                seeded_count += 1
            else:
                print(f"Couldn't create '{title}' (Status {create_response.status_code}): {create_response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"Error while creating '{title}': {e}")

    print(f"Seeding completed! Added {seeded_count} new categories.")

if __name__ == "__main__":
    run_seed()