# -*- coding: utf-8 -*-
# 417574686f723a205061747269636520506f6e6368616e74
# The future package will provide support for running your code on Python 2.6, 2.7, and 3.3+ mostly unchanged.
# http://python-future.org/quickstart.html
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *

##### For the basic function #####
import datetime
import sys
import glob
import os
#import re

import csv
import pandas as pd
import numpy as np

from argparse import ArgumentParser
from argparse import RawTextHelpFormatter

# gaph
from jinja2 import Template

from bokeh.io import output_file, export_png
from bokeh.plotting import *
from bokeh.models import *
from bokeh.layouts import gridplot, column, layout
from bokeh.models.widgets import CheckboxButtonGroup
from bokeh.embed import components
from bokeh.resources import INLINE
from bokeh.util.browser import view

# progress bar
from tqdm import *

####### Code #######
def main():
    parser = ArgumentParser(description='Create HTML CTD Report.',
        epilog='Example: \n To create the html interactif report from CTD csv data use python ctdreport.py c:/temp/ctd/ c:/temp/ctdList.csv \n', formatter_class=RawTextHelpFormatter)
    parser.add_argument('ctdFolder', action='store', help='ctdFolder (str): CTD folder path. This is the path where the files to process are.')
    parser.add_argument('ctdCSV', action='store', help='ctdCSV (str): CTD csv list path. This is the CTD csv file path with all the needed information are for each CTD.')

    if len(sys.argv)==1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()
    process(args)

def process(args):
    """
    Uses this if called as __main__.
    """
    ctdFolder = args.ctdFolder
    ctdCSV = args.ctdCSV
    ctdListFile = glob.glob(ctdFolder + "\\*.csv")
    resultFolder = os.path.dirname(os.path.realpath(ctdCSV))
    csvmetadata = resultFolder + '\\report\\ctdmetada.csv'

    # Creating the folder struture
    if not os.path.exists(resultFolder + '\\report\\'):
        os.makedirs(resultFolder + '\\report\\')
    
    if not os.path.exists(resultFolder + '\\report\\HTML\\'):
        os.makedirs(resultFolder + '\\report\\HTML\\')

    # for f in ctdListFile:
    #     foldername = os.path.splitext(os.path.basename(f))[0]
    #     if not os.path.exists(resultFolder + '\\report\\' + foldername):
    #         os.makedirs(resultFolder + '\\report\\' + foldername)

    if not os.path.exists(csvmetadata):
        with open(csvmetadata, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Number','Date','Time','Product / Location','KP <KP db>','Lat','Lon','Easting','Northing','Water Depth',
                            'Average SV (m/s)','SV at seabed (m/s)','SV at 10m (m/s)','Temp at seabed (ºC)','Cond. at seabed',
                            'Density at seabed (Kg/m3)','Average density (Kg/m3)','Average gravity','Comments'])
    
    df = pd.read_csv(ctdCSV, sep=',') # Number,Location,KP,Lat,Lon,Easting,Northing,Comments,FileName,Instrument,Geodetic,Gravity,SVP,htmltitle
    with tqdm(total=len(ctdListFile)) as pbar:
        for index, row in df.iterrows():
            rowList = [row.Number, row.Location, row.KP, round(row.Lat,6), round(row.Lon,6), round(row.Easting,2), round(row.Northing,2), row.Comments, row.FileName, row.Instrument, row.Geodetic, row.SVP, row.htmltitle]
            csvname = ctdFolder + row.FileName + '.csv'
            htmlfile = resultFolder + '\\report\\HTML\\' + row.FileName + '_report.html'
            dateparse = lambda x: datetime.datetime.strptime(x, '%d/%m/%Y %H:%M:%S.%f')
            dfcsv = pd.read_csv(csvname, skiprows=3, header=None, sep=',', parse_dates=[0], date_parser=dateparse)
            statsList = stats(dfcsv)
            graph(dfcsv, htmlfile, csvmetadata, rowList, statsList)
            del rowList, csvname, dfcsv, statsList
            pbar.update(1)
    del df

    
