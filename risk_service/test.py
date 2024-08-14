from pymongo import MongoClient

client = MongoClient(
    'mongodb+srv://pallavy57:pallavy57@cluster0.unsm7.mongodb.net/',
    tls=True,
    tlsAllowInvalidCertificates=True
)

db = client['risk_analysis']
collection = db['users_with_portfolios']

# Attempt to insert some test data to check the connection
try:
    test_data = {"test": "connection"}
    result = collection.insert_one(test_data)
    print(f"Connection successful, test data inserted with ID: {result.inserted_id}")
except Exception as e:
    print(f"An error occurred: {e}")
