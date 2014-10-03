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
	print "---------------------------------"
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
		print coIndex

	if pm10:
		pm10Index = index(tablePm10, pm10, 1)
		f = f+1
		print pm10Index

	if no2:
		no2Index = index(tableNo2, no2, 1000)
		f = f+1
		print no2Index

	if f > 0:
		return (coIndex+pm10Index+no2Index)/f


#Examples
#co(ppm)0-50.4(GBG-ex:3.86)
#pm10(micro-g/m3)
#no2(ppm) 0-2.4

print aqi({"co":50,"pm10":600,"no2":2})
print aqi({"co":25,"pm10":None,"no2":1.123})
print aqi({"co":25,"pm10":None,"no2":None})
print aqi({"co":4.123,"pm10":None,"no2":0.024})
