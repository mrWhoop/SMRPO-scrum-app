# Generated by Django 2.2.4 on 2021-04-07 21:27

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
                ('projectName', models.TextField()),
                ('description', models.TextField()),
                ('product_owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='product_owner', to=settings.AUTH_USER_MODEL)),
                ('scrum_master', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='scrum_master', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Sprint',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start', models.DateTimeField()),
                ('end', models.DateTimeField()),
                ('expectedSpeed', models.IntegerField()),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='scrum_app.Project')),
            ],
        ),
        migrations.CreateModel(
            name='Story',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField()),
                ('description', models.TextField()),
                ('priority', models.TextField()),
                ('businessValue', models.IntegerField()),
                ('timeCost', models.DecimalField(decimal_places=2, max_digits=5, null=True)),
                ('timeSpent', models.DecimalField(decimal_places=2, max_digits=5, null=True)),
                ('comment', models.TextField(null=True)),
                ('developmentStatus', models.TextField()),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='scrum_app.Project')),
                ('sprint', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='scrum_app.Sprint')),
            ],
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timeCost', models.DecimalField(decimal_places=2, max_digits=5, null=True)),
                ('time_spent', models.DecimalField(decimal_places=2, max_digits=5, null=True)),
                ('description', models.TextField()),
                ('userConfirmed', models.TextField()),
                ('assignedUser', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('story', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='scrum_app.Story')),
            ],
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.TextField()),
                ('time_posted', models.DateTimeField()),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='scrum_app.Project')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='LastLogin',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('lastLoginTime', models.DateTimeField(null=True)),
                ('user', models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
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
