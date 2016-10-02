import urllib.request
import json
import dml
import prov.model
import datetime
import uuid
from bson.code import Code
from bson.json_util import dumps
from helpers import *


class merge(dml.Algorithm):
    contributor = 'aydenbu_huangyh'
    reads = ['aydenbu_huangyh.zip_PublicSchool_count',
             'aydenbu_huangyh.zip_communityGardens_count']
    writes = ['aydenbu_huangyh.zip_public']

    @staticmethod
    def execute(trial = False):

        startTime = datetime.datetime.now()

        # Set up the database connection
        repo = openDb(getAuth("db_username"), getAuth("db_password"))

        # Get the collections
        gardens = repo['aydenbu_huangyh.zip_communityGardens_count']
        schools = repo['aydenbu_huangyh.zip_PublicSchool_count']


        # For every document in hospitals zip find the number of store that associate with that zip
        zip_public = []
        for document in gardens.find():
            schools_count = schools.find_one({'_id': document['_id']}, {'_id': False, 'value.numofSchool': True})
            if schools_count is None:
                zip = {'_id': document['_id'],
                        'value': {
                            'numofGarden': document['value']['numofGarden'],
                            'numofSchool': 0.0}  # Assign the 0 to the num if there is no result
                       }
                zip_public.append(zip)
                continue
            else:
                zip = {'_id': document['_id'],
                        'value': {
                            'numofGarden': document['value']['numofGarden'],
                            'numofSchool': schools_count['value']['numofSchool']}
                       }
                zip_public.append(zip)
        ''''''''''''''''''''''''''''''''''''''''''''''''


        # Create a new collection and insert the result data set
        repo.dropPermanent("merge_school_garden")
        repo.createPermanent("merge_school_garden")
        repo['aydenbu_huangyh.merge_school_garden'].insert_many(zip_public)

        repo.logout()
        endTime = datetime.datetime.now()

        return {"start": startTime, "end": endTime}





    @staticmethod
    def provenance(doc = prov.model.ProvDocument(), startTime = None, endTime = None):

        # Set up the database connection
        client = dml.pymongo.MongoClient()
        repo = client.repo
        repo.authenticate('aydenbu_huangyh', 'aydenbu_huangyh')

        doc.add_namespace('alg', 'http://datamechanics.io/algorithm/')  # The scripts are in <folder>#<filename> format.
        doc.add_namespace('dat', 'http://datamechanics.io/data/')  # The data sets are in <user>#<collection> format.
        doc.add_namespace('ont',
                          'http://datamechanics.io/ontology#')  # 'Extension', 'DataResource', 'DataSet', 'Retrieval', 'Query', or 'Computation'.
        doc.add_namespace('log', 'http://datamechanics.io/log/')  # The event log.
        doc.add_namespace('bdp', 'https://data.cityofboston.gov/resource/')

        '''
        '''
        # The agent
        this_script = doc.agent('alg:aydenbu_huangyh#merge_school_garden',
                                {prov.model.PROV_TYPE: prov.model.PROV['SoftwareAgent'], 'ont:Extension': 'py'})

        # The source entity
        school_source = doc.entity('dat:public_school_count',
                              {'prov:label': 'Public School Count', prov.model.PROV_TYPE: 'ont:DataResource',
                               'ont:Extension': 'json'})
        garden_source = doc.entity('dat:community_garden_count',
                                  {'prov:label': 'Community Garden Count', prov.model.PROV_TYPE: 'ont:DataResource',
                                   'ont:Extension': 'json'})

        # The activity
        get_zip_public = doc.activity('log:uuid' + str(uuid.uuid4()), startTime, endTime,
                                               {prov.model.PROV_LABEL: "Merge the numbers of garden and school in each zip"})

        # The activity is associated with the agent
        doc.wasAssociatedWith(get_zip_public, this_script)

        # Usage of the activity: Source Entity
        doc.usage(get_zip_public, school_source, startTime, None,
                  {prov.model.PROV_TYPE: 'ont:Computation'})
        doc.usage(get_zip_public, garden_source, startTime, None,
                  {prov.model.PROV_TYPE: 'ont:Computation'})

        # The Result Entity
        zip_public = doc.entity('dat:aydenbu_huangyh#merge_school_garden',
                                            {prov.model.PROV_LABEL: 'Merge Public Building Count',
                                             prov.model.PROV_TYPE: 'ont:DataSet'})

        # Result Entity was attributed to the agent
        doc.wasAttributedTo(zip_public, this_script)

        # Result Entity was generated by the activity
        doc.wasGeneratedBy(zip_public, get_zip_public, endTime)

        # Result Entity was Derived From Source Entity
        doc.wasDerivedFrom(zip_public, school_source, get_zip_public, get_zip_public,
                           get_zip_public)
        doc.wasDerivedFrom(zip_public, garden_source, get_zip_public, get_zip_public,
                           get_zip_public)

        repo.record(doc.serialize())
        repo.logout()

        return doc

merge.execute()
doc = merge.provenance()
print(doc.get_provn())
print(json.dumps(json.loads(doc.serialize()), indent=4))