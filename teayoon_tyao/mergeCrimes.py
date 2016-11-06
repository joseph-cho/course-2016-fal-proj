import urllib.request
import json
import dml
import prov.model
import datetime
import uuid

class mergeCrimes(dml.Algorithm):
    contributor = 'teayoon_tyao'
    reads = ['teayoon_tyao.crimesLegacy', 'teayoon_tyao.crimesCurrent']
    writes = ['teayoon_tyao.crimesMaster']

    @staticmethod
    def execute(trial = False):
        startTime = datetime.datetime.now()

        client = dml.pymongo.MongoClient()
        repo = client.repo
        repo.authenticate('teayoon_tyao', 'teayoon_tyao')

        repo.dropPermanent('teayoon_tyao.crimesMaster')
        repo.createPermanent('teayoon_tyao.crimesMaster')

        data = repo.teayoon_tyao.crimesLegacy.find()
        for document in data:
            legacyDict = dict(document)
            if legacyDict['incident_type_description'] == 'Drug Violation' or legacyDict['incident_type_description'] == 'DRUG CHARGES' and legacyDict['location']['coordinates'] and legacyDict['fromdate'] and legacyDict['day_week']:

                dateAndTime = legacyDict['fromdate'].split("T")
                date = dateAndTime[0].split("-")
                time = dateAndTime[1].split(":")
                date = date[1] + "/" + date[2] + "/" + date[0]
                time = time[0] + ":" + time[1]
                dateAndTime = date + " " + time

                entry = {'date':dateAndTime,'day':legacyDict['day_week'], 'latitude':legacyDict['location']['coordinates'][0], 'longitude':legacyDict['location']['coordinates'][1]}
                
                res = repo.teayoon_tyao.crimesMaster.insert_one(entry)

        data = repo.teayoon_tyao.crimesCurrent.find()
        for document in data:
            currentDict = dict(document)
            if currentDict['offense_code_group'] == 'Drug Violation' and currentDict['occurred_on_date'] and currentDict['day_of_week']:
                
                dateAndTime = currentDict['occurred_on_date'].split("T")
                date = dateAndTime[0].split("-")
                time = dateAndTime[1].split(":")
                date = date[1] + "/" + date[2] + "/" + date[0]
                time = time[0] + ":" + time[1]
                dateAndTime = date + " " + time

                try:
                    latitude = currentDict['location_2']['coordinates'][0]
                    longitude = currentDict['location_2']['coordinates'][1]
                except:
                    latitude = None
                    longitude = None


                entry = {'date':dateAndTime, 'day':currentDict['day_of_week'], 'latitude':latitude, 'longitude':longitude}

                res = repo.teayoon_tyao.crimesMaster.insert_one(entry)
                
        endTime = datetime.datetime.now()
        return {"Start ":startTime, "End ":endTime}

            
    @staticmethod
    def provenance(doc = prov.model.ProvDocument(), startTime = None, endTime = None):
        client = dml.pymongo.MongoClient()
        repo = client.repo
        repo.authenticate('teayoon_tyao', 'teayoon_tyao')

        doc.add_namespace('alg', 'http://datamechanics.io/algorithm/') # The scripts are in <folder>#<filename> format.
        doc.add_namespace('dat', 'http://datamechanics.io/data/') # The data sets are in <user>#<collection> format.
        doc.add_namespace('ont', 'http://datamechanics.io/ontology#') # 'Extension', 'DataResource', 'DataSet', 'Retrieval', 'Query', or 'Computation'.
        doc.add_namespace('log', 'http://datamechanics.io/log/') # The event log.
        doc.add_namespace('cob', 'https://data.cityofboston.gov/resource/')
        doc.add_namespace('bod', 'http://bostonopendata.boston.opendata.arcgis.com/datasets/')

        this_script = doc.agent('alg:teayoon_tyao#mergeCrimes', {prov.model.PROV_TYPE:prov.model.PROV['SoftwareAgent'], 'ont:Extension':'py'})
        mergeCRI = doc.activity('log:uuid' + str(uuid.uuid4()), startTime, endTime, {'prov:label':'Merge Crime Data', prov.model.PROV_TYPE:'ont:Computation'})
        doc.wasAssociatedWith(mergeCRI, this_script)
        
        resource_crimesLegacy = doc.entity('dat:teayoon_tyao#crimesLegacy', {'prov:label':'Past Crime Incident Reports', prov.model.PROV_TYPE:'ont:Dataset'})
        doc.usage(mergeCRI, resource_crimesLegacy, startTime)

        resource_crimesCurrent = doc.entity('dat:teayoon_tyao#crimesCurrent', {'prov:label':'Current Crime Incident Reports', prov.model.PROV_TYPE:'ont:Dataset'})
        doc.usage(mergeCRI, resource_crimesCurrent, startTime)

        resource_crimesMaster = doc.entity('dat:teayoon_tyao#crimesMaster', {'prov:label':'All Crime Incident Reports', prov.model.PROV_TYPE:'ont:Dataset'})

        doc.wasAttributedTo(resource_crimesMaster, this_script)
        doc.wasGeneratedBy(resource_crimesMaster, mergeCRI, endTime)
        doc.wasDerivedFrom(resource_crimesMaster, resource_crimesLegacy, mergeCRI, mergeCRI, mergeCRI)
        doc.wasDerivedFrom(resource_crimesMaster, resource_crimesCurrent, mergeCRI, mergeCRI, mergeCRI)

        repo.record(doc.serialize()) # Record the provenance document.
        repo.logout()

        return doc

mergeCrimes.execute()
doc = mergeCrimes.provenance()
print(doc.get_provn())
print(json.dumps(json.loads(doc.serialize()), indent=4))