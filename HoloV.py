""" HoloViz Data Analysis

This script generates a variety of widgets that enable users
to explore a data set. Users can interactively view the data
set, explore column statistics of entire or filtered data frames, 
or visualize the data through scatter plots, histograms, boxplots, 
density plots, and even maps.

To achieve this functionality you must first run view_data() by
providing it a valid csv file. You can then consecutively run 
select_data, explore_data, and visualize. Please note that if
data set was modified in the accompanying script 'FileScript'
through the 'variable selector widget', select_data() should be
run after this. If no modifications were made, you may continue.

This script requires that pandas, panel, holoviews, hvplot, 
and datashader be installed within the Python environment you 
are running this script on.
"""


# Importing libraries
import panel as pn
import holoviews as hv
from holoviews import opts
import hvplot.pandas
import datashader.geo
import pandas as pd
from holoviews.element.tiles import OSM

# Importing other scripts
import FileScript as fs

# Loading extensions
pn.extension()
hv.extension('bokeh')


def view_data(path, df=False, rows=True):
    """
    view_data produces an interactive display of a
    data frame that allows the user to navigate rows
    and columns
    
    :param path: file path
    :param df: whether input is data frame
    :param rows: whether to show row widget
    :returns: interactive data frame display
    """
    
    global original_df
    
    if not df:
        # Reading file at path
        if path.endswith(('.txt', 'tsv')):
            try:
                data = pd.read_csv(path, sep='\t', encoding="latin-1")
            except UnicodeDecodeError:
                data = pd.read_csv(path, sep='\t', encoding="ISO-8859-1")
        elif path.endswith('.csv'):
            try:
                data = pd.read_csv(path, encoding="latin-1")
            except UnicodeDecodeError:
                data = pd.read_csv(path, encoding="ISO-8859-1")
        else:
            return None
    
        # Reads in data set
        original_df = data
    
    else:
        # Reads in data set
        original_df = path
        
    # Row Selector widget
    row_selection = pn.widgets.IntSlider(name='Navigate Rows', start=0, 
                                         end=len(original_df)-1, width=300, 
                                         margin=(25,50,-15,15))

    # Column Selector widget
    col_selection = pn.widgets.IntSlider(name='Navigate Columns', start=0, 
                                         end=len(original_df.columns)-1, width=300, 
                                         margin=(25,0,5,5))
        
    if len(original_df.columns) <= 10:
        if not rows:
            widgets = pn.Column(original_df)
        else:
            row_selection.margin = (25,50,5,15)
            # Produces slider widget to interactively view columns
            @pn.depends(row_selection.param.value)
            def select_row(row=0):
                return original_df.iloc[row:row+4, :]

            widgets = pn.Column(row_selection, select_row)

    elif rows:

        # Produces slider widget to interactively view rows and columns
        @pn.depends(row_selection.param.value, col_selection.param.value)
        def select_row(row=0, col=0):
            return original_df.iloc[row:row+4, col:col+10]

        selector = pn.Row(row_selection, col_selection)
        widgets = pn.Column(selector, select_row)
    
    else:

        # Produces slider widget to interactively view columns
        @pn.depends(col_selection.param.value)
        def select_row(col=0):
            return original_df.iloc[:, col:col+10]

        widgets = pn.Column(col_selection, select_row)
    
    return widgets


def select_data():
    """
    select_data allows users to select the data frame
    they would like to analyze.
    
    :returns: widget to select data frame
    """
    
    # Determines the existance of a user created data frame
    possible_opts = ['---','Original', 'Saved']
    saved =  hasattr(fs, 'final_df')
    original = 'original_df' in globals()
    true_opts = possible_opts[:original+saved+1]

    # Uses user input to choose data frame 
    def df_selected(event):
        """
        df_selected reacts to user input to the
        data frame selector widget
        
        :param event: string representing data frame
        """
        
        global df
        if event.new == '---':
            return
        elif event.new == 'Saved':
            df=fs.final_df
        elif event.new == 'Original':
            df=original_df

    # Data Frame Selector widget
    df_selection = pn.widgets.Select(name='Select table to analyze:', options=true_opts)
    df_selection.param.watch(df_selected, ['value'])

    return df_selection


