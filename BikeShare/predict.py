from tensorflow.keras.models import load_model

# Class representing a tensorflow ml model
class BikeShareModel:
  # Initialize the data model by importing from file
  def __init__(self, model_file):
    self.model = load_model(model_file)

  # Return predictions based on input data
  def predict(self, data):

    return self.model.predict(data)

    
  