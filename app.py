from flask import Flask, render_template, request, redirect, url_for, flash
import psycopg2
from datetime import datetime
from config import DB_CONFIG
import base64

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Отключаем кэширование для разработки


# Подключение к БД
def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)


# Главная страница с поиском
@app.route('/', methods=['GET', 'POST'])
def index():
    conn = get_db_connection()
    cur = conn.cursor()

    # Получаем уникальные города для фильтра
    cur.execute("SELECT DISTINCT city FROM venues ORDER BY city")
    cities = [row[0] for row in cur.fetchall()]

    # Получаем артистов для фильтра
    cur.execute("SELECT id, name FROM artists ORDER BY name")
    artists = [{'id': row[0], 'name': row[1]} for row in cur.fetchall()]

    results = []
    if request.method == 'POST':
        # Параметры поиска
        artist_id = request.form.get('artist_id')
        city = request.form.get('city')
        date_str = request.form.get('date')

        # Формируем SQL-запрос
        query = """
                SELECT concerts.date, \
                       artists.name AS artist_name, \
                       tours.name   AS tour_name, \
                       venues.name  AS venue_name, \
                       venues.city, \
                       concerts.ticket_price,
                       get_remaining_tickets(concerts.id) AS remaining_tickets
                FROM concerts
                         JOIN tours ON concerts.tour_id = tours.id
                         JOIN artists ON tours.artist_id = artists.id
                         JOIN venues ON concerts.venue_id = venues.id
                WHERE 1 = 1 \
                """

        params = []

        if artist_id and artist_id != 'all':
            query += " AND artists.id = %s"
            params.append(artist_id)

        if city and city != 'all':
            query += " AND venues.city = %s"
            params.append(city)

        if date_str:
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                query += " AND DATE(concerts.date) = %s"
                params.append(date_obj)
            except ValueError:
                flash('Неверный формат даты! Используйте ГГГГ-ММ-ДД', 'error')

        query += " ORDER BY concerts.date ASC"

        cur.execute(query, params)
        columns = [desc[0] for desc in cur.description]
        results = [dict(zip(columns, row)) for row in cur.fetchall()]

    cur.close()
    conn.close()
    return render_template('index.html',
                           cities=cities,
                           artists=artists,
                           concerts=results)


# ... (прежний код поиска концертов) ...


# CRUD для Artists
@app.route('/artists')
def artists():
    return entity_list('artists', 'Артисты', ['id', 'name', 'country', 'genre'])


@app.route('/artists/create', methods=['GET', 'POST'])
def create_artist():
    return entity_form('artists', 'Добавить артиста', None, ['name', 'country', 'genre', 'photo'])


@app.route('/artists/edit/<int:id>', methods=['GET', 'POST'])
def edit_artist(id):
    return entity_form('artists', 'Редактировать артиста', id, ['name', 'country', 'genre', 'photo'])


@app.route('/artists/delete/<int:id>')
def delete_artist(id):
    return delete_entity('artists', id, 'artists')


# Аналогичные маршруты для других сущностей (tours, venues, concerts, tickets)
# ...
# CRUD для Tours
@app.route('/tours')
def tours():
    conn = get_db_connection()
    cur = conn.cursor()

    # Запрос с JOIN для получения имени артиста вместо artist_id
    cur.execute("""
                SELECT t.id, a.name AS artist_name, t.name, t.start_date, t.end_date
                FROM tours t
                         JOIN artists a ON t.artist_id = a.id
                """)
    rows = cur.fetchall()

    # Получаем названия колонок
    columns = [desc[0] for desc in cur.description]

    cur.close()
    conn.close()

    return render_template('list.html',
                           entity_name='tours',
                           title='Туры',
                           columns=columns,
                           rows=rows)


@app.route('/tours/create', methods=['GET', 'POST'])
def create_tour():
    return entity_form('tours', 'Добавить тур', None, ['artist_id', 'name', 'start_date', 'end_date'])

@app.route('/tours/edit/<int:id>', methods=['GET', 'POST'])
def edit_tour(id):
    return entity_form('tours', 'Редактировать тур', id, ['artist_id', 'name', 'start_date', 'end_date'])

@app.route('/tours/delete/<int:id>')
def delete_tour(id):
    return delete_entity('tours', id, 'tours')

# CRUD для Venues
@app.route('/venues')
def venues():
    return entity_list('venues', 'Площадки', ['id', 'name', 'country', 'city', 'address'])

@app.route('/venues/create', methods=['GET', 'POST'])
def create_venue():
    return entity_form('venues', 'Добавить площадку', None, ['name', 'country', 'city', 'address'])

