from bson import ObjectId
from pymongo import MongoClient
from datetime import datetime, timedelta
import yfinance as yf
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.decomposition import PCA
from celery import Celery, shared_task
from pymongo import MongoClient
import numpy as np
from datetime import datetime
from pymongo.errors import PyMongoError
from collections import defaultdict



# Set up the Celery app
app = Celery('risk_service', broker='redis://redis:6379/0')

# Connect to MongoDB
client = MongoClient('mongodb+srv://pallavy57:pallavy57@cluster0.unsm7.mongodb.net/')
db = client['risk_analysis']  # Replace with your actual database name

def calculate_var(returns, portfolio_value, confidence_level=0.95):
    portfolio_std = np.std(returns)
    z_score = np.percentile(returns, (1 - confidence_level) * 100)
    var = portfolio_value * z_score * portfolio_std
    return var

def calculate_sensitivity(portfolio_value, factor_weight, change=0.01):
    modified_value = portfolio_value * (1 + change * factor_weight)
    sensitivity = (modified_value - portfolio_value) / change
    return sensitivity

def perform_stress_test(portfolio, extreme_change):
    stressed_value = sum([
        asset['asset_quantity'] * asset['current_price'] * (1 + extreme_change)
        for asset in portfolio['assets']
    ])
    return stressed_value

def regression_analysis(portfolio_returns, risk_factor_returns):
    model = LinearRegression().fit(risk_factor_returns, portfolio_returns)
    contributions = model.coef_
    return contributions

def pca_analysis(risk_factor_returns):
    pca = PCA()
    pca.fit(risk_factor_returns)
    explained_variance = pca.explained_variance_ratio_
    return explained_variance

def variance_decomposition(portfolio_returns, risk_factor_returns):
    total_variance = np.var(portfolio_returns)
    risk_factor_variances = np.var(risk_factor_returns, axis=0)
    variance_contributions = risk_factor_variances / np.sum(risk_factor_variances) * total_variance
    return variance_contributions

def insert_user_data_into_collections(user_portfolio_data):
    """
    Inserts user portfolio data into the Portfolios and FactorContributions collections,
    with calculations for VaR, Sensitivity, Stress Tests, Regression, PCA, and Variance Decomposition.
    """

    # Insert into Portfolios collection
    for portfolio in user_portfolio_data['portfolios']:
        portfolio_doc = {
            "user_id": user_portfolio_data['user_id'],
            "portfolio_id": ObjectId(),  # Generating a new ObjectId for the portfolio
            "name": portfolio['portfolio_name'],
            "description": portfolio['portfolio_desc'],
            "assets": portfolio['assets'],  # Assuming assets are a list of dicts with 'asset_ticker' and 'asset_quantity'
            "created_at": datetime.fromisoformat(portfolio['portfolio_created_at'])
        }
        
        # Calculate portfolio value and daily returns for each asset
        portfolio_value = 0
        portfolio_returns = []

        for asset in portfolio['assets']:
            stock = yf.Ticker(asset['asset_ticker'])
            data = stock.history(period="1y")
            if not data.empty:
                current_price = data['Close'].iloc[-1]
                daily_returns = data['Close'].pct_change().dropna()
                asset['current_price'] = current_price
                portfolio_value += asset['asset_quantity'] * current_price
                portfolio_returns.append(daily_returns * asset['asset_quantity'])
            else:
                asset['current_price'] = 0

        # Combine returns into a single portfolio return
        if portfolio_returns:
            portfolio_returns = np.sum(portfolio_returns, axis=0)

        # Define the risk factors you want to use, e.g., S&P 500
        risk_factor_tickers = ["^GSPC", "^IXIC", "^DJI"]  # Example: S&P 500, NASDAQ, Dow Jones
        risk_factor_returns = []

        for factor_ticker in risk_factor_tickers:
            factor_data = yf.Ticker(factor_ticker).history(period="1y")
            if not factor_data.empty:
                risk_factor_returns.append(factor_data['Close'].pct_change().dropna())

        risk_factor_returns = np.array(risk_factor_returns).T

        # Insert portfolio document
        portfolio_id = db.portfolios.insert_one(portfolio_doc).inserted_id

        # Calculate and store VaR, Sensitivity, Stress Test, and other factors
        for factor_ticker, factor_returns in zip(risk_factor_tickers, risk_factor_returns.T):
            weight = 1  # Replace with actual weight if applicable

            var = calculate_var(portfolio_returns, portfolio_value)
            sensitivity = calculate_sensitivity(portfolio_value, weight)
            stress_test_result = perform_stress_test(portfolio, extreme_change=-0.3)
            regression_contributions = regression_analysis(portfolio_returns, risk_factor_returns)
            pca_contributions = pca_analysis(risk_factor_returns)
            variance_contributions = variance_decomposition(portfolio_returns, risk_factor_returns)

            factor_contribution_doc = {
                "user_id": user_portfolio_data['user_id'],
                "portfolio_id": portfolio_id,
                "risk_factor_id": ObjectId(),  # Assuming you have some logic to determine or generate risk factor ids
                "factor_name": factor_ticker,  # Using factor_ticker as factor_name
                "var": var,
                "sensitivity": sensitivity,
                "stress_test_result": stress_test_result,
                "regression_contributions": regression_contributions.tolist(),
                "pca_contributions": pca_contributions.tolist(),
                "variance_contributions": variance_contributions.tolist(),
                "timestamp": datetime.utcnow()
            }

            # Insert factor contribution document
            db.factor_contributions.insert_one(factor_contribution_doc)






