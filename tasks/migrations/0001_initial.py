from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='Назва')),
                ('description', models.TextField(blank=True, verbose_name='Опис')),
                ('status', models.CharField(
                    choices=[('new', 'Нова'), ('in_progress', 'В процесі'), ('done', 'Виконана')],
                    default='new', max_length=20, verbose_name='Статус'
                )),
                ('priority', models.CharField(
                    choices=[('low', 'Низький'), ('medium', 'Середній'), ('high', 'Високий')],
                    default='medium', max_length=10, verbose_name='Пріоритет'
                )),
                ('due_date', models.DateField(blank=True, null=True, verbose_name='Дедлайн')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Створено')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Оновлено')),
                ('owner', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='tasks',
                    to='auth.user',
                    verbose_name='Власник'
                )),
            ],
            options={
                'verbose_name': 'Задача',
                'verbose_name_plural': 'Задачі',
                'ordering': ['-created_at'],
            },
        ),
    ]
