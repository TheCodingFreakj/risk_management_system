from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework import status
import logging
from bson import ObjectId
from .models import FactorContributions, Portfolios

logger = logging.getLogger(__name__)

class RiskExposureAPIView(APIView):

    def get(self, request, portfolio_id):
        try:
            # Convert the portfolio_id from string to ObjectId
            portfolio_id_obj = ObjectId(portfolio_id)
            logger.debug(f"Received request with portfolio_id: {portfolio_id_obj}")

            if not portfolio_id:
                logger.warning("No portfolio_id provided in request.")
                return JsonResponse({"error": "portfolio_id is required"}, status=status.HTTP_400_BAD_REQUEST)
            
            # Querying Portfolios by _id
            logger.debug(f"Querying Portfolios with _id={portfolio_id_obj}")
            risk_exposures = Portfolios.objects.filter(_id=portfolio_id_obj)
            logger.debug(f"Found {risk_exposures.count()} risk exposures")

            # Querying FactorContributions by portfolio_id
            logger.debug(f"Querying FactorContributions with portfolio_id={portfolio_id_obj}")
            factor_contributions = FactorContributions.objects.filter(portfolio_id=portfolio_id_obj)
            logger.debug(f"Found {factor_contributions.count()} factor contributions")
            
            # Serialize the data manually
            risk_exposure_data = []
            for exposure in risk_exposures:
                risk_exposure_data.append({
                    "portfolio_id": str(exposure.id),
                    "name": exposure.name,
                    "description": exposure.description,
                    "assets": exposure.assets,
                    "created_at": exposure.created_at.isoformat() if exposure.created_at else None,
                })

            factor_contribution_data = []
            for contribution in factor_contributions:
                factor_contribution_data.append({
                    "portfolio_id": str(contribution.portfolio_id),
                    "risk_factor_id": str(contribution.risk_factor_id),
                    "factor_name": contribution.factor_name,
                    "var": contribution.var,
                    "sensitivity": contribution.sensitivity,
                    "stress_test_result": contribution.stress_test_result,
                    "regression_contributions": contribution.regression_contributions if contribution.regression_contributions else [],
                    "pca_contributions": contribution.pca_contributions if contribution.pca_contributions else [],
                    "variance_contributions": contribution.variance_contributions if contribution.variance_contributions else [],
                    "timestamp": contribution.timestamp.isoformat() if contribution.timestamp else None,
                })
                        
            response_data = {
                'risk_exposure': risk_exposure_data,
                'factor_contributions': factor_contribution_data
            }
            logger.debug(f"Returning response data: {response_data}")

            return JsonResponse(response_data, safe=False)
        
        except Exception as e:
            logger.error(f"An error occurred while processing the request: {e}")
            return JsonResponse({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
