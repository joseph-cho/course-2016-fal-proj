import urllib.request
import json
import dml
import prov.model
import datetime
import uuid
from helpers import *

class example(dml.Algorithm):
    contributor = 'aydenbu_huangyh'
    reads = []
    writes = [
              'aydenbu_huangyh.hospitalLocation',
              'aydenbu_huangyh.healthyCornerStores',
              'aydenbu_huangyh.healthyCornerStores',
              'aydenbu_huangyh.communityGardens',
              'aydenbu_huangyh.publicSchool'
             ]

    @staticmethod
    def execute(trial = False):
        '''Retrieve some data sets (not using the API here for the sake of simplicity).'''
        startTime = datetime.datetime.now()
        
        # Set up the database connection.
        repo = openDb(getAuth("db_username"), getAuth("db_password"))


        url = "https://data.cityofboston.gov/resource/u6fv-m8v4.json"
        response = urllib.request.urlopen(url).read().decode("utf-8")
        r = json.loads(response)
        s = json.dumps(r, sort_keys=True, indent=2)
        repo.dropPermanent("hospitalLocation")
        repo.createPermanent("hospitalLocation")
        repo['aydenbu_huangyh.hospitalLocation'].insert_many(r)

        url = "https://data.cityofboston.gov/resource/bejm-5s9g.json"
        response = urllib.request.urlopen(url).read().decode("utf-8")
        r = json.loads(response)
        s = json.dumps(r, sort_keys=True, indent=2)
        repo.dropPermanent("earningsReport")
        repo.createPermanent("earningsReport")
        repo['aydenbu_huangyh.earningsReport'].insert_many(r)

        url = "https://data.cityofboston.gov/resource/ybm6-m5qd.json"
        response = urllib.request.urlopen(url).read().decode("utf-8")
        r = json.loads(response)
        s = json.dumps(r, sort_keys=True, indent=2)
        repo.dropPermanent("healthyCornerStores")
        repo.createPermanent("healthyCornerStores")
        repo['aydenbu_huangyh.healthyCornerStores'].insert_many(r)

        url = "https://data.cityofboston.gov/resource/rdqf-ter7.json"
        response = urllib.request.urlopen(url).read().decode("utf-8")
        r = json.loads(response)
        s = json.dumps(r, sort_keys=True, indent=2)
        repo.dropPermanent("communityGardens")
        repo.createPermanent("communityGardens")
        repo['aydenbu_huangyh.communityGardens'].insert_many(r)

        url = "https://data.cityofboston.gov/resource/492y-i77g.json"
        response = urllib.request.urlopen(url).read().decode("utf-8")
        r = json.loads(response)
        s = json.dumps(r, sort_keys=True, indent=2)
        repo.dropPermanent("publicSchool")
        repo.createPermanent("publicSchool")
        repo['aydenbu_huangyh.publicSchool'].insert_many(r)

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
        repo = openDb(getAuth("db_username"), getAuth("db_password"))

        doc.add_namespace('alg', 'http://datamechanics.io/algorithm/') # The scripts are in <folder>#<filename> format.
        doc.add_namespace('dat', 'http://datamechanics.io/data/') # The data sets are in <user>#<collection> format.
        doc.add_namespace('ont', 'http://datamechanics.io/ontology#') # 'Extension', 'DataResource', 'DataSet', 'Retrieval', 'Query', or 'Computation'.
        doc.add_namespace('log', 'http://datamechanics.io/log/') # The event log.
        doc.add_namespace('bdp', 'https://data.cityofboston.gov/resource/')

        this_script = doc.agent('alg:aydenbu_huangyh#example', {prov.model.PROV_TYPE:prov.model.PROV['SoftwareAgent'], 'ont:Extension':'py'})
        resource = doc.entity('bdp:wc8w-nujj', {'prov:label':'City of Boston Dataset', prov.model.PROV_TYPE:'ont:DataResource', 'ont:Extension':'json'})
        get_earningsReport = doc.activity('log:uuid'+str(uuid.uuid4()), startTime, endTime)
        get_hospitalLocation = doc.activity('log:uuid'+str(uuid.uuid4()), startTime, endTime)
        get_healthyCornerStores = doc.activity('log:uuid'+str(uuid.uuid4()), startTime, endTime)
        get_communityGardens = doc.activity('log:uuid'+str(uuid.uuid4()), startTime, endTime)
        get_publicSchool = doc.activity('log:uuid'+str(uuid.uuid4()), startTime, endTime)

        doc.wasAssociatedWith(get_hospitalLocation, this_script)
        doc.wasAssociatedWith(get_earningsReport, this_script)
        doc.wasAssociatedWith(get_healthyCornerStores, this_script)
        doc.wasAssociatedWith(get_communityGardens, this_script)
        doc.wasAssociatedWith(get_publicSchool, this_script)

        doc.usage(get_earningsReport, resource, startTime, None,
                {prov.model.PROV_TYPE:'ont:Retrieval',
                 'ont:Query':'?type=POSTAL, Earnings'
                }
            )
        doc.usage(get_hospitalLocation, resource, startTime, None,
                {prov.model.PROV_TYPE:'ont:Retrieval',
                 'ont:Query':'?type=zipcode'
                }
            )
        doc.usage(get_healthyCornerStores, resource, startTime, None,
                  {prov.model.PROV_TYPE:'ont:Retrieval',
                   'ont:Query':'?type=zipcode'
                   }
            )

        doc.usage(get_communityGardens, resource, startTime, None,
                  {prov.model.PROV_TYPE: 'ont:Retrieval',
                   'ont:Query': '?type=zipcode'
                   }
                  )

        doc.usage(get_publicSchool, resource, startTime, None,
                  {prov.model.PROV_TYPE: 'ont:Retrieval',
                   'ont:Query': '?type=zipcode'
                   }
                  )

        earningsReport = doc.entity('dat:aydenbu_huangyh#earningsReport', {prov.model.PROV_LABEL:'Earnings Report', prov.model.PROV_TYPE:'ont:DataSet'})
        doc.wasAttributedTo(earningsReport, this_script)
        doc.wasGeneratedBy(earningsReport, get_earningsReport, endTime)
        doc.wasDerivedFrom(earningsReport, resource, get_earningsReport, get_earningsReport, get_earningsReport)

        hospitalLocation = doc.entity('dat:aydenbu_huangyh#hospitalLocation', {prov.model.PROV_LABEL:'Hospital Location', prov.model.PROV_TYPE:'ont:DataSet'})
        doc.wasAttributedTo(hospitalLocation, this_script)
        doc.wasGeneratedBy(hospitalLocation, get_hospitalLocation, endTime)
        doc.wasDerivedFrom(hospitalLocation, resource, get_hospitalLocation, get_hospitalLocation, get_hospitalLocation)

        healthyCornerStores = doc.entity('dat:aydenbu_huangyh#healthCornerStores',
                                      {prov.model.PROV_LABEL: 'Health Corner Store', prov.model.PROV_TYPE: 'ont:DataSet'})
        doc.wasAttributedTo(healthyCornerStores, this_script)
        doc.wasGeneratedBy(healthyCornerStores, get_healthyCornerStores, endTime)
        doc.wasDerivedFrom(healthyCornerStores, resource, get_healthyCornerStores, get_healthyCornerStores, get_healthyCornerStores)

        communityGardens = doc.entity('dat:aydenbu_huangyh#communityGardens',
                                         {prov.model.PROV_LABEL: 'Community Gardens',
                                          prov.model.PROV_TYPE: 'ont:DataSet'})
        doc.wasAttributedTo(communityGardens, this_script)
        doc.wasGeneratedBy(communityGardens, get_communityGardens, endTime)
        doc.wasDerivedFrom(communityGardens, resource, get_communityGardens, get_communityGardens,
                           get_communityGardens)

        publicSchool = doc.entity('dat:aydenbu_huangyh#publicSchools',
                                      {prov.model.PROV_LABEL: 'publicSchools',
                                       prov.model.PROV_TYPE: 'ont:DataSet'})
        doc.wasAttributedTo(publicSchool, this_script)
        doc.wasGeneratedBy(publicSchool, get_publicSchool, endTime)
        doc.wasDerivedFrom(publicSchool, resource, get_publicSchool, get_publicSchool,
                           get_publicSchool)


        repo.record(doc.serialize()) # Record the provenance document.
        repo.logout()

        return doc

example.execute()
doc = example.provenance()
print(doc.get_provn())
print(json.dumps(json.loads(doc.serialize()), indent=4))

## eof