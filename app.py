import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

# Carga las variables de entorno desde .env
load_dotenv()

# Crear instancia de la aplicación Flask
app = Flask(__name__)

# -----------------
# Configuración de la Base de Datos PostgreSQL
# -----------------
# La variable de entorno DATABASE_URL debe estar definida en tu archivo .env
DATABASE_URL = os.environ.get("DATABASE_URL")

# Si no se encuentra la variable de entorno, la aplicación no debe iniciar.
if not DATABASE_URL:
    raise RuntimeError("Define la variable de entorno 'DATABASE_URL' en tu archivo .env (o entorno de despliegue) apuntando a PostgreSQL.")
    
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# -----------------
# Modelo de la base de datos (Team)
# -----------------
class Team(db.Model):
    __tablename__ = 'teams' 
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    ciudad = db.Column(db.String(100))
    estadio = db.Column(db.String(100))
    entrenador = db.Column(db.String(100))
    
    def to_dict(self):
        """Convierte el objeto Team en un diccionario para serialización JSON."""
        return {
            'id': self.id,
            'nombre': self.nombre,
            'ciudad': self.ciudad,
            'estadio': self.estadio,
            'entrenador': self.entrenador
        }

# Asegura que las tablas existan al iniciar la aplicación
with app.app_context():
    db.create_all()

# -----------------
# Endpoints de la API REST para Teams (CRUD)
# -----------------

# GET / : Ruta Raíz
@app.route('/', methods=['GET'])
def index():
    return jsonify({
        'msg': '⚽️ API REST de Equipos de Fútbol activa',
        'rutas_disponibles': {
            'GET todos / POST nuevo': '/teams',
            'GET, PUT, DELETE por ID': '/teams/<id>'
        }
    })

# GET /teams: Obtener todos los equipos
@app.route('/teams', methods=['GET'])
def get_teams():
    teams = Team.query.all()
    lista_equipos = [team.to_dict() for team in teams]
    return jsonify(lista_equipos)
    
# GET /teams/<id>: Obtener un equipo por ID
@app.route('/teams/<int:id>', methods=['GET'])
def get_team(id):
    team = Team.query.get(id)
    if team is None:
        return jsonify ({'msg':'Equipo no encontrado'}), 404
    return jsonify(team.to_dict())

# 🔴 FUNCIÓN CORREGIDA: POST /teams: Agregar un nuevo equipo (CREATE)
@app.route('/teams', methods=['POST'])
def create_team():
    data = request.get_json()
    
    # 400 Bad Request si falta 'nombre'
    if not data or 'nombre' not in data:
        return jsonify({'msg': 'Faltan campos requeridos (nombre)'}), 400

    nuevo_equipo = Team(
        # SE ELIMINÓ la referencia a 'no_control' para evitar el KeyError
        nombre = data['nombre'],
        ciudad = data.get('ciudad'),
        estadio = data.get('estadio'),
        entrenador = data.get('entrenador'),
    )
    
    try:
        db.session.add(nuevo_equipo)
        db.session.commit()
        # 201 Created si es exitoso
        return jsonify ({'msg': f'Equipo "{nuevo_equipo.nombre}" agregado correctamente',
                         'equipo': nuevo_equipo.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        # 500 Internal Server Error para otros errores de DB/código
        print(f"Error al crear equipo: {e}") 
        return jsonify({'msg': 'Error al agregar el equipo', 'error': str(e)}), 500

# PUT /teams/<id>: Actualizar un equipo existente (UPDATE)
@app.route('/teams/<int:id>', methods=['PUT'])
def update_team(id):
    team = Team.query.get(id)
    if team is None:
        return jsonify ({'msg':'Equipo no encontrado'}), 404
        
    data = request.get_json()
    
    team.nombre = data.get('nombre', team.nombre)
    team.ciudad = data.get('ciudad', team.ciudad)
    team.estadio = data.get('estadio', team.estadio)
    team.entrenador = data.get('entrenador', team.entrenador)
    
    try:
        db.session.commit()
        return jsonify ({'msg': f'Equipo "{team.nombre}" actualizado correctamente', 
                         'equipo': team.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': 'Error al actualizar el equipo', 'error': str(e)}), 500

# DELETE /teams/<id>: Eliminar un equipo (DELETE)
@app.route('/teams/<int:id>', methods=['DELETE'])
def delete_team(id):
    team = Team.query.get(id)
    if team is None:
        return jsonify ({'msg':'Equipo no encontrado'}), 404
    
    nombre_equipo = team.nombre
    
    try:
        db.session.delete(team)
        db.session.commit()
        return jsonify ({'msg': f'Equipo "{nombre_equipo}" eliminado correctamente'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': 'Error al eliminar el equipo', 'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5001)), debug=True)