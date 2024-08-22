# backtest/management/commands/create_portfolio_and_backtest.py

from django.core.management.base import BaseCommand
from backtest.models import Asset, Portfolio, BacktestConfig

class Command(BaseCommand):
    help = 'Create a portfolio and apply a backtest configuration'

    def handle(self, *args, **kwargs):
        # List of symbols you want to include in the portfolio
        symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'JNJ', 'PG']

        # Fetch the assets from the database
        assets = Asset.objects.filter(symbol__in=symbols)

        if not assets.exists():
            self.stdout.write(self.style.ERROR("No assets found in the database for the provided symbols."))
            return

        self.stdout.write(self.style.SUCCESS(f"Fetched the following assets from the database:"))
        for asset in assets:
            self.stdout.write(f"- {asset.name} ({asset.symbol})")

        # Create or fetch a portfolio
        portfolio, created_portfolio = Portfolio.objects.get_or_create(
            name="Tech Growth and Blue-Chip Portfolio",
            defaults={'initial_capital': 2000000.00}  # $2,000,000 initial capital
        )

        if created_portfolio:
            self.stdout.write(self.style.SUCCESS(f"Created Portfolio: {portfolio.name}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Portfolio already exists: {portfolio.name}"))

        # Associate assets with the portfolio
        portfolio.assets.add(*assets)
        portfolio.save()

        self.stdout.write(self.style.SUCCESS(f"Associated {assets.count()} assets with Portfolio '{portfolio.name}'"))

        # Create or fetch a backtest configuration
        backtest_config, created_backtest_config = BacktestConfig.objects.get_or_create(
            portfolio=portfolio,
            defaults={
                'rebalancing_frequency': 'monthly',
                'weighting_scheme': 'market_cap'
            }
        )

        if created_backtest_config:
            self.stdout.write(self.style.SUCCESS(f"Created BacktestConfig: {backtest_config.portfolio.name} - {backtest_config.weighting_scheme}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"BacktestConfig already exists for Portfolio: {backtest_config.portfolio.name}"))

        # Output the assets in the portfolio
        self.stdout.write(self.style.SUCCESS(f"Portfolio '{portfolio.name}' now includes the following assets:"))
        for asset in portfolio.assets.all():
            self.stdout.write(f"- {asset.name} ({asset.symbol})")

