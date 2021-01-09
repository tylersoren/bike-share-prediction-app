from tensorflow.keras.models import load_model

class BikeShareModel:

  def __init__(self, model_file):
    self.model = load_model(model_file)

  def predict(self, data):

    return self.model.predict(data)
  