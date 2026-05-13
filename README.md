# TaskFlow v5

## Нові фічі
- 🌐 **Відкриті задачі** — будь-хто може переглядати і брати задачі (як фріланс)
- 🎨 **Новий дизайн** — повністю перероблений темний інтерфейс
- ⚡ **Kanban drag & drop** — переміщення без перезавантаження, тост-сповіщення
- 💬 **Коментарі з відповідями** — треди + @mentions
- 🏷 **Теги в задачах** — @тегання користувачів
- Task Tracking (замість старого бейджа)

## Запуск
```bash
python -m venv venv
venv\Scripts\activate      # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
Сайт: http://127.0.0.1:8000
