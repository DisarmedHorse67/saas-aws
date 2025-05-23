from flask import Flask, render_template, request, redirect, url_for, flash, session
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# Configuración del administrador
ADMIN_CREDENTIALS = {
    'username': 'admin',
    'password': 'admin123'
}

# Configuración para MySQL
def get_db_connection():
    return pymysql.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password='1234',
        database=os.getenv('DB_NAME', 'saas_db'),
        cursorclass=pymysql.cursors.DictCursor
    )

# Rutas principales
@app.route('/')
def home():
    return render_template('index.html')

# Autenticación
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if (request.form['username'] == ADMIN_CREDENTIALS['username'] and 
            request.form['password'] == ADMIN_CREDENTIALS['password']):
            session['admin_logged_in'] = True
            return redirect(url_for('admin_users'))
        flash('Credenciales incorrectas', 'error')
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('home'))

# Panel de administración
@app.route('/admin/users')
def admin_users():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute('SELECT id, username, email, created_at FROM users')
            users = cursor.fetchall()
            return render_template('admin_users.html', users=users)
    except Exception as e:
        flash(f'Error al obtener usuarios: {str(e)}', 'error')
        return redirect(url_for('home'))
    finally:
        if 'conn' in locals():
            conn.close()

# Operaciones CRUD
@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute('DELETE FROM users WHERE id = %s', (user_id,))
            conn.commit()
            flash('Usuario eliminado correctamente', 'success')
    except Exception as e:
        flash(f'Error al eliminar usuario: {str(e)}', 'error')
    finally:
        if 'conn' in locals():
            conn.close()
    return redirect(url_for('admin_users'))

@app.route('/admin/users/update/<int:user_id>', methods=['POST'])
def update_user(user_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                'UPDATE users SET username = %s, email = %s WHERE id = %s',
                (request.form['username'], request.form['email'], user_id)
            )
            conn.commit()
            flash('Usuario actualizado correctamente', 'success')
    except pymysql.IntegrityError:
        flash('El correo electrónico ya está en uso', 'error')
    except Exception as e:
        flash(f'Error al actualizar usuario: {str(e)}', 'error')
    finally:
        if 'conn' in locals():
            conn.close()
    return redirect(url_for('admin_users'))

# Registro de usuarios
@app.route('/register', methods=['POST'])
def register():
    if not all(key in request.form for key in ['username', 'email', 'password']):
        flash('Todos los campos son requeridos', 'error')
        return redirect(url_for('home'))
    
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                'INSERT INTO users (username, email, password) VALUES (%s, %s, %s)',
                (request.form['username'], request.form['email'], request.form['password'])
            )
            conn.commit()
            flash('Registro exitoso! Ahora puedes iniciar sesión.', 'success')
    except pymysql.IntegrityError:
        flash('El correo electrónico ya está registrado.', 'error')
    except Exception as e:
        flash(f'Error en la base de datos: {e}', 'error')
    finally:
        if 'conn' in locals():
            conn.close()
    return redirect(url_for('home'))

# API
@app.route('/api/users')
def api_users():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute('SELECT id, username, email, created_at FROM users')
            return {'users': cursor.fetchall()}
    except Exception as e:
        return {'error': str(e)}, 500
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    app.run(debug=True)