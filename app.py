from flask import Flask, render_template, request, jsonify, session, url_for
from auth import get_user_info
from models import StrippedDocs, db, Jobs, Votes
from config import FILESERVER_PATH, RDS_URL, FLASK_SESSION_KEY
from flask_cors import CORS
from uploads import upload_bp
from votes import votes_bp

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = RDS_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
if (FLASK_SESSION_KEY is None):
    print('flask session key not set')
    exit()
app.config['SECRET_KEY'] = FLASK_SESSION_KEY

db.init_app(app)
CORS(app)

app.register_blueprint(upload_bp)
app.register_blueprint(votes_bp)

# parse header for auth tokens
@app.before_request
def before_request():
    get_user_info()


# Home page with links to other routes
@app.route('/')
def home():
    routes = {
        '/vote': {
            'link': 'votes.vote',
            'note': 'POST endpoint to save votes to the database'
        },
        '/jobs': {
            'link': 'jobs',
            'note': 'GET and POST endpoint to create and list jobs',
        },
        '/user': {
            'link': 'user',
            'note': 'GET decode supbase JWT from Auth header',
        },
        '/upload': {
            'link': 'upload.upload',
            'note': 'POST endpoint for resume sample upload'
        }
    }
    
    # generate links to the other routes using url_for
    route_links = {route: url_for(routes[route]['link']) for route in routes}
    
    return jsonify({
        'message': 'Welcome to the Flask app!',
        'routes': routes,
        'route_links': route_links
    })

# Endpoint to get user information
@app.route('/user')
def user():
    print(session['user'])
    return jsonify(session['user'])

@app.route('/all_jobs', methods=['GET', 'POST'])
def json_jobs():
  if request.method == 'GET':
        jobs = Jobs.query.all()
        return jsonify({"data": [x.as_dict() for x in jobs]})
        
@app.route('/jobs', methods=['GET', 'POST'])
def jobs():
    if request.method == 'GET':
        jobs = Jobs.query.all()
        return render_template('jobs.html', jobs=jobs)
    elif request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        job = Jobs(title=title, description=description)
        db.session.add(job)
        db.session.commit()
        return jsonify({'message': 'Job created successfully!'})

@app.route('/images')
def images():
    images: StrippedDocs = StrippedDocs.query.all()
    image_list = []
    for image in images:
        image_url = image.filename
        image_list.append(image_url)
    return jsonify({'images': image_list})



if __name__ == '__main__':
    app.run(debug=True)
