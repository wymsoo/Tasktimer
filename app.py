from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import exc
from sqlalchemy import create_engine
from datetime import datetime, timedelta



app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///tasks.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# app.config['STATIC_FOLDER'] = 'static'
db = SQLAlchemy(app)

class Task(db.Model):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(nullable=False)
    deadline: Mapped[str] = mapped_column(nullable=True)
    timeleft: Mapped[str] = mapped_column(nullable=True)
    completed: Mapped[bool] = mapped_column(default=False)

    def __repr__(self):
        return f'<Task {self.title}>'
    # def __init__(self, title, deadline, timeleft):
    #     self.title = title
    #     self.deadline = deadline
    #     self.timeleft = timeleft



@app.route('/')
def index():
    return send_from_directory('.', 'app.html')

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    try:
        tasks = Task.query.all()
        task_list = [{"id": task.id, "title": task.title, "deadline": task.deadline, "completed": task.completed, "timeleft": task.timeleft} for task in tasks]
        return jsonify(task_list), 200
    except Exception as e:
        return jsonify({"msg": "Error retrieving tasks", "error": str(e)}), 500

@app.route('/api/tasks', methods=['POST'])
def add_task():
    data = request.json
    try:
        if not data or "title" not in data:
            raise ValueError("Invalid input: title must be provided")

        new_task = Task(title=data["title"], deadline=data.get("deadline"), timeleft=data.get("timeleft"))
        db.session.add(new_task)
        db.session.commit()
        return jsonify({"msg": "Task added", "id": new_task.id}), 201
    except exc.IntegrityError as e:
        db.session.rollback()
        return jsonify({"msg": "Database integrity error", "details": str(e)}), 400
    except ValueError as ve:
        return jsonify({"msg": str(ve)}), 400
    except Exception as e:
        return jsonify({"msg": "An error occurred", "error": str(e)}), 500

@app.route('/api/tasks/<int:task_id>/complete', methods=['PUT'])
def complete_task(task_id):
    try:
        task = Task.query.get(task_id)
        if not task:
            return jsonify({"msg": "Task not found"}), 404

        task.completed = True
        db.session.commit()
        return jsonify({"msg": "Task marked as complete"}), 200
    except Exception as e:
        return jsonify({"msg": "Error updating task", "error": str(e)}), 500

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    try:
        task = Task.query.get(task_id)
        if not task:
            return jsonify({"msg": "Task not found"}), 404

        db.session.delete(task)
        db.session.commit()
        return jsonify({"msg": "Task deleted"}), 200
    except Exception as e:
        return jsonify({"msg": "Error deleting task", "error": str(e)}), 500

@app.route('/select_task/<int:task_id>', methods=['POST'])
def select_task(task_id):
    task = Task.query.get(task_id)
    if task:
        return jsonify({'task_id': task.id, 'task_name': task.title, 'timeleft': task.timeleft}), 200
    return jsonify({'msg': 'Task not found'}), 404

@app.route('/api/tasks/<int:task_id>/pause', methods=['PUT'])
def pause_task(task_id):
    data = request.get_json()
    timeleft = data.get('timeleft')

    task = Task.query.get(task_id)

    if task:
        task.timeleft = timeleft
        db.session.commit()  # Use Flask-SQLAlchemy's session
        return jsonify({'msg': 'Task paused successfully', 'timeleft': task.timeleft}), 200
    else:
        return jsonify({'msg': 'Task not found'}), 404
    

@app.route('/api/tasks/completed', methods=['GET'])
def get_completed_tasks():
    try:
        tasks = Task.query.filter_by(completed=True).all()
        task_list = [{"id": task.id, "title": task.title, "deadline": task.deadline} for task in tasks]
        return jsonify(task_list), 200
    except Exception as e:
        return jsonify({"msg": "Error retrieving completed tasks", "error": str(e)}), 500

@app.route('/api/tasks/uncompleted', methods=['GET'])
def get_uncompleted_tasks():
    try:
        tasks = Task.query.filter_by(completed=False).all()
        task_list = [{"id": task.id, "title": task.title, "deadline": task.deadline} for task in tasks]
        return jsonify(task_list), 200
    except Exception as e:
        return jsonify({"msg": "Error retrieving uncompleted tasks", "error": str(e)}), 500
    
@app.route('/api/tasks/new_week', methods=['POST'])
def new_week():

    # Get the current date and calculate the deadline for one week from now
    current_date = datetime.now()
    deadline_date = current_date + timedelta(weeks=1)
    formatted_deadline = deadline_date.strftime('%Y-%m-%d')  # Format the date as a string

    default_tasks = [
        {"title": "PHYS3142 Lecture", "deadline": formatted_deadline, "timeleft": "120"},
        {"title": "LIFS2040 Lecture", "deadline": formatted_deadline, "timeleft": "120"},
        {"title": "LIFES3420 Lecture", "deadline": formatted_deadline, "timeleft": "120"},
        {"title": "PHYS3036 Revision", "deadline": formatted_deadline, "timeleft": "120"},
        {"title": "PHYS3036 Prep", "deadline": formatted_deadline, "timeleft": "120"},
        {"title": "PHYS3036 Revision", "deadline": formatted_deadline, "timeleft": "120"},
        {"title": "PHYS3142 Prep", "deadline": formatted_deadline, "timeleft": "120"},
        {"title": "PHYS3142 Revision", "deadline": formatted_deadline, "timeleft": "120"},
        {"title": "EMIA4110 Prep", "deadline": formatted_deadline, "timeleft": "120"},
        {"title": "EMIA4110 Revision", "deadline": formatted_deadline, "timeleft": "120"}
    ]

    try:
        for task in default_tasks:
            new_task = Task(title=task["title"], deadline=task["deadline"], timeleft=task["timeleft"])
            db.session.add(new_task)
        db.session.commit()
        return jsonify({"msg": "Default tasks added for the week"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Error adding default tasks", "error": str(e)}), 500

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        app.run(debug = False)