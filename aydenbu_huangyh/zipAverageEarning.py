import urllib.request
import json
import dml
import prov.model
import datetime
import uuid
from bson.code import Code
from bson.json_util import dumps
from helpers import *



class zipAverageEarning(dml.Algorithm):
    contributor = 'aydenbu_huangyh'
    reads = ['aydenbu_huangyh.earningReport']
    writes = ['aydenbu_huangyh.zip_avg_earnings']

    @staticmethod
    def execute(trial = False):

        startTime = datetime.datetime.now()

        # Setup the database connection
        # client = dml.pymongo.MongoClient()
        # repo = client.repo
        # repo.authenticate(getAuth('db_username'), getAuth('db_password'))

        # Connect to the Database
        repo = openDb(getAuth("db_username"), getAuth("db_password"))

        # get the collection
        earnings = repo['aydenbu_huangyh.earningsReport']

        # MaoReduce function
        mapper = Code(
            """
            function() {
                var k = this.postal;
                if  (k != null) {
                    k = k.substring(1);
                    var v = {count:1, totalEarnings:parseFloat(this.total_earnings), avg:parseFloat(this.total_earnings)};
                    emit(k, v)
                }
            }
            """
        )

        reducer = Code(
            """
            function(k, vs) {
                reduceVal = {count:0, totalEarnings:0, avg:0};
                for (var i = 0; i < vs.length; i++) {
                    reduceVal.count += vs[i].count;
                    reduceVal.totalEarnings += parseFloat(vs[i].totalEarnings);
                }
                reduceVal.avg = (reduceVal.totalEarnings/reduceVal.count).toFixed(2);
                return reduceVal;
            }
            """
        )

        repo.dropPermanent("zip_avg_earnings")
        result = earnings.map_reduce(mapper, reducer, "aydenbu_huangyh.zip_avg_earnings")

        zip_avg_earnings = repo['aydenbu_huangyh.zip_avg_earnings']


        # Remove the unrelated field, only keep the avg field
        zip_avg_earnings.update(
            {},
            { '$unset': {'value.count': '', 'value.totalEarnings': ''}},
            multi = True,
            upsert = False
        )

        '''
                # Save the result to the db
                # repo.dropPermanent("zip_hospitals_count")
                #repo.createPermanent("zip_hospitals_count")
                # repo['aydenbu_huangyh.zip_hospitals_count'].insert_many(result)
                '''
        repo.logout()
        endTime = datetime.datetime.now()

        return {"start": startTime, "end": endTime}

    @staticmethod
    def provenance(doc=prov.model.ProvDocument(), startTime=None, endTime=None):
        '''
        Create the provenance document describing everything happening
        in this script. Each run of the script will generate a new
        document describing that invocation event.
        '''

        # Set up the database connection.
        repo = openDb(getAuth("db_username"), getAuth("db_password"))

        doc.add_namespace('alg', 'http://datamechanics.io/algorithm/')  # The scripts are in <folder>#<filename> format.
        doc.add_namespace('dat', 'http://datamechanics.io/data/')  # The data sets are in <user>#<collection> format.
        doc.add_namespace('ont',
                          'http://datamechanics.io/ontology#')  # 'Extension', 'DataResource', 'DataSet', 'Retrieval', 'Query', or 'Computation'.
        doc.add_namespace('log', 'http://datamechanics.io/log/')  # The event log.
        doc.add_namespace('bdp', 'https://data.cityofboston.gov/resource/')

        this_script = doc.agent('alg:aydenbu_huangyh#zipAverageEarning',
                                {prov.model.PROV_TYPE: prov.model.PROV['SoftwareAgent'], 'ont:Extension': 'py'})
        resource = doc.entity('dat:employee_earnings_report_2015',
                              {'prov:label': 'Employee Earnings Report 2015', prov.model.PROV_TYPE: 'ont:DataResource',
                               'ont:Extension': 'json'})

        get_zip_avg_earnings = doc.activity('log:uuid' + str(uuid.uuid4()), startTime, endTime, {prov.model.PROV_LABEL: "Compute the avg earning from each zip"})
        doc.wasAssociatedWith(get_zip_avg_earnings, this_script)
        doc.usage(get_zip_avg_earnings, resource, startTime, None,
                  {prov.model.PROV_TYPE: 'ont:Computation'})

        zip_avg_earnings = doc.entity('dat:aydenbu_huangyh#zip_avg_earnings',
                                         {prov.model.PROV_LABEL: 'Avg Earnings',
                                          prov.model.PROV_TYPE: 'ont:DataSet'})
        doc.wasAttributedTo(zip_avg_earnings, this_script)
        doc.wasGeneratedBy(zip_avg_earnings, get_zip_avg_earnings, endTime)
        doc.wasDerivedFrom(zip_avg_earnings, resource, get_zip_avg_earnings, get_zip_avg_earnings,
                           get_zip_avg_earnings)

        repo.record(doc.serialize())  # Record the provenance document.
        repo.logout()

        return doc


zipAverageEarning.execute()
doc = zipAverageEarning.provenance()
print(doc.get_provn())
print(json.dumps(json.loads(doc.serialize()), indent=4))

## add provenance
## eof