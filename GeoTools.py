""" Geocoder

This script has one main functions: geocode a user defined 
column from a pandas data frame 

To achieve this functionality simply run geocoder().

This script requires that requests, pandas, numpy, and panel 
be installed within the Python environment you are running 
this script on.
"""

# Importing libraries
import requests
import pandas as pd
import numpy as np
import panel as pn

# Importing required scripts
import HoloV as ho

# Loading extensions
pn.extension()


def geocoder(df):
    """
    geocoder allows users to select a column to geocode
    and produce latitude/longitude columns for those
    respective locations.
    
    :param df: data frame containing a column that can be geocoded
    :returns: widgets to select column to geocode
    """
    # Determine string columns
    is_string = df.dtypes == 'object'
    options = is_string[is_string==True]
    # Geocode Column Selector widget
    geo_options = ['None'] + list(options.index.unique())
    geo_select = pn.widgets.Select(name='Select Column to Geocode', options=geo_options, width=200)

    # Geocode Button widget
    geo_button = pn.widgets.Toggle(name='Geocode', margin=(15,0,0,30), width=200)
    
    # Progress widget
    global progress_geocode
    progress_geocode = pn.pane.Markdown('')
    
    # Stores geocoded and non-geocoded values
    global is_geocoded
    global not_geocoded
    is_geocoded = []
    not_geocoded = []


    @pn.depends(geo_button.param.value)
    def geocode_trigger(click):
        """
        geocode_trigger initializes geocoding when the 
        geocode button widget is selected.
    
        :param click: bool indicated click on geocode button widget
        :returns: updated data frame with latitude and longitude columns
        """
        
        updated_df = df
        if geo_select.value == 'None':
            geo_button.value = False
            return ho.view_data(updated_df, True, True)

        if geo_button.value == True:
            # Temporarily disables geocode button
            geo_button.disabled = True
            geo_button.value = False
            return 'Geocoding in progress. Please wait..'
        
        # Checks for existing latitude/longitude columns
        for col in updated_df.columns:
            if ('latitude' in col.lower()) or ('longitude' in col.lower()):
                error = '#####Coordinate columns already exist.'
                return pn.Column(error, ho.view_data(updated_df, True, True))
            
        # Geocodes and stores latitude/longitude for each address
        unique_vals = updated_df[geo_select.value].dropna().unique()
        coords = pd.Series(unique_vals).apply(get_coords)
        address_dict = {}
        coords.apply(lambda address: address_dict.update(address))
        
        # Creating latitude/longitude columns
        updated_df['Latitude'] = (updated_df[geo_select.value]
                                  .map(address_dict)
                                  .apply(lambda x: x[0] if type(x) == list else None))
        updated_df['Longitude'] = (updated_df[geo_select.value]
                                   .map(address_dict)
                                   .apply(lambda x: x[1] if type(x) == list else None))

        progress_geocode.object = ''
        
        report_message = pn.pane.Markdown('**Geocoding Finished:**', margin=(24,20,0,0))
        geocoded_vals = pn.widgets.Select(name='Geocoded Values', options=is_geocoded, width=200)
        non_geocoded_vals = pn.widgets.Select(name='Non Geocoded Values', options=not_geocoded, width=200)
        full_report = pn.Row(report_message, geocoded_vals, non_geocoded_vals, margin=(5,0,20,0))
                        
        row_slider = ho.view_data(updated_df, True, True)
        full_display = pn.Column(full_report, row_slider)

        return full_display
    
    geo_widgets = pn.Row(geo_select, geo_button, margin=(0,0,15,0))
    widgets = pn.Column(geo_widgets, geocode_trigger, progress_geocode)

    return widgets


def get_coords(address):
    """
    get_coords uses the data science tool kit to geocode
    addresses.
    
    :param address: string representing location
    :returns: dictionary with keys as addresses and
              values as latitude/longitude coordinates
    """
        
    # Base progress menu for geocoder
    base_progress = ('| Placename | Status | Latitude | Longitude |' + 
                     '\n|:---------:|:-------:|:--------:|:---------:|')
    
    if pd.isnull(address):
        progress_geocode.object = base_progress + '\n| Null | Failed | Null | Null |'
        return 
    
    # dstk API url
    partial_url = "http://www.datasciencetoolkit.org/maps/api/geocode/json?sensor=false&address="
    
    # Reformats string to work with dstk API
    address_reformat = address.replace(" ", "+").replace("'", "")
    
    # Geocodes address
    response = requests.get(partial_url+address_reformat).json()
    
    # Handles case of no results/invalid address
    if response['status'] == 'ZERO_RESULTS':
        not_geocoded.append(address)
        progress_geocode.object = base_progress + '\n| ' + address + ' | Failed | Null | Null |'
        return {address: [None, None]}
    
    # Extracts result
    coords = response['results'][0]['geometry']['location']
    lat = coords['lat']
    lon = coords['lng']
    
    progress_geocode.object = base_progress + ('\n| ' + address + ' | Geocoded | ' + 
                                               str(lat) + ' | ' + str(lon) + ' |')
    
    is_geocoded.append(address)
    
    return {address: [lat, lon]}



    