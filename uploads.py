from werkzeug.utils import secure_filename
from flask import Blueprint, Flask, render_template, request, jsonify, session, url_for
from auth import get_user_info
from models import StrippedDocs, db, Jobs, Votes
from config import FILESERVER_PATH, RDS_URL, FLASK_SESSION_KEY
from flask_cors import CORS
import os

upload_bp = Blueprint('upload', __name__)

@upload_bp.route('/upload', methods=['POST'])
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
    # stripped_doc = StrippedDocs.query.filter_by(filename=file.filename).first()
    # if stripped_doc:
    #     return {'message': 'File already exists in the database'}, 400

    # Save the file to disk and set its path in the StrippedDocs object
    filename = secure_filename(file.filename)
    filepath = os.path.join(FILESERVER_PATH,  filename)
    file.save(filepath)

    file = open(filepath, 'rb')
    # Create a new StrippedDocs object and set its attributes
    user_id = 1
    if 'user' in session:
        user_id = session['user']['user_id']
        print('set user id to', user_id)

    stripped_doc = StrippedDocs.upload_and_host(file, filename)
    stripped_doc.user_id = user_id
    stripped_doc.job_id = job.id

    # Add the StrippedDocs object to the database
    try:
        db.session.add(stripped_doc)
        db.session.commit()
        return {'message': 'Upload successful'}
    except Exception as e:
        db.session.rollback()
        return {'message': 'Upload failed', 'error': str(e)}, 500

