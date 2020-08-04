import sqlite3
from hashlib import sha256

ADMIN_PASSWORD = "Mathews32"


def create_password(admin_pass, service_name, pass_key):
    return sha256(admin_pass.encode('utf-8') + service_name.encode('utf-8') + pass_key.encode('utf-8')).hexdigest()[:15]


def get_hex_key(admin_pass, service_name):
    return sha256(admin_pass.encode('utf-8') + service_name.encode('utf-8')).hexdigest()


conn = sqlite3.connect('pass_manager.db')


def get_admin_password():
    cursor = conn.execute(''' SELECT name FROM sqlite_master WHERE type = 'table' AND name= 'KEYS' ''')
    if cursor.fetchone() is None:
        return None
    else:
        admin_cursor = conn.execute('SELECT ADMIN_PASS FROM KEYS')
        admin_password = admin_cursor.fetchall()
        return admin_password[0][0]


def set_admin_password(new_admin_pass):
    conn.execute('INSERT INTO KEYS (ADMIN_PASS) VALUES (?)', (new_admin_pass,))
    conn.commit()


admin_pass = get_admin_password()
if admin_pass is None:
    connect = input("Create admin password: ")
    conn.execute(
        """CREATE TABLE KEYS (PASS_KEY TEXT PRIMARY KEY, SERVICE_NAME TEXT, ADMIN_PASS TEXT);""")
    set_admin_password(connect)
else:
    connect = input("Enter admin password: ")

    while connect != get_admin_password():
        print("Incorrect password")
        connect = input("Enter admin password: ")
        if connect == "q":
            break


def get_password(admin_pass, service_name):
    secret_key = get_hex_key(admin_pass, service_name)
    cursor = conn.execute('SELECT * FROM KEYS WHERE PASS_KEY =' + "'" + secret_key + "'")

    pass_key = ""
    for row in cursor:
        pass_key = row[0]

    return create_password(admin_pass, service_name, pass_key)


def add_password(admin_pass, service_name):
    secret_key = get_hex_key(admin_pass, service_name)
    conn.execute('INSERT INTO KEYS (PASS_KEY, SERVICE_NAME) VALUES (%s, %s);' % (
        "'" + secret_key + "'", "'" + service_name + "'"))
    conn.commit()

    return create_password(admin_pass, service_name, secret_key)


def delete_password(service_name):
    conn.execute('DELETE FROM KEYS WHERE SERVICE_NAME = ?', (service_name,))
    conn.commit()

    cursor = conn.execute('SELECT * FROM KEYS WHERE SERVICE_NAME = ?', (service_name,))
    records = cursor.fetchall()
    if len(records) == 0:
        print("\nService " + "\"" + service_name.capitalize() + "\"" + " deleted SUCCESSFULLY")
    else:
        print("\nFailed to delete " + "\"" + service_name.capitalize() + "\"" + " from records")


if connect == get_admin_password():
    try:
        conn.execute(
            """CREATE TABLE KEYS (PASS_KEY TEXT PRIMARY KEY, SERVICE_NAME TEXT, ADMIN_PASS TEXT);""")
        print("Your safe has been created!\nWhat would you like to do?")
    except:
        print("You already have a safe, what would you like to do")
    while True:
        print("-" * 15)
        print("COMMANDS:")
        print("q: Quit program")
        print("sp: Store password")
        print("gp: Get password")
        print("dp: Delete password")
        print("-" * 15)
        input_ = input(":")

        if input_.lower() == "q":  # QUIT
            break
        if input_.lower() == "sp":  # STORE PASSWORD
            service = input("What is the name of the service: ")
            print("\n" + "\"" + service + "\"" + " password created: \n" + add_password(ADMIN_PASSWORD, service))
        if input_.lower() == "gp":  # GET PASSWORD
            print("List of services:")

            cursor = conn.execute('SELECT SERVICE_NAME FROM KEYS')
            service_name = ""
            i = 1
            for row in cursor:
                service_name = row[0]
                print(str(i) + ". " + service_name)
                i += 1

            service = input("Select a service: ")

            cursor = conn.execute('SELECT EXISTS(SELECT 1 FROM KEYS WHERE SERVICE_NAME = ?)', (service,))
            service_exists = cursor.fetchall()  # Puts data from SELECT query into list of tuples

            if service_exists[0][0] == 0:
                print("\nService " + "\"" + service + "\"" + " doesn't exist.")
            else:
                print("\n" + "\"" + service + "\"" + " password: \n" + get_password(ADMIN_PASSWORD, service))
        if input_.lower() == "dp":  # DELETE PASSWORD
            print("List of services:")

            cursor = conn.execute('SELECT SERVICE_NAME FROM KEYS')
            service_name = ""
            i = 1
            for row in cursor:
                service_name = row[0]
                print(str(i) + ". " + service_name)
                i += 1

            service = input("Select a service: ")
            cursor = conn.execute('SELECT EXISTS(SELECT 1 FROM KEYS WHERE SERVICE_NAME = ?)', (service,))
            service_exists = cursor.fetchall()  # Puts data from SELECT query into list of tuples

            if service_exists[0][0] == 0:
                print("\nService " + "\"" + service + "\"" + " doesn't exist.")
            else:
                delete_password(service)