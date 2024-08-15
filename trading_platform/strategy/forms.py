from django import forms
from .models import StrategyConfig

class StrategyConfigForm(forms.ModelForm):
    class Meta:
        model = StrategyConfig
        fields = ['name', 'short_ma_period', 'long_ma_period', 'stop_loss', 'take_profit', 'max_drawdown']