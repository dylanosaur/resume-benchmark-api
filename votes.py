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

        urls = [x for x in all_images]
        results = db.session.query(StrippedDocs, Jobs)\
            .filter(StrippedDocs.job_id==Jobs.id)\
            .filter(StrippedDocs.url.in_(urls))\
            .all()

        matching_docs = [x[0] for x in results]
        job = [x[0] for x in results][0]
        print(matching_docs)

        docs_by_url = {x.url: x for x in matching_docs}
        selected_doc = docs_by_url[selected_image]
        loser_docs = [x for x in matching_docs if x.url != selected_image]

        vote = Votes(selected_image=selected_doc.id, all_images=urls, 
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
    ranked_results = db.session.query(StrippedDocs, Rankings)\
        .filter(Rankings.stripped_doc_id==StrippedDocs.id)\
        .order_by(Rankings.score.desc()).all()
    print(ranked_results)
    result = [{'filename': x[0].filename,
               'url': x[0].url,
               'ranking': x[1].score if x[1].score else 0} for x in ranked_results]
    return jsonify(result)
