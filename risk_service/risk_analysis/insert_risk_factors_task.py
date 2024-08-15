import random
from bson import ObjectId
from pymongo import MongoClient
from datetime import datetime
import yfinance as yf
import time
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.decomposition import PCA
from celery import Celery, shared_task
from pymongo import MongoClient
import numpy as np
from datetime import datetime
from pymongo.errors import OperationFailure, PyMongoError
from collections import defaultdict



# Set up the Celery app
app = Celery('risk_service', broker='redis://redis:6379/0')

# Connect to MongoDB
client = MongoClient('mongodb+srv://pallavy57:pallavy57@cluster0.unsm7.mongodb.net/')
db = client['risk_analysis']  # Replace with your actual database name

def remove_outliers(returns, method="zscore", threshold=3.0):
    """
    Remove outliers from returns data using the specified method.
    
    :param returns: An array of portfolio returns.
    :param method: Method to remove outliers ('zscore' or 'iqr').
    :param threshold: Threshold for outlier removal.
    :return: Cleaned returns array.
    """
    if method == "zscore":
        z_scores = np.abs((returns - np.mean(returns)) / np.std(returns))
        filtered_returns = returns[z_scores < threshold]
    elif method == "iqr":
        q1, q3 = np.percentile(returns, [25, 75])
        iqr = q3 - q1
        lower_bound = q1 - threshold * iqr
        upper_bound = q3 + threshold * iqr
        filtered_returns = returns[(returns >= lower_bound) & (returns <= upper_bound)]
    else:
        raise ValueError("Unsupported outlier removal method.")
    return filtered_returns

def calculate_var(returns, portfolio_value, confidence_level=0.95, remove_outliers_method=None):
    """
    Calculate the Value at Risk (VaR) for a portfolio, with optional outlier handling.
    
    :param returns: An array of portfolio returns.
    :param portfolio_value: The current value of the portfolio.
    :param confidence_level: The confidence level for VaR calculation (e.g., 0.95 for 95% confidence).
    :param remove_outliers_method: Method to remove outliers ('zscore' or 'iqr').
    :return: The calculated VaR value.
    """
    # Handle outliers if a method is provided
    if remove_outliers_method:
        returns = remove_outliers(returns, method=remove_outliers_method)
        if returns.size == 0:
            raise ValueError("All data removed by outlier filtering.")

    # Clip the returns to avoid issues with log transformation
    returns = np.clip(returns, -0.999, None)

    # Log transformation (optional, depending on skewness)
    returns = np.log1p(returns)  # Use log(1 + returns) to avoid issues with negative values

    # Check for NaN values after transformation
    if np.isnan(returns).any():
        raise ValueError("NaN values detected after log transformation.")

    # Calculate the z-score for the desired confidence level
    z_score = np.percentile(returns, (1 - confidence_level) * 100)
    print(f"Calculated z-score at {(1 - confidence_level) * 100}% percentile: {z_score}")
    
    # Calculate VaR
    var = portfolio_value * z_score
    print(f"Portfolio value: {portfolio_value}, VaR: {var}")
    
    return var




def calculate_sensitivity(portfolio_value, factor_weight, change=0.01):
    modified_value = portfolio_value * (1 + change * factor_weight)
    sensitivity = (modified_value - portfolio_value) / change
    return sensitivity

def perform_stress_test(portfolio, factor_return, extreme_change):
    stressed_value = sum([
        asset['asset_quantity'] * asset['current_price'] * (1 + extreme_change * (factor_return[idx] if idx < len(factor_return) else 0))
        for idx, asset in enumerate(portfolio['assets'])
    ])
    return stressed_value




def regression_analysis(portfolio_returns, risk_factor_returns):
    """
    Perform a linear regression analysis between portfolio returns and risk factor returns.

    :param portfolio_returns: Array of portfolio returns (1D).
    :param risk_factor_returns: Array of risk factor returns (1D or 2D).
    :return: Coefficients of the linear regression model.
    """
    # Ensure risk_factor_returns is a 2D array (n_samples, n_features)
    if risk_factor_returns.ndim == 1:
        risk_factor_returns = risk_factor_returns.reshape(-1, 1)

    # Ensure portfolio_returns is a 1D array (n_samples,)
    if portfolio_returns.ndim > 1:
        portfolio_returns = portfolio_returns.ravel()

    model = LinearRegression().fit(risk_factor_returns, portfolio_returns)
    contributions = model.coef_
    return contributions





def pca_analysis(risk_factor_returns):
    """
    Perform PCA analysis on risk factor returns.

    :param risk_factor_returns: Array of risk factor returns (1D or 2D).
    :return: Array of principal component contributions.
    """
    # Ensure risk_factor_returns is a 2D array
    if risk_factor_returns.ndim == 1:
        risk_factor_returns = risk_factor_returns.reshape(-1, 1)

    # Determine the maximum number of components
    n_samples, n_features = risk_factor_returns.shape
    n_components = min(n_samples, n_features)  # Set n_components to the maximum possible value

    pca = PCA(n_components=n_components)
    transformed_data = pca.fit_transform(risk_factor_returns)
    
    # Return the transformed data (principal components)
    return transformed_data



def variance_decomposition(portfolio_returns, risk_factor_returns):
    total_variance = np.var(portfolio_returns)
    risk_factor_variances = np.var(risk_factor_returns, axis=0)
    variance_contributions = risk_factor_variances / np.sum(risk_factor_variances) * total_variance
    return variance_contributions

