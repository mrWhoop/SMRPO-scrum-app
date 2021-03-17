# Generated by Django 2.2.4 on 2021-03-17 22:06

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='product_owner', to=settings.AUTH_USER_MODEL)),
                ('scrum_master', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='scrum_master', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Sprint',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='scrum_app.Project')),
            ],
        ),
        migrations.CreateModel(
            name='Story',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timeCost', models.DecimalField(decimal_places=2, max_digits=5, null=True)),
                ('timeSpent', models.DecimalField(decimal_places=2, max_digits=5, null=True)),
                ('userConfirmed', models.BooleanField(default=False)),
                ('comment', models.TextField(null=True)),
                ('assignedUser', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='scrum_app.Project')),
                ('sprint', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='scrum_app.Sprint')),
            ],
        ),
        migrations.CreateModel(
            name='DevTeamMember',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('projectId', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='scrum_app.Project')),
                ('userId', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
