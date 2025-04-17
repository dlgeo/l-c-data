import pandas as pd
import glob
import plotly.graph_objects as go
import plotly.io as pio


# send the figures generated with plotly to the browser
pio.renderers.default = "browser"

# set up a custom template for plotly graphs
go_template = dict(
    layout=dict(
        yaxis=dict(
            range=[90, 105],
            tick0=90,
            dtick=5
        )
    )    
)

# apply the template globally
pio.templates["custom"] = go_template
pio.templates.default = "custom"


# Get all csv files in a specified directory
# UPDATE PATH AS REQUIRED
data_files = glob.glob('________*.csv') # INSERT PATH


# Create an empty dictionary to hold the DataFrames we will create
dataframes = {}


# create a filepath for output
file_path = '______' # INSERT PATH


# Read each csv file from directory above into a separate DataFrame
for file in data_files:
    # Extract the file name w/out the extension
    file_name = file.split('/')[-1].split('.')[0]
    # Read csv file into the df and store it in the dict
    dataframes[file_name] = pd.read_csv(file, parse_dates=['taken_on'])


# read the csv containing constant info for each load cell
# and make it a dataframe
# UPDATE PATH AS REQUIRED
info_df = pd.read_csv('________/loadcelldata.csv') # INSERT PATH



# BLOCK to create more columns in each DataFrame
# add new columns to the df, using a calc that refs another df
for name, df in dataframes.items():
    # find the index of the correct row in the referenced df
    value = df.at[1, 'INSTRUMENT ID']
    index = info_df.loc[info_df['load_cell'] == value].index[0]
    # pull constants for that load cell from the info_df
    guage_factor = info_df.at[index, 'guage_factor']
    regression_no_load = info_df.at[index, 'regression_no_load']
    install_temp = info_df.at[index, 'install_temp']
    baseline = info_df.at[index, 'baseline']
    calibration = info_df.at[index, 'calibration_baseline']       
    # calculate the check load to verify accuracy of reported load
    df['Check Load'] = guage_factor * (df['Reading_Ave'] - regression_no_load ) * 0.001
    # calculate the difference between the reported load and the check load
    df['delta'] = df['Load'] - df['Check Load']
    # calculate the load, corrected for temp
    df['Temp Corrected Load'] = guage_factor * (df['Reading_Ave'] 
        - regression_no_load + df['Temperature'] - install_temp) * 0.001
    # calculate the possible percentages of anchor load
    df['Reported as % of Baseline'] = df['Load'] / baseline * 100
    df['Checkload as % of Baseline'] = df['Check Load'] / baseline * 100
    df['Temp Corrected as % of Baseline'] = df['Temp Corrected Load'] / baseline * 100
    df['Temp Corrected as % of Calibration'] = df['Temp Corrected Load'] / calibration * 100
    # create a temp_fault column in the dataframe to be true when
    # thermistor readings are lower than the temp at installation
    df['temp_diff'] = df['Temperature'] - install_temp
    df['temp_fault'] = (df['temp_diff']) < 0
    df['subzero'] = (df['Temperature']) < -1
    # reorder the dataframe according to date
    df.sort_values(by='taken_on', inplace=True)
    # loop thru the DF to add background color when temp_fault is True
    highlight_temp_below_install = []
    highlight_temp_below_zero = []
    for i in range(len(df)):
        # check if current and next rows satisfy the condition
        if df['temp_fault'].iloc[i]:
            x_start = df['taken_on'].iloc[i]
            x_end = df['taken_on'].iloc[i + 1] if i + 1 < len(df) else x_start + pd.Timedelta(1, unit="d")
            highlight_temp_below_install.append((x_start, x_end))
        if df['subzero'].iloc[i]:
            x_start = df['taken_on'].iloc[i]
            x_end = df['taken_on'].iloc[i + 1] if i + 1 < len(df) else x_start + pd.Timedelta(1, unit="d")
            highlight_temp_below_zero.append((x_start, x_end))
    
    
    # BLOCK to create graphs for individual load cells
#   for name, df in dataframes.items():
    fig_load = go.Figure()   # sets up an empty figure   
    # add lines to the graph
    # add a line for the load reported by ADAS
    fig_load.add_trace(go.Scatter(
        x=df['taken_on'],
        y=df['Load'],
        mode='lines+markers',
        name='Load Reported by ADAS'
    ))
    # add a line for the check load, calculated from the individual strain guages
    fig_load.add_trace(go.Scatter(
        x=df['taken_on'],
        y=df['Check Load'],
        mode='lines+markers',
        name='Check Load'
    ))
    # add a line for the temp-corrected load
    fig_load.add_trace(go.Scatter(
        x=df['taken_on'],
        y=df['Temp Corrected Load'],
        mode='lines+markers',
        name='Load Corrected for Temp'
    ))
    # scale the y axis to be +/- 1% from max and min values
    fig_load.update_yaxes(range=[df[['Load', 'Check Load']].min().min() * 0.99, 
                            df[['Load', 'Check Load']].max().max() * 1.01])
    fig_load.update_layout(title='Load Cell {}'.format(name[-3:]))
    fig_load.update_layout(
        xaxis=dict(title='Date'),
        yaxis=dict(title='Load, kips')
    )
    # add a rectangle for each temp_fault range
    for x_start, x_end in highlight_temp_below_install:
        fig_load.add_shape(
            type="rect",
            x0=x_start,
            x1=x_end,
            y0=0,
            y1=1,
            xref="x",
            yref="paper",
            fillcolor="pink",
            opacity=0.3,
            layer="below",
            line=dict(color="pink", width=0)
        )
    for x_start, x_end in highlight_temp_below_zero:
        fig_load.add_shape(
            type="rect",
            x0=x_start,
            x1=x_end,
            y0=0,
            y1=1,
            xref="x",
            yref="paper",
            fillcolor="pink",
            opacity=0.6,
            layer="below",
            line=dict(color="pink", width=0)
        )
    # display the graph    
    #fig_load.show()
    # save figure as PDF
    fig_load.write_image("{}/{} Load.pdf".format(file_path, name[-3:]))
    # save figure as HTML
    fig_load.write_html("{}/{} Load.html".format(file_path, name[-3:]))


