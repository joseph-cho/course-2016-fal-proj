import urllib.request
import json
import dml
import prov.model
import datetime
import uuid

class convertToGeo(dml.Algorithm):
    contributor = 'arjunlam'
    reads = ['arjunlam.crime', 'arjunlam.closed311', 'arjunlam.hotline', 'arjunlam.potholes', 'arjunlam.develop']
    writes = ['arjunlam.crime', 'arjunlam.closed311', 'arjunlam.hotline', 'arjunlam.potholes', 'arjunlam.develop']

    @staticmethod
    def execute(trial = False):
        '''Retrieve some data sets (not using the API here for the sake of simplicity).'''
        startTime = datetime.datetime.now()
        
        # Set up the database connection.
        client = dml.pymongo.MongoClient()
        repo = client.repo
        repo.authenticate('arjunlam', 'arjunlam')
        
        #Load in json file that maps polic districts to zipcodes
        url = 'http://datamechanics.io/data/PoliceDistrictsToZipcodes.json'
        response = urllib.request.urlopen(url).read().decode("utf-8")
        zipcode_data = json.loads(response)

        #Set up geojson format
        def crimeGeoJason(crimeData):
            type = crimeData['location_2']['type']
            geometryType = crimeData['location_2']['type']
            longitude = crimeData['long']
            latitude = crimeData['lat']
            police_district = crimeData['district']
            zipcode = zipcode_data[police_district]
            
            return {
                'type': type,
                'geometry': {
                    'type': geometryType,
                    'coordinates': [longitude, latitude]
                }, 
                'properties': {
                    'police_district': police_district,
                    'zipcode': zipcode
                }
            }
            
        def hotlineGeoJason(hotlineData):
            type = hotlineData['geocoded_location']['type']
            longitude = hotlineData['geocoded_location']['coordinates'][0]
            latitude = hotlineData['geocoded_location']['coordinates'][1]
            police_district = hotlineData['police_district']
            zipcode = hotlineData['location_zipcode']
            
            return {
                'type': type,
                'geometry': {
                    'type': type,
                    'coordinates': [longitude, latitude]
                }, 
                'properties': {
                    'police_district': police_district,
                    'zipcode': zipcode
                }
            }
        
        def closed311GeoJason(closedData):
            type = closedData['geocoded_location']['type']
            longitude = closedData['longitude']
            latitude = closedData['latitude']
            police_district = closedData['police_district']
            zipcode = closedData['location_zipcode']
            
            return {
                'type': type,
                'geometry': {
                    'type': type,
                    'coordinates': [longitude, latitude]
                }, 
                'properties': {
                    'police_district': police_district,
                    'zipcode': zipcode
                }
            }
        
        def potholesGeoJason(potholesData):
            type = "Point"
            longitude = potholesData['longitude']
            latitude = potholesData['latitude']
            police_district = potholesData['police_district']
            zipcode = zipcode_data[police_district]
            
            return {
                'type': type,
                'geometry': {
                    'type': type,
                    'coordinates': [longitude, latitude]
                }, 
                'properties': {
                    'police_district': police_district,
                    'zipcode': zipcode
                }
            }
        
        def developGeoJason(developData):
            type = developData['the_geom']['type']
            coordinates = developData['the_geom']['coordinates'][0][0]
            zipcode = developData['zipcode']
            
            return {
                'type': type,
                'geometry': {
                    'type': type,
                    'coordinates': coordinates
                }, 
                'properties': {
                    'police_district': 'NA',
                    'zipcode': zipcode
                }
            }
        
        #get id by using repo.arjunlam.crime.find()['_id']
        #to add new column use repo.arjunlam.crime.update({'_id': some id}, {$set: {"geo_location": value/dict}})
        #To delete a field (ie column) use repo.arjunlam.crime.update({'_id': some id}, {$unset: {"some field": 1}})
        
        #Update datasets
        crime = repo.arjunlam.crime
        hotline = repo.arjunlam.hotline
        closed311 = repo.arjunlam.closed311
        develop = repo.arjunlam.develop
        potholes = repo.arjunlam.potholes
        
        collectionsArray = [crime, hotline, closed311, develop, potholes]
        
        output = '' #did this since some records don't have location information
        for collection in collectionsArray:
            for row in collection.find():
                rowId = row['_id']
    
                if (collection == repo.arjunlam.crime):
                    if ('location_2' in row) and ('district' in row): #check if the fields exists
                        output = crimeGeoJason(row)
                        collection.update({'_id': rowId}, {'$unset': {'location_2': 1}})
                        collection.update({'_id': rowId}, {'$unset': {'lat': 1}})
                        collection.update({'_id': rowId}, {'$unset': {'long': 1}})
                elif (collection == repo.arjunlam.hotline):
                    if ('geocoded_location' in row) and ('police_district' in row) and ('location_zipcode' in row):
                        output = hotlineGeoJason(row)
                        collection.update({'_id': rowId}, {'$unset': {'geocoded_location': 1}})
                        collection.update({'_id': rowId}, {'$unset': {'location_zipcode': 1}})
                        collection.update({'_id': rowId}, {'$unset': {'latitude': 1}})
                        collection.update({'_id': rowId}, {'$unset': {'longitude': 1}})
                elif (collection == repo.arjunlam.closed311):
                    if ('geocoded_location' in row) and ('police_district' in row) and ('location_zipcode' in row):
                        output = closed311GeoJason(row)
                        collection.update({'_id': rowId}, {'$unset': {'geocoded_location': 1}})
                        collection.update({'_id': rowId}, {'$unset': {'location_zipcode': 1}})
                        collection.update({'_id': rowId}, {'$unset': {'latitude': 1}})
                        collection.update({'_id': rowId}, {'$unset': {'longitude': 1}})
                elif (collection == repo.arjunlam.develop):
                    if ('the_geom' in row) and ('zipcode' in row):
                        output = developGeoJason(row)
                        collection.update({'_id': rowId}, {'$unset': {'the_geom': 1}})
                        collection.update({'_id': rowId}, {'$unset': {'zipcode': 1}})
                else:
                    if ('geocoded_location' in row) and ('police_district' in row) and ('location_zipcode' in row):
                        output = potholesGeoJason(row)
                        collection.update({'_id': rowId}, {'$unset': {'geocoded_location': 1}})
                        collection.update({'_id': rowId}, {'$unset': {'location_zipcode': 1}})
                        collection.update({'_id': rowId}, {'$unset': {'latitude': 1}})
                        collection.update({'_id': rowId}, {'$unset': {'longitude': 1}})
    
                collection.update({'_id': rowId}, {'$set': {'geo_location': output}})
        

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
        repo.authenticate('arjunlam', 'arjunlam')

        doc.add_namespace('alg', 'http://datamechanics.io/algorithm/') # The scripts are in <folder>#<filename> format.
        doc.add_namespace('dat', 'http://datamechanics.io/data/') # The data sets are in <user>#<collection> format.
        doc.add_namespace('ont', 'http://datamechanics.io/ontology#') # 'Extension', 'DataResource', 'DataSet', 'Retrieval', 'Query', or 'Computation'.
        doc.add_namespace('log', 'http://datamechanics.io/log/') # The event log.
        doc.add_namespace('bdp', 'https://data.cityofboston.gov/resource/')

        this_script = doc.agent('alg:arjunlam#convertToGeo', {prov.model.PROV_TYPE:prov.model.PROV['SoftwareAgent'], 'ont:Extension':'py'})
        
        crime_entity = doc.entity('bdp:29yf-ye7n', {'prov:label':'Crime Incident Report', prov.model.PROV_TYPE:'ont:DataResource', 'ont:Extension':'json'})
        
        closed311_entity = doc.entity('bdp:wc8w-nujj', {'prov:label':'Closed 311 Requests', prov.model.PROV_TYPE:'ont:DataResource', 'ont:Extension':'json'})
        
        develop_entity = doc.entity('bdp:k26b-7bmj', {'prov:label':'DND Developed Property', prov.model.PROV_TYPE:'ont:DataResource', 'ont:Extension':'json'})
        
        hotline_entity = doc.entity('bdp:jbcd-dknd', {'prov:label':'Mayor 24hr Hotline', prov.model.PROV_TYPE:'ont:DataResource', 'ont:Extension':'json'})
        
        pothole_entity = doc.entity('bdp:wivc-syw7', {'prov:label':'Closed Pothole Cases', prov.model.PROV_TYPE:'ont:DataResource', 'ont:Extension':'json'})
        
        get_crime = doc.activity('log:uuid'+str(uuid.uuid4()), startTime, endTime)
        get_closed311 = doc.activity('log:uuid'+str(uuid.uuid4()), startTime, endTime)
        get_develop = doc.activity('log:uuid'+str(uuid.uuid4()), startTime, endTime)
        get_hotline = doc.activity('log:uuid'+str(uuid.uuid4()), startTime, endTime)
        get_potholes = doc.activity('log:uuid'+str(uuid.uuid4()), startTime, endTime)
        
        doc.wasAssociatedWith(get_crime, this_script)
        doc.wasAssociatedWith(get_closed311, this_script)
        doc.wasAssociatedWith(get_develop, this_script)
        doc.wasAssociatedWith(get_hotline, this_script)
        doc.wasAssociatedWith(get_potholes, this_script)
        
        doc.usage(get_crime, crime_entity, startTime, None, {prov.model.PROV_TYPE:'ont:Retrieval'})
        doc.usage(get_closed311, closed311_entity, startTime, None, {prov.model.PROV_TYPE:'ont:Retrieval'})
        doc.usage(get_develop, develop_entity, startTime, None, {prov.model.PROV_TYPE:'ont:Retrieval'})
        doc.usage(get_hotline, hotline_entity, startTime, None, {prov.model.PROV_TYPE:'ont:Retrieval'})
        doc.usage(get_potholes, pothole_entity, startTime, None, {prov.model.PROV_TYPE:'ont:Retrieval'})
        
        crime = doc.entity('dat:arjunlam#crime', {prov.model.PROV_LABEL:'Crime Incident Report', prov.model.PROV_TYPE:'ont:DataSet'})
        doc.wasAttributedTo(crime, this_script)
        doc.wasGeneratedBy(crime, get_crime, endTime)
        doc.wasDerivedFrom(crime, crime_entity, get_crime, get_crime, get_crime)

        closed311 = doc.entity('dat:arjunlam#closed311', {prov.model.PROV_LABEL:'Closed 311', prov.model.PROV_TYPE:'ont:DataSet'})
        doc.wasAttributedTo(closed311, this_script)
        doc.wasGeneratedBy(closed311, get_closed311, endTime)
        doc.wasDerivedFrom(closed311, closed311_entity, get_closed311, get_closed311, get_closed311)
        
        develop = doc.entity('dat:arjunlam#develop', {prov.model.PROV_LABEL:'DND Developed Property', prov.model.PROV_TYPE:'ont:DataSet'})
        doc.wasAttributedTo(develop, this_script)
        doc.wasGeneratedBy(develop, get_develop, endTime)
        doc.wasDerivedFrom(develop, develop_entity, get_develop, get_develop, get_develop)
        
        hotline = doc.entity('dat:arjunlam#hotline', {prov.model.PROV_LABEL:'Mayor 24hr Hotline', prov.model.PROV_TYPE:'ont:DataSet'})
        doc.wasAttributedTo(hotline, this_script)
        doc.wasGeneratedBy(hotline, get_hotline, endTime)
        doc.wasDerivedFrom(hotline, hotline_entity, get_hotline, get_hotline, get_hotline)
        
        potholes = doc.entity('dat:arjunlam#potholes', {prov.model.PROV_LABEL:'Closed Pothole Cases', prov.model.PROV_TYPE:'ont:DataSet'})
        doc.wasAttributedTo(potholes, this_script)
        doc.wasGeneratedBy(potholes, get_potholes, endTime)
        doc.wasDerivedFrom(potholes, pothole_entity, get_potholes, get_potholes, get_potholes)

        

        repo.record(doc.serialize()) # Record the provenance document.
        repo.logout()

        return doc


convertToGeo.execute()
#doc = convertToGeo.provenance()
#print(doc.get_provn())
#print(json.dumps(json.loads(doc.serialize()), indent=4))

## eof