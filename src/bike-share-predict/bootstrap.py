from predict import BikeShareModel
from tables import BikeData

import os

model_path = os.path.abspath(os.path.join(os.getcwd(), '../..', 'models/bike_share_v1.0' ))

def startup():
  model = BikeShareModel(model_path)

  data = BikeData()
  
  return model, data