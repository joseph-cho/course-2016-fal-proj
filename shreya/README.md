#Project 1

My overall goal for this project is to identify trends between average income of neighborhoods and other possibly related factors such as new building permits and crime.

Data sets from the City of Boston:

1. Approved Building Permits (2006-2016)

2. Crime Incident Reports (July 2012 - August 2015)

3. Employee Earnings Report 2012

4. Employee Earnings Report 2013

5. Employee Earnings Report 2014

6. Employee Earnings Report 2015

Transformations:

1. The new dataset for Approved Building Permits only has building permits approved between July 2012 and August 2015 are in the new dataset, to be consistent with the Crime Incident Reports dataset. Some of the json objects from the API did not have location coordinates, so I used the Python module geopy (https://pypi.python.org/pypi/geopy) to return the latitude and longitude of each location based on zipcode. Then, I calculated the k-means of approved building permits by year. The new dataset maps each year to a list of 45 means. I wasn't sure whether or not to include building permits with the status "expired" because I'm not sure how relevant that will be to the question I am trying to answer.

2. I split up the Crime Incident Reports by year and found the k-means of crime incident reports by year. The new dataset maps years to a list of 45 means.

3. For each Employee Earnings Report, I found the k-means. Instead of giving each employee a value of 1, I made the weight the salary. This way the k-means algorithm will determine where the wealth is most concentrated in Boston. For these datasets as well, I had to use the geopy module to change the zipcode to latitude and longitude coordinates.Since the City of Boston employees aren't an accurate representation of all wealth, I got the average of each zipcode by adding up the wealth in each zipcode and dividing it by the number of people in that zipcode to get a better idea. I'm not sure if this is the best approach so I might change this in the future.

All of the new datasets are of the form: (year, list of 45 means found through the k-means algorithm). This is to see the progression of the building permits, crime, and wealth over the period of 4 years and attempt to find a correlation between the 3. I chose 45 means because according to the City of Boston website, that is how many zipcodes are approximately in the Greater Boston area.

The k-means algorithm I used is very similar to the one used in lecture notes, but instead of taking in 2 sets of points (M, P), M is defined as 45 points in the 02215 zipcode and the input is a dictionary with the keys being points and the values being the weight. This way in the part of the algorithm which puts 1 as the weight for each point, based on the point the salary can be used as a weight. For the other two usages of k-means, I used the same code and input dictionaries where every key has a value of 1. I implemented a check where the distance between each of the old means and new means are below a certain threshold, and I chose 0.1 for this project. If I figure out a better way to determine this value, I'll change it in the future.


			