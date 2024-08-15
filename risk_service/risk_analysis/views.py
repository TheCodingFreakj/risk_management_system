from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework import status
import logging
from bson import ObjectId
from .models import FactorContributions, Portfolios
from django.http import JsonResponse
from bson import ObjectId
from rest_framework import status
import logging

logger = logging.getLogger(__name__)

class PortfolioPerformanceView(APIView):
    def get(self, request, portfolio_id):
        try:
            # Convert the portfolio_id from string to ObjectId
            try:
                portfolio_id_obj = ObjectId(portfolio_id)
                print(f"Received request with portfolio_id: {portfolio_id_obj}")
            except Exception as e:
                logger.error(f"Invalid portfolio_id format: {e}")
                return JsonResponse({"error": "Invalid portfolio_id format"}, status=400)

            if not portfolio_id:
                logger.warning("No portfolio_id provided in request.")
                return JsonResponse({"error": "portfolio_id is required"}, status=400)

            # Querying Portfolios by _id
            try:
                print(f"Querying Portfolios with _id={portfolio_id_obj}")
                portfolio = Portfolios.objects.get(_id=portfolio_id_obj)
                print(f"Found portfolio: {portfolio.name}")
            except Portfolios.DoesNotExist:
                logger.error(f"Portfolio with id {portfolio_id} does not exist.")
                return JsonResponse({"error": "Portfolio not found"}, status=404)
            except Exception as e:
                logger.error(f"Error querying portfolio: {e}")
                return JsonResponse({"error": str(e)}, status=500)

            # Log before the query
            print("About to query FactorContributions")

            # Querying FactorContributions by portfolio_id
            try:
                factor_contributions = FactorContributions.objects.filter(portfolio_id=portfolio_id_obj)
                print(f"Found {factor_contributions.count()} factor contributions")
            except Exception as e:
                logger.error(f"Error querying FactorContributions: {e}")
                return JsonResponse({"error": str(e)}, status=500)
 
            # Serialize the data manually
            performance_data = []
            risk_factors= []
            for contribution in factor_contributions:
                try:
                    print(f"Processing contribution: {contribution}")
                    # Extract the first element from each nested array in pca_contributions
                    pca_contributions = [item[0] for item in contribution.pca_contributions if item]
                    performance_data.append({
                        "risk_factor_id": str(contribution.risk_factor_id),
                        "risk_factor_name": contribution.factor_name,
                        "pca_contributions": pca_contributions,
                        "regression_contributions": contribution.regression_contributions if contribution.regression_contributions else [],
                        "sensitivity": float(contribution.sensitivity) if isinstance(contribution.sensitivity, (int, float)) else None,
                        "stress_test_result": float(contribution.stress_test_result) if isinstance(contribution.stress_test_result, (int, float)) else None,
                        "var": float(contribution.var) if isinstance(contribution.var, (int, float)) else None,
                        "timestamp": contribution.timestamp.isoformat() if contribution.timestamp else None,
                    })

                    risk_factors.append({
                        "risk_factor_id": str(contribution.risk_factor_id),
                        "risk_factor_name": contribution.factor_name,
                        "metrics": {
                            "var": contribution.var,
                            "sensitivity": contribution.sensitivity,
                            "stress_test_result": contribution.stress_test_result,
                            "regression_contributions": contribution.regression_contributions[0] if contribution.regression_contributions else None,
                            "pca_contributions": contribution.pca_contributions[0][0] if contribution.pca_contributions else None,
                            "variance_contributions": contribution.variance_contributions
                        }
                    })
                except Exception as e:
                    logger.error(f"Error processing contribution {contribution._id}: {e}")

            response_data = {
                "portfolio_id": str(portfolio._id),
                "portfolio_name": portfolio.name,
                "performance": performance_data,
                "risk_factors":risk_factors
            }
            print(f"Returning response data: {response_data}")

            return JsonResponse(response_data, safe=False)

        except Exception as e:
            logger.error(f"An error occurred while processing the request: {e}")
            return JsonResponse({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# class PortfolioPerformanceView(APIView):
#     def get(self, request, portfolio_id):
#         try:
#           response_data =  {
#     "portfolio_id": "66bd74838e1a6c68d98c09a0",
#     "portfolio_name": "Balanced Portfolio",
#     "performance": [
#         {
#             "risk_factor_id": "rf1",
#             "risk_factor_name": "Technology Sector",
#             "pca_contributions": [0.25, 0.15, 0.10],
#             "regression_contributions": [0.30],
#             "sensitivity": 1.2,
#             "stress_test_result": 0.8,
#             "var": 0.05,
#             "timestamp": "2024-07-15T10:00:00Z"
#         },
#         {
#             "risk_factor_id": "rf2",
#             "risk_factor_name": "Healthcare Sector",
#             "pca_contributions": [0.20, 0.12, 0.08],
#             "regression_contributions": [0.25],
#             "sensitivity": 1.1,
#             "stress_test_result": 0.7,
#             "var": 0.04,
#             "timestamp": "2024-07-15T10:00:00Z"
#         },
#         {
#             "risk_factor_id": "rf3",
#             "risk_factor_name": "Energy Sector",
#             "pca_contributions": [0.15, 0.10, 0.05],
#             "regression_contributions": [0.20],
#             "sensitivity": 0.9,
#             "stress_test_result": 0.6,
#             "var": 0.03,
#             "timestamp": "2024-07-15T10:00:00Z"
#         }
#     ],
#     "risk_factors": [
#         {
#             "risk_factor_id": "rf1",
#             "risk_factor_name": "Technology Sector",
#             "metrics": {
#                 "var": 0.05,
#                 "sensitivity": 1.2,
#                 "stress_test_result": 0.8,
#                 "regression_contributions": 0.30,
#                 "pca_contributions": 0.25,
#                 "variance_contributions": [0.12]
#             }
#         },
#         {
#             "risk_factor_id": "rf2",
#             "risk_factor_name": "Healthcare Sector",
#             "metrics": {
#                 "var": 0.04,
#                 "sensitivity": 1.1,
#                 "stress_test_result": 0.7,
#                 "regression_contributions": 0.25,
#                 "pca_contributions": 0.20,
#                 "variance_contributions": [0.10]
#             }
#         },
#         {
#             "risk_factor_id": "rf3",
#             "risk_factor_name": "Energy Sector",
#             "metrics": {
#                 "var": 0.03,
#                 "sensitivity": 0.9,
#                 "stress_test_result": 0.6,
#                 "regression_contributions": 0.20,
#                 "pca_contributions": 0.15,
#                 "variance_contributions": [0.08]
#             }
#         }
#     ]
# }

#           return JsonResponse(response_data, safe=False)

#         except Exception as e:
#             logger.error(f"An error occurred while processing the request: {e}")
#             return JsonResponse({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
