from django.db import models

class StrategyConfig(models.Model):
    name = models.CharField(max_length=100)
    short_ma_period = models.IntegerField(default=50)
    long_ma_period = models.IntegerField(default=200)
    stop_loss = models.FloatField(default=0.05, help_text="Stop-loss percentage")
    take_profit = models.FloatField(default=0.1, help_text="Take-profit percentage")
    max_drawdown = models.FloatField(default=0.2, help_text="Maximum drawdown percentage")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} (Short MA: {self.short_ma_period}, Long MA: {self.long_ma_period})"

    class Meta:
        verbose_name = "Strategy Configuration"
        verbose_name_plural = "Strategy Configurations"



from django.contrib.postgres.fields import JSONField  # Use this if using PostgreSQL

class BacktestResult(models.Model):
    strategy = models.ForeignKey(StrategyConfig, on_delete=models.CASCADE, related_name="backtests")
    equity_curve = models.JSONField(help_text="Equity curve data as a list of portfolio values over time")
    sharpe_ratio = models.FloatField(help_text="Sharpe ratio of the strategy during the backtest")
    max_drawdown = models.FloatField(help_text="Maximum drawdown during the backtest")
    total_return = models.FloatField(help_text="Total return percentage of the strategy")
    start_date = models.DateField(help_text="Start date of the backtest")
    end_date = models.DateField(help_text="End date of the backtest")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Backtest of {self.strategy.name} from {self.start_date} to {self.end_date}"

    class Meta:
        verbose_name = "Backtest Result"
        verbose_name_plural = "Backtest Results"


class TradingLog(models.Model):
    strategy = models.ForeignKey(StrategyConfig, on_delete=models.CASCADE, related_name="trades")
    backtest_result = models.ForeignKey(BacktestResult, on_delete=models.CASCADE, related_name="trades", null=True, blank=True)
    symbol = models.CharField(max_length=10, help_text="Ticker symbol of the traded asset")
    action = models.CharField(max_length=4, choices=[('BUY', 'Buy'), ('SELL', 'Sell')], help_text="Buy or Sell action")
    price = models.FloatField(help_text="Price at which the trade was executed")
    quantity = models.IntegerField(help_text="Quantity of the asset traded")
    trade_time = models.DateTimeField(help_text="Time when the trade was executed")
    profit_loss = models.FloatField(null=True, blank=True, help_text="Profit or loss from the trade")
    stop_loss_triggered = models.BooleanField(default=False, help_text="Was the trade closed due to a stop-loss?")
    take_profit_triggered = models.BooleanField(default=False, help_text="Was the trade closed due to take-profit?")

    def __str__(self):
        return f"{self.action} {self.quantity} of {self.symbol} at {self.price} on {self.trade_time}"

    class Meta:
        verbose_name = "Trading Log"
        verbose_name_plural = "Trading Logs"        
