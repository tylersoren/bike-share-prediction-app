# Requires Python 3.8
from azstorage import AzureStorage
from flask import Flask, request, render_template
import logging
import numpy as np

from helper import get_predict_form_values, create_plot
import app_config

# Configure Default Logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.WARNING)

# Configure App Logger
logger = logging.getLogger('bike-share-predict')
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', "%Y-%m-%d %H:%M:%S")
ch.setFormatter(formatter)
logger.addHandler(ch)

app = Flask(__name__, instance_relative_config=True)

model, data, data_storage = app_config.startup()

# Main page handling
@app.route('/', methods=['GET', 'POST'])
def index():
    
    return render_template('main.html'), 200


@app.route('/predict', methods=['GET', 'POST'])
def predict():
    # If request is a Post, handle the prediction
    if request.method == 'POST':
        
        # Get values from user submitted fields
        values = get_predict_form_values(request.form)

        # run predictions and round to nearest integer and clip any negative numbers to 0
        predictions = np.rint(model.predict(values).clip(min=0)).astype(int).flatten()
        results = []
        for index, hour in enumerate(values['Hour']):
            results.append(dict(hour=f" {hour} : 00", count=predictions[index]))
        
        # Graph the results and create image
        img_url = create_plot(values['Hour'], predictions)
        
        # Render prediction results html page
        return render_template('predict.html',
                                    results = results,
                                    sum = predictions.sum(),
                                    img_url= img_url)
    
    else:
        return "No data submitted for prediction"

@app.route('/data', methods=['GET', 'POST'])
def display_data(count = 50, page = 1):
    columns=['DATE','TAVG']

    values = data.get_weather()[columns].iloc[count*(page-1):count*page]
    # convert to list of dict
    values = values.to_dict(orient='records')

    return render_template('data.html',
                                    columns = columns,
                                    values = values)

# Start the application
if __name__ == '__main__':
    app.run()