quantitative, qualitative = [], []

def explore_data():
    """
    explore_data displays widgets that enable the user to
    explore a data frame. This includes the ability to view
    column statistics or filter the data frame where a column
    is of a certain value.
    
    :returns: widgets that enable the user to explore data
    """
    
    # Finding quantitative and qualitative variables
    for column in df.columns:
        if df[column].dtype == 'O':
            qualitative.append(column)
            continue
        quantitative.append(column)
    
    # Comparison Selector widget
    comp_operators = ['None', 'less than', 'greater than', 'equal to', 'not equal to']
    comparison_selector = pn.widgets.Select(name='Comparison Operator', options=comp_operators)
    
    # Column Selector widget
    column_selector = pn.widgets.Select(name='Variable', options=['Entire table']+df.columns.tolist())
    
    # Value Selector widget
    value_selector = pn.widgets.Select(name='Value')
    
    # Value Slider widget
    value_slider = pn.widgets.FloatSlider(name='Value')
    
    # Info Selector widget
    info_select = pn.widgets.Select(name='Variable Statistics (Shown Below)', options=df.columns.tolist())

    @pn.depends(column_selector.param.value)
    def show_values(column):
        """
        show_values displays unique values for variable selected
        with the column selector widget. This can be either a 
        slider (quantitative) or a selector (qualitative)
        
        :param column: string representing column name
        :returns: widget, either slider or selector
        """
        
        # Displays value selector with no values if entire
        # table is selected
        if column == 'Entire table':
            return pn.Row(value_selector, width=150)
    
        # Displays slider when quantitative variable selected
        elif column in quantitative:
            value_slider.start = df[column].min()
            value_slider.end = df[column].max()
            comparison_selector.options = comp_operators
            return pn.Row(value_slider, width=150)
    
        # Displays selector when qualitative values selected
        else:
            options = df[column].unique().tolist()
            value_selector.options = ['None']+options
            comparison_selector.options = ['None', 'equal to', 'not equal to']
            return pn.Row(value_selector, width=150)
        

    @pn.depends(column_selector.param.value, comparison_selector.param.value, 
                value_selector.param.value, value_slider.param.value, info_select.param.value)
    def display_data(col, comp, val_select, val_slide, info_col):
        """
        display_data displays filtered data frame and column statistics
        
        :param col: string representing column selector selection
        :param comp: string representing comparison selector selection
        :param val_select: string representing value selector selection
        :param val_slide: integer representing value slider selection
        :param info_col: string representing info selector selection
        :returns: interactive filtered data frame and info widget
        """
    
        # User selects 'Entire table'
        if col == 'Entire table':
            comparison_selector.disabled = True
            value_selector.disabled = True
        
            # Interactive data frame + slider
            up_row = pn.Row(view_data(df, True), margin=(-20,0,0,0))
        
            # Column info widget
            info = df[[info_col]].describe().T.reset_index(drop=True)
            info_widget = pn.Row(info, margin=(-10,0,0,480))
        
            return pn.Column(info_widget, up_row)
    
        # Ensures comparison and value are enabled
        elif comparison_selector.disabled:
            comparison_selector.disabled = False
            value_selector.disabled = False
    
        # Data frame not displayed if expression not complete
        if (comp == 'None') or (val_select == 'None'):
            return
    
        # Filters dataframe and creates information table
        filtered = filter_data(col, comp, val_select, val_slide)
        info = filtered[[info_col]].describe().T.reset_index(drop=True)
        info_widget = pn.Row(info, margin=(-10,0,0,480))
    
        # Row slider will not function correctly if data frame is of size 1.
        if len(filtered) <= 1:
            return pn.Column(info_widget, view_data(filtered, True, False))
        else:
            up_row = pn.Row(view_data(filtered, True, True), margin=(-20,0,0,0))

            return pn.Column(info_widget, up_row)
        
        
    def filter_data(col, comp, val_select, val_slide):
        """
        Helper function for display data
        
        filter_data filters the displayed data frame based on
        the user's selected options with the widgets
        
        :param col: string representing column in df
        :param comp: string representing comparison operator
        :param val_select: string representing value to compare to
        :param val_slide: integer representing value to compare to
        :returns: filtered data frame
        """
        
        if col == 'Entire table':
            return df
    
        elif col in quantitative:
            if comp == 'less than':
                filtered = df[df[col] < val_slide]
            elif comp == 'greater than':
                filtered = df[df[col] > val_slide]
            elif comp == 'equal to':
                filtered = df[df[col] == val_slide]
            else:
                filtered = df[df[col] != val_slide]
        
        else:
            if comp == 'not equal to':
                filtered = df[df[col] != val_select]
            else:
                filtered = df[df[col] == val_select]
            
        return filtered

    # Displays widgets produced above
    var_comp = pn.Row(column_selector, comparison_selector, width=300)
    expression = pn.Row(var_comp, show_values, css_classes=['widget-box'])
    info = pn.Column(info_select, margin=(0,0,0,20), css_classes=['widget-box'])
    head = pn.Row(expression, info)
    widgets = pn.Column(head, display_data)
    
    return widgets


