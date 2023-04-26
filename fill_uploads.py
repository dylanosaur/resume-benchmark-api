import os
import boto3
from config import RDS_URL
from models import db, StrippedDocs

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(RDS_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Replace 'directory_path' with the path to your directory
directory_path = '/home/dylan/resume-tinder/public'

for filename in os.listdir(directory_path):
    filepath = os.path.join(directory_path, filename)
    
    # Generate the URL for the media item using the S3 bucket name and file key
    file_key = f'{filename}'

    
    # Create the StrippedDocs item and add it to the database
    stripped_doc = StrippedDocs(filename=filename, url='fakeurl.com')
    session.add(stripped_doc)
    session.commit()

print('All files in directory have been processed and added to the database.')
