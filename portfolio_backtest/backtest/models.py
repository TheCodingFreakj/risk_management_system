# backtest/models.py

from django.db import models
# {'c': 226.5226, 'd': 0.0126, 'dp': 0.0056, 'h': 227.03, 'l': 225.91, 'o': 227.03, 'pc': 226.51, 't': 1724247757}
class Asset(models.Model):
    symbol = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    market_cap = models.BigIntegerField()
    volatility = models.FloatField()

    def __str__(self):
        return self.symbol

class Portfolio(models.Model):
    name = models.CharField(max_length=100)
    initial_capital = models.DecimalField(max_digits=20, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    assets = models.ManyToManyField('Asset', related_name='portfolios')

    def __str__(self):
        return self.name

class BacktestConfig(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    rebalancing_frequency = models.CharField(max_length=10, choices=[('daily', 'Daily'), ('monthly', 'Monthly'), ('quarterly', 'Quarterly')])
    weighting_scheme = models.CharField(max_length=20, choices=[('market_cap', 'Market Cap'), ('risk_parity', 'Risk Parity')])

    def __str__(self):
        return f"{self.portfolio.name} - {self.weighting_scheme}"



class AlgorithmResult(models.Model):
    name = models.CharField(max_length=100)
    result_data = models.JSONField()  # Store algorithm result as JSON
    benchmark_data = models.JSONField(null=True, blank=True)  # Store benchmark data as JSON
    comparison_metrics = models.JSONField(null=True, blank=True)  # Store metrics like Sharpe Ratio, Alpha, etc.
    created_at = models.DateTimeField(auto_now_add=True)