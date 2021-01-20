# Bike Share Prediction

This application is an exploration of machine learning prediction using weather data and bike sharing transaction data from Capital Bikeshare in the Washington, DC area.

The application can create predictions for number of bike share rides per hour given a date and expected weather conditions. The main page will automatically pull the weather forecast for the next day and graph the prediction. Manual entry of prediction parameters is also available.

The application also has options for exploring and updating the historical data in memory and visualizing historical values.

This repository includes a Jupyter notebook for preparing the source data and training the machine learning model.

# Data cleansing, exploration, and ML model training

Open the Jupyter notebook in `models/ml-model.ipynb`. Follow the instructions to explore the data and create and save a trained Machine Learning model

# Application Configuration

The application can use local storage or Azure storage for pulling data files and storing generated images. It will default to local storage in which case the prepared hourly_rides.csv file should be placed in this directory under `\data\prepared\` directory as will be done by the Jupyter notebook. It will expect the saved Tensorflow data model to be in the `models\bike_share` directory as output by the Jupyter notebook. All generated images will be placed in the Flask static directory.

For either local or Azure storage options. The following environment variable must be set:

  * WEATHER_API_KEY - This is the API key that allows access to the weather forecast API. A free account can be set up at https://openweathermap.org/api

To configure Azure Storage the following variables are required:

  * AZURE_STORAGE_ACCOUNT_URL - Azure storage account where the data file and images are stored (e.g. https://bikeshare.blob.core.windows.net/)
  * AZURE_STORAGE_DATA_CONTAINER_NAME - The Azure storage container in the account where the data file is stored. This should be a private container.
  * AZURE_STORAGE_IMAGE_CONTAINER_NAME - he Azure storage container in the account where the image files will be uploaded. This should be a public blob container.

If running the application on a system in Azure with managed identity assigned, the application will automatically use those credentials. If not, you must create and Azure Service Principal and secret and set the following variables to configure authentication:
  
  * AZURE_TENANT_ID
  * AZURE_CLIENT_ID
  * AZURE_CLIENT_SECRET

# Application installation

The application requires that python 3.8 be installed. It also has several prerequisite packages that must be installed. Pipenv can be used for local testing and will install all dependencies from the pipfile.

```
pipenv install
```

The dependencies can also be installed with pip using the requirements file

```
pip install -r requirements.txt
```

# Running the Application

Once all prerequisites and configurations are handled the application can be started by running

```
python app.py
```

This will run the Flask application using the built-in dev server. In production it would be recommended to use a dedicated WSGI server like gunicorn or run this code in a platform like Azure App Service that handles that for you.