def get_all_users():
    """
    Retrieves all users with portfolios from MongoDB and processes their portfolios.

    Returns:
        list: A list of dictionaries containing user details and their portfolio data.
    """
    # Fetch all users with portfolios
    users_cursor = db.users_with_portfolios.find()
    
    user_data_dict = defaultdict(lambda: {"portfolios": defaultdict(lambda: {"assets": []})})

    # Process each document in the cursor
    for user_data in users_cursor:
        user_id = user_data['user_id']
        portfolio_name = user_data['portfolio_name']

        # Aggregate user information
        user_data_dict[user_id]['user_id'] = user_id
        user_data_dict[user_id]['username'] = user_data['username']
        user_data_dict[user_id]['email'] = user_data['email']

        # Aggregate portfolio information
        user_data_dict[user_id]['portfolios'][portfolio_name]['portfolio_name'] = portfolio_name
        user_data_dict[user_id]['portfolios'][portfolio_name]['portfolio_desc'] = user_data['portfolio_desc']
        user_data_dict[user_id]['portfolios'][portfolio_name]['portfolio_created_at'] = user_data['portfolio_created_at'].isoformat()

        # Aggregate asset information
        asset_info = {
            "asset_ticker": user_data['asset_ticker'],
            "asset_quantity": user_data['asset_quantity']
        }
        user_data_dict[user_id]['portfolios'][portfolio_name]['assets'].append(asset_info)

    # Convert the defaultdict structure to the desired format
    final_user_portfolio_data = []
    for user_id, user_info in user_data_dict.items():
        portfolios = []
        for portfolio_name, portfolio_info in user_info['portfolios'].items():
            portfolios.append(portfolio_info)
        final_user_portfolio_data.append({
            "user_id": user_info['user_id'],
            "username": user_info['username'],
            "email": user_info['email'],
            "portfolios": portfolios
        })

        return final_user_portfolio_data

# Celery task to process the user data
@shared_task
def process_portfolio():
    all_users_data = get_all_users()
    print(f"all_users_data------------------------> {all_users_data}")
    for user_data in all_users_data:
        print(f"user_data------------------------> {user_data}")
        insert_user_data_into_collections(user_data)
