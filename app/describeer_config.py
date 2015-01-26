DEFAULT_MODEL_PATH = './app/WholeReviewNameAnStyleFixedAlphaTrained10x.doc2vec'
DEFAULT_CSV_PATH = './app/filtered_raw_reviews.csv'

DEFAULT_PICKLE_PATH = './app/pickles/'
name_to_style_path = 'nametostyle.pickle'
name_to_popularity_path = 'nametopopularity.pickle'
name_to_rating_path = 'nametorating.pickle'
style_list_path = 'stylelist.pickle'
name_list_path = 'namelist.pickle'

N_SEARCH_RESULTS = 50

style_column = 5
name_column = 4
overall_score_column = 8

# weights for overall scoring of beers
STYLE_SIM_WEIGHT = 0.25
BEER_SIM_WEIGHT = 1.0
BEER_POP_WEIGHT = 0.0
BEER_RATING_WEIGHT = 0.0