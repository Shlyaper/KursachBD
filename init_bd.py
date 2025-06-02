import psycopg2
from config import DB_CONFIG


def init_db():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Удаление существующих таблиц
    cur.execute("DROP TABLE IF EXISTS tickets, concerts, venues, tours, artists CASCADE;")

    # Создание таблиц
    cur.execute("""
                CREATE TABLE artists
                (
                    id      SERIAL PRIMARY KEY,
                    name    VARCHAR(100) NOT NULL,
                    country VARCHAR(50),
                    genre   VARCHAR(50),
                    photo   BYTEA
                );

                CREATE TABLE tours
                (
                    id         SERIAL PRIMARY KEY,
                    artist_id  INTEGER REFERENCES artists (id) ON DELETE CASCADE,
                    name       VARCHAR(100) NOT NULL,
                    start_date DATE         NOT NULL,
                    end_date   DATE         NOT NULL
                );

                CREATE TABLE venues
                (
                    id      SERIAL PRIMARY KEY,
                    name    VARCHAR(100) NOT NULL,
                    country VARCHAR(50)  NOT NULL,
                    city    VARCHAR(50)  NOT NULL,
                    address TEXT         NOT NULL
                );

                CREATE TABLE concerts
                (
                    id           SERIAL PRIMARY KEY,
                    tour_id      INTEGER REFERENCES tours (id) ON DELETE CASCADE,
                    venue_id     INTEGER REFERENCES venues (id) ON DELETE CASCADE,
                    date         TIMESTAMP      NOT NULL,
                    ticket_price DECIMAL(10, 2) NOT NULL
                );

                CREATE TABLE tickets
                (
                    id         SERIAL PRIMARY KEY,
                    concert_id INTEGER REFERENCES concerts (id) ON DELETE CASCADE,
                    price      DECIMAL(10, 2) NOT NULL,
                    is_sold    BOOLEAN DEFAULT FALSE,
                    sale_date  DATE
                );
                """)

    # Тестовые данные
    # ... (после создания таблиц)

    # Тестовые данные
    cur.execute("""
                INSERT INTO artists (name, country, genre)
                VALUES ('Imagine Dragons', 'USA', 'Pop Rock'),
                       ('Limp Bizkit', 'USA', 'Nu Metal'),
                       ('Rammstein', 'Germany', 'Industrial Metal');
                """)

    cur.execute("""
                INSERT INTO venues (name, country, city, address)
                VALUES ('Olimpiyskiy', 'Russia', 'Moscow', 'Olimpiyskiy Ave, 16'),
                       ('SKK Peterburgsky', 'Russia', 'Saint Petersburg', 'Peterburgsky Island, 2'),
                       ('Arena Riga', 'Latvia', 'Riga', 'Skantes iela 21');
                """)

    cur.execute("""
                INSERT INTO tours (artist_id, name, start_date, end_date)
                VALUES (1, 'Mercury World Tour', '2023-06-01', '2023-12-31'),
                       (2, 'Still Sucks Tour', '2023-07-15', '2023-11-20'),
                       (3, 'Zeit Tour', '2023-05-10', '2023-10-30');
                """)

    cur.execute("""
                INSERT INTO concerts (tour_id, venue_id, date, ticket_price)
                VALUES (1, 1, '2023-07-10 19:00:00', 4500.00),
                       (1, 2, '2023-08-05 20:00:00', 5000.00),
                       (2, 3, '2023-09-15 21:00:00', 6000.00),
                       (3, 1, '2023-10-20 19:30:00', 7500.00);
                """)

    cur.execute("""
                INSERT INTO tickets (concert_id, price, is_sold, sale_date)
                VALUES (1, 4500.00, TRUE, '2023-06-01'),
                       (1, 4500.00, FALSE, NULL),
                       (2, 5000.00, TRUE, '2023-07-15'),
                       (3, 6000.00, TRUE, '2023-08-20'),
                       (4, 7500.00, FALSE, NULL);
                """)

    # ... (остальной код)
    cur.execute("""
                INSERT INTO artists (name, country, genre)
                VALUES ('Imagine Dragons', 'USA', 'Pop Rock'),
                       ('Limp Bizkit', 'USA', 'Nu Metal'),
                       ('Rammstein', 'Germany', 'Industrial Metal');

                INSERT INTO venues (name, country, city, address)
                VALUES ('Olimpiyskiy', 'Russia', 'Moscow', 'Olimpiyskiy Ave, 16'),
                       ('SKK Peterburgsky', 'Russia', 'Saint Petersburg', 'Peterburgsky Island, 2'),
                       ('Arena Riga', 'Latvia', 'Riga', 'Skantes iela 21');

                INSERT INTO tours (artist_id, name, start_date, end_date)
                VALUES (1, 'Mercury World Tour', '2023-06-01', '2023-12-31'),
                       (2, 'Still Sucks Tour', '2023-07-15', '2023-11-20'),
                       (3, 'Zeit Tour', '2023-05-10', '2023-10-30');

                INSERT INTO concerts (tour_id, venue_id, date, ticket_price)
                VALUES (1, 1, '2023-07-10 19:00:00', 4500.00),
                       (1, 2, '2023-08-05 20:00:00', 5000.00),
                       (2, 3, '2023-09-15 21:00:00', 6000.00),
                       (3, 1, '2023-10-20 19:30:00', 7500.00);
                """)

    conn.commit()
    cur.close()
    conn.close()


if __name__ == '__main__':
    init_db()
    print("Database initialized successfully!")