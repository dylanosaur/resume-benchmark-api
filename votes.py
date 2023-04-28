from flask import Blueprint, request, jsonify, session
from auth import get_user_info
from models import StrippedDocs, db, Votes

votes_bp = Blueprint('votes', __name__)



# Vote endpoint to save votes to the database
# class Votes(db.Model):
#     id = Column(Integer, primary_key=True)
#     selected_image = Column(String)
#     all_images = Column(String)
#     user_id = Column(Integer(), ForeignKey('users.id'))


@votes_bp.route('/vote', methods=['GET', 'POST'])
def vote():
    if request.method == 'GET':
        votes = Votes.query.all()
        return jsonify([{'id': vote.id, 'selectedImage': vote.selected_image, 'allImages': vote.all_images} for vote in votes])
    elif request.method == 'POST':
        data = request.get_json()
        selected_image = data.get('selectedImage')
        all_images = data.get('allImages')
        user_id = None
        if 'user' in session:
            user_id = session['user']['user_id']
            print('set user id to', user_id)
        vote = Votes(selected_image=selected_image, all_images=all_images, user_id=user_id)
        db.session.add(vote)
        db.session.commit()

        matching_docs = StrippedDocs.query.all()
        docs_by_filename = {x.filename: x for x in matching_docs}
        selected_doc = docs_by_filename[selected_image]
        try:
            selected_doc.ranking += 1
        except Exception as ex:
            print(ex)
            selected_doc.ranking = 1
        print(all_images)
        loser_docs = [docs_by_filename[x] for x in all_images if x != selected_image]
        for loser_doc in loser_docs:
            try:
                loser_doc.ranking -= 1
            except:
                loser_doc.ranking = -1
        db.session.commit()
        return jsonify({'message': 'Vote saved successfully!'})
    
@votes_bp.route('/leaderboard')
def leaderboard():
    stripped_docs = StrippedDocs.query.order_by(StrippedDocs.ranking.desc()).all()
    result = [{'filename': doc.filename,
               'url': doc.url,
                'ranking': doc.ranking if doc.ranking else 0} for doc in stripped_docs]
    result.sort(key=lambda x:x['ranking'], reverse=True)
    return jsonify(result)
