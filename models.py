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

class Users(db.Model):
    id = Column(Integer, primary_key=True)
    email = Column(String)
    supabase_id = Column(String)