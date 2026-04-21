
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Table, TableStyle
import datetime
import pandas as pd
import numpy as np
import matplotlib.patches as patches
import plotly.express as px
import tempfile
import os

# Import PDF generation from pdf.py
from .pdf import generate_gpx_analysis_pdf

#convert pace between min/km and min/mile
def convert_to_mph(pace_min_per_km):
    """Convert pace from min/km to min/mile"""
    return pace_min_per_km * 1.60934

def convert_to_kmh(pace_min_per_mile):
    """Convert pace from min/mile to min/km"""
    return pace_min_per_mile / 1.60934

def convert_to_miles(km):
    """Convert kilometers to miles"""
    return km / 1.60934

def convert_to_km(miles):
    """Convert miles to kilometers"""
    return miles * 1.60934

def calculate_time_difference(row):
    """
    Calculate the difference between cutoff time and clock time in minutes.
    
    Args:
        row: DataFrame row containing 'cutoff_time_formatted' and 'clock_time' columns
    
    Returns:
        float: Difference in minutes (positive = arrive before cutoff, negative = arrive after cutoff)
        pd.NA: If either time is missing or invalid
    """
    if pd.notna(row['cutoff_time_formatted']) and pd.notna(row['clock_time']):
        try:
            # Parse clock_time string to time object if it's a string
            if isinstance(row['clock_time'], str):
                clock_time = datetime.datetime.strptime(row['clock_time'], "%H:%M:%S").time()
            else:
                clock_time = row['clock_time']
            
            cutoff_time = row['cutoff_time_formatted']
            
            # Convert both times to datetime for calculation (using arbitrary date)
            base_date = datetime.date.today()
            cutoff_datetime = datetime.datetime.combine(base_date, cutoff_time)
            clock_datetime = datetime.datetime.combine(base_date, clock_time)
            
            # Calculate difference in minutes
            diff_minutes = (cutoff_datetime - clock_datetime).total_seconds() / 60
            return round(diff_minutes, 1)
        except (ValueError, TypeError):
            return pd.NA
    return pd.NA



def merge_custom_markers(analyzer_final_df, custom_marker_data, use_km_markers=True):
    """
    Merge custom markers (like aid stations) with the analyzer's final DataFrame
    based on the nearest kilometer marker.
    
    Args:
        analyzer_final_df: DataFrame from GPXAnalyzer.final_df
        custom_marker_data: DataFrame with columns ['Distance', 'Nickname']
        use_km_markers: Boolean indicating if distances are in km (True) or miles (False)
    
    Returns:
        DataFrame: Updated final_df with custom marker information merged
    """
    
    # Create a copy to avoid modifying the original
    df = analyzer_final_df.copy()
    
    # Initialize custom marker columns if they don't exist
    if 'custom_marker' not in df.columns:
        df['custom_marker'] = ''
    if 'marker_nickname' not in df.columns:
        df['marker_nickname'] = ''
    
    # Return original df if no custom markers provided
    if custom_marker_data is None or len(custom_marker_data) == 0:
        return df
    
    # Clean and validate custom marker data
    custom_markers = custom_marker_data.copy()
    
    # Remove rows with missing or invalid data
    custom_markers = custom_markers.dropna(subset=['Distance', 'Nickname'])
    custom_markers['Distance'] = pd.to_numeric(custom_markers['Distance'], errors='coerce')
    custom_markers = custom_markers[custom_markers['Distance'] > 0]
    custom_markers = custom_markers[custom_markers['Nickname'].str.strip() != '']
    
    if len(custom_markers) == 0:
        return df
    
    #try to interpret cutoff times from custom markers
    if not custom_markers.empty and len(custom_markers) > 0:
        # Check if 'Cutoff Time' column exists and has valid entries
        if 'Cutoff Time' in custom_markers.columns:
            # Initialize cutoff_time_formatted column if it doesn't exist
            if 'cutoff_time_formatted' not in custom_markers.columns:
                custom_markers['cutoff_time_formatted'] = pd.NA
                
            for idx, row in custom_markers.iterrows():
                cutoff_time_str = row.get('Cutoff Time', None)
                if pd.notna(cutoff_time_str) and str(cutoff_time_str).strip() != '':
                    try:
                        cutoff_str = str(cutoff_time_str).strip()
                        # Try parsing with seconds first (HH:MM:SS)
                        try:
                            custom_markers.at[idx, 'cutoff_time_formatted'] = datetime.datetime.strptime(cutoff_str, "%H:%M:%S").time()
                        except ValueError:
                            # If that fails, try parsing without seconds (HH:MM)
                            custom_markers.at[idx, 'cutoff_time_formatted'] = datetime.datetime.strptime(cutoff_str, "%H:%M").time()
                    except ValueError:
                        # Fill with NA value instead of showing warning to avoid breaking computation
                        custom_markers.at[idx, 'cutoff_time_formatted'] = pd.NA


    # Convert distances to km if they're in miles
    if not use_km_markers:
        custom_markers['Distance'] = custom_markers['Distance'].apply(convert_to_km)
    
    # Get only kilometer marker rows for matching
    km_markers = df[df['is_km_marker'] == 1].copy()
    
    if len(km_markers) == 0:
        return df
    
    # Initialize cutoff_time_formatted column in main df if cutoff times exist in input
    if 'Cutoff Time' in custom_marker_data.columns:
        if 'cutoff_time_formatted' not in df.columns:
            df['cutoff_time_formatted'] = pd.NA

    # For each custom marker, find the nearest kilometer marker
    for _, marker in custom_markers.iterrows():
        target_distance = marker['Distance']
        nickname = marker['Nickname'].strip()
        cutoff_time = marker.get('cutoff_time_formatted', pd.NA) if 'cutoff_time_formatted' in marker else pd.NA
        
        # Find the closest km marker by total_distance
        distances = np.abs(km_markers['total_distance'] - target_distance)
        closest_idx = distances.idxmin()
        
        # Get the km_number of the closest marker
        closest_km = km_markers.loc[closest_idx, 'km_number']
        
        # Update all rows with this km_number to include the custom marker
        mask = (df['km_number'] == closest_km) & (df['is_km_marker'] == 1)
        
        if mask.any():
            # If there's already a custom marker, append with separator
            existing_marker = df.loc[mask, 'custom_marker'].iloc[0]
            existing_nickname = df.loc[mask, 'marker_nickname'].iloc[0]
            
            if existing_marker and existing_marker.strip():
                df.loc[mask, 'custom_marker'] = f"{existing_marker}, {nickname}"
                df.loc[mask, 'marker_nickname'] = f"{existing_nickname}, {nickname}"
            else:
                df.loc[mask, 'custom_marker'] = nickname
                df.loc[mask, 'marker_nickname'] = nickname
            
            # Add cutoff time if column is available (even if cutoff_time is NA)
            if 'cutoff_time_formatted' in df.columns:
                df.loc[mask, 'cutoff_time_formatted'] = cutoff_time
    
    return df

