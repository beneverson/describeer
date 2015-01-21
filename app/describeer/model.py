#!/usr/bin/env python
import logging
import csv
import re
from gensim.models import Doc2Vec
from collections import defaultdict
from numpy import argsort
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
from describeer_config import DEFAULT_MODEL_PATH, DEFAULT_CSV_PATH, style_column, name_column

# variables
_model = None

# lookups
_name_to_style = {}
_name_to_popularity = defaultdict(int)
_style_list = []
_name_list = []

def tokenize_beer_noun(beer_noun, reverse=False):
	if reverse: # de-tokenize the term
		return beer_noun.replace('_', ' ')
	return beer_noun.replace(' ', '_')

# TODO: add cPickle functionality to speed this up
def init_lookups():
	with open(DEFAULT_CSV_PATH, 'rb') as f:
		reader = csv.reader(f)
		next(reader, None) # skip the header
		for row in reader:
			beer_name = tokenize_beer_noun(row[name_column])
			beer_style = tokenize_beer_noun(row[style_column])

			# increment this beer's popularity count
			_name_to_popularity[beer_name] += 1 

			# init the other lookups
			if beer_name not in _name_to_style.keys():
				_name_to_style[beer_name] = beer_style

			if beer_name not in _name_list:
				_name_list.append(beer_name)

			if beer_style not in _style_list:
				_style_list.append(beer_style)

# add/swap additional search terms for every term in lookup_list encountered
# lookup_list = reference list of terms to replace (ex. beer names)
# replacement_dict = dict of new terms to insert/swap in (ex. beer name >> beer style)
def prepare_search_terms(search_terms=[], include_original = True, lookup_list=[], replacement_dict={}):
	prepared_search_terms = [] 
	for term in search_terms:
		tokenized_term = tokenize_beer_noun(term) # tokenize the term
		if tokenized_term in lookup_list:
			prepared_search_terms.append(replacement_dict[tokenized_term])
			if include_original:
				prepared_search_terms.append(tokenized_term)
		else:
			prepared_search_terms.append(tokenized_term)

	return prepared_search_terms

# return list of relevant beers (dicts) for a given positive, negative search query
# TODO: account for the case where no search terms are included
def get_relevant_terms(positive=[], negative=[], n_results = 20, use_cosmul = False, returnable_words = []):

	positive_terms = prepare_search_terms(positive)
	negative_terms = prepare_search_terms(negative)
	all_search_terms = positive_terms + negative_terms

	if use_cosmul:
		sims = _model.most_similar_cosmul(positive=positive_terms, negative=negative_terms, topn=len(_model.vocab))
	else:
		sims = _model.most_similar(positive=positive_terms, negative=negative_terms, topn=len(_model.vocab))

	# populate list of terms to return
	# filter by returnable_words
	relevant_terms = []
	for word, score in sims:
		if word in returnable_words and word not in all_search_terms:
			relevant_terms.append({'name':word, 'similarity':score})

	return relevant_terms

def init_model(model_path = DEFAULT_MODEL_PATH):
	global _model
	_model = Doc2Vec.load(model_path)

# parse a search term into positive and negative terms
# and feed to get_relevant_terms function
def search_beers(search_term):
	pass

# initialization
def initialize():
	init_model()
	init_lookups()