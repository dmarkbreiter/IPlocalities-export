import math

from arcgis import GIS
import pandas as pd



def meters_to_wgs84(meters, direction):
    """Converts longitude/latitude point from Spherical Mercator EPSG:900913 to lat/long in WGS84 Datum"""
    origin_shift = 2 * math.pi * 6378137 / 2.0

    if direction.lower() == 'longitude':
        wgs84 = (meters / origin_shift) * 180.0
    elif direction.lower() == 'latitude':
        wgs84 = (meters/ origin_shift) * 180.0
        wgs84 = 180 / math.pi * (2 * math.atan(math.exp(wgs84 * math.pi / 180.0)) - math.pi / 2.0)
    else:
        print("Accepted values for direction include 'latitude' and 'longitude' only!")

    return wgs84


def meters_to_lat(y):
    """Converts latitude point from Spherical Mercator EPSG:900913 to latitude in WGS84 Datum"""
    lat = 180 / math.pi * (2 * math.atan(math.exp(lat * math.pi / 180.0)) - math.pi / 2.0)
    return lat


def get_localities_layer(url, username, password):
    # Access to ArcGIS Online account
    gis = GIS(url, username, password)

    # Retrieve Field Localities by name, and access first layer in collection
    localities_layer = gis.content.search(query="title:Field Localities", item_type="Feature Layer")[0].layers[0]

    return localities_layer

class Localities:
    def __init__(self, localities_layer):
        # Create a spatially enabled dataframe from ArcGIS Online web layer
        self.sdf = pd.DataFrame.spatial.from_layer(localities_layer)


    def choose_dates(self, start_date, end_date):
        # Reformat 'Loc2DateStart' column so its MM/DD/YYYY
        self.sdf['Loc2DateStart'] = pd.to_datetime(self.sdf['Loc2DateStart']).dt.strftime('%m/%d/%Y')

        # Reformat start_date and end_date to MM/DD/YYYY

        # Create Boolean mask
        date_mask = (self.sdf['Loc2DateStart'] > start_date) & (self.sdf['Loc2DateStart'] <= end_date)

        # Apply mask to sdf and return a spatially enabled dataframe
        sdf_date_mask = self.sdf.loc[date_mask]

        return sdf_date_mask


    def reformat(self, header_schema=''):
        # Add columns
        self.sdf.insert(0, 'SitSiteNumber', ['' for x in range(self.sdf.shape[0])])
        self.sdf.insert(1, 'IPLocInstCode_tab', ['field number' for x in range(self.sdf.shape[0])])
        self.sdf.insert(3, 'Loc2Source', ['Recorded using ArcCollector in field' for x in range(self.sdf.shape[0])])
        self.sdf['Loc2DateStart'] = pd.to_datetime(self.sdf['Loc2DateStart']).dt.strftime('%m/%d/%Y')
        self.sdf.insert(0, 'Loc2DateEnd', self.sdf['Loc2DateStart'])
        self.sdf.insert(0, 'LatDetDate0', self.sdf['Loc2DateStart'])
        self.sdf.insert(0, 'LatDatum_tab', ['WGS 84' for x in range(self.sdf.shape[0])])
        self.sdf.insert(0, 'LatRadiusNumeric_tab', [5 for x in range(self.sdf.shape[0])])
        self.sdf.insert(0, 'LatRadiusUnit_tab', ['meters' for x in range(self.sdf.shape[0])])
        self.sdf.insert(0, 'LatPreferred_tab', ['yes' for x in range(self.sdf.shape[0])])
        self.sdf.insert(0, 'LatVerificationStatus_tab', ['verified by curator' for x in range(self.sdf.shape[0])])
        self.sdf.insert(0, 'LatDeterminedByRef_tab.irn', ['' for x in range(self.sdf.shape[0])])
        self.sdf['samplingProtocol'] = [f'SAMPLING PROTOCOL: {x}' for x in self.sdf['samplingProtocol']]
        self.sdf = self.sdf.rename({'samplingProtocol': 'NotNotes'}, axis=1)
        self.sdf.insert(0, 'LatLatLongDetermination_tab', ['Field GPS' for x in range(self.sdf.shape[0])])

        # Drop extra columns dataframe
        self.sdf.drop('OBJECTID', axis=1, inplace=True)
        self.sdf.drop('GlobalID', axis=1, inplace=True)

        # Reorder columns according to header from user specified csv (header_schema) by creating dataframe and listing
        # column values
        if header_schema != '':
            header = list(pd.read_csv(header_schema).columns.values)
            self.sdf = self.sdf[header]

        # Add x,y columns to dataframe
        self.sdf['Longitude'] = [meters_to_wgs84(x.x, 'longitude') for x in self.sdf['SHAPE']]
        self.sdf['Latitude'] = [meters_to_wgs84(y.y, 'latitude') for y in self.sdf['SHAPE']]
        self.sdf.drop('SHAPE', axis=1, inplace=True)

        return self


    def export_to_csv(self, out_path):
        # Export dataframe to csv
        return self.sdf.to_csv(out_path, sep=',', index=False)


# Consume code
if __name__ == '__main__':
    ip_localities_layer = get_localities_layer("https://nhmlac.maps.arcgis.com/home/index.html",
                                         "dmarkbreiter_NHMLAC", "j5BDj%k3@BaG")

    IP_Localities = Localities(ip_localities_layer).reformat()

    IP_Localities.export_to_csv('/Users/macbook/Desktop/FieldLocalitiesTestExport3_22.csv')
