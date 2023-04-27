import uuid
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String


db = SQLAlchemy()



# Vote endpoint to save votes to the database
class Votes(db.Model):
    id = Column(Integer, primary_key=True)
    selected_image = Column(String)
    all_images = Column(String)


# Endpoint to create and list jobs
class Jobs(db.Model):
    id = Column(Integer, primary_key=True)
    title = Column(String)
    description = Column(String)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Users(db.Model):
    id = Column(Integer, primary_key=True)
    email = Column(String)
    supabase_id = Column(String)


from datetime import datetime
import boto3
from botocore.exceptions import ClientError
from sqlalchemy import ForeignKey

class StrippedDocs(db.Model):
    __tablename__ = 'stripped_docs'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    job_id = db.Column(db.Integer(), ForeignKey('jobs.id'))
    user_id = db.Column(db.Integer(), ForeignKey('users.id'))
    
    @classmethod
    def upload_and_host(cls, file_obj, filename):
        """
        Uploads a file to an S3 bucket and returns a StrippedDocs object with the hosted url.
        """
        # Upload file to S3 bucket
        session = boto3.Session(region_name='us-west-1')

        s3 = boto3.client('s3')
        bucket_name = 'resume-helper-5f2d3'
        file_key = f'resume-samples/{uuid.uuid4()}-{filename}'
        s3.upload_fileobj(file_obj, bucket_name, file_key)

        # Create a new StrippedDocs object with the hosted url
        url = f'https://{bucket_name}.s3.amazonaws.com/{file_key}'
        stripped_doc = cls(filename=filename, url=url)
        db.session.add(stripped_doc)
        db.session.commit()

        return stripped_doc
