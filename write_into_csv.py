import csv
from pymongo import MongoClient


if __name__ == "__main__":
    
    client = MongoClient()
    db = client["Stores"]
    col = db["Fashion Store"]
    xItems = []
    with open("results.csv", "w", encoding="utf-8", newline="") as f:
        fieldnames = ["_id", "name", "store", "website", "location", "address", "phone", "email", "rating", "title"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for x in col.find():
            writer.writerow(x)
    f.close()