#!/usr/bin/env python
from app import app
from app.model import DescribeerModel
app.beer_model = DescribeerModel()
app.run(debug = False)