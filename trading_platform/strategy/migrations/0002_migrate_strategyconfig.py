from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('strategy', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='strategyconfig',
            name='stock',
            field=models.CharField(max_length=100, default=''),  # Add a default value if needed
        ),
    ]