def visualize():
    
    # Finds columns with only unique values - too many options!
    unique = find_unique()

    # Detects latitude and longitude columns and
    # creates data frame containing these coordinates.
    coord_out = detect_coords()
    coordinates = coord_out[0]
    has_coords = coord_out[1]
        
    # Defining available plot types – for user
    uni = ['histogram', 'boxplot']
    multi = ['scatter']
    group = ['density']
    maps = []
    if has_coords:
        maps = ['map']
    
    # Plot Type Selector widget
    p_selector = pn.widgets.Select(name='1. Plot Type', options=multi+uni+group+maps)
    
    # X Variable Selector widget
    x_selector = pn.widgets.Select(name='2. X Variable', options=quantitative)
    
    # Y Variable Selector widget
    y_selector = pn.widgets.Select(name='3. Y Variable', options=quantitative)
    
    # Identifier Selector widget
    identifier = pn.widgets.Select(name='Identifier', options=qualitative)
    
    # Size Selector widget
    size = pn.widgets.FloatSlider(name='Size', start=3, value=6, end=12)
    
    # Groupby Selector widget
    g_selector = pn.widgets.Select(name='Groupby (Density Only)', options=['None']+unique)
    
    # Subgroup Selector widget
    sg_selector = pn.widgets.Select(name='Subgroup', options=['None'])
    
    # Dummy Selector widget
    dummy = pn.widgets.Select(name='Dummy')


    def disabler(x, y, s, i, g, sg):
        """
        Helper function
        
        disabler disabled and enables widgets. Used when
        particular plot types are selected and widgets
        are not needed
        
        :param x: bool to enable/disable x selector
        :param y: bool to enable/disable y selector
        :param s: bool to enable/disable size selector
        :param i: bool to enable/disable identifier selector
        :param g: bool to enable/disable groupby selector
        :param sg: bool to enable/disable subgroup selector
        """
        
        x_selector.disabled = x
        y_selector.disabled = y
        size.disabled = s
        identifier.disabled = i
        g_selector.disabled = g
        sg_selector.disabled = sg
    
    
    @pn.depends(p_selector.param.value, x_selector.param.value, y_selector.param.value,
                identifier.param.value, size.param.value, g_selector.param.value, 
                sg_selector.param.value)
    def plotter(p_selector, x, y, identifier, size, group_col, sg_value):
        """
        plotter creates plots based on the selected values for the selectors
        defined above. The kind of plot is determined by the p_selector and
        the plot's qualities are dependent on the other selectors.
        
        :param p_selector: string representing type of plot to produce
        :param x: string representing the x value
        :param y: string representing the y value
        :param identifier: string representing identifier to use
        :param size: string representing the size of plot values
        :param group_col: string representing the group by column
        :param sg_value: string representing the subgroup column
        :returns: hvplot
        """
    
        # Defining available plot types – for hvplot()
        multi = ['scatter']
        uni = ['histogram', 'boxplot']
    
        # Case for scatterplot, all wdigets except Groupby and Subgroup enabled
        if (x == y) and not (p_selector in uni+group+maps):
            disabler(False, False, False, False, True, True)
            return
    
        # Multivariate plots
        elif p_selector in multi:
            disabler(False, False, False, False, True, True)
            
            ident = []
            if len(qualitative) > 0:
                ident = [identifier]
        
            # Scatter plots with more than 4000 points significantly increase lag in plot
            # interactivity. HoloViz's datashade made to alleviate these situations.
            if len(df) > 4000:
                plot = df.hvplot(x, y, hover_cols=ident, datashade=True,
                             hover_color='red', kind=p_selector).opts(frame_height=300)
                
            else:
                plot = df.hvplot(x, y, hover_cols=ident, hover_color='red', 
                                 kind=p_selector).opts(frame_height=300, size=size)
    
        # Univariate plots
        elif p_selector in uni:
            disabler(False, True, True, True, True, True)
            
            # Determining univariate plot selection
            choice = [i for i in ['hist', 'box'] if p_selector.startswith(i)][0]
            horizontal = False
        
            if choice == 'box':
                horizontal = True
            
            plot = df.hvplot(y=x, hover_color='red', kind=choice, invert=horizontal).opts(frame_height=300)
    
        # Density/groupby plot
        elif p_selector in group:
            disabler(False, True, True, True, False, False)
        
            # Filter data frame to group restrictions
            if (group_col != 'None') & (sg_value != 'None'):   
                filtered_df = df[df[group_col] == sg_value]
                plot = filtered_df.hvplot(y=x, kind='kde').opts(frame_height=300)
                
            else:
                plot = df.hvplot(y=x, kind='kde').opts(frame_height=300)

        # Map plot
        elif p_selector in maps:
            disabler(True, True, False, False, True, True)
            
            ident = []
            if len(qualitative) > 0:
                ident = [identifier]
                
            plot = OSM() * coordinates.hvplot.points(x='easting', y='northing',
                                                     hover_cols=ident, size=size)
        
        return plot


    # Produces options for 'Subgroup' after selecting groupby
    def group_trigger(event):
        """
        group_trigger updates options for subgroup selector
        after groupby selector is chosen.
        
        :param event: string representing the groupby selector selection
        """
        
        if g_selector.value == 'None':
            sg_selector.value == 'None'
            sg_selector.disabled = True
            return
        sg_selector.disabled = False
        sg_selector.options = ['None'] + df[g_selector.value].dropna().unique().tolist()
    
    g_selector.param.watch(group_trigger, ['value'])


    # Displays widgets produced above
    selectors2 = pn.Row(p_selector, x_selector, y_selector)
    scatter_options = pn.Column(identifier, size, margin=(40,0,0,0), 
                                width=250, css_classes=['widget-box'])

    group_options = pn.Column(g_selector, sg_selector, margin=(20,0,0,0), 
                              width=250, css_classes=['widget-box'])

    toolbar = pn.Column(scatter_options, group_options, margin=(0,10,0,0))

    widgets = pn.Column(selectors2, pn.Row(toolbar, plotter))
    
    return widgets


