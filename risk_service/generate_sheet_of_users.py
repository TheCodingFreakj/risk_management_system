# Updated code to generate 20 data points for the Excel sheet

import pandas as pd
import random
from datetime import datetime, timedelta, timezone

# Predefined lists of data
usernames = [
    "john_doe", "jane_smith", "alex_jones", "mary_ann", "william_brown", 
    "emma_wilson", "oliver_jones", "ava_smith", "isabella_martin", "liam_clark", 
    "noah_scott", "sophia_turner", "logan_white", "elijah_hall", "james_miller", 
    "mia_king", "lucas_walker", "amelia_hill", "harper_wright", "mason_green"
]
emails = ["example.com", "mail.com", "service.com"]
portfolio_names = ["Growth Portfolio", "Income Portfolio", "Balanced Portfolio", "Tech Portfolio", "Dividend Portfolio"]
portfolio_descriptions = [
    "A portfolio focused on high-growth technology stocks.",
    "A portfolio focused on dividend-paying stocks.",
    "A portfolio with a mix of growth and income assets.",
    "A portfolio focused on technology sector stocks.",
    "A portfolio focused on stable, dividend-paying companies."
]
tickers = ["AAPL", "MSFT", "TSLA", "GOOGL", "AMZN", "T", "VZ", "IBM", "JNJ", "PG", "KO", "PEP"]


def generate_random_timestamp():
    # Generate a random number of days to subtract (up to 1000 days)
    random_days = random.randint(0, 1000)
    # Subtract the random number of days from the current UTC time with timezone awareness
    random_timestamp = datetime.now(timezone.utc) - timedelta(days=random_days)
    # Convert timezone-aware datetime to naive datetime by removing timezone info
    naive_timestamp = random_timestamp.replace(tzinfo=None)
    return naive_timestamp
# Function to generate a random portfolio
def generate_random_portfolio():
    portfolio = {
        "name": random.choice(portfolio_names),
        "description": random.choice(portfolio_descriptions),
        "assets": [],
        "created_at": generate_random_timestamp()
    }
    
    num_assets = random.randint(2, 5)  # Random number of assets per portfolio
    selected_tickers = random.sample(tickers, num_assets)
    
    for ticker in selected_tickers:
        portfolio["assets"].append({
            "ticker": ticker,
            "quantity": random.randint(10, 500)  # Random quantity of stocks
        })
    
    return portfolio

# Function to generate random user data
def generate_random_user_data(num_users=20):
    users_with_portfolios = []
    
    for i in range(1, num_users + 1):
        user = {
            "user_id": f"user_{i:03d}",
            "username": random.choice(usernames),
            "email": f"{random.choice(usernames)}@{random.choice(emails)}",
            "portfolio": [generate_random_portfolio()]
        }
        
        users_with_portfolios.append(user)
    
    return users_with_portfolios

# Generate random data for 20 users
users_with_portfolios = generate_random_user_data(20)

# Prepare a list to hold the flattened data
data = []

# Flatten the data
for user in users_with_portfolios:
    for portfolio in user['portfolio']:
        for asset in portfolio['assets']:
            data.append({
                "user_id": user['user_id'],
                "username": user['username'],
                "email": user['email'],
                "portfolio_name": portfolio['name'],
                "portfolio_desc": portfolio['description'],
                "portfolio_created_at": portfolio['created_at'],
                "asset_ticker": asset['ticker'],
                "asset_quantity": asset['quantity']
            })

# Create a DataFrame from the flattened data
df = pd.DataFrame(data)

# Save the DataFrame to an Excel file
df.to_excel("random_users_with_portfolios_20.xlsx", index=False)

df.head()  # Display the first few rows of the DataFrame to verify the data
