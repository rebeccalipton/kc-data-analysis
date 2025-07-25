def ingest_manipulate_data():
    """
    Input: N/A

    Goal: Defining function to be run as import for dashboard. Ingests data from API endpoint, cleans, and manipulates to desired output for dashboard integration.

    Output: Cleaned dataframe (pd.DataFrame)
    """
    # Imports
    import pandas as pd
    from sodapy import Socrata
    from dotenv import load_dotenv
    import os
    import ast

    # Loading app_token from environment variables
    load_dotenv()
    app_token = os.getenv('app_token')

    # Connecting to API endpoint per documentation
    client =  Socrata("data.kingcounty.gov", app_token)
    results = client.get('sep3-3pj3')

    df = pd.DataFrame.from_records(results) # Converting to dataframe

    # Dropping unnecessary columns
    df = df.drop([':@computed_region_pg2z_4vz6', ':@computed_region_6hpt_4ha3', ':@computed_region_ujgi_eduq', 'website', 'phone', 'locations'], axis=1) 

    # Extracting keys/values from address field into their own columns of dataframe
    df_address = pd.json_normalize(df['address'])
    df = pd.concat([df, df_address], axis=1)

    def extract_zipcode_from_address(address: str) -> str | None:
        """ 
        Input: `address` (string)

        Goal: Data import has address formatted as a dict but in type string. Try to evaluate address string as a dict and extract the "zip" key. 

        Output: Return the zip code (str) if available. If an error is thrown, return None.
        """
        try:
            address_dict = ast.literal_eval(address)
            zipcode = address_dict['zip']
        except:
            zipcode = None
        return zipcode


    df['zipcode'] = df.apply(lambda x: extract_zipcode_from_address(x['human_address']), axis=1) # Applying extract_zipcode_from_address function to dataframe
    df = df.drop(['human_address', 'latitude', 'longitude', 'address'], axis=1) # Drop unnecessary columns

    # Defining services offered
    services = ['sud_residential', 'substance_use', 'mental_health','opioid', 'housing', 'involuntary', 'detox', 'mh_residential', 'crisis_services', 'mental_health_and_sud'] 

    # Defining audiences served
    audiences = ['adults', 'youth', 'families', 'older_adults']

    # Transforming data to desired format
    df = pd.melt(df, id_vars = list(set(df.columns) ^ set(services)), value_vars=services, var_name='service', value_name='service_offered')
    df = pd.melt(df, id_vars = list(set(df.columns) ^ set(audiences)), value_vars=audiences, var_name='audience', value_name='audience_offered')
    df = df[(df['audience_offered']==True) | (df['service_offered']==True)] # Filtering data by rows where provider does offer that audience or service
    df.reset_index(inplace=True,drop=True)
    df.drop_duplicates(inplace=True)


    # Separating data into focus on service and focus on audience for later combination into desired format.df

    # Filtering to desired columns 
    df_service = df[['zipcode', 'provider', 'service', 'service_offered', 'notes']]
    df_audience = df[['zipcode', 'provider', 'audience', 'audience_offered', 'notes']]

    # Filtering to if that service or audience is offered, and filtering to desired columns
    df_service = df_service[df_service['service_offered']==True][['zipcode', 'provider', 'service', 'notes']].reset_index(drop=True)
    df_audience = df_audience[df_audience['audience_offered']==True][['zipcode', 'provider', 'audience', 'notes']].reset_index(drop=True)

    df_audience.drop_duplicates(inplace=True)
    df_service.drop_duplicates(inplace=True)

    df_audience.reset_index(inplace=True,drop=True)
    df_service.reset_index(inplace=True,drop=True)

    df = pd.concat([df_audience, df_service]) # Combining both audience and service dataframes

    # Group combined data by provider and zip code, keeping a unique list of non-null audiences, services, and notes
    df = df.groupby(['provider','zipcode']).agg({'audience': lambda x: list(set(x.dropna())), 'service': lambda x: list(set(x.dropna())), 'notes': lambda x: list(set(x.dropna()))}).reset_index()
    return df