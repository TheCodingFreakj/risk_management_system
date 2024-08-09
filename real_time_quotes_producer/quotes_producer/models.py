from django.db import models

class MarketData(models.Model):
    ticker = models.CharField(max_length=10)
    date = models.DateField()
    price = models.FloatField()

    class Meta:
        unique_together = ('ticker', 'date')
    
    def __str__(self):
        return f'{self.ticker} - {self.date}: {self.price}'
    


class DailyReturn(models.Model):
    ticker = models.CharField(max_length=10)
    date = models.DateField()
    return_value = models.FloatField()

    class Meta:
        unique_together = ('ticker', 'date')

class PortfolioReturn(models.Model):
    date = models.DateField(unique=True)
    return_value = models.FloatField()

class VaR(models.Model):
    date = models.DateField(unique=True)
    var_value = models.FloatField()
    confidence_level = models.FloatField()

