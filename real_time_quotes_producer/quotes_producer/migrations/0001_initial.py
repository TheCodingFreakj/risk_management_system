# Generated by Django 3.2.25 on 2024-08-08 22:58

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='PortfolioReturn',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(unique=True)),
                ('return_value', models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name='VaR',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(unique=True)),
                ('var_value', models.FloatField()),
                ('confidence_level', models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name='MarketData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ticker', models.CharField(max_length=10)),
                ('date', models.DateField()),
                ('price', models.FloatField()),
            ],
            options={
                'unique_together': {('ticker', 'date')},
            },
        ),
        migrations.CreateModel(
            name='DailyReturn',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ticker', models.CharField(max_length=10)),
                ('date', models.DateField()),
                ('return_value', models.FloatField()),
            ],
            options={
                'unique_together': {('ticker', 'date')},
            },
        ),
    ]