@app.route('/venues/edit/<int:id>', methods=['GET', 'POST'])
def edit_venue(id):
    return entity_form('venues', 'Редактировать площадку', id, ['name', 'country', 'city', 'address'])

@app.route('/venues/delete/<int:id>')
def delete_venue(id):
    return delete_entity('venues', id, 'venues')

# CRUD для Concerts
@app.route('/concerts')
def concerts():
    conn = get_db_connection()
    cur = conn.cursor()

    # Запрос с JOIN для получения названий вместо ID
    cur.execute("""
                SELECT c.id,
                       t.name AS tour_name,
                       v.name AS venue_name,
                       c.date,
                       c.ticket_price,
                       get_remaining_tickets(c.id) AS remaining_tickets
                FROM concerts c
                         JOIN tours t ON c.tour_id = t.id
                         JOIN venues v ON c.venue_id = v.id
                """)
    rows = cur.fetchall()

    # Получаем названия колонок
    columns = [desc[0] for desc in cur.description]

    cur.close()
    conn.close()

    return render_template('list.html',
                           entity_name='concerts',
                           title='Концерты',
                           columns=columns,
                           rows=rows)

@app.route('/concerts/create', methods=['GET', 'POST'])
def create_concert():
    return entity_form('concerts', 'Добавить концерт', None, ['tour_id', 'venue_id', 'date', 'ticket_price'])

@app.route('/concerts/edit/<int:id>', methods=['GET', 'POST'])
def edit_concert(id):
    return entity_form('concerts', 'Редактировать концерт', id, ['tour_id', 'venue_id', 'date', 'ticket_price'])

@app.route('/concerts/delete/<int:id>')
def delete_concert(id):
    return delete_entity('concerts', id, 'concerts')

# CRUD для Tickets
@app.route('/tickets')
def tickets():
    conn = get_db_connection()
    cur = conn.cursor()

    # Запрос с JOIN для получения информации о концерте
    cur.execute("""
                SELECT t.id,
                       CONCAT(a.name, ' @ ', v.name, ' (', TO_CHAR(c.date, 'DD.MM.YYYY'), ')') AS concert_info,
                       t.price,
                       t.is_sold,
                       t.sale_date
                FROM tickets t
                         JOIN concerts c ON t.concert_id = c.id
                         JOIN tours tr ON c.tour_id = tr.id
                         JOIN artists a ON tr.artist_id = a.id
                         JOIN venues v ON c.venue_id = v.id
                """)
    rows = cur.fetchall()

    # Получаем названия колонок
    columns = [desc[0] for desc in cur.description]

    cur.close()
    conn.close()

    return render_template('list.html',
                           entity_name='tickets',
                           title='Билеты',
                           columns=columns,
                           rows=rows)

@app.route('/tickets/create', methods=['GET', 'POST'])
def create_ticket():
    return entity_form('tickets', 'Добавить билет', None, ['concert_id', 'price', 'is_sold', 'sale_date'])

@app.route('/tickets/edit/<int:id>', methods=['GET', 'POST'])
def edit_ticket(id):
    return entity_form('tickets', 'Редактировать билет', id, ['concert_id', 'price', 'is_sold', 'sale_date'])

@app.route('/tickets/delete/<int:id>')
def delete_ticket(id):
    return delete_entity('tickets', id, 'tickets')

# Общие функции для CRUD
def entity_list(entity_name, title, columns):
    conn = get_db_connection()
    cur = conn.cursor()

    # Получаем данные
    cur.execute(f"SELECT * FROM {entity_name}")
    rows = cur.fetchall()

    # Получаем названия колонок
    cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{entity_name}'")
    db_columns = [col[0] for col in cur.fetchall()]

    cur.close()
    conn.close()

    return render_template('list.html',
                           entity_name=entity_name,
                           title=title,
                           columns=db_columns,
                           rows=rows)


