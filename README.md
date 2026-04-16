# Task Tracker — Django проєкт

Система трекінгу задач з підтримкою кількох користувачів, фільтрацією та управлінням доступом.

## Технічний стек

- Python 3.10+
- Django 4.x
- Bootstrap 4.5
- SQLite

## Встановлення та запуск

### 1. Клонування репозиторію

```bash
git clone <your-repo-url>
cd task_tracker
```

### 2. Створення та активація віртуального оточення

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python -m venv venv
source venv/bin/activate
```

### 3. Встановлення залежностей

```bash
pip install -r requirements.txt
```

### 4. Міграції бази даних

```bash
python manage.py migrate
```

### 5. Створення суперкористувача

```bash
python manage.py createsuperuser
```

### 6. Запуск сервера

```bash
python manage.py runserver
```

Відкрийте браузер: [http://127.0.0.1:8000/tasks/](http://127.0.0.1:8000/tasks/)

Адмін-панель: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## Структура проєкту

```
task_tracker/
├── task_tracker/        # Головний модуль Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── tasks/               # Додаток задач
│   ├── migrations/
│   ├── templates/
│   │   ├── tasks/
│   │   │   ├── base.html
│   │   │   ├── task_list.html
│   │   │   ├── task_detail.html
│   │   │   ├── task_form.html
│   │   │   └── task_confirm_delete.html
│   │   └── registration/
│   │       └── login.html
│   ├── admin.py
│   ├── forms.py
│   ├── mixins.py
│   ├── models.py
│   ├── urls.py
│   └── views.py
├── manage.py
├── requirements.txt
└── README.md
```

## Функціонал

- ✅ Реєстрація/вхід користувачів
- ✅ Список задач поточного користувача
- ✅ Деталі задачі
- ✅ Створення задачі (автоматично встановлюється власник)
- ✅ Редагування задачі (тільки власник)
- ✅ Видалення задачі (тільки власник)
- ✅ Фільтрація за статусом, пріоритетом та пошуком
- ✅ Статистика (всього / в процесі / виконано)
- ✅ Адмін-панель
- ✅ Пагінація

## Моделі

### Task (Задача)
| Поле        | Тип              | Опис                        |
|-------------|------------------|-----------------------------|
| title       | CharField(200)   | Назва задачі                |
| description | TextField        | Опис                        |
| status      | CharField        | new / in_progress / done    |
| priority    | CharField        | low / medium / high         |
| owner       | ForeignKey(User) | Власник                     |
| due_date    | DateField        | Дедлайн (необов'язково)     |
| created_at  | DateTimeField    | Дата створення (авто)       |
| updated_at  | DateTimeField    | Дата оновлення (авто)       |

## URLs

| URL                      | View             | Опис                |
|--------------------------|------------------|---------------------|
| /tasks/                  | TaskListView     | Список задач        |
| /tasks/create/           | TaskCreateView   | Створення задачі    |
| /tasks/<pk>/             | TaskDetailView   | Деталі задачі       |
| /tasks/<pk>/edit/        | TaskUpdateView   | Редагування         |
| /tasks/<pk>/delete/      | TaskDeleteView   | Видалення           |
| /accounts/login/         | Django auth      | Вхід                |
| /accounts/logout/        | Django auth      | Вихід               |
| /admin/                  | Django admin     | Адмін-панель        |
