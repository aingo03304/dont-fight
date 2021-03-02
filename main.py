import json
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy.exc import IntegrityError

config = json.load(open('config.json', "r"))

app = Flask(__name__)
limiter = Limiter(
    app,
    key_func=get_remote_address
)
app.config['SQLALCHEMY_DATABASE_URI'] = config['db_url']
db = SQLAlchemy(app)

@app.errorhandler(429)
def ratelimit_handler(e):
    return {
        "status": {
            "code": 429,
            "message": f"Only {config['limit']}"
        }
    }, 429
    
time_table = config['time_table']

class Demo(db.Model):
    __tablename__ = "demo"
    
    demo_datetime = db.Column(db.String, primary_key=True)
    ta_id = db.Column(db.String, primary_key=True)
    team_id = db.Column(db.Integer, unique=True)

@app.route('/api/submit', methods=['POST'])
@limiter.limit(config['limit'])
def submit():
    try:
        if request.method == "POST":
            _demo_datetime = request.json['demo_datetime']
            _ta_id = request.json['ta_id']
            _team_id = request.json['team_id']
            row = Demo(demo_datetime=_demo_datetime, ta_id=_ta_id, team_id=_team_id)
            db.session.add(row)
            db.session.commit()
            return {
                'status': {
                    'code': 200,
                    'message': 'success',
                }
            }
    except IntegrityError:
        return {
            'status': {
                'code': 400,
                'message': 'Taken',
            }
        }, 400
    return {
        'status': {
            'code': 400,
            'message': 'How dare you!',
        }
    }, 400

@app.route('/')
@limiter.exempt
def demo():
    query_all = Demo.query.all()
    taken_time_ta = []
    taken_team_id = {}
    for row in query_all:
        taken_time_ta.append((row.demo_datetime, row.ta_id))
        taken_team_id[row.demo_datetime + '_' + row.ta_id] = row.team_id
    return render_template('index.html', 
                           time_list=time_table['time'], 
                           ta_list=time_table['ta_id'], 
                           taken_time_ta=taken_time_ta,
                           taken_team_id=taken_team_id)

if __name__ == "__main__":
    db.create_all()
    app.run()

