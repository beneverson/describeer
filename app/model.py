#!/usr/bin/env python
import logging
import csv
import re
from gensim.models import Doc2Vec
from collections import defaultdict
from numpy import argsort
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
import describeer_config as dbc
from operator import itemgetter
import cPickle as pickle
import os

class DescribeerModel(object):
	def __init__(self):
		self.init_model()
		self.init_lookups()

	def init_model(self, model_path = dbc.DEFAULT_MODEL_PATH):
		self._model = Doc2Vec.load(model_path)

	def init_lookups(self):

		self._name_to_style = {}
		self._name_to_rating = {}
		self._name_to_popularity = {}
		self._name_list = []
		self._style_list = []

		try:
			print "Trying to load pre-pickled data..."
			self._name_to_style = pickle.load(open(dbc.DEFAULT_PICKLE_PATH + dbc.name_to_style_path, 'rb'))
			self._name_to_popularity = pickle.load(open(dbc.DEFAULT_PICKLE_PATH + dbc.name_to_popularity_path, 'rb'))
			self._name_to_rating = pickle.load(open(dbc.DEFAULT_PICKLE_PATH + dbc.name_to_rating_path, 'rb'))
			self._style_list = pickle.load(open(dbc.DEFAULT_PICKLE_PATH + dbc.style_list_path, 'rb'))
			self._name_list = pickle.load(open(dbc.DEFAULT_PICKLE_PATH + dbc.name_list_path, 'rb'))
			return
		except IOError:
			print "Can't find pickles, loading all data..."


		# local variables
		_name_to_popularity_not_norm = defaultdict(int)
		_name_to_rating_not_norm = defaultdict(float)
		total_reviews = 0 
		max_reviews_any_beer = 0

		# populate the lookups
		with open(dbc.DEFAULT_CSV_PATH, 'rb') as f:
			reader = csv.reader(f)
			next(reader, None) # skip the header
			for row in reader:
				try:
					beer_name = self.tokenize_beer_noun(row[dbc.name_column])
					beer_style = self.tokenize_beer_noun(row[dbc.style_column])
					beer_rating = float(row[dbc.overall_score_column])

					# increment this beer's overall popularity
					_name_to_popularity_not_norm[beer_name] += 1 

					# update the max reviews for any one beer
					if _name_to_popularity_not_norm[beer_name] > max_reviews_any_beer:
						max_reviews_any_beer = _name_to_popularity_not_norm[beer_name]

					# increment this beer's overall rating
					_name_to_rating_not_norm[beer_name] += beer_rating

					# init the other lookups
					if beer_name not in self._name_to_style.keys():
						self._name_to_style[beer_name] = beer_style

					if beer_name not in self._name_list:
						self._name_list.append(beer_name)

					if beer_style not in self._style_list:
						self._style_list.append(beer_style)

					total_reviews += 1 # increment total reviews
				
				except ValueError as e:
					print "WARNING: attempt to parse " + str(row)  + " failed. Initialization continuing."

		# populate _name_to_rating with average rating per review for each beer name
		for rated_beer in _name_to_rating_not_norm.keys():
			self._name_to_rating[rated_beer] = (1.0 * _name_to_rating_not_norm[rated_beer])/_name_to_popularity_not_norm[rated_beer]

		# populate _name_to_popularity with (# reviews for this beer)/(max # reviews for any beer)
		for reviewed_beer in _name_to_popularity_not_norm.keys():
			self._name_to_popularity[reviewed_beer] = (1.0 * _name_to_popularity_not_norm[reviewed_beer])/max_reviews_any_beer

		# pickle the data so we can recall it later
		pickle.dump(self._name_to_style, open(str(dbc.DEFAULT_PICKLE_PATH + dbc.name_to_style_path), "w+"))
		pickle.dump(self._name_to_popularity, open(str(dbc.DEFAULT_PICKLE_PATH + dbc.name_to_popularity_path), "w+"))
		pickle.dump(self._name_to_rating, open(str(dbc.DEFAULT_PICKLE_PATH + dbc.name_to_rating_path), "w+"))
		pickle.dump(self._name_list, open(str(dbc.DEFAULT_PICKLE_PATH + dbc.name_list_path), "w+"))
		pickle.dump(self._style_list, open(str(dbc.DEFAULT_PICKLE_PATH + dbc.style_list_path), "w+"))

	def tokenize_beer_noun(self, beer_noun, reverse=False):
		if reverse: # de-tokenize the term
			return beer_noun.replace('_', ' ')
		return beer_noun.replace(' ', '_')

	#add/swap additional search terms for every term in lookup_list encountered
	# lookup_list = reference list of terms to replace (ex. beer names)
	# replacement_dict = dict of new terms to insert/swap in (ex. beer name >> beer style)
	def prepare_search_terms(self, search_terms=[], include_original = True, lookup_list=[], replacement_dict={}):
		prepared_search_terms = [] 
		for term in search_terms:
			tokenized_term = self.tokenize_beer_noun(term) # tokenize the term
			if tokenized_term in lookup_list:
				prepared_search_terms.append(replacement_dict[tokenized_term])
				if include_original:
					prepared_search_terms.append(tokenized_term)
			else:
				prepared_search_terms.append(tokenized_term)

		return prepared_search_terms

	# return list of relevant beers (dicts) for a given positive, negative search query
	# TODO: account for the case where no search terms are included
	def get_relevant_terms(self, positive=[], negative=[], use_cosmul = True, returnable_words = []):

		positive_terms = self.prepare_search_terms(positive, lookup_list=self._name_list, replacement_dict=self._name_to_style)
		negative_terms = self.prepare_search_terms(negative, lookup_list=self._name_list, replacement_dict=self._name_to_style)
		all_search_terms = positive_terms + negative_terms

		if use_cosmul:
			sims = self._model.most_similar_cosmul(positive=positive_terms, negative=negative_terms, topn=None)
		else:
			sims = self._model.most_similar(positive=positive_terms, negative=negative_terms, topn=None)

		# sort the resulting array, and represent as inidces
		best_distance_indices = argsort(sims)[::-1]

		# populate a relevant terms dictionary
		relevant_terms = {}
		for distance_index in best_distance_indices:
			word = self._model.index2word[distance_index]
			if word in returnable_words:
				relevant_terms[word] = float(sims[distance_index])

		return relevant_terms

	# combine relevant beers, relevant styles, popularity, and average rating to 
	# compute a score for each beer passed in
	def calculate_beer_score(self, relevant_beers=[], relevant_styles=[]):
		
		scored_beers = []
		for beer_name in relevant_beers.keys():
			scored_beer = {}
			try:
				scored_beer['name'] = self.tokenize_beer_noun(beer_name.decode('unicode_escape').encode('ascii','ignore'), reverse=True)
			except UnicodeDecodeError:
				import pdb; pdb.set_trace()

			beer_style = self._name_to_style[beer_name]
			try:
				scored_beer['style'] = self.tokenize_beer_noun(beer_style.decode('unicode_escape').encode('ascii','ignore'), reverse= True)
			except UnicodeDecodeError:
				import pdb; pdb.set_trace()

			# calculate the score on this beerusing a weighted sum of other scores
			# TODO: check that these numbers make sense
			
			beer_score = dbc.BEER_SIM_WEIGHT * relevant_beers[beer_name] + dbc.STYLE_SIM_WEIGHT * relevant_styles[beer_style] + dbc.BEER_POP_WEIGHT * self._name_to_popularity[beer_name] + dbc.BEER_RATING_WEIGHT * self._name_to_rating[beer_name]

			try:
				scored_beer['score'] = float(beer_score)
			except UnicodeDecodeError:
				import pdb; pdb.set_trace()

			scored_beers.append(scored_beer)

		# return a sorted list of beer disctionaries
		print scored_beers
		return sorted(scored_beers, key=lambda d:d['score'], reverse=True)

	# parse search terms from a query string into two lists
	# WARNING: Currently no support for phrases (e.g. Sierra Nevada Pale Ale)
	# for this functionality, it is necessary to pre-tokenize the input.
	# TODO: Use regex to support this kind of input
	def parse_search_terms(self, query_string):

		positive_terms = []
		negative_terms = []
		all_terms = query_string.split()

		# populate the positive and negative 
		# lists using a simple flaggind scheme
		positive = True
		for term in all_terms:
			if term is '-':
				positive = False
			elif term is '+':
				positive = True
			elif positive:
				positive_terms.append(term)
			else:
				negative_terms.append(term)

		return {'positive_terms':positive_terms, 'negative_terms':negative_terms}

	# generate beer score for a given query string
	def search_beers(self, query_string, n_results = dbc.N_SEARCH_RESULTS):
		# parse query into positive and negative terms
		parsed_terms_dictionary = self.parse_search_terms(query_string)
		positive_search_terms = parsed_terms_dictionary['positive_terms']
		print "positive search terms" + str(positive_search_terms)
		negative_search_terms = parsed_terms_dictionary['negative_terms']

		# get beer relevance scores
		_relevant_beers = self.get_relevant_terms(positive=positive_search_terms, negative=negative_search_terms, returnable_words=self._name_list)

		# get style relevance scores
		_relevant_styles = self.get_relevant_terms(positive=positive_search_terms, negative=negative_search_terms, returnable_words=self._style_list)

		# figure out the scores for these beers based on above scores
		_scored_beers = self.calculate_beer_score(relevant_beers=_relevant_beers, relevant_styles=_relevant_styles)

		return _scored_beers[:n_results]
