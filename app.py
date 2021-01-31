# Requires Python 3.8
from flask import Flask, request, render_template, redirect
import logging

from app_config import initialize

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
service = initialize()

# Main page handling
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Get values from user submitted fields
        values = service.get_predict_form_values(request.form)
        message = f"Estimated Ride counts for {request.form['date']}"
    else:
        # Generate values for tomorrow
        values = service.get_predict_values()
        message = "Tomorrow's Estimated Ride counts"
    
    results, predictions = service.get_predictions(values)
        
    # Graph the results and create image
    img_url = service.create_prediction_plot(values['Hour'], predictions)
        
    # Render prediction results html page
    return render_template('main.html',
                                message = message,
                                results = results,
                                sum = predictions.sum(),
                                img_url= img_url), 200

@app.route('/predict', methods=['GET'])
def predict():

    return render_template('predict.html'), 200


@app.route('/data', methods=['GET', 'POST'])
def data_page():
    # Get page number if supplied
    page = request.args.get('page')
    max_page = service.data.max_page
    if page is None:
        page = 1
    else:
        try: 
            page = int(page)
            if page > max_page:
                return redirect(f"/data?page={max_page}")
            elif page < 1:
                return redirect(f"/data?page=1")
        except ValueError:
            return redirect(f"/data?page=1")

    # set default message to null
    message = ''
    if request.args.get('save'):
        url = service.save_data_values()
        message = f"Data saved to {url}"

    # Handle data update from edit        
    if request.method == 'POST':
        timestamp = request.args.get('timestamp')

        service.update_data_values(request.form, timestamp)

        return redirect(f"/data?page={page}")

    # check if edit param was set to true
    edit_flag = request.args.get('edit')
    if edit_flag is None:
        edit = False
    elif edit_flag.lower() == "true": 
        edit = True
    else:
        edit = False


    values = service.get_data(page=page)
    # convert to list of dict
    values = values.to_dict(orient='records')

    return render_template('data.html',
                                    columns = service.data.display_columns,
                                    values = values,
                                    edit = edit,
                                    page = page,
                                    max_page = max_page,
                                    message = message)



@app.route('/visuals', methods=['GET'])
def visuals():

    selected, subtype, img_url = service.create_data_plot(request)

    return render_template('visual.html',
                    img_url = img_url,
                    type = selected,
                    subtype = subtype)


# Start the application
if __name__ == '__main__':
    app.run()
