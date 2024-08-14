import pandas as pd
from pymongo import MongoClient

# Step 1: Read the Excel sheet into a DataFrame
excel_file = 'random_users_with_portfolios_20.xlsx'
df = pd.read_excel(excel_file)

# Step 2: Connect to MongoDB using basic TLS settings
client = MongoClient(
    'mongodb+srv://pallavy57:pallavy57@cluster0.unsm7.mongodb.net/',
    tls=True,  # Enable TLS
    tlsAllowInvalidCertificates=True  # This disables certificate verification
)

db = client['risk_analysis']  # Replace with your database name
collection = db['users_with_portfolios']  # Replace with your collection name

# Step 3: Convert DataFrame to dictionary and insert into MongoDB
data_dict = df.to_dict(orient='records')

# Insert the dictionary into MongoDB
try:
    result = collection.insert_many(data_dict)
    print(f"Data has been successfully inserted into MongoDB. Inserted IDs: {result.inserted_ids}")
except Exception as e:
    print(f"An error occurred: {e}")