def entity_form(entity_name, title, id, fields):
    conn = get_db_connection()
    cur = conn.cursor()

    # Получаем данные записи если редактирование
    record = None
    if id:
        cur.execute(f"SELECT * FROM {entity_name} WHERE id = %s", (id,))
        row = cur.fetchone()
        if row:
            # Преобразуем в словарь для удобства
            col_names = [desc[0] for desc in cur.description]
            record = dict(zip(col_names, row))

    # Для связанных сущностей (выпадающие списки)
    related_data = {}
    if entity_name == 'tours':
        cur.execute("SELECT id, name FROM artists")
        related_data['artist'] = cur.fetchall()
    elif entity_name == 'concerts':
        cur.execute("SELECT id, name FROM tours")
        related_data['tour'] = cur.fetchall()
        cur.execute("SELECT id, name FROM venues")
        related_data['venue'] = cur.fetchall()
    elif entity_name == 'tickets':
        cur.execute("""
                    SELECT c.id,
                           CONCAT(a.name, ' @ ', v.name, ' (', TO_CHAR(c.date, 'DD.MM.YYYY'), ')')
                    FROM concerts c
                             JOIN tours t ON c.tour_id = t.id
                             JOIN artists a ON t.artist_id = a.id
                             JOIN venues v ON c.venue_id = v.id
                    """)
        related_data['concert'] = cur.fetchall()

    if request.method == 'POST':
        values = []
        for field in fields:
            if field == 'photo' and entity_name == 'artists':
                photo_file = request.files.get('photo')
                if photo_file and photo_file.filename:
                    values.append(photo_file.read())
                else:
                    values.append(record['photo'] if record and 'photo' in record else None)
            elif field == 'is_sold':
                values.append('is_sold' in request.form)
            elif field == 'sale_date':
                date_val = request.form.get(field)
                values.append(date_val if date_val else None)
            else:
                values.append(request.form.get(field))

        try:
            if id:  # Редактирование
                set_clause = ", ".join([f"{field} = %s" for field in fields])
                query = f"UPDATE {entity_name} SET {set_clause} WHERE id = %s"
                values.append(id)
                cur.execute(query, values)
            else:  # Создание
                columns = ", ".join(fields)
                placeholders = ", ".join(["%s"] * len(fields))
                query = f"INSERT INTO {entity_name} ({columns}) VALUES ({placeholders})"
                cur.execute(query, values)

            conn.commit()
            flash('Данные сохранены успешно!', 'success')
            return redirect(url_for(entity_name))
        except Exception as e:
            conn.rollback()
            flash(f'Ошибка: {str(e)}', 'danger')

    cur.close()
    conn.close()

    return render_template('form.html',
                           entity_name=entity_name,
                           title=title,
                           fields=fields,
                           record=record,  # Передаем данные записи
                           related_data=related_data,
                           id=id)

def delete_entity(entity_name, id, redirect_to):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute(f"DELETE FROM {entity_name} WHERE id = %s", (id,))
        conn.commit()
        flash('Запись успешно удалена!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Ошибка при удалении: {str(e)}', 'danger')

    cur.close()
    conn.close()
    return redirect(url_for(redirect_to))

@app.template_filter('b64encode')
def b64encode_filter(data):
    if data:
        return base64.b64encode(data).decode('utf-8')
    return None

if __name__ == '__main__':
    app.run(debug=True)

