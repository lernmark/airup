tableAqiIndex = [ range(0, 50, 1),range(51, 100, 1),range(101, 150, 1),range(151, 200, 1),range(201, 300, 1),range(301, 400, 1),range(401, 500, 1) ]
tableCo = [ range(0, 44, 1),range(45, 94, 1),range(95, 124, 1),range(125, 154, 1),range(155, 304, 1),range(305, 404, 1),range(405, 504, 1) ] 
tableNo2 = [ range(0, 53, 1),range(54, 100, 1),range(101, 360, 1),range(361, 640, 1),range(650, 1240, 1),range(1250, 1640, 1),range(1650, 2040, 1) ] 
tablePm10 = [ range(0, 54, 1),range(55, 154, 1),range(155, 254, 1),range(255, 354, 1),range(355, 424, 1),range(425, 504, 1),range(505, 604, 1) ] 

def index(table, v, fac):
	row = [i for i,l in enumerate(table) if int(v*fac) in l][0]
	bpLow = float(table[row][0])/fac
	bpHigh = (float(table[row][len(table[row])-1]+1)/fac)
	iLow = tableAqiIndex[row][0]
	iHigh = tableAqiIndex[row][len(tableAqiIndex[row])-1]+1
	index = (
		(float(iHigh) - float(iLow)) / 
		(float(bpHigh) - float(bpLow))
		) * (float(v)-(float(bpLow))) + float(iLow)
	return int(index)

def aqi(values):
	co=values["co"]
	pm10=values["pm10"]
	no2=values["no2"]

	f = 0
	coIndex = 0
	pm10Index = 0
	no2Index = 0

	if co:
		coIndex = index(tableCo, co, 10)
		f = f+1
		#print coIndex

	if pm10:
		pm10Index = index(tablePm10, pm10, 1)
		f = f+1
		#print pm10Index

	if no2:
		no2Index = index(tableNo2, no2, 1000)
		f = f+1
		#print no2Index

	if f > 0:
		return (coIndex+pm10Index+no2Index)/f



#print "-------- CO ---------"
# kan vara mellan 0 - 50 ppm
index(tableCo, 3.5, 10)
index(tableCo, 2, 10)
index(tableCo, 3, 10)
index(tableCo, 4, 10)
index(tableCo, 4.2, 10)
index(tableCo, 4.7, 10)
index(tableCo, 5, 10)
index(tableCo, 5.2, 10)
index(tableCo, 5.7, 10)
index(tableCo, 6, 10)
index(tableCo, 8.4, 10)

#print "-------- pm10 ---------"
# Kan vara mellan 0 - 600
index(tablePm10, 20, 1)
index(tablePm10, 30, 1)
index(tablePm10, 40, 1)
index(tablePm10, 50, 1)
index(tablePm10, 60, 1)
index(tablePm10, 70, 1)
index(tablePm10, 80, 1)
index(tablePm10, 90, 1)
index(tablePm10, 100, 1)
index(tablePm10, 210, 1)

#print "-------- no2 ---------"
# Kan vara mellan 0 - 2
#print tableNo2
index(tableNo2, 0.033, 1000)
index(tableNo2, 1.823, 1000)
index(tableNo2, 1.930, 1000)
#print index(tableNo2, 2.039, 1000)
#print aqi({"co":50,"pm10":600,"no2":2})
#print aqi({"co":25,"pm10":None,"no2":1.123})
#print aqi({"co":4.123,"pm10":None,"no2":0.024})
#NO2 30.37 ug/m3
#CO 2.73 ug/m3
#PM10 10.71 ug/m3
#'no2':str(((no2/1000)*24.45)/46.01),
#'co':str(((co/1000)*24.45)/28.01),
print aqi({"co":(((45.02/1000.00000)*24.45000)/28.01000),"pm10":10.710,"no2":(((63.45/1000.00000)*24.45000)/46.01000)})