def find_unique():
    """
    Helper function for visualize
    
    find_unique finds qualitative variables that contain
    only/mostly unique values. Prevents groupby selector
    from displaying all values in a column containing only
    or more than 150 unique values
    
    :returns: list of variables with many unique values
    """
    
    unique = []
    for col in qualitative:
        col_data = df[col].dropna()
        size = len(col_data)
        n_unique = col_data.nunique()
        
        if n_unique >= 150:
            continue
            
        if col_data.nunique() < size-1:
            unique.append(col)
            
    return unique


def detect_coords():
    """
    Helper function for visualize
    
    detect_coords detects latitude and longitude columns
    and creates new data frame containing these coordinates
    
    :returns: data frame containing coordinates if coordinates exist
    """
    lat, lon = [],[] 

    for col in df.columns:
        if '#number#hidden' in col:
            if 'lon' in col:
                lon.append(col)
            elif 'lat' in col:
                lat.append(col)
        elif 'latitude' in col.lower():
            lat.append(col)
        elif 'longitude' in col.lower():
            lon.append(col)

    if len(lat) > 0 and len(lon) > 0:
        x, y = datashader.geo.lnglat_to_meters(df[lon[0]], df[lat[0]])
        coordinates = df.join([pd.DataFrame({'easting': x}), 
                               pd.DataFrame({'northing': y})])
        
        return coordinates, True
    
    return None, False
