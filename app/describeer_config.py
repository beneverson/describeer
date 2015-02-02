DEFAULT_MODEL_PATH = './app/WholeReviewNameAnStyleFixedAlphaTrained10x.doc2vec'
DEFAULT_CSV_PATH = './app/filtered_raw_reviews.csv'
DEFAULT_PICKLE_PATH = './app/pickles/'

name_to_style_path = 'nametostyle.pickle'
name_to_popularity_path = 'nametopopularity.pickle'
name_to_rating_path = 'nametorating.pickle'
style_list_path = 'stylelist.pickle'
name_list_path = 'namelist.pickle'
name_to_id_path = 'nametoid.pickle'
descriptors_path = 'descriptors.pickle'

N_SEARCH_RESULTS = 10

style_column = 5
name_column = 4
overall_score_column = 8
id_column = 2

# weights for overall scoring of beers
STYLE_SIM_WEIGHT = 1.35
BEER_SIM_WEIGHT = 0.5
BEER_POP_WEIGHT = 0.0
BEER_RATING_WEIGHT = 0.1