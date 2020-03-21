from arcgis import GIS
import pandas as pd
import math


def meters_to_long(x):
    # Converts longitude point from Spherical Mercator EPSG:900913 to lat/lon in WGS84 Datum
    origin_shift = 2 * math.pi * 6378137 / 2.0
    long = (x / origin_shift) * 180.0
    return long


def meters_to_lat(y):
    origin_shift = 2 * math.pi * 6378137 / 2.0
    lat = (y / origin_shift) * 180.0
    lat = 180 / math.pi * (2 * math.atan(math.exp(lat * math.pi / 180.0)) - math.pi / 2.0)
    return lat


def get_localities(url, username, password):
    # Access to ArcGIS Online account
    gis = GIS(url, username, password)

    # Retrieve Field Localities by name, and access first layer in collection
    localities = gis.content.search(query="title:Field Localities", item_type="Feature Layer")[0].layers[0]

    # Create and return spatially enabled dataframe
    sdf = pd.DataFrame.spatial.from_layer(localities)

    return sdf


def export(sdf, out_path):
    # Add columns
    sdf.insert(0, 'SitSiteNumber', ['' for x in range(sdf.shape[0])])
    sdf.insert(1, 'IPLocInstCode_tab', ['field number' for x in range(sdf.shape[0])])
    sdf.insert(3, 'Loc2Source', ['Recorded using ArcCollector in field' for x in range(sdf.shape[0])])
    sdf['Loc2DateStart'] = pd.to_datetime(sdf['Loc2DateStart']).dt.strftime('%m/%d/%Y')
    sdf.insert(0, 'Loc2DateEnd', sdf['Loc2DateStart'])
    sdf.insert(0, 'LatDetDate0', sdf['Loc2DateStart'])
    sdf.insert(0, 'LatDatum_tab', ['WGS 84' for x in range(sdf.shape[0])])
    sdf.insert(0, 'LatRadiusNumeric_tab', [5 for x in range(sdf.shape[0])])
    sdf.insert(0, 'LatRadiusUnit_tab', ['meters' for x in range(sdf.shape[0])])
    sdf.insert(0, 'LatPreferred_tab', ['yes' for x in range(sdf.shape[0])])
    sdf.insert(0, 'LatVerificationStatus_tab', ['verified by curator' for x in range(sdf.shape[0])])
    sdf.insert(0, 'LatDeterminedByRef_tab.irn', ['' for x in range(sdf.shape[0])])
    sdf['samplingProtocol'] = [f'SAMPLING PROTOCOL: {x}' for x in sdf['samplingProtocol']]
    sdf = sdf.rename({'samplingProtocol': 'NotNotes'}, axis=1)
    sdf.insert(0, 'LatLatLongDetermination_tab', ['Field GPS' for x in range(sdf.shape[0])])

    # Drop extra columns dataframe
    sdf.drop('OBJECTID', axis=1, inplace=True)
    sdf.drop('GlobalID', axis=1, inplace=True)

    # Reorder columns
    header = ['SitSiteNumber', 'IPLocInstCode_tab', 'IPLocInstNumber_tab', 'Loc2Source', 'LocPreciseLocation',
              'LocContinent_tab', 'LocCountry_tab', 'LocProvinceStateTerritory_tab', 'LocDistrictCountyShire_tab',
              'LocTownship_tab', 'LocNearestNamedPlace_tab', 'IPLithoStratDetails', 'NotNotes', 'IPLithology',
              'IPLithification', 'IPLithPreservation', 'IPLocCollName', 'Loc2DateStart', 'Loc2DateEnd', 'IPLithoFormation',
              'IPLithoMember', 'LatRadiusNumeric_tab', 'LatRadiusUnit_tab', 'LatDatum_tab', 'LatPreferred_tab',
              'LatVerificationStatus_tab', 'LatDetSource_tab', 'LatLatLongDetermination_tab', 'LatDeterminedByRef_tab.irn',
              'LatDetDate0', 'SHAPE']
    sdf = sdf[header]

    # Add x,y columns to dataframe
    sdf['Longitude'] = [meters_to_long(x.x) for x in sdf['SHAPE']]
    sdf['Latitude'] = [meters_to_lat(y.y) for y in sdf['SHAPE']]
    sdf.drop('SHAPE', axis=1, inplace=True)

    # Export dataframe to csv
    return sdf.to_csv(out_path, sep=',', index=False)


