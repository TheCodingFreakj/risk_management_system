from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient('mongodb+srv://pallavy57:pallavy57@cluster0.unsm7.mongodb.net/')
db = client['risk_analysis']

# Drop the existing risk_factors collection
db.risk_factors.drop()
print("Dropped the risk_factors collection.")

# Define new risk factors with the weight property
risk_factors = [
    { "name": "Market Risk", "description": "Risk due to market fluctuations.", "weight": 0.5 },
    { "name": "Credit Risk", "description": "Risk of borrower default.", "weight": 0.3 },
    { "name": "Liquidity Risk", "description": "Risk of being unable to sell assets quickly.", "weight": 0.2 },
    { "name": "Operational Risk", "description": "Risk of operational failures.", "weight": 0.4 },
    { "name": "Interest Rate Risk", "description": "Risk due to changes in interest rates.", "weight": 0.6 },
    { "name": "Inflation Risk", "description": "Risk of inflation reducing returns.", "weight": 0.1 },
    { "name": "Political/Regulatory Risk", "description": "Risk due to political instability or regulatory changes.", "weight": 0.3 },
    { "name": "Exchange Rate Risk", "description": "Risk of loss due to exchange rate fluctuations.", "weight": 0.25 },
    { "name": "Environmental, Social, and Governance (ESG) Risk", "description": "Risk related to ESG factors.", "weight": 0.35 }
]

# Insert the new risk factors into the risk_factors collection
db.risk_factors.insert_many(risk_factors)

print("Recreated the risk_factors collection with the weight property.")