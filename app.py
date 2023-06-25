
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

app = Flask(__name__)


# Database configuration
# app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+mysqlconnector://'root':''@localhost/kanban"
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql://root:''@localhost/kanban"


db = SQLAlchemy(app)

# Email configuration
app.config['MAIL_SERVER'] = 'your-mail-server'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-username'
app.config['MAIL_PASSWORD'] = 'your-password'
mail = Mail(app)

# Define database models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

class Board(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    users = db.relationship('User', secondary='board_user')

class BoardUser(db.Model):
    board_id = db.Column(db.Integer, db.ForeignKey('board.id'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)

class Column(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    estimate = db.Column(db.String(100), nullable=False)
    actual_duration = db.Column(db.String(100))
    column_id = db.Column(db.Integer, db.ForeignKey('column.id'))
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'))

class TicketMovement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'))
    from_column_id = db.Column(db.Integer, db.ForeignKey('column.id'))
    to_column_id = db.Column(db.Integer, db.ForeignKey('column.id'))
    timestamp = db.Column(db.DateTime, nullable=False)

# API endpoints




# Endpoint to create a board
@app.route('/boards', methods=['POST'])
def create_board():
    data = request.get_json()
    name = data.get('name')
    user_ids = data.get('user_ids', [])

    # Create the board
    board = Board(name=name)

    # Add users to the board
    for user_id in user_ids:
        user = User.query.get(user_id)
        if user:
            board.users.append(user)

    db.session.add(board)
    db.session.commit()

    return jsonify({'message': 'Board created successfully', 'board_id': board.id}), 201

# Endpoint to add a ticket to a board
@app.route('/boards/<int:board_id>/tickets', methods=['POST'])
def add_ticket(board_id):
    board = Board.query.get(board_id)
    if not board:
        return jsonify({'message': 'Board not found'}), 404

    data = request.get_json()
    title = data.get('title')
    estimate = data.get('estimate')
    assigned_to = data.get('assigned_to')

    column = Column.query.filter_by(name='TODO').first()
    if not column:
        return jsonify({'message': 'Column not found'}), 404

    ticket = Ticket(title=title, estimate=estimate, column_id=column.id, assigned_to=assigned_to)
    db.session.add(ticket)
    db.session.commit()

    return jsonify({'message': 'Ticket added successfully', 'ticket_id': ticket.id}), 201

# Endpoint to move a ticket to a different column
@app.route('/boards/<int:board_id>/tickets/<int:ticket_id>/move', methods=['PUT'])
def move_ticket(board_id, ticket_id):
    board = Board.query.get(board_id)
    if not board:
        return jsonify({'message': 'Board not found'}), 404

    ticket = Ticket.query.get(ticket_id)
    if not ticket:
        return jsonify({'message': 'Ticket not found'}), 404

    data = request.get_json()
    to_column_id = data.get('to_column_id')

    from_column = ticket.column
    to_column = Column.query.get(to_column_id)
    if not to_column:
        return jsonify({'message': 'Column not found'}), 404

    ticket.column = to_column

    movement = TicketMovement(ticket_id=ticket.id, from_column_id=from_column.id, to_column_id=to_column.id)
    db.session.add(movement)
    db.session.commit()

    return jsonify({'message': 'Ticket moved successfully'}), 200

# Endpoint to update the actual duration of a ticket in the 'In Progress' column
@app.route('/tickets/<int:ticket_id>/duration', methods=['PUT'])
def update_actual_duration(ticket_id):
    ticket = Ticket.query.get(ticket_id)
    if not ticket:
        return jsonify({'message': 'Ticket not found'}), 404

    data = request.get_json()
    start_time = data.get('start_time')
    end_time = data.get('end_time')

    start_time = datetime.strptime(start_time, '%H:%M:%S')
    end_time = datetime.strptime(end_time, '%H:%M:%S')

    duration = end_time - start_time

    ticket.actual_duration = str(duration)
    db.session.commit()

    return jsonify({'message': 'Actual duration updated successfully'}), 200

# Function to send the sprint summary email
def send_sprint_summary():
    # Get the tickets completed in the previous sprint
    # Calculate the completion percentage and individual progress
    # Prepare the email content

    with app.app_context():
        msg = Message('Sprint Summary', recipients=['user1@example.com', 'user2@example.com'])
        msg.body = 'Here is the summary of tasks completed in the previous sprint:\n\n'
        # Add the summary details

        mail.send(msg)

# Schedule the email to be sent every Friday evening
scheduler = BackgroundScheduler()
scheduler.add_job(send_sprint_summary, 'cron', day_of_week='fri', hour=18)
scheduler.start()
import sys
if __name__ == '__main__':
    arg=sys.argv[1:]
    print("hi:::", arg)
    if arg[0]=="create":
        with app.app_context():
            db.drop_all()
            db.create_all()
    # app.run()
