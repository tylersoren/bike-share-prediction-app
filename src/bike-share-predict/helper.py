import pandas as pd
import numpy as np
import os, uuid
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime


def get_predict_form_values(form):
    date = datetime.strptime(form['date'], '%Y-%m-%d')
    holiday = form.get('holiday')
    # Check if box was checked and set to 0 or 1
    if holiday is None:
        holiday = float(0)
    else:
        if holiday == 'on':
            holiday = float(1)
        else:
            error_flag = 1
            error_msg = "Holiday flag selection error"

    lotemp = float(form['lotemp'])
    hitemp = float(form['hitemp'])
    wind = float(form['wind'])
    precip = float(form['precip'])

    month = date.month
    day = date.weekday()
    hours = np.arange(0,24,1)        

    values = pd.DataFrame()
    values['Hour'] = hours
    values['TMAX'] = hitemp
    values['TMIN'] = lotemp
    values['Day of week'] = day
    values['Month'] = month
    values['Holiday'] = holiday
    values['AWND'] = wind
    values['PRCP'] = precip

    return values

def create_plot(hours, predictions):
    results = []
    for index, hour in enumerate(values['Hour']):
            results.append(dict(hour=f" {hour} : 00", count=predictions[index]))

    img_loc = "images/plots/" + str(uuid.uuid4()) + ".png"
        
    sns.set_style("whitegrid")
    sns.lineplot(hours,predictions)
    plt.title('Predicted Ride Count per Hour')
    plt.xlabel('Hour')
    plt.ylabel('Ride Count')
    plt.xticks(np.arange(0, 23, 4))
    print(os.getcwd())
    plt.savefig(f"C:/repos/bike-share-prediction-app/src/bike-share-predict/static/{ img_loc}", format='png')
    plt.close()

    return img_loc