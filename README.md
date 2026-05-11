# TaskFlow v4 — Jira-подібний трекер

## Фічі
- 🏠 **Лендінг** для незареєстрованих (live demo задач)
- 📁 **Проєкти** з учасниками, ключем (PROJ-1)
- 🏃 **Спринти** зі своєю Kanban-дошкою
- 📋 **Kanban** drag & drop для всіх задач
- 💬 **Коментарі** до задач
- ⏱ **Логування часу** (оцінка + залоговані години)
- 👥 **Призначення** задач іншим користувачам
- 🏷 **Теги** з кольором
- 🔍 **Фільтрація** за статусом, пріоритетом, типом, виконавцем
- 🌑 **Темна тема** у стилі Jira/ClickUp

## Запуск
```bash
python -m venv venv
venv\Scripts\activate       # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
Сайт: http://127.0.0.1:8000/