def insert_user_data_into_collections(user_portfolio_data, session):
    """
    Upserts user portfolio data into the Portfolios and FactorContributions collections,
    with calculations for VaR, Sensitivity, Stress Tests, Regression, PCA, and Variance Decomposition.
    """
    try:
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
                data = stock.history(period="5d")
                if not data.empty:
                    current_price = data['Close'].iloc[-1]
                    daily_returns = data['Close'].pct_change().dropna()
                    asset['current_price'] = current_price
                    asset_value = asset['asset_quantity'] * current_price
                    portfolio_value += asset_value
                    portfolio_returns.append(daily_returns * asset['asset_quantity'])
                else:
                    asset['current_price'] = 0

            # Combine returns into a single portfolio return
            if portfolio_returns:
                portfolio_returns = np.sum(portfolio_returns, axis=0)

            # Calculate the weight of each asset in the portfolio
            weights = []
            for asset in portfolio['assets']:
                if portfolio_value > 0:
                    weight = (asset['asset_quantity'] * asset['current_price']) / portfolio_value
                else:
                    weight = 0  # Avoid division by zero if portfolio_value is zero
                weights.append(weight)

            # Define the risk factors you want to use, e.g., S&P 500
            risk_factor_tickers = ["^GSPC", "^IXIC", "^DJI"]  # Example: S&P 500, NASDAQ, Dow Jones
            risk_factor_returns = []

            for factor_ticker in risk_factor_tickers:
                factor_data = yf.Ticker(factor_ticker).history(period="5d")
                if not factor_data.empty:
                    risk_factor_returns.append(factor_data['Close'].pct_change().dropna())

            # Ensure risk_factor_returns has the correct shape
            risk_factor_returns = np.array(risk_factor_returns).T if risk_factor_returns else np.array([])
            print(f"risk_factor_returns.......................> {len(risk_factor_returns)}")
            # Upsert the portfolio document
            portfolio_filter = {
                "user_id": user_portfolio_data['user_id'],
                "name": portfolio['portfolio_name']
            }
            portfolio_update = {
                "$set": portfolio_doc
            }

            db.portfolios.update_one(portfolio_filter, portfolio_update, upsert=True, session=session)
            portfolio_id = db.portfolios.find_one(portfolio_filter, session=session)["_id"]

            # Calculate and store VaR, Sensitivity, Stress Test, and other factors
            if portfolio_returns.size > 0 and risk_factor_returns.size > 0:
                confidence_level = 0.95  # 95% confidence level
                for i, factor_ticker in enumerate(risk_factor_tickers):
                    factor_return = risk_factor_returns[:, i]

                    # Calculate VaR for the factor using the portfolio returns and factor returns
                    # Here you might consider the impact of the factor on the portfolio's returns
                    combined_returns = portfolio_returns + factor_return  # Example of combining the factor with portfolio returns
                    var = calculate_var(combined_returns, portfolio_value, confidence_level)

                                # Apply the weight calculation appropriately
                    if i < len(weights):
                        sensitivity = calculate_sensitivity(portfolio_value, weights[i])
                    else:
                        # Handle the mismatch or calculate a generic sensitivity if needed
                        sensitivity = calculate_sensitivity(portfolio_value, sum(weights) / len(weights))  # Example: average weight

                    stress_test_result = perform_stress_test(portfolio, factor_return, extreme_change=-0.3)
                    regression_contributions = regression_analysis(portfolio_returns, factor_return)
                    pca_contributions = pca_analysis(factor_return)
                    variance_contributions = variance_decomposition(portfolio_returns, factor_return)

                    factor_contribution_doc = {
                        "user_id": user_portfolio_data['user_id'],
                        "portfolio_id": portfolio_id,
                        "risk_factor_id": ObjectId(),  # This should be a unique ID for each risk factor
                        "factor_name": factor_ticker,
                        "var": var,
                        "sensitivity": sensitivity,
                        "stress_test_result": stress_test_result,
                        "regression_contributions": regression_contributions.tolist(),
                        "pca_contributions": pca_contributions.tolist(),
                        "variance_contributions": variance_contributions.tolist(),
                        "timestamp": datetime.utcnow()
                    }

                    db.factor_contributions.update_one(
                        {
                            "user_id": user_portfolio_data['user_id'],
                            "portfolio_id": portfolio_id,
                            "factor_name": factor_ticker
                        },
                        {"$set": factor_contribution_doc},
                        upsert=True,
                        session=session
                    )

    except OperationFailure as e:
        print(f"Operation failed: {e.details}")
        raise  # Re-raise the exception to be handled by the retry logic







def get_all_users():
    """
    Retrieves all users with portfolios from MongoDB and processes their portfolios.

    Returns:
        list: A list of dictionaries containing user details and their portfolio data.
    """
    # Fetch all users with portfolios
    users_cursor = db.users_with_portfolios.find()
    
    user_data_dict = defaultdict(lambda: {"portfolios": defaultdict(lambda: {"assets": []})})
    final_user_portfolio_data = []
    
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
    
    max_retries = 10
    base_retry_interval = 1

    for user_data in all_users_data:
        for attempt in range(max_retries):
            with client.start_session() as session:
                with session.start_transaction():
                    try:
                        print(f"user_data------------------------> {user_data}")
                        insert_user_data_into_collections(user_data, session)
                        break
                    except OperationFailure as e:
                            print(f"Retry {attempt + 1}/{max_retries} failed with error: {str(e)}")
                            if 'TransientTransactionError' in e.details.get('errorLabels', []):
                                retry_interval = base_retry_interval + random.uniform(0, base_retry_interval)
                                print(f"TransientTransactionError: Retrying {attempt + 1}/{max_retries} after {retry_interval:.2f} seconds...")
                                time.sleep(retry_interval)
                                base_retry_interval *= 2
                            else:
                                print("Operation failed for a non-retryable reason.")
                                raise
                    except PyMongoError as e:
                        print(f"Transaction failed: {e}")
                        session.abort_transaction()
                        raise

    print("Processing complete.")