'''
from flask import Flask, render_template, request, redirect, url_for, flash
import psycopg2
from datetime import datetime
from config import DB_CONFIG
import base64

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Отключаем кэширование для разработки


# Подключение к БД
def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)


# Главная страница с поиском
@app.route('/', methods=['GET', 'POST'])
def index():
    conn = get_db_connection()
    cur = conn.cursor()

    # Получаем уникальные города для фильтра
    cur.execute("SELECT DISTINCT city FROM venues ORDER BY city")
    cities = [row[0] for row in cur.fetchall()]

    # Получаем артистов для фильтра
    cur.execute("SELECT id, name FROM artists ORDER BY name")
    artists = [{'id': row[0], 'name': row[1]} for row in cur.fetchall()]

    results = []
    if request.method == 'POST':
        # Параметры поиска
        artist_id = request.form.get('artist_id')
        city = request.form.get('city')
        date_str = request.form.get('date')

        # Формируем SQL-запрос
        query = """
                SELECT concerts.date, 
                       artists.name AS artist_name, 
                       tours.name AS tour_name, 
                       venues.name AS venue_name, 
                       venues.city, 
                       concerts.ticket_price,
                       get_remaining_tickets(concerts.id) AS remaining_tickets
                FROM concerts
                         JOIN tours ON concerts.tour_id = tours.id
                         JOIN artists ON tours.artist_id = artists.id
                         JOIN venues ON concerts.venue_id = venues.id
                WHERE 1 = 1 
                """

        params = []

        if artist_id and artist_id != 'all':
            query += " AND artists.id = %s"
            params.append(artist_id)

        if city and city != 'all':
            query += " AND venues.city = %s"
            params.append(city)

        if date_str:
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                query += " AND DATE(concerts.date) = %s"
                params.append(date_obj)
            except ValueError:
                flash('Неверный формат даты! Используйте ГГГГ-ММ-ДД', 'error')

        query += " ORDER BY concerts.date ASC"

        cur.execute(query, params)
        columns = [desc[0] for desc in cur.description]
        results = [dict(zip(columns, row)) for row in cur.fetchall()]

    cur.close()
    conn.close()
    return render_template('index.html',
                           cities=cities,
                           artists=artists,
                           concerts=results)


# CRUD для Artists
@app.route('/artists')
def artists():
    return entity_list('artists', 'Артисты', ['id', 'name', 'country', 'genre'])


@app.route('/artists/create', methods=['GET', 'POST'])
def create_artist():
    return entity_form('artists', 'Добавить артиста', None, ['name', 'country', 'genre'])


@app.route('/artists/edit/<int:id>', methods=['GET', 'POST'])
def edit_artist(id):
    return entity_form('artists', 'Редактировать артиста', id, ['name', 'country', 'genre'])


@app.route('/artists/delete/<int:id>')
def delete_artist(id):
    return delete_entity('artists', id, 'artists')


# CRUD для Tours
@app.route('/tours')
def tours():
    conn = get_db_connection()
    cur = conn.cursor()

    # Запрос с JOIN для получения имени артиста вместо artist_id
    cur.execute("""
                SELECT t.id, a.name AS artist_name, t.name, t.start_date, t.end_date
                FROM tours t
                         JOIN artists a ON t.artist_id = a.id
                """)
    rows = cur.fetchall()

    # Получаем названия колонок
    columns = [desc[0] for desc in cur.description]

    cur.close()
    conn.close()

    return render_template('list.html',
                           entity_name='tours',
                           title='Туры',
                           columns=columns,
                           rows=rows)


@app.route('/tours/create', methods=['GET', 'POST'])
def create_tour():
    return entity_form('tours', 'Добавить тур', None, ['artist_id', 'name', 'start_date', 'end_date'])

@app.route('/tours/edit/<int:id>', methods=['GET', 'POST'])
def edit_tour(id):
    return entity_form('tours', 'Редактировать тур', id, ['artist_id', 'name', 'start_date', 'end_date'])


@app.route('/tours/delete/<int:id>')
def delete_tour(id):
    return delete_entity('tours', id, 'tours')


# CRUD для Venues
@app.route('/venues')
def venues():
    return entity_list('venues', 'Площадки', ['id', 'name', 'country', 'city', 'address'])


@app.route('/venues/create', methods=['GET', 'POST'])
def create_venue():
    return entity_form('venues', 'Добавить площадку', None, ['name', 'country', 'city', 'address'])


@app.route('/venues/edit/<int:id>', methods=['GET', 'POST'])
def edit_venue(id):
    return entity_form('venues', 'Редактировать площадку', id, ['name', 'country', 'city', 'address'])


@app.route('/venues/delete/<int:id>')
def delete_venue(id):
    return delete_entity('venues', id, 'venues')


# CRUD для Concerts
@app.route('/concerts')
def concerts():
    conn = get_db_connection()
    cur = conn.cursor()

    # Запрос с JOIN для получения названий вместо ID
    cur.execute("""
                SELECT c.id,
                       t.name AS tour_name,
                       v.name AS venue_name,
                       c.date,
                       c.ticket_price,
                       get_remaining_tickets(c.id) AS remaining_tickets
                FROM concerts c
                         JOIN tours t ON c.tour_id = t.id
                         JOIN venues v ON c.venue_id = v.id
                """)
    rows = cur.fetchall()

    # Получаем названия колонок
    columns = [desc[0] for desc in cur.description]

    cur.close()
    conn.close()

    return render_template('list.html',
                           entity_name='concerts',
                           title='Концерты',
                           columns=columns,
                           rows=rows)


@app.route('/concerts/create', methods=['GET', 'POST'])
def create_concert():
    return entity_form('concerts', 'Добавить концерт', None, ['tour_id', 'venue_id', 'date', 'ticket_price'])


@app.route('/concerts/edit/<int:id>', methods=['GET', 'POST'])
def edit_concert(id):
    return entity_form('concerts', 'Редактировать концерт', id, ['tour_id', 'venue_id', 'date', 'ticket_price'])


@app.route('/concerts/delete/<int:id>')
def delete_concert(id):
    return delete_entity('concerts', id, 'concerts')


# CRUD для Tickets
@app.route('/tickets')
def tickets():
    conn = get_db_connection()
    cur = conn.cursor()

    # Запрос с JOIN для получения информации о концерте
    cur.execute("""
                SELECT t.id,
                       CONCAT(a.name, ' @ ', v.name, ' (', TO_CHAR(c.date, 'DD.MM.YYYY'), ')') AS concert_info,
                       t.price,
                       t.is_sold,
                       t.sale_date
                FROM tickets t
                         JOIN concerts c ON t.concert_id = c.id
                         JOIN tours tr ON c.tour_id = tr.id
                         JOIN artists a ON tr.artist_id = a.id
                         JOIN venues v ON c.venue_id = v.id
                """)
    rows = cur.fetchall()

    # Получаем названия колонок
    columns = [desc[0] for desc in cur.description]

    cur.close()
    conn.close()

    return render_template('list.html',
                           entity_name='tickets',
                           title='Билеты',
                           columns=columns,
                           rows=rows)


@app.route('/tickets/create', methods=['GET', 'POST'])
def create_ticket():
    return entity_form('tickets', 'Добавить билет', None, ['concert_id', 'price', 'is_sold', 'sale_date'])


@app.route('/tickets/edit/<int:id>', methods=['GET', 'POST'])
def edit_ticket(id):
    return entity_form('tickets', 'Редактировать билет', id, ['concert_id', 'price', 'is_sold', 'sale_date'])


@app.route('/tickets/delete/<int:id>')
def delete_ticket(id):
    return delete_entity('tickets', id, 'tickets')


# Общие функции для CRUD
def entity_list(entity_name, title, columns):
    conn = get_db_connection()
    cur = conn.cursor()

    # Получаем данные
    cur.execute(f"SELECT * FROM {entity_name}")
    rows = cur.fetchall()

    # Получаем названия колонок
    cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{entity_name}'")
    db_columns = [col[0] for col in cur.fetchall()]

    cur.close()
    conn.close()

    return render_template('list.html',
                           entity_name=entity_name,
                           title=title,
                           columns=db_columns,
                           rows=rows)


def entity_form(entity_name, title, id, fields):
    conn = get_db_connection()
    cur = conn.cursor()

    # Получаем данные записи если редактирование
    record = None
    if id:
        cur.execute(f"SELECT * FROM {entity_name} WHERE id = %s", (id,))
        row = cur.fetchone()
        if row:
            # Преобразуем в словарь для удобства
            col_names = [desc[0] for desc in cur.description]
            record = dict(zip(col_names, row))

    # Для связанных сущностей (выпадающие списки)
    related_data = {}
    if entity_name == 'tours':
        cur.execute("SELECT id, name FROM artists")
        related_data['artists'] = cur.fetchall()
    elif entity_name == 'concerts':
        cur.execute("SELECT id, name FROM tours")
        related_data['tours'] = cur.fetchall()
        cur.execute("SELECT id, name FROM venues")
        related_data['venues'] = cur.fetchall()
    elif entity_name == 'tickets':
        cur.execute("""
                    SELECT c.id,
                           CONCAT(a.name, ' @ ', v.name, ' (', TO_CHAR(c.date, 'DD.MM.YYYY'), ')')
                    FROM concerts c
                             JOIN tours t ON c.tour_id = t.id
                             JOIN artists a ON t.artist_id = a.id
                             JOIN venues v ON c.venue_id = v.id
                    """)
        related_data['concerts'] = cur.fetchall()

    if request.method == 'POST':
        # Обработка отправки формы
        values = []
        for field in fields:
            values.append(request.form.get(field))

        try:
            if id:  # Редактирование
                set_clause = ", ".join([f"{field} = %s" for field in fields])
                query = f"UPDATE {entity_name} SET {set_clause} WHERE id = %s"
                values.append(id)
                cur.execute(query, values)
            else:  # Создание
                columns = ", ".join(fields)
                placeholders = ", ".join(["%s"] * len(fields))
                query = f"INSERT INTO {entity_name} ({columns}) VALUES ({placeholders})"
                cur.execute(query, values)

            conn.commit()
            flash('Данные сохранены успешно!', 'success')
            return redirect(url_for(entity_name))
        except Exception as e:
            conn.rollback()
            flash(f'Ошибка: {str(e)}', 'danger')

    cur.close()
    conn.close()

    return render_template('form.html',
                           entity_name=entity_name,
                           title=title,
                           fields=fields,
                           record=record,  # Передаем данные записи
                           related_data=related_data,
                           id=id)


def delete_entity(entity_name, id, redirect_to):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute(f"DELETE FROM {entity_name} WHERE id = %s", (id,))
        conn.commit()
        flash('Запись успешно удалена!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Ошибка при удалении: {str(e)}', 'danger')

    cur.close()
    conn.close()
    return redirect(url_for(redirect_to))


@app.template_filter('b64encode')
def b64encode_filter(data):
    if data:
        return base64.b64encode(data).decode('utf-8')
    return None


if __name__ == '__main__':
    app.run(debug=True)
'''


