from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('tasks', '0001_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]
    operations = [
        migrations.CreateModel(
            name='Company',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='Назва компанії')),
                ('username', models.CharField(max_length=50, unique=True, verbose_name='Username')),
                ('description', models.TextField(blank=True)),
                ('avatar_color', models.CharField(default='#7c3aed', max_length=7)),
                ('is_open', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='owned_companies', to='auth.user')),
            ],
            options={'ordering': ['-created_at'], 'verbose_name': 'Компанія', 'verbose_name_plural': 'Компанії'},
        ),
        migrations.CreateModel(
            name='CompanyMembership',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('display_name', models.CharField(max_length=100, verbose_name="Ім'я у компанії")),
                ('tag', models.CharField(max_length=50, verbose_name='Тег / роль')),
                ('motivation', models.TextField(verbose_name='Що хочу робити')),
                ('status', models.CharField(choices=[('pending','Очікує'),('approved','Прийнято'),('rejected','Відхилено')], default='pending', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('reject_reason', models.TextField(blank=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='memberships', to='tasks.company')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='memberships', to='auth.user')),
                ('reviewed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_memberships', to='auth.user')),
            ],
            options={'ordering': ['-created_at'], 'unique_together': {('company', 'user')}},
        ),
        migrations.AddField(
            model_name='company',
            name='members',
            field=models.ManyToManyField(blank=True, related_name='companies', through='tasks.CompanyMembership', to='auth.user'),
        ),
    ]
