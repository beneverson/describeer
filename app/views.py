from flask import render_template, redirect, url_for, request
from app import app
from forms import SearchForm
from config import MAX_SEARCH_RESULTS

@app.before_request
def before_request():
	pass

@app.route('/')
@app.route('/index')
def index():
	return render_template('index.html', title='Home')
	
    
@app.route('/search', methods=['POST'])
def search():
	return request.form['test1']+request.form['test2']
	'''
    if not g.search_form.validate_on_submit():
            return redirect(url_for('search'))
    return redirect(url_for('search_results', query=g.search_form.search.data))
    '''
    
@app.route('/search_results/<query>')
def search_results(query):
	return query
	#likely_beers = app.beer_model.search_beers(query.encode('utf-8'))
	#return render_template('search_results.html', query=query, results=likely_beers)