from mongoengine import Document,FloatField, StringField,IntField, ListField, DateTimeField, ObjectIdField

class Portfolios(Document):
    _id = ObjectIdField(primary_key=True)  # MongoDB ObjectId as the primary key
    user_id = ObjectIdField(required=True)
    portfolio_id = StringField(required=True)
    name = StringField(max_length=200)
    description = StringField(max_length=500)
    assets = ListField(StringField(max_length=200))  # Assuming assets are strings; modify as needed
    created_at = DateTimeField()




class FactorContributions(Document):
    _id = ObjectIdField(primary_key=True)  # MongoDB ObjectId as the primary key
    user_id = StringField(required=True)  # Storing the user ID as a string
    portfolio_id = ObjectIdField(required=True)  # Storing the portfolio's ObjectId
    risk_factor_id = ObjectIdField(required=True)  # Storing the risk factor's ObjectId
    factor_name = StringField(max_length=200)  # Name of the risk factor
    var = FloatField()  # Value-at-Risk (VaR) for the factor
    sensitivity = FloatField()  # Sensitivity analysis result for the factor
    stress_test_result = FloatField()  # Stress testing result for the factor
    regression_contributions = ListField(FloatField())  # Coefficients from Regression Analysis
    pca_contributions = ListField(ListField(FloatField()))  # Nested array structure for PCA contributions
    variance_contributions = FloatField()  # Contributions from Variance Decomposition
    timestamp = DateTimeField()  # Timestamp of the contribution


class RiskFactors(Document):
    _id = ObjectIdField(primary_key=True)  # MongoDB ObjectId as the primary key
    portfolio_id = ObjectIdField(required=True)  # Storing the portfolio's ObjectId
    name = StringField(max_length=200, required=True)  # Name of the risk factor
    description = StringField(max_length=500)  # Optional description of the risk factor
    weight = FloatField(required=True)  # The weight or importance of this risk factor


# from djongo import models

# class RiskFactor(models.Model):
#     name = models.CharField(max_length=255)
#     description = models.TextField()

#     class Meta:
#         # This ensures the model uses PostgreSQL by default
#         db_table = "risk_factors"

# class Portfolios(models.Model):
#     risk_factor = models.ForeignKey(RiskFactor, on_delete=models.CASCADE)
#     exposure_value = models.DecimalField(max_digits=18, decimal_places=4)
#     portfolio_id = models.CharField(max_length=255)
#     timestamp = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         # This ensures the model uses MongoDB
#         db_table = "portfolios"

# class FactorContributions(models.Model):
#     risk_factor = models.ForeignKey(RiskFactor, on_delete=models.CASCADE)
#     contribution_value = models.DecimalField(max_digits=18, decimal_places=4)
#     portfolio_id = models.CharField(max_length=255)
#     timestamp = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         # This ensures the model uses MongoDB
#         db_table = "factor_contributions"
