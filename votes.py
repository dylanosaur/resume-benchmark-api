from flask import Blueprint, request, jsonify, session
from auth import get_user_info
from models import StrippedDocs, db, Votes, Jobs, Rankings

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

        filenames = [x["doc_filename"] for x in all_images]
        matching_docs = db.session.query(StrippedDocs, Jobs)\
            .filter(StrippedDocs.job_id==Jobs.id)\
            .filter(StrippedDocs.filename.in_([x["doc_filename"] for x in all_images]))\
            .all()

        docs_by_filename = {x[0].filename: x[0] for x in matching_docs}
        selected_doc = docs_by_filename[selected_image]
        loser_docs = [docs_by_filename[x["doc_filename"]] for x in all_images if x["doc_filename"] != selected_image]

        vote = Votes(selected_image=selected_doc.id, all_images=filenames, 
                     user_id=user_id, job_id=selected_doc.job_id)
        db.session.add(vote)
        db.session.commit()

        # get rankings
        all_document_ids = [selected_doc.id] + [x.id for x in loser_docs]
        rankings = Rankings.query.filter(Rankings.job_id==selected_doc.job_id)\
                        .filter(Rankings.stripped_doc_id.in_(all_document_ids))\
                        .all()
        
        # update rankings
        indexed_rankings = {f"{x.job_id}-{x.stripped_doc_id}":x for x in rankings}
        winner_rank_key = f"{selected_doc.job_id}-{selected_doc.id}"
        if winner_rank_key not in indexed_rankings:
            new_ranking = Rankings(job_id=selected_doc.job_id, stripped_doc_id=selected_doc.id, score=1)
            db.session.add(new_ranking)
        else:
            winner_ranking = indexed_rankings[f"{selected_doc.job_id}-{selected_doc.id}"]
            winner_ranking.score += 1
            db.session.add(winner_ranking)

        for loser_doc in loser_docs:
            loser_rank_key = f"{loser_doc.job_id}-{loser_doc.id}"
            if loser_rank_key not in indexed_rankings:
                new_ranking = Rankings(job_id=loser_doc.job_id, stripped_doc_id=loser_doc.id, score=-1)
                db.session.add(new_ranking)
            else: 
                loser_ranking = indexed_rankings[f"{loser_doc.job_id}-{loser_doc.id}"]
                loser_ranking.score -= 1

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
