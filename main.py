# import modules:
from uk_covid19 import Cov19API
import numpy as np
from flask import Flask, render_template, request

# for plotting:
#import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import base64 
import io


def generate_df(area_type, area_name, data_to_display, 
                from_date="", to_date=""):
    """
    Function to generate COVID data (pandas dataframe).
    
    Parameters:
        area_type: string
            One of the areaType metrics as per the API documentation
            (https://coronavirus.data.gov.uk/details/developers-guide)
            
        area_name: string
            Name of the region (dependent on area_type parameter)
            
        data_to_display: string
            One of the valid metrics for structure as per the API documentation
            
        from_date (Optional): string
            Should be in the format "yyyy-mm-dd". The date at which the
            data should begin to be considered.
            
        to_date (Optional): string
            Should be in the format "yyyy-mm-dd". The end date for which the
            data should be considered.
            
    Returns:
        
        df: pandas.DataFrame object
            pandas DataFrame containing the relevant COVID data.
        
        from_date: string
            In the format "yyyy-mm-dd". Can vary from the input from_date if
            it's not valid or not specified.
            
        from_date: string
            In the format "yyyy-mm-dd". Can vary from the input from_date if
            it's not valid or not specified.
    
    """
    
    filters = [
        f"areaType={area_type}",
        f"areaName={area_name}"
    ]

    structure = {
        "date": "date",
        "areaName": "areaName",
        "areaCode": "areaCode", 
        data_to_display: data_to_display
    }

    api = Cov19API(filters=filters, structure=structure)
    df = api.get_dataframe()

    # reverse row order so data are in chronological order:
    df = df.iloc[::-1]
    df.reset_index(drop=True, inplace=True)
    
    # dealing with bad user inputs and splicing the data:
    if from_date == "":
        from_date = df["date"][0]
    elif from_date <= df["date"][0] or from_date >= list(df["date"])[-1]:
        from_date = df["date"][0]
    else:
        df = df[df["date"] >= from_date]
    
    if to_date == "":
        to_date = list(df["date"])[-1]
    elif to_date >= list(df["date"])[-1] or to_date <= list(df["date"])[0]:
        to_date = list(df["date"])[-1]
    else:
        df = df[df["date"] <= to_date]
    
    # reset indices again:
    df.reset_index(drop=True, inplace=True)
    return df, from_date, to_date    


# creating Flask app:
app = Flask(__name__)

@app.route("/", methods=['GET', 'POST'])
def home():
    # home page
    return render_template("index.html")

# displaying figure based on:
# https://matplotlib.org/stable/gallery/user_interfaces/web_application_server_sgskip.html

# translation dictionary so that graphs have better titles/axis labels:
dataStr2names = {
    "newCasesByPublishDate": "New cases", 
    "newDeaths28DaysByDeathDate": "New deaths"
}

@app.route("/image", methods=['GET', 'POST'])
def image():
    # page on which we'll display the graph representation of the relevant data
    
    # get data inputted by user on home page:
    areaType = request.form.get('areaType')
    areaName = request.form.get('areaName')
    from_date = request.form.get("start_date")
    to_date = request.form.get("end_date")
    data_to_display = request.form.get("data_to_display")
    
    # generate dataframe according to user inputs:
    df, from_date, to_date = generate_df(areaType, areaName, data_to_display, 
                                         from_date=from_date, to_date=to_date)
    
    # create and edit matplotlib figure (to make it more readable):
    #fig = plt.figure()
    fig = Figure()
    fig.supxlabel("date")
    fig.supylabel(dataStr2names[data_to_display])
    ax = fig.subplots()
    ax.set_title(f"{dataStr2names[data_to_display]} in {areaName}" +
                 f"\n from {from_date} to {to_date}")
    ax.plot(df["date"], df[data_to_display])
    start, end = ax.get_xlim()
    ax.tick_params(which="major", labelsize=8)
    ax.tick_params(axis="y", labelsize=7)
    ax.set_xticks(np.arange(start, end, step=(end-start)/6))    # change ticks to make it more readable
    
    # save image as png and render:
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    data = base64.b64encode(buf.getbuffer()).decode("ascii")
    return render_template("image.html", data=data, from_date=from_date, to_date=to_date)
    

# run app:
if __name__ == "__main__":
    app.run()
    
"""
Some brief ideas on testing (there wasn't enough time to implement all my
ideas for testing)

The software was tested and adjusted for robustness mostly by simply trying
different edge cases when the app was running. For example, seeing what happens
when the start date inputted is later than the end date inputted. 

One could implement unit tests, for example, checking that the size of the 
data frame changes as expected with changing dates (i.e. smaller time windows
lead to smaller data frames).

One could also implement unit tests checking that data exists in different 
cases (i.e. a non-empty data frame is produced). This would become more important
when different area types and structure metrics are used 
(since not all area types are compatible with all structure metrics)

"""