# BLOCK for creating percentage graphs for each load cell
#    for name, df in dataframes.items():
    fig_pct = go.Figure()   # sets up an empty figure   
    # add lines to the graph
    # add a line for the load reported by ADAS
    fig_pct.add_trace(go.Scatter(
        x=df['taken_on'],
        y=df['Reported as % of Baseline'],
        mode='lines+markers',
        name='Baseline Load'
    ))
    # add a line for the check load, calculated from the individual strain guages
    fig_pct.add_trace(go.Scatter(
        x=df['taken_on'],
        y=df['Checkload as % of Baseline'],
        mode='lines+markers',
        name='Check Load'
    ))
    # add a line for the temp-corrected load vs baseline load
    fig_pct.add_trace(go.Scatter(
        x=df['taken_on'],
        y=df['Temp Corrected as % of Baseline'],
        mode='lines+markers',
        name='Temp Corrected vs Baseline'
    ))
    # add a line for the temp-corrected load vs calibration load
    fig_pct.add_trace(go.Scatter(
        x=df['taken_on'],
        y=df['Temp Corrected as % of Calibration'],
        mode='lines+markers',
        name='Temp Corrected vs Calibration'
    ))
    # scale the y axis to be +/- 1% from max and min values
    fig_pct.update_layout(title='Load Cell {}'.format(name[-3:]))
    # add a rectangle for each temp_fault range
    for x_start, x_end in highlight_temp_below_install:
        fig_pct.add_shape(
            type="rect",
            x0=x_start,
            x1=x_end,
            y0=0,
            y1=1,
            xref="x",
            yref="paper",
            fillcolor="pink",
            opacity=0.3,
            layer="below",
            line=dict(color="pink", width=0)
        )
    for x_start, x_end in highlight_temp_below_zero:
        fig_pct.add_shape(
            type="rect",
            x0=x_start,
            x1=x_end,
            y0=0,
            y1=1,
            xref="x",
            yref="paper",
            fillcolor="pink",
            opacity=0.6,
            layer="below",
            line=dict(color="pink", width=0)
        )
    # display the graph    
    #fig_pct.show()
    # save figure as PDF
    fig_pct.write_image("{}/{} Percent.pdf".format(file_path, name[-3:]))
    # save figure as HTML
    fig_pct.write_html("{}/{} Percent.html".format(file_path, name[-3:]))


# create an empty figure to plot multiple traces on
fig_ADAS_loads = go.Figure()
fig_check_vs_baseline = go.Figure()
fig_temp_vs_baseline = go.Figure()
fig_temp_vs_calibration = go.Figure()
for name, df in dataframes.items():
    # graph for ADAS reported loads from all load cells
    fig_ADAS_loads.add_trace(go.Scatter(
        x=df['taken_on'],
        y=df['Reported as % of Baseline'],
        mode='lines+markers',
        name='Load Cell {}'.format(name[-3:])
    ))
    # graph for check loads for all load cells
    fig_check_vs_baseline.add_trace(go.Scatter(
        x=df['taken_on'],
        y=df['Checkload as % of Baseline'],
        mode='lines+markers',
        name='Load Cell {}'.format(name[-3:])
    ))
    # graph for temp corrected loads for all load cells
    fig_temp_vs_baseline.add_trace(go.Scatter(
        x=df['taken_on'],
        y=df['Temp Corrected as % of Baseline'],
        mode='lines+markers',
        name='Load Cell {}'.format(name[-3:])
    ))
    # add a line for the temp-corrected load vs calibration load
    fig_temp_vs_calibration.add_trace(go.Scatter(
        x=df['taken_on'],
        y=df['Temp Corrected as % of Calibration'],
        mode='lines+markers',
        name='Load Cell {}'.format(name[-3:])
    ))
    # create the various % graphs
    fig_ADAS_loads.update_layout(title='Load as % of Baseline')
    fig_check_vs_baseline.update_layout(title='Check Load vs Baseline')
    fig_temp_vs_baseline.update_layout(title='Temp Corrected Load vs Baseline')
    fig_temp_vs_calibration.update_layout(title='Temp Corrected Load vs Calibration')
#fig_ADAS_loads.show()
fig_ADAS_loads.write_image('{}/ADAS_loads_vs_baseline.pdf'.format(file_path))
fig_ADAS_loads.write_html('{}/ADAS_loads_vs_baseline.html'.format(file_path))
#fig_check_vs_baseline.show()
fig_check_vs_baseline.write_image('{}/check_vs_baseline.pdf'.format(file_path))
fig_check_vs_baseline.write_html('{}/check_vs_baseline.html'.format(file_path))
#fig_temp_vs_baseline.show()
fig_temp_vs_baseline.write_image('{}/temp_vs_baseline.pdf'.format(file_path))
fig_temp_vs_baseline.write_html('{}/temp_vs_baseline.html'.format(file_path))
#fig_temp_vs_calibration.show()
fig_temp_vs_calibration.write_image('{}/temp_vs_calibration.pdf'.format(file_path))
fig_temp_vs_calibration.write_html('{}/temp_vs_calibration.html'.format(file_path))

