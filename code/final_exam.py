# import the http requests library to get stuff from the internet
import requests
# import the url parsing library to urlencode the query
import urllib.parse
# define the query to launch
endpointUrl = "https://query.wikidata.org/sparql?query=";
# define the query to launch
query = """
SELECT ?label ?coord ?subj ?year
WHERE
{
    ?subj wdt:P31 wd:Q178561 .
    {?subj wdt:P17 wd:Q38} UNION {?subj wdt:P17 wd:Q183}.
    ?subj wdt:P625 ?coord .
    OPTIONAL {?subj wdt:P580 ?d1}
    OPTIONAL {?subj wdt:P585 ?d2}
    OPTIONAL {?subj wdt:P582 ?d3}
    BIND(IF(!BOUND(?d1),(IF(!BOUND(?d2),?d3,?d2)),?d1) as ?date)
    BIND(YEAR(?date) as ?year)
    ?subj rdfs:label ?label filter (lang(?label) = "en")
}"""

# URL encode the query string
encoded_query = urllib.parse.quote(query)
# prepare the final url
url = f"{endpointUrl}{encoded_query}&format=json"
# run the query online and get the produced result as a dictionary
r=requests.get(url)
result = r.json()
#print(result)




###########################################################################
from pyqgis_scripting_ext.core import*
HMap.remove_layers_by_name(["OpenStreetMap", "Battles","countriesLayer3857",citiesName, countriesName, "rivers_italy"])
folder="C:/Users/marti/Desktop/advanced geomatics/github/"
data_folder=folder+"data/"
output_folder=folder+"tmp/"
geopackage_path=data_folder+"reduced_ne.gpkg"
countriesName = 'ne_50m_admin_0_countries'
countriesLayer=HVectorLayer.open(geopackage_path, countriesName)

crsHelper=HCrs()
crsHelper.from_srid(4326)
crsHelper.to_srid(3857)

countriesLayer3857=HVectorLayer.new('countriesLayer3857', 'multipolygon', 'EPSG:3857', {'NAME':'string'})
countriesFeatures=countriesLayer.features()
nameIndex = countriesLayer.field_index('NAME')
for feature in countriesFeatures:
    countryName = feature.attributes[nameIndex]
    countryGeometry = feature.geometry
    geometry=crsHelper.transform(countryGeometry)
    countriesLayer3857.add_feature(geometry,[countryName])
countriesLayer3857.subset_filter("NAME='Italy' OR NAME='Germany'")



head=result['head']['vars']
features=result['results']['bindings']




# Define the attribute fields for the layer
fields = {
    'label': 'String',
    'lon': 'float',
    'lat': 'float',
    'subj': 'String',
    'year': 'Integer'
}

BattlesLayer = HVectorLayer.new('Battles', 'Point', 'EPSG:3857', fields)

counter_italy1 = 0
counter_germany1 = 0

counter_italy2 = 0
counter_germany2 = 0

counter_italy3 = 0
counter_germany3 = 0

for item in features:
    label=item.get("label").get("value")
    coord=item.get("coord").get("value").strip(")").strip("Point(").split(" ")
    subj=item.get("subj").get("value")
    if "year" in item:
        year=int(item.get("year").get("value"))
    else:
        year=None
    lon=float(coord[0])
    lat=float(coord[1])

    location=HPoint(lon,lat)
    location3857=crsHelper.transform(location)
    for feature in countriesFeatures:
        countryName = feature.attributes[nameIndex]
        countryGeometry = feature.geometry
        if location.intersects(countryGeometry):
            BattlesLayer.add_feature(location3857,[label,lon,lat , subj, year])
            if year and 0<=year<=1000:
                if countryName=="Italy":
                    counter_italy1+=1
                elif countryName=="Germany":
                    counter_germany1+=1
    
print(f"their was {counter_italy1} battle in Italy during the first milenary and {counter_germany1} in Germany")

#styling

country_style=HFill('0,255,0,35')+HStroke("black", 1)
countriesLayer3857.set_style(country_style)


ranges = [
    [float('-inf'),0],
    [0, 1000],
    [1001, 1500],
    [1501, 2000]]

point_style= [HStroke("black", 0.1)+HMarker("star",3)+HFill("red"),
                HStroke("black", 0.1)+HMarker("star",3)+HFill("orange"),
                HStroke("black", 0.1)+HMarker("star",3)+HFill("green"),
                HStroke("black", 0.1)+HMarker("star",3)+HFill("blue")]
                
########################################################################################
######################################################################################################
field="if(year>0 AND year<=1000,label,'')"
labelProperties = {
    "font": "Arial",
    "color": "black",
    "size": 5,
    "field": field,
    "along_line": True,
    "bold": True,
    "italic": True
}
labelStyle = HLabel(**labelProperties) + HHalo("white", 1)
###########################################################################################
#############################################################################
BattlesLayer.set_graduated_style('year',ranges,point_style,labelStyle)



path = output_folder + 'Battles.gpkg'

error = BattlesLayer.dump_to_gpkg(path, overwrite=True)

if error:
    print(error)
osm=HMap.get_osm_layer()
HMap.add_layer(osm)
HMap.add_layer(countriesLayer3857)
HMap.add_layer(BattlesLayer)

#set the extente
extente=countriesLayer3857.bbox()
new_coords=[]
for index, coords in enumerate(extente):
    if index<2:
        coord1=coords-100000
        new_coords.append(coord1)
    else:
        coord2=coords+100000
        new_coords.append(coord2)



printer = HPrinter(iface)
map_properties={
        "x":5,
        "y":5,
        "width":215,
        "height":200,
        "extent":new_coords,
        "frame":True
}
printer.add_map(**map_properties)


Scalebar_Properties={
        "x":5,
        "y":5,
        "style":"Single Box"
}

printer.add_scalebar(**Scalebar_Properties)
label_properties1={
        "x":225, 
        "y":100, 
        "text":f"Between the year 0 and 1000 \ntheir have been:\n{counter_italy1} battles in Italy\n{counter_germany1} battles in Germany", 
        "font":"Arial",
        "font_size":14, 
        "bold":False,
        "italic":False, 
        "underline":False
}
printer.add_label(**label_properties1)

label_properties2={
        "x":225, 
        "y":10, 
        "text":" Battles in Italy\n and Germany",
        "font":"Arial",
        "font_size":20, 
        "bold":False,
        "italic":False, 
        "underline":False
}

printer.add_label(**label_properties2)

legend_properties={"x": 225, 
        "y":30, 
        "width":150, 
        "height":100, 
        "frame":True, 
        "max_symbol_size":3}
printer.add_legend(**legend_properties)

outputPdf =f"{output_folder}final_map.pdf"
printer.dump_to_pdf(outputPdf)
