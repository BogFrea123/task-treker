from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]
    operations = [
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50, verbose_name='Назва')),
                ('color', models.CharField(default='#6366f1', max_length=7, verbose_name='Колір')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tags', to='auth.user')),
            ],
            options={'verbose_name': 'Тег', 'verbose_name_plural': 'Теги', 'unique_together': {('name', 'owner')}},
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=200, verbose_name='Назва')),
                ('description', models.TextField(blank=True, verbose_name='Опис')),
                ('status', models.CharField(choices=[('todo','To Do'),('in_progress','In Progress'),('review','Review'),('done','Done')], default='todo', max_length=20)),
                ('priority', models.CharField(choices=[('low','Low'),('medium','Medium'),('high','High'),('urgent','Urgent')], default='medium', max_length=10)),
                ('due_date', models.DateField(blank=True, null=True, verbose_name='Дедлайн')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tasks', to='auth.user')),
                ('tags', models.ManyToManyField(blank=True, related_name='tasks', to='tasks.tag')),
            ],
            options={'verbose_name': 'Задача', 'verbose_name_plural': 'Задачі', 'ordering': ['-created_at']},
        ),
    ]
