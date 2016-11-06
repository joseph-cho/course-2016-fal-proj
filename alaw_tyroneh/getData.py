import urllib.request
import json
import dml
import csv
import prov.model
import datetime
import uuid
import xmltodict

class getData(dml.Algorithm):
    contributor = 'alaw_tyroneh'
    reads = []
    writes = ['alaw_tyroneh.BostonProperty','alaw_tyroneh.CambridgeProperty','alaw_tyroneh.SomervilleProperty','alaw_tyroneh.BrooklineProperty', 'alaw_tyroneh.HubwayStations', 'alaw_tyroneh.TCStops']

    @staticmethod
    def execute(trial = False):
        '''Retrieve datasets for mongoDB storage and later transformations'''
        
        startTime = datetime.datetime.now()
            
        client = dml.pymongo.MongoClient()
        repo = client.repo
        repo.authenticate('alaw_tyroneh', 'alaw_tyroneh')
        
        
        #JSON urls with SoQL queries
        jsonURLs = {"BostonProperty": 'https://data.cityofboston.gov/resource/jsri-cpsq.json?$select=location',
                    "CambridgeProperty": 'https://data.cambridgema.gov/resource/ufnx-m9uc.json?$query=SELECT%20location_1%20WHERE%20land_use_category%20=%20%22Residential%22%20OR%20land_use_category%20=%20%22Vacant%20Residential%22',
                    "SomervilleProperty":'https://data.somervillema.gov/resource/dhs3-5kuu.json?$query=SELECT%20location_1%20WHERE%20building_type%20=%20%27Residential%27%20OR%20building_type%20=%20%27Condominium%27'}
        
        for key in jsonURLs:  
            url = jsonURLs[key]
            response = urllib.request.urlopen(url).read().decode("utf-8")
            r = json.loads(response)
            
            if(trial == True):
                s = json.dumps(r, sort_keys=True, indent=2)
                print(key)
                print(s)
                print('-----------------')
            
            else:
                # Set up the database connection
                repo.dropPermanent(key)
                repo.createPermanent(key)
                repo['alaw_tyroneh.'+key].insert_many(r)
        
        #GeoJSON urls with queries, read list of features
        geojsonURLs = {"BrooklineProperty":"http://data.brooklinema.gov/datasets/a725742a993f425ea463c2c509d91ca3_1.geojson?where=FEATURECODE%20like%20'%25Building%20General%25'"}
        
        for key in geojsonURLs:  
            url = geojsonURLs[key]
            response = urllib.request.urlopen(url).read().decode("utf-8")
            r = json.loads(response)['features']
            
            if(trial == True):
                s = json.dumps(r, sort_keys=True, indent=2)
                print(key)
                print(s)
                print('-----------------')
            
            else:
                # Set up the database connection
                repo.dropPermanent(key)
                repo.createPermanent(key)
                repo['alaw_tyroneh.'+key].insert_many(r) 
                
        
        #CSV urls, converts them to python dictionaries 
        csvURLs = {"HubwayStations":'https://s3.amazonaws.com/hubway-data/2016_0429_Hubway_Stations.csv'}
        csvFields = {"HubwayStations":['Station','Station ID','Latitude','Longitude','Municipality','# of Docks']}        
        
        for key in csvURLs:
            url = csvURLs[key]
            fieldnames = csvFields[key]
            
            response = urllib.request.urlopen(url)
            csvfile = csv.DictReader(response.read().decode('utf-8').splitlines()[1:],fieldnames)
            
            if(trial == True):
                print(key)
                print(csvfile)
                print('-----------------')
            
            else:
                # Set up the database connection
                repo.dropPermanent(key)
                repo.createPermanent(key)
                repo['alaw_tyroneh.'+key].insert_many(csvfile) 
        
        
        #MBTA API, gets xml files of every T and Commuter rail stop
        route_url = "http://realtime.mbta.com/developer/api/v2/routes?api_key=wX9NwuHnZU2ToO7GmGR9uw&format=json"

        response = urllib.request.urlopen(route_url).read().decode("utf-8")
        r = json.loads(response)
        s = json.dumps(r, sort_keys=True, indent=2)

        routesA = [mode for mode in r["mode"] if mode["mode_name"] == "Subway" or mode["mode_name"] == "Commuter Rail"]
        '''
        routesB = []
        for mode in routesA:
            for route in mode['route']:
                route["mode_name"] = mode["mode_name"]
                routesB.append(route) 
        '''
        routesB = [(mode["mode_name"], route["route_id"]) for mode in routesA for route in mode['route']]

        stop_base = "http://realtime.mbta.com/developer/api/v2/stopsbyroute?api_key=wX9NwuHnZU2ToO7GmGR9uw"
        stop_urls = {route:"{}&route={}&format=json".format(stop_base, route[1]) for route in routesB}
        responses = {route:urllib.request.urlopen(stop_urls[route]).read().decode("utf-8") for route in stop_urls}

        json_stops = []
        for route, response in responses.items():
            stops_by_route = {}

            mode, route_id = route
    
            stops_by_route['name'] = route_id 
            stops_by_route['mode'] = mode
            stops_by_route['path'] = json.loads(response)

            json_stops.append(stops_by_route)

        #json_stops = {oute':route, 'path':json.loads(responses[route]) for route in responses}
        #stops_dumps = {route:json.dumps(json_stops[route], sort_keys=True, indent=2) for route in json_stops}
        stops_dumps = json.dumps(json_stops, sort_keys=True, indent=2)

        result = []
        for route in json_stops:
            result.append({'route':route})

        if(trial == True):
                print(result)
                print('-----------------')
        else:
            # Set up the database connection
            repo.dropPermanent('TCStops')
            repo.createPermanent('TCStops')
            repo['alaw_tyroneh.TCStops'].insert_many(result) 

        repo.logout()
        endTime = datetime.datetime.now()
        
        return {"start":startTime, "end":endTime}

    @staticmethod
    def provenance(doc = prov.model.ProvDocument(), startTime = None, endTime = None):
        '''
        Create the provenance document describing everything happening
        in this script. Each run of the script will generate a new
        document describing that invocation event.
        '''

         # Set up the database connection.
        client = dml.pymongo.MongoClient()
        repo = client.repo
        repo.authenticate('alaw_tyroneh', 'alaw_tyroneh')

        doc.add_namespace('alg', 'http://datamechanics.io/algorithm/') # The scripts are in <folder>#<filename> format.
        doc.add_namespace('dat', 'http://datamechanics.io/data/') # The data sets are in <user>#<collection> format.
        doc.add_namespace('ont', 'http://datamechanics.io/ontology#') # 'Extension', 'DataResource', 'DataSet', 'Retrieval', 'Query', or 'Computation'.
        doc.add_namespace('log', 'http://datamechanics.io/log/') # The event log.
        
        doc.add_namespace('bdp', 'https://data.cityofboston.gov/resource/') # Boston Data Portal
        doc.add_namespace('cdp', 'https://data.cambridgema.gov/resource/') # Cambridge Data Portal
        doc.add_namespace('sdp', 'https://data.somervillema.gov/resource/') # Somerville Data Portal
        doc.add_namespace('brdp', 'http://data.brooklinema.gov/datasets/') # Brookline Data Portal
        doc.add_namespace('hub', 'https://s3.amazonaws.com/hubway-data/') # Hubway Data 
        doc.add_namespace('mbta', 'http://realtime.mbta.com/developer/api/v2/routes') # MBTA API

        this_script = doc.agent('alg:alaw_tyroneh#getData', {prov.model.PROV_TYPE:prov.model.PROV['SoftwareAgent'], 'ont:Extension':'py'})
        
        resource_BostonProperty = doc.entity('bdp:jsri-cpsq', {'prov:label':'Boston Residential Property Coordinates', prov.model.PROV_TYPE:'ont:DataResource', 'ont:Extension':'json'})
        get_BostonProperty = doc.activity('log:uuid'+str(uuid.uuid4()), startTime, endTime, {'prov:label':'Get Boston Residential Property Coordinates'})
        doc.wasAssociatedWith(get_BostonProperty, this_script)
        doc.usage(get_BostonProperty, resource_BostonProperty, startTime, None,
                {prov.model.PROV_TYPE:'ont:Retrieval',
                 'ont:Query':'?$select=location'
                }
            )
        
        resource_CambridgeProperty = doc.entity('cdp:ufnx-m9uc', {'prov:label':'Cambridge Residential Property Coordinates', prov.model.PROV_TYPE:'ont:DataResource', 'ont:Extension':'json'})
        get_CambridgeProperty = doc.activity('log:uuid'+str(uuid.uuid4()), startTime, endTime, {'prov:label':'Get Cambridge Residential Property Coordinates'})
        doc.wasAssociatedWith(get_CambridgeProperty, this_script)
        doc.usage(get_CambridgeProperty, resource_CambridgeProperty, startTime, None,
                {prov.model.PROV_TYPE:'ont:Retrieval',
                 'ont:Query':'?$query=SELECT%20location_1%20WHERE%20land_use_category%20=%20%22Residential%22%20OR%20land_use_category%20=%20%22Vacant%20Residential%22'
                }
            )
            
        resource_SomervilleProperty = doc.entity('sdp:dhs3-5kuu', {'prov:label':'Somerville Residential Property Coordinates', prov.model.PROV_TYPE:'ont:DataResource', 'ont:Extension':'json'})
        get_SomervilleProperty = doc.activity('log:uuid'+str(uuid.uuid4()), startTime, endTime, {'prov:label':'Get Somerville Residential Property Coordinates'})
        doc.wasAssociatedWith(get_SomervilleProperty, this_script)
        doc.usage(get_SomervilleProperty, resource_SomervilleProperty, startTime, None,
                {prov.model.PROV_TYPE:'ont:Retrieval',
                 'ont:Query':'?$query=SELECT%20location_1%20WHERE%20building_type%20=%20%27Residential%27%20OR%20building_type%20=%20%27Condominium%27'
                }
            )
        
        resource_BrooklineProperty = doc.entity('brdp:a725742a993f425ea463c2c509d91ca3_1', {'prov:label':'Brookline Residential Property Coordinates', prov.model.PROV_TYPE:'ont:DataResource', 'ont:Extension':'geojson'})
        get_BrooklineProperty = doc.activity('log:uuid'+str(uuid.uuid4()), startTime, endTime, {'prov:label':'Get Brookline Residential Property Coordinates'})
        doc.wasAssociatedWith(get_BrooklineProperty, this_script)
        doc.usage(get_BrooklineProperty, resource_BrooklineProperty, startTime, None,
                {prov.model.PROV_TYPE:'ont:Retrieval',
                 'ont:Query':"?where=FEATURECODE%20like%20'%25Building%20General%25"
                }
            )  
        
        resource_HubwayStations = doc.entity('hub:2016_0429_Hubway_Stations', {'prov:label':'Hubway Stations Coordinates', prov.model.PROV_TYPE:'ont:DataResource', 'ont:Extension':'csv'})
        get_HubwayStations = doc.activity('log:uuid'+str(uuid.uuid4()), startTime, endTime, {'prov:label':'Get Hubway Stations Coordinates'})
        doc.wasAssociatedWith(get_HubwayStations, this_script)
        doc.usage(get_HubwayStations, resource_HubwayStations, startTime, None,
                {prov.model.PROV_TYPE:'ont:Retrieval',
                 'ont:Query':""
                }
            )
        
        resource_TCStops = doc.entity('mbta:wX9NwuHnZU2ToO7GmGR9uw', {'prov:label':'T and Commuter Stations', prov.model.PROV_TYPE:'ont:DataResource', 'ont:Extension':'json'})
        get_TCStops = doc.activity('log:uuid'+str(uuid.uuid4()), startTime, endTime, {'prov:label':'Get T and Commuter Stations'})
        doc.wasAssociatedWith(get_TCStops, this_script)
        doc.usage(get_TCStops, resource_TCStops, startTime, None,
                {prov.model.PROV_TYPE:'ont:Retrieval',
                 'ont:Query':""
                }
            )

        BostonProperty = doc.entity('dat:alaw_tyroneh#BostonProperty', {prov.model.PROV_LABEL:'Boston Residential Property Coordinates', prov.model.PROV_TYPE:'ont:DataSet'})
        doc.wasAttributedTo(BostonProperty, this_script)
        doc.wasGeneratedBy(BostonProperty, get_BostonProperty, endTime)
        
        CambridgeProperty = doc.entity('dat:alaw_tyroneh#CambridgeProperty', {prov.model.PROV_LABEL:'Cambridge Property Property Coordinates', prov.model.PROV_TYPE:'ont:DataSet'})
        doc.wasAttributedTo(CambridgeProperty, this_script)
        doc.wasGeneratedBy(CambridgeProperty, get_CambridgeProperty, endTime)
        
        SomervilleProperty = doc.entity('dat:alaw_tyroneh#SomervilleProperty', {prov.model.PROV_LABEL:'Somerville Property Property Coordinates', prov.model.PROV_TYPE:'ont:DataSet'})
        doc.wasAttributedTo(SomervilleProperty, this_script)
        doc.wasGeneratedBy(SomervilleProperty, get_SomervilleProperty, endTime)
        
        BrooklineProperty = doc.entity('dat:alaw_tyroneh#BrooklineProperty', {prov.model.PROV_LABEL:'Brookline Property Property Coordinates', prov.model.PROV_TYPE:'ont:DataSet'})
        doc.wasAttributedTo(BrooklineProperty, this_script)
        doc.wasGeneratedBy(BrooklineProperty, get_BrooklineProperty, endTime)
        
        HubwayStations = doc.entity('dat:alaw_tyroneh#HubwayStations', {prov.model.PROV_LABEL:'Hubway Stations Coordinates', prov.model.PROV_TYPE:'ont:DataSet'})
        doc.wasAttributedTo(HubwayStations, this_script)
        doc.wasGeneratedBy(HubwayStations, get_HubwayStations, endTime)

        TCStops = doc.entity('dat:alaw_tyroneh#TCStops', {prov.model.PROV_LABEL:'T and Commuter Stations', prov.model.PROV_TYPE:'ont:DataSet'})
        doc.wasAttributedTo(TCStops, this_script)
        doc.wasGeneratedBy(TCStops, get_TCStops, endTime)

        repo.record(doc.serialize()) # Record the provenance document.
        repo.logout()

        return doc
    
    def run(t=False):
        '''
        Scrap datasets and write provenance files
        '''

        times = getData.execute(trial=t)
        getData.provenance(startTime = times['start'], endTime = times['end'])

if __name__ == '__main__':
    getData.run()
## eof