def stats(dfcsv):
    # Average SV [m/s] = avSV, SV at Seabed [m/s] = SVS, SV at 10 m [m/s] = SV10, Temperature at Seabed [°C] = temp, Conductivity at Seabed [] = cond, 
    # Density at Seabed [kg/m3] = dens, Average Density [kg/m3] = avDens, Average Gravity [m/s2] = avG
    # # Fields pos: Time[0],Direction[1],Depth(m)[2],Pressure(bar)[3],Temperature(C)[4],Salinity[5],Conductivity[6],Velocity(m/s)[7],Density(kg/m^3)[8],HarmonicDensity(kg/m^3)[9],
    #               GravityAtPressure[10],CorrTemperature(C)[11],CorrVelocity(m/s)[12],CorrDensity(kg/m^3)[13],Absorption[14],HarmVelocityTDX1(m/s)[15],HarmVelocityTDX2(m/s)[16],
    #               HarmVelocityMBE(m/s)[17],HarmAbsorption[18],ProcFlags[19],PressureTime[20]
    dfcsv[0] = pd.to_datetime(dfcsv[0])
    date = dfcsv[0].min().strftime("%d %B %Y")
    time = dfcsv[0].min().strftime('%H:%M')
    timeend = dfcsv[0].max().strftime('%H:%M')
    temp = round(dfcsv[11].mean(),2) #°C
    salinity = round(dfcsv[5].mean(),2) #PSU
    pressure = round(dfcsv[3].max() * 10,2) # pressure is in bar no cast file
    avSV = round(dfcsv[12].mean(),2)
    SVS = round(dfcsv[12].iloc[-1],2)
    idx = dfcsv[2].sub(10).abs().idxmin()
    SV10 = round(dfcsv.iloc[[idx],12].iloc[0],2)
    cond = round(dfcsv[6].mean(),2)
    if cond <10:
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("!! Please Verify the Units !!")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        cond = round(cond*10,2)
        dfcsv[6] = dfcsv[6]*10
    else:
        cond = round(cond,2)
    avDens = round(dfcsv[13].mean(),2)
    dens = round(dfcsv[13].iloc[-1],2)
    depth = round(dfcsv[2].max(),2)*-1
    avG = round(dfcsv[10].mean(),2)

    statsList = [date, time, timeend, temp, salinity, pressure, avSV, SVS, SV10, cond, avDens, dens, depth, avG]

    return statsList

