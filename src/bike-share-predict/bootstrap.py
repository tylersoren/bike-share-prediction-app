from predict import BikeShareModel
from tables import BikeData

def startup():
  model_path = 'C:\\repos\\bike-share-prediction-app\\models\\bike_share_v1.0'
  model = BikeShareModel(model_path)

  data = BikeData()
  
  return model, data