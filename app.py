from flask import Flask, render_template, request, jsonify, session, url_for
from auth import get_user_info
from models import StrippedDocs, db, Jobs, Votes
from config import FILESERVER_PATH, RDS_URL, FLASK_SESSION_KEY
from flask_cors import CORS

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = RDS_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
if (FLASK_SESSION_KEY is None):
    print('flask session key not set')
    exit()
app.config['SECRET_KEY'] = FLASK_SESSION_KEY

db.init_app(app)
CORS(app)

# parse header for auth tokens
@app.before_request
def before_request():
    get_user_info()


# Home page with links to other routes
@app.route('/')
def home():
    routes = {
        '/vote': 'POST endpoint to save votes to the database',
        '/jobs': 'GET and POST endpoint to create and list jobs',
        '/user': 'GET endpoint to get user information from Supabase cookie/JWT'
    }
    
    # generate links to the other routes using url_for
    route_links = {route: url_for(route[1:]) for route in routes}
    
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

@app.route('/vote', methods=['GET', 'POST'])
def vote():
    if request.method == 'GET':
        votes = Votes.query.all()
        return jsonify([{'id': vote.id, 'selectedImage': vote.selected_image, 'allImages': vote.all_images} for vote in votes])
    elif request.method == 'POST':
        data = request.get_json()
        selected_image = data.get('selectedImage')
        all_images = data.get('allImages')
        vote = Votes(selected_image=selected_image, all_images=all_images)
        db.session.add(vote)
        db.session.commit()
        return jsonify({'message': 'Vote saved successfully!'})

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

from werkzeug.utils import secure_filename
import os

@app.route('/upload', methods=['POST'])
def upload():
    # Get the uploaded file and job role tag from the request
    file = request.files['file']
    job_role = request.form.get('job')

    # Check if job role already exists in the database. If not, add it.
    job = Jobs.query.filter_by(title=job_role).first()
    if not job:
        job = Jobs(title=job_role, description='')
        db.session.add(job)
        db.session.commit()

    # Check if filename already exists in the database. If so, return an error.
    stripped_doc = StrippedDocs.query.filter_by(filename=file.filename).first()
    if stripped_doc:
        return {'message': 'File already exists in the database'}, 400

    # Create a new StrippedDocs object and set its attributes
    stripped_doc = StrippedDocs(filename=file.filename, url='fakeurl.com', job_id=job.id)

    # Save the file to disk and set its path in the StrippedDocs object
    filename = secure_filename(file.filename)
    filepath = os.path.join(FILESERVER_PATH,  filename)
    file.save(filepath)
    stripped_doc.file_path = filepath

    # Add the StrippedDocs object to the database
    try:
        db.session.add(stripped_doc)
        db.session.commit()
        return {'message': 'Upload successful'}
    except Exception as e:
        db.session.rollback()
        return {'message': 'Upload failed', 'error': str(e)}, 500



if __name__ == '__main__':
    app.run(debug=True)
