from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('strategy', '0002_migrate_strategyconfig'),
    ]

    operations = [
        migrations.AddField(
            model_name='strategyconfig',
            name='start_date',
            field=models.DateField(help_text="Start date of the strategy", default='2024-01-01'),  # Add a sensible default
        ),
        migrations.AddField(
            model_name='strategyconfig',
            name='end_date',
            field=models.DateField(help_text="End date of the strategy", default='2024-12-31'),  # Add a sensible default
        ),
    ]
