# serializers.py
from rest_framework_mongoengine import serializers
from .models import RiskFactors, Portfolios, FactorContributions

class RiskFactorSerializer(serializers.DocumentSerializer):
    class Meta:
        model = RiskFactors
        fields = ['id', 'name', 'description']

class RiskExposureSerializer(serializers.DocumentSerializer):
    risk_factor = RiskFactorSerializer()

    class Meta:
        model = Portfolios
        fields = ['risk_factor', 'exposure_value', 'portfolio_id', 'timestamp']

class FactorContributionSerializer(serializers.DocumentSerializer):
    risk_factor = RiskFactorSerializer()

    class Meta:
        model = FactorContributions
        fields = ['risk_factor', 'contribution_value', 'portfolio_id', 'timestamp']
