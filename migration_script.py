import requests

BASE_URL = "http://127.0.0.1:8000/inventory/products/"
DEFAULT_CATEGORY = "Uncategorized"

def run_migration():
    print("Starting API-driven category migration...")

    try:
        response = requests.get(BASE_URL)
        response.raise_for_status() 
        all_products = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Ouldn't connect to API: {e}")
        return

    orphans = [
        product for product in all_products
        if product.get("product_category") in [None, ""] or "product_category" not in product
    ]

    total_orphans = len(orphans)

    if total_orphans == 0:
        print("No products need migration. Database is already clean!")
        return

    print(f"Found {total_orphans} products missing a category. Migrating...")

    updated_count = 0
    for product in orphans:
        product_id = product.get("id")

        update_url = f"{BASE_URL}{product_id}/" 
        
        payload = {
            "product_category": DEFAULT_CATEGORY
        }

        try:
            update_response = requests.patch(update_url, json=payload)
            
            if update_response.status_code in [200, 204]:
                updated_count += 1
            else:
                print(f"Couldn't update {product_id} (Status {update_response.status_code}): {update_response.text}")

        except requests.exceptions.RequestException as e:
            print(f"Error updating {product_id}: {e}")


    print(f"Migration complete! Successfully updated {updated_count} products.")

if __name__ == "__main__":
    run_migration()