def graph(dfcsv, htmlfile, csvmetadata, rowList, statsList):
    
    number, location, kp, lat, lon, easting, northing, comments, fileName, instrument, geodetic, svp, htmltitle = [i for i in rowList]
    date, time, timeend, temp, salinity, pressure, avSV, SVS, SV10, cond, avDens, dens, depth, gravity = [i for i in statsList]

    ################ DATA PARAMETERS ################
    ###### -- Create Column Data Source that will be used by the plot -- ########

    datarawdata = dict(Pressure=dfcsv[3]*-10,
                        Depth=dfcsv[2]*-1,
                        Temperature=dfcsv[11],
                        Salinity=dfcsv[5],
                        Density=dfcsv[13],
                        Conductivity=dfcsv[6],
                        SoundVelocity=dfcsv[12]
                        )
    sourcerawdata = ColumnDataSource(datarawdata)
    ###### -- end -- ########

    ################ PLOTS PARAMETERS ################
    ###### -- Main-- ########
    TOOLTIPS = [
    ("Depth", "$y{0.1f}"),
    ("Measure", "$x{0.1f}"),
    ]

    plot_options = dict(y_axis_label='Depth [Hydrostatic, m]',
                        background_fill_color='#F4ECDC',
                        width=600,
                        height=600,
                        title="",
                        toolbar_location=None,
                        tooltips=TOOLTIPS
                        #tools='crosshair,pan,wheel_zoom,box_zoom,reset,hover,save'
                        )
    ###### -- end -- ########

    ################ PLOTS ################
    ###### -- First one -- ########
    line0 = figure(**plot_options)
    #xaxis = LinearAxis(line0=line0, location="above")
    line0.line('Temperature', 'Depth', source=sourcerawdata, color='#6788B1')
    line0.xaxis.axis_label = "Temperature [°C]"
    line0.x_range.bounds = 'auto'
    line0.y_range.bounds = 'auto'
    line0.axis.axis_label_text_font_size = "14pt"
    line0.axis.axis_label_text_font_style = "bold"

    ## -- Salinity -- ##
    line1 = figure(y_range=line0.y_range, **plot_options)
    line1.line('Salinity', 'Depth', source=sourcerawdata, color='#6788B1')
    line1.xaxis.axis_label = "Salinity [PSU]"
    line1.x_range.bounds = 'auto'
    line1.y_range.bounds = 'auto'
    line1.axis.axis_label_text_font_size = "14pt"
    line1.axis.axis_label_text_font_style = "bold"

    ## -- Conductivity -- ##
    line2 = figure(y_range=line0.y_range, **plot_options)
    line2.line('Conductivity', 'Depth', source=sourcerawdata, color='#6788B1')
    line2.xaxis.axis_label = "Conductivity [mS/cm]"
    line2.x_range.bounds = 'auto'
    line2.y_range.bounds = 'auto'
    line2.axis.axis_label_text_font_size = "14pt"
    line2.axis.axis_label_text_font_style = "bold"

    ## -- Density -- ##
    line3 = figure(y_range=line0.y_range, **plot_options)
    line3.line('Density', 'Depth', source=sourcerawdata, color='#6788B1')
    line3.xaxis.axis_label = "Density [kg/m^3]"
    line3.x_range.bounds = 'auto'
    line3.y_range.bounds = 'auto'
    line3.axis.axis_label_text_font_size = "14pt"
    line3.axis.axis_label_text_font_style = "bold"

    ## -- Sound Velocity -- ##
    line4 = figure(y_range=line0.y_range, **plot_options)
    line4.line('SoundVelocity', 'Depth', source=sourcerawdata, color='#6788B1')
    line4.xaxis.axis_label = svp
    line4.x_range.bounds = 'auto'
    line4.y_range.bounds = 'auto'
    line4.axis.axis_label_text_font_size = "14pt"
    line4.axis.axis_label_text_font_style = "bold"

    ###### -- end -- ########

    ################ TABLE ################
    ###### -- Set up table bottle columns-- ########
    columnstable = [
        TableColumn(field="Pressure",       title="Pressure [dBar]",        formatter=NumberFormatter(format="0.00")),
        TableColumn(field="Depth",          title="Depth [m]",              formatter=NumberFormatter(format="0.00")),
        TableColumn(field="SoundVelocity",  title=svp, 			            formatter=NumberFormatter(format="0.00")),
        TableColumn(field="Conductivity",   title="Conductivity [mS/cm]",   formatter=NumberFormatter(format="0.00")),
        TableColumn(field="Temperature",    title="Temperature [°C]",       formatter=NumberFormatter(format="0.00")),
        TableColumn(field="Density",        title="Density [kg/m^3]",     formatter=NumberFormatter(format="0.00")),
        TableColumn(field="Salinity",       title="Salinity [PSU]", 	    formatter=NumberFormatter(format="0.00"))
    ]
    ###### -- end -- ########

    ###### -- Create tables -- ########
    data_table = DataTable(source=sourcerawdata, columns=columnstable, editable=False, sortable=False, selectable=True)
    ###### -- end -- ########
    

    ########## PLOTS LAYOUT ################
    ###### -- Set up Plots layout -- ########
    p = gridplot([[line4, line2],[line0, line3],[line1, None]])
    datatbl = layout([[data_table]], sizing_mode='stretch_both')

    ########## RENDER PLOTS ################
    ###### -- Define our html template for out plots -- ########
    template = Template('''<!DOCTYPE html>
    <html lang="en">
        <head>
            <meta charset="utf-8">
        <title>'CTD Number {{number}}'</title>
            {{ js_resources }}
            {{ css_resources }}
        <style>
        	h1 {font-family: 'segoe ui', sans-serif;
                display: block;
                font-size: 160%;
                margin-block-start: 0em;
                margin-block-end: 0em;
                margin-inline-start: 0px;
                margin-inline-end: 0px;
                font-weight: bold;
                padding-top: 7px;
		        }
            h2 	{font-family: 'segoe ui', sans-serif;
                color: #ffffff;
                margin: 60px 0px 0px 0px;
                padding: 0px 0px 6px 150px;
                font-size: 35px;
                line-height: 48px;
                letter-spacing: -2px;
                font-weight: bold;
                background-color: #011E41;
                }
            h3  {font-family: 'segoe ui', sans-serif;
                color: #011E41;
                margin: 20px 0px 0px 15px;
                padding: 0px 0px 6px 0px;
                font-size: 28px;
                line-height: 44px;
                letter-spacing: -2px;
                #font-weight: bold;
                }
            h4  {font-family: 'segoe ui', sans-serif;
                color: #011E41;
                margin: 0px 0px 10px 15px;
                padding: 0px 0px -5px 0px;
                font-size: 24px;
                line-height: 44px;
                letter-spacing: -2px;
                font-style: italic;
                border-bottom-style: solid;
                border-width: 2px;
                border-color: #011E41;
                }
            p {font-family: 'segoe ui', sans-serif;
                font-size: 16px;
                line-height: 24px;
                margin: 0 0 24px 15px;
                text-align: left;
                ///text-justify: inter-word;
                }
            ul {font-family: 'segoe ui', sans-serif;
                font-size: 16px;
                line-height: 24px;
                margin: 0 0 24px;
                text-align: left;
                ///text-justify: inter-word;
                }
            p.TableText, li.TableText, div.TableText
                {margin-top:3.0pt;
                margin-right:5.65pt;
                margin-bottom:3.0pt;
                margin-left:5.65pt;
                font-size:9.0pt;
                font-family:"Segoe UI",sans-serif;
                }
            .TableText.Centre
                {text-align:center;
                }                
            p.TableHeading, li.TableHeading, div.TableHeading
                {margin-top:3.0pt;
                margin-right:5.65pt;
                margin-bottom:3.0pt;
                margin-left:5.65pt;
                font-size:9.0pt;
                font-family:"Segoe UI Semibold",sans-serif;
                }
            .TableHeading.Centre
                {text-align:center;
                }   
            td.TableHeadingGridTable
                {border:solid #6788B1 1.0pt;
                border-right:solid white 1.0pt;
                background:#6788B1;
                vertical-align: top;
                padding:0cm 0cm 0cm 0cm;
                }
            td.TableTextGridTable
                {border-top:none;
                border-left:none;
                border-bottom:solid #6788B1 1.0pt;
                border-right:solid #6788B1 1.0pt;
                vertical-align: top;
                padding:0cm 0cm 0cm 0cm;
                }
            td.TableHeadingLinedTable
                {border:none;
                border-bottom:solid #6788B1 1.0pt;
                background:white;
                vertical-align: bottom;
                padding:0cm 0cm 0cm 0cm;
                }
            td.TableTextLinedTable
                {border:none;
                border-bottom:solid #7F7F7F 1.0pt;
                vertical-align: top;
                padding:0cm 0cm 0cm 0cm;
                }
            .app_header {
                height:80px;
                width: 100%;
                background-color:#011E41;
                color:#eee;
                margin-left: auto;
                margin-right: auto;
            }
            @media screen and (min-width : 1024px) {
                .app_header {
                    width: 100%;
                }
            }
            .app_header a {
                color: #900;
            }
            .app_header_icon {			
                background: url('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAHgAAABDCAYAAABX2cG8AAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAALiMAAC4jAXilP3YAAASVSURBVHhe7ZxdiFVVFMfnq0LSJsI0CpKwhzJ6iXwYLQiiCAYCn4QeRJLoqbRUjKC0t6EPwd4iKiMsSsge+kA0kiIjQQoSpMwIYYixtI9RCZM7/dY+y+s995572feMZz72/H/wZ++19jr77LPX3fuec7xjjxBCCCGEEEIIIYQQQghRMb1eVkatVnuQ4g10Q3B0z7G+vr5lXhcziYmJiX4SPEZZGo7/0bsTJejzsioW9Pb2LvK6mAYq3aJZgNdS/JlZeWgbpfg+szoyyhb9uNfFTMISbNtsEWy9qz1MVEjVW3Qn/vNSVEjXWzSLbyGKPW6Q7+BjXs9BH49SfJJZnWGLPulVuyu/jmIgsy7Bec6gc24GPLY/s6I4x7nOej1AH6XvIWw8Ni4369j82TxSjZ5/+jmNLrhZHVzwGQY31dR3Gs5/2H058K/3EJvAQewvspZ4OOY8et67CWDXvLlrOPQC+pDqoHdn/S1FR7OIeDhmFA15N9FM5xZ9uZnw0hK8kU/7fW5GwzFXoBeYyDvdNSnoqx+tYjzPuMt4Ed9tXo+GY26keD2z4ul6i+bi3+FkV7nZES5swC7QzRy0fUvbCTfNvgX7bjebsYmqWYXzH6Z+V/A2wPHr2V5ftToxbxGzNjQ0QdwPFMfREDGLg7MJYobp61Or01eNuJZ5IuZ9in2Z1WPb7bOEXZOZeYh9j/4esTrdHSJueWhogBj7gO5BY2g1Mfb1koOQcfopPMe0wIDm28CL4ELDBV8Ee503FRGzRT/pISHB7m7mAArJImYx+hodLFB9K6ReuEXj3uAhAeyt3tQCbe96mMUdcnczOz3EYh5wXw78/3hINElu0e1gjn5iZYQ4VsIYWolWFOibcEB3nPeyFIztO68aR72cNCklOBomcxur4ecOGvbQTiyzONca7NyKbqLwZc9UMKdW8EVI8EJW8tJ2ImR+Ftke4h5DH7veRoWPU5zrOG2vuBlLuN+4HMzJFcyEv8zED6E/3NU1HNvxRQ3tI+geznU7+sXdU86sSDATdauXV1LcbPWShFXGhP+KjlC92uySvMR47G68Hes4xyiKfWPXuAPc5OWkmS0r+AO+555gQvcwYfZIUkTMtvYw/byGNtDXXvqa5/4y/I6G6edUZuah7+tp+4hzxX6IniJ+hPjN1Hdlrhaiv4amBAbczWPSCm8qS/3Fhk2S+0rB8fV/CKHe8TGJ8l70r7tboG03Rf05mvrO0FAC+vrSu4lmxqxgHk0Ocg0bkf1AwF6Hxuok2sKKOeBd2erZge9N9JfHNOs0eg7tavDVRReN73xb2j0mbL2M+yuKtfjGm2NMtD1E+bTFOpuwP0OF8W1k493Pddnd+syBQUWvYFENc/Iuei6hBCeOEpw4SnDiKMGJowQnjhKcOEpw4ijBiaMEJ44SnDhKcOIowYmjBCeOEpw4SnDiKMGJU3WC7df+f2fVFuxHa2K2U8t+wZgD3+feLGY75HOAhB7JUhuSa3+De4c3ixQgofd7fi3B290tUoLE7ka/keP6X7uLhCC5S5D+Zx0hhBBCCCGEEEIIIYQQIil6ev4H0L1DGlhlR+UAAAAASUVORK5CYII=')
                no-repeat;

                /* margin:-29px; */
                margin-top: 5px;
                margin-left:5px;
                margin-right: 70px;
                float:left;
                width: 120px;
                height: 67px;
            }
            .app_header_search {
                float:right;
                padding:15px;
            }
            .slick-header-column {
                background-color: #6788B1 !important;
                background-image: none !important;
                color: white !important;
                font-size:9.0pt;
                font-family:"Segoe UI Semibold",sans-serif;
            }
            .slick-row {
                background-color: white !important;
                background-image: none !important;
                color:black !important;
                font-size:9.0pt;
                font-family:"Segoe UI",sans-serif;
            }
            .bk-cell-index {
                background-color: white !important;
                background-image: none !important;
                color:black !important;
                font-size:9.0pt;
                font-family:"Segoe UI",sans-serif;
            }
        </style>
        <!-- 50 61 74 72 69 63 65 20 50 6f 6e 63 68 61 6e 74 -->
        </head>
        <body>
        <div id="app_header" class="app_header">		
			<span class="app_header_icon"></span>
			<h1>{{ title }}</h1>
		</div>
        <h3>Executive Summary</h3>
        <h4></h4>
        <p>The CTD was collected on the {{ date }} using a {{ instrument }}.</p> 
        <p>The recommended United Nations Educational, Scientific and Cultural Organisation (UNESCO) formulae was used to process the data and can be found in the <a href="http://unesdoc.unesco.org/images/0005/000598/059832eb.pdf">UNESCO technical papers in marine science 44</a>.
        Chen Milero formula was use to determided sound velocity from the CTD data.
        </p>
        <table class=FugroGridTable border=1 cellspacing=0 cellpadding=0
        style='border-collapse:collapse;border:none;margin-left:15px'>
        <thead>
        <tr>
        <td class=TableHeadingGridTable>
        <p class=TableHeading><span style='color:white'>CTD Number</span></p>
        </td>
        <td class=TableHeadingGridTable>
        <p class=TableHeading><span style='color:white'>Date</span></p>
        </td>
        <td class=TableHeadingGridTable>
        <p class=TableHeading><span style='color:white'>Time</span></p>
        </td>
        <td class=TableHeadingGridTable>
        <p class=TableHeading><span style='color:white'>Product &#47; Location</span></p>
        </td>
        <td class=TableHeadingGridTable>
        <p class=TableHeading><span style='color:white'>Instrument</span></p>
        </td>
        <td style='border:solid #6788B1 1.0pt;
        border-left:none;background:#6788B1;padding:0cm 0cm 0cm 0cm'>
        <p class=TableHeading><span style='color:white'>Comments</span></p>
        </td>
        </tr>
        </thead>
        <tr>
        <td style='border:solid #6788B1 1.0pt;
        border-top:none;padding:0cm 0cm 0cm 0cm'>
        <p class=TableText>{{ number }}</p>
        </td>
        <td class=TableTextGridTable>
        <p class=TableText>{{ date }}</p>
        </td>
        <td class=TableTextGridTable>
        <p class=TableText>{{ time }}</p>
        </td>
        <td class=TableTextGridTable>
        <p class=TableText>{{ location }}</p>
        </td>
        <td class=TableTextGridTable>
        <p class=TableText>{{ instrument }}</p>
        </td>
        <td class=TableTextGridTable>
        <p class=TableText>{{ comments }}</p>
        </td>
        </tr>
        </table>
        <p></p>
        <table class=FugroLinedTable border=1 cellspacing=0 cellpadding=0
        style='border-collapse:collapse;border:none;margin-left:15px'>
        <thead>
        <tr>
        <td class=TableHeadingLinedTable>
        <p class="TableHeading Centre"><span style='color:#6788B1'>Latitude</span></p>
        </td>
        <td class=TableHeadingLinedTable>
        <p class="TableHeading Centre"><span style='color:#6788B1'>Longitude</span></p>
        </td>
        <td class=TableHeadingLinedTable>
        <p class="TableHeading Centre"><span style='color:#6788B1'>Easting &#91;m&#93;</span></p>
        </td>
        <td class=TableHeadingLinedTable>
        <p class="TableHeading Centre"><span style='color:#6788B1'>Northing &#91;m&#93;</span></p>
        </td>
        <td class=TableHeadingLinedTable>
        <p class="TableHeading Centre"><span style='color:#6788B1'>Depth &#91;m&#93;</span></p>
        </td>
        </tr>
        </thead>
        <tr>
        <td class=TableTextLinedTable>
        <p class="TableText Centre">{{ lat }}</p>
        </td>
        <td class=TableTextLinedTable>
        <p class="TableText Centre">{{ lon }}</p>
        </td>
        <td class=TableTextLinedTable>
        <p class="TableText Centre">{{ easting }}</p>
        </td>
        <td class=TableTextLinedTable>
        <p class="TableText Centre">{{ northing }}</p>
        </td>
        <td class=TableTextLinedTable>
        <p class="TableText Centre">{{ depth }}</p>
        </td>
        </tr>
        <tr>
        <td colspan=5 class=TableTextLinedTable>
        <p class=TableText><span style='color:#808080;font-size:8.0pt;'>Note: {{ geodetic }}</span></p>
        </td>
        </tr>
        </table>
        <p></p>
        <table class=FugroLinedTable border=1 cellspacing=0 cellpadding=0
        style='border-collapse:collapse;border:none;margin-left:15px'>
        <thead>
        <tr>
        <td class=TableHeadingLinedTable>
        <p class="TableHeading Centre"><span style='color:#6788B1'>Average SV &#91;m/s&#93;</span></p>
        </td>
        <td class=TableHeadingLinedTable>
        <p class="TableHeading Centre"><span style='color:#6788B1'>SV at Seabed &#91;m/s&#93;</span></p>
        </td>
        <td class=TableHeadingLinedTable>
        <p class="TableHeading Centre"><span style='color:#6788B1'>SV at 10&nbsp;m &#91;m/s&#93;</span></p>
        </td>
        <td class=TableHeadingLinedTable>
        <p class="TableHeading Centre"><span style='color:#6788B1'>Temperature at Seabed &#91;&#176;C&#93;</span></p>
        </td>
        <td class=TableHeadingLinedTable>
        <p class="TableHeading Centre"><span style='color:#6788B1'>Conductivity at Seabed &#91;mS/cm&#93;</span></p>
        </td>
        <td class=TableHeadingLinedTable>
        <p class="TableHeading Centre"><span style='color:#6788B1'>Density at Seabed &#91;kg/m<sup>3</sup>&#93;</span></p>
        </td>
        <td class=TableHeadingLinedTable>
        <p class="TableHeading Centre"><span style='color:#6788B1'>Average Density &#91;kg/m<sup>3</sup>&#93;</span></p>
        </td>
        <td class=TableHeadingLinedTable>
        <p class="TableHeading Centre"><span style='color:#6788B1'>Average Gravity &#91;m/s<sup>2</sup>&#93;</span></p>
        </td>
        </tr>
        </thead>
        <tr>
        <td class=TableTextLinedTable>
        <p class="TableText Centre">{{ avSV }}</p>
        </td>
        <td class=TableTextLinedTable>
        <p class="TableText Centre">{{ SVS }}</p>
        </td>
        <td class=TableTextLinedTable>
        <p class="TableText Centre">{{ SV10 }}</p>
        </td>
        <td class=TableTextLinedTable>
        <p class="TableText Centre">{{ temp }}</p>
        </td>
        <td class=TableTextLinedTable>
        <p class="TableText Centre">{{ cond }}</p>
        </td>
        <td class=TableTextLinedTable>
        <p class="TableText Centre">{{ dens }}</p>
        </td>
        <td class=TableTextLinedTable>
        <p class="TableText Centre">{{ avDens }}</p>
        </td>
        <td class=TableTextLinedTable>
        <p class="TableText Centre">{{ gravity }}</p>
        </td>
        </tr>
        </table>
        <h3>Interactive Plots</h3>
        <h4></h4>
        <div style="margin-left: 15px;">
        {{ plot_div.p }}
        </div>
        <h3>Interactive Table</h3>
        <h4></h4>
        <div style="margin-left: 15px;">
        {{ plot_div.tbl }}
        </div>
        {{ plot_script }}
        </body>
    </html>
    ''')

    resources = INLINE

    js_resources = resources.render_js()
    css_resources = resources.render_css()

    script, div = components({'p': p, 'tbl': datatbl})

    html = template.render(js_resources=js_resources,css_resources=css_resources,plot_script=script,plot_div=div,title=htmltitle,
                        number=number,location=location,lat=lat,lon=lon,easting=easting,northing=northing,comments=comments,
                        instrument=instrument,geodetic=geodetic,gravity=gravity,date=date,time=time,temp=temp,avSV=avSV,SVS=SVS,
                        SV10=SV10,cond=cond,avDens=avDens,dens=dens,depth=depth
                        )
    ###### -- end -- ########

    ###### -- save the document in a HTML -- ########
    with open(htmlfile, 'w', encoding="utf-8") as f:
        f.write(html)

    with open(csvmetadata, "a", newline='', encoding="utf-8") as output:
        writer = csv.writer(output)
        writer.writerow([number, date, time, location, kp, lat, lon, easting, northing, depth, avSV, SVS, SV10, temp, cond, dens, avDens, gravity, comments])

    ###### -- end -- ########

    reset_output()


if __name__ == "__main__":
    now = datetime.datetime.now() # time the process
    main()
    print('')
    print("Process Duration: ", (datetime.datetime.now() - now)) # print the processing time. It is handy to keep an eye on processing performance.