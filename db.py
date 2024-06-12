import mysql.connector

config = {
    'user': 'root',
    'password': '',
    'host': 'localhost',
    'database': 'ryanair'
}

def connect_to_db(config):
    try:
        conn = mysql.connector.connect(**config)
        if conn.is_connected():
            print('Connected to MySQL database')
    except mysql.connector.Error as e:
        print(e)
        exit(1)
    return conn

def insert_data(conn, data):
    cursor = conn.cursor()
    query = "INSERT INTO flights (flight_number, departure, arrival, flight_date, price) VALUES (%s, %s, %s, %s, %s)"
    cursor.execute(query, data)
    conn.commit()
    cursor.close()

def get_latest_flight_price(date, frm="AGA", to="TNG"):
    cursor = conn.cursor()
    query = "SELECT price FROM flights WHERE departure=%s AND arrival=%s AND flight_date=%s ORDER BY created_at DESC LIMIT 1"
    cursor.execute(query, (frm, to, date))
    price = cursor.fetchone()
    cursor.close()
    if price:
        return float(price[0])
    else:
        return None


def get_data(conn):
    cursor = conn.cursor()
    query = "SELECT * FROM flights"
    cursor.execute(query)
    rows = cursor.fetchall()
    cursor.close()
    return rows


if __name__ == '__main__':
    conn = connect_to_db(config)

    latest = get_latest_flight_price("2024-06-22")
    print(latest)
