# Data Structures / Algorithms Enhancement

## Narrative

This artifact is almost wholly original though it was definitely inspired by the animal shelter project that incorporated MongoDB database software and Plotly dashboard software.

The idea behind this was to create a better thermostat demo. The TI board (via I2C) delivered temperature information (every 200 ms), the information was put out as an appended row to a CSV file (every 1000 ms), and then in here that last line gets parsed and has its values used for the thermostat display (every 1000 ms). The algorithm here keeps things constantly flowing. See a demonstration of the flow in the video below:

![UART -> CSV -> Dash]({{site.url}})

Note that though there is the inclusion and reference to the MongoDB CRUD class "therm_records" apart from creating the initial pandas dataframe it doesn't come into play. It turns out that it was just simpler and faster to grab the needed information directly rather than going through the intermediary of adding that information to a database and then pulling that same information from the database to present here.

```python
import os # to seek the end of the file
import dash # for the app
from dash.dependencies import Input, Output
import dash_daq as daq
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd

from therm_records import thermRecords

username = "admin"
password = "123456"
dbName = "ti_temps"
records = thermRecords(username, password, dbName)

df = pd.DataFrame.from_records(records.read({}))

# function to get and return the last line appended to CSV
def get_last_line():
    # getting the CSV source
    with open("/Users/Tennyson/temps_outfile.csv", "rb") as f:
        try:  # catch OSError in case of a one line file 
            f.seek(-2, os.SEEK_END)
            while f.read(1) != b'\n':
                f.seek(-2, os.SEEK_CUR)
        except OSError:
            f.seek(0)
    last_line = f.readline().decode()
    return last_line

# getting the initial value for the thermostat display
initVal = get_last_line()

app = dash.Dash(__name__)

app.layout = html.Div([
    # ultimately use the DAQ LED Display rather than the thermometer
    daq.LEDDisplay(
        id='my-thermostat-1',
        label="Temperature",
        value=int(initVal.split(",")[0]),
        size=256,
        color='black',
        backgroundColor="#777777"
    ),
    dcc.Interval(
            id='interval-component',
            interval=1*1000, # in milliseconds
            n_intervals=0
        )
])

# the function that updates the themostat every 1 second
@app.callback(
    Output('my-thermostat-1', 'value'),
    Input('interval-component', 'n_intervals')
)
def update_thermostat(n):
    value=get_last_line()
    return f"{value.strip().split(',')[0]} ºC"

# the function that updates the digits color
@app.callback(
    Output('my-thermostat-1', 'color'),
    [Input('interval-component', 'n_intervals')]
)
def update_temp_col(n):
    heatVal=get_last_line()
    if heatVal.strip().split(",")[2] == "1":
        return 'orange'
    else:
        return 'black'

# the function that updates the background color
@app.callback(
    Output('my-thermostat-1', 'backgroundColor'),
    [Input('interval-component', 'n_intervals')]
)
def update_bg_col(n):
    heatVal=get_last_line()
    if heatVal.strip().split(",")[2] == "1":
        return '#FF5E5E'
    else:
        return '#777777'

# the function that updates the label
@app.callback(
    Output('my-thermostat-1', 'label'),
    [Input('interval-component', 'n_intervals')]
)
def update_label(n):
    heatVal=get_last_line()
    if heatVal.strip().split(",")[2] == "1":
        return f'Heating to {heatVal.strip().split(",")[1]} ºC'
    else:
        return 'Temperature'

if __name__ == '__main__':
    app.run_server(debug=False)
```
[tennyson-mccalla.github.io](https://tennyson-mccalla.github.io)