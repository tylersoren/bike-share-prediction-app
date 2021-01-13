import pandas as pd
import numpy as np
import os, uuid, tempfile, shutil
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from flask import url_for
from azstorage import AzureStorage

temp_dir = base_path = tempfile.gettempdir()


# Fetch Environment variables for configuration
storage_url = os.getenv('AZURE_STORAGE_ACCOUNT_URL')
if not storage_url:
  raise ValueError("Need to define AZURE_STORAGE_ACCOUNT_URL")

container_name = os.getenv('AZURE_STORAGE_IMAGE_CONTAINER_NAME')
if not container_name:
  raise ValueError("Need to define AZURE_STORAGE_IMAGE_CONTAINER_NAME")

# Configure Azure Storage connection for image files
img_storage = AzureStorage(storage_url, container_name)

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

def create_plot(hours, predictions, destination_type = 'azure'):

    filename = str(uuid.uuid4()) + ".png"
    temp_path = os.path.join(temp_dir, filename)

    sns.set_style("whitegrid")
    sns.lineplot(x=hours, y=predictions)
    plt.title('Predicted Ride Count per Hour')
    plt.xlabel('Hour')
    plt.ylabel('Ride Count')
    plt.xticks(np.arange(0, 23, 4))
    plt.savefig(temp_path, format='png')
    plt.close()

    # Upload image to public storage bucket
    if destination_type == 'azure':
        img_storage.upload_blob(temp_path)
        img_url =  img_storage.account_url + img_storage.container_name + '/' + filename

    # Default to local path in static directory
    else:
        static_path = 'images/plots/' + filename
        local_path = os.path.join('./static', static_path)
        shutil.copyfile(temp_path, local_path)
        img_url =  url_for('static', static_path)
    
    # Cleanup temp file
    # os.remove(temp_path)
    return img_url

    