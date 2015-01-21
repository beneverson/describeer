from flask import render_template, redirect, url_for, g
from app import app
from forms import SearchForm
from config import MAX_SEARCH_RESULTS

@app.before_request
def before_request():
    g.search_form = SearchForm()

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title='Home', search_form=g.search_form)
    
@app.route('/search', methods=['POST'])
def search():
    if not g.search_form.validate_on_submit():
            return redirect(url_for('search'))
    return redirect(url_for('search_results', query=g.search_form.search.data))
    
@app.route('/search_results/<query>')
def search_results(query):
    dummy_data = [{'name':'Bud Light', 'ABV':5.2, 'score':0.51}, 
    {'name':'Sierra Nevada Pale Ale', 'ABV':6.1, 'score':0.42}]
    return render_template('search_results.html', query=query, results=dummy_data)