def get_custom_markers_summary(analyzer_final_df):
    """
    Extract a summary of custom markers from the final DataFrame.
    
    Args:
        analyzer_final_df: DataFrame with merged custom markers
    
    Returns:
        DataFrame: Summary of custom markers with their positions and details
    """
    
    # Filter for km markers that have custom markers
    custom_marker_rows = analyzer_final_df[
        (analyzer_final_df['is_km_marker'] == 1) & 
        (analyzer_final_df['custom_marker'].str.strip() != '')
    ].copy()
    
    if len(custom_marker_rows) == 0:
        return pd.DataFrame(columns=['KM', 'Distance', 'Marker', 'Pace', 'Time'])
    
    # Create summary DataFrame
    summary = custom_marker_rows[[
        'km_number', 'total_distance', 'custom_marker', 'pace', 'cumulative_time_hms'
    ]].copy()
    
    summary.columns = ['KM', 'Distance', 'Marker', 'Pace', 'Time']
    summary = summary.reset_index(drop=True)
    
    return summary

def plotly_elevation_plot(analyzer, total_elevation_gain, use_metric=True):
    "create elevation plot using plotly for output"

    elevation_df = analyzer.final_df[['total_distance', 'elevation']].copy()
    elevation_df = elevation_df.dropna(subset=['elevation'])

    #creating plotly chart if elevation data exists
    if total_elevation_gain > 0:
        # Convert units if imperial is selected
        if not use_metric:
            elevation_df['total_distance'] = elevation_df['total_distance'].apply(convert_to_miles)
            elevation_df['elevation'] = elevation_df['elevation'] * 3.28084  # Convert meters to feet
            distance_label = 'Distance (miles)'
            elevation_label = 'Elevation (ft)'
        else:
            distance_label = 'Distance (km)'
            elevation_label = 'Elevation (m)'
        
        elevation_plot = px.line(
            elevation_df,
            x='total_distance',
            y='elevation',
            labels={
                'total_distance': distance_label,
                'elevation': elevation_label
            },
            height=300
        )
        elevation_plot.update_traces(line=dict(color='#3498DB', width=2))
        elevation_plot.update_layout(
            plot_bgcolor='white',
            xaxis=dict(showgrid=True, gridcolor='lightgrey', zeroline=False),
            yaxis=dict(showgrid=True, gridcolor='lightgrey', zeroline=False)
        )
    else:
        elevation_plot = None


    return elevation_plot


def plotly_pace_plot(data, use_metric=True):
    "create pace plot used in the streamlit output"
    
    # Handle both analyzer objects and DataFrames
    if hasattr(data, 'final_df'):
        # It's an analyzer object
        pace_df = data.final_df[['total_distance', 'pace']].copy()
    else:
        # It's a DataFrame - assume it has the correct column names
        pace_df = data[['total_distance', 'pace']].copy()
    
    pace_df = pace_df.dropna(subset=['pace'])

    #creating plotly chart if elevation data exists
    if len(pace_df) > 1:
        # Convert units if imperial is selected
        if not use_metric:
            pace_df['total_distance'] = pace_df['total_distance'].apply(convert_to_miles)
            pace_df['pace'] = pace_df['pace'].apply(convert_to_mph)
            distance_label = 'Distance (miles)'
            pace_label = 'Pace (min/mile)'
        else:
            distance_label = 'Distance (km)'
            pace_label = 'Pace (min/km)'
        
        pace_plot = px.line(
            pace_df,
            x='total_distance',
            y='pace',
            labels={
                'total_distance': distance_label,
                'pace': pace_label
            },
            height=300
        )
        pace_plot.update_traces(line=dict(color='#3498DB', width=2))
        pace_plot.update_layout(
            plot_bgcolor='white',
            xaxis=dict(showgrid=True, gridcolor='lightgrey', zeroline=False),
            yaxis=dict(showgrid=True, gridcolor='lightgrey', zeroline=False)
        )
    else:
        pace_plot = None



    return pace_plot