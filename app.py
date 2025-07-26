import pandas as pd
import ingest_manipulate_data as imd
import plotly_express as px
from dash import Dash, dcc, html, Input, Output, dash_table as dt
import os
from dotenv import load_dotenv

import warnings
warnings.filterwarnings('ignore')

# Loading app_token from environment variables
load_dotenv()
port = os.getenv('port')


df = imd.ingest_manipulate_data()
zipcodes = list(df.zipcode.unique()) # Unique list of zipcodes

# Creating dictionary with the audience and service options for the dependent dropdown (id: filter-dropdown)
filter_options = {
    'audience': ['adults', 'youth', 'older_adults', 'families'],
    'service': ['sud_residential', 'substance_use','mental_health','mental_health_and_sud', 'housing',
    'mh_residential','opioid','crisis_services','involuntary','detox']
}

app = Dash() # Initializing app

# Setting app layout 
app.layout = html.Div(
    children=[
        html.Div([
            html.Label("Filter by zipcode: "), # Label for dropdown
            dcc.Dropdown(zipcodes, '98144', id='zipcode-dropdown'), # Zipcode dropdown
        ]),
        html.Br(), # Br tag to separate content
        html.Br(), # Br tag to separate content

        html.Div([
            html.Label('Filter by intended audience or desired service: '), # Label for dropdown
            # Audience/service dropdown that sets values for next dropdown
            dcc.Dropdown(options = list(filter_options.keys()),
                     value = 'audience', id='audience-service-dropdown')
        ]),
        html.Br(), # Br tag to separate content

        # Specific audience/service dropdown, filter set by above dropdown
        dcc.Dropdown(id = 'filter-dropdown'),
        html.Br(), # Br tag to separate content

        # Creates data table
        dt.DataTable(
            id="table-container",
            style_cell={
                'whiteSpace': 'normal',
                'height': 'auto'
            },
           columns=[
                {"name": i, "id": i} for i in ['provider','service','audience', 'notes']
            ],
            data=[]
        ),
    
        # Creates graph
        dcc.Graph(id='graph')
        
    ]
)

@app.callback(
    Output('filter-dropdown', 'options'),
    Input('audience-service-dropdown','value')
)
def decide_filter(filter_selection):
    """
    Input: List of possible filter options to select from. 

    Goal: Inform options in dependent dropdown based on independent dropdown.

    Output: Dependent dropdown options.
    """
    return [{'label': i, 'value': i} for i in filter_options[filter_selection]]


@app.callback(
    Output('filter-dropdown', 'value'),
    Input('filter-dropdown','options')
)
def set_filter_value(filter_dropdown_options):
    """
    Input: List of possible dropdown options.

    Goal: Select initial dropdown value from list.

    Output: Set initial dropdown value.
    """
    return filter_dropdown_options[0]['value']


@app.callback(
    Output('graph', 'figure'),
    [Input('zipcode-dropdown', 'value'),
    Input('audience-service-dropdown', 'value')]
)
def display_graph(zipcode_dropdown:str, audience_service_dropdown:str):
    """
    Input: `df` (pd.DataFrame) to create the graph, `zipcode_dropdown` (str) indicating the user's selected zipcode, `audience_service_dropdown` (str) indicating if the user selected 'audience' or 'service'

    Goal: Filter the dataframe depending on `zipcode_dropdown` and `audience_service_dropdown` values. 
    Create a graph depicting the distribution of providers per audience/service type in selected zipcode.

    Output: Graph
    """
    global df
    filter_df = df[df['zipcode']==zipcode_dropdown].reset_index(drop=True) # Filter to selected zipcode

    # Explode selected audience/service to have one row for each provider meeting the criteria
    filter_df = filter_df.explode(audience_service_dropdown).reset_index(drop=True) 
    
    # Custom title depending on audience/provider input
    if audience_service_dropdown == 'audience':
        specific_title = 'Distribution of providers per audience type in ' + zipcode_dropdown
    elif audience_service_dropdown == 'service':
        specific_title = 'Distribution of providers per service type in ' + zipcode_dropdown

    # Create graph with filtered data and custom title
    fig= px.histogram(filter_df, x=audience_service_dropdown, title=specific_title) 

    return fig



@app.callback(
    Output("table-container", "data"), 
    Input('zipcode-dropdown', 'value') ,
    Input('audience-service-dropdown', 'value'),
    Input('filter-dropdown', 'value')
)
def update_table(zipcode_dropdown, audience_service_dropdown, filter_dropdown):
    """
    Input: Selected zipcode, audience/service, and dependent filter.

    Goal: Create a filtered data table with information from dropdowns.

    Output: Data table showing filtered information.
    """
    global df
    
    zipcode_df = df[df['zipcode']==zipcode_dropdown].reset_index(drop=True) # Filter to selected zipcode
    
    # Filter to selected audience/service of interest, if it is provided
    filter_df = zipcode_df[zipcode_df[audience_service_dropdown].apply(lambda x: filter_dropdown in x)] 

    # If the data exists
    if len(filter_df) > 0: 
        # Convert list objects to comma-separated string
        filter_df['audience'] = filter_df.apply(lambda x: ", ".join(x['audience']), axis=1)
        filter_df['service'] = filter_df.apply(lambda x: ", ".join(x['service']), axis=1)
        filter_df['notes'] = filter_df.apply(lambda x: ", ".join(x['notes']), axis=1)

        # Replace empty notes with None
        filter_df.loc[filter_df['notes'] == '', 'notes'] = None

        filter_df.reset_index(inplace=True,drop=True)

    return filter_df.to_dict("records")
        

if __name__ == '__main__':
    app.run(use_reloader=False, port=port) # debug=True)
