import xml.etree.ElementTree as ET
import base64, zlib, json, argparse, os

# Set up argument parser
parser = argparse.ArgumentParser(description="Process XML file and apply coordinate offset.")
parser.add_argument("xml_file", type=str, help="Path to the XML file")
parser.add_argument("-x", type=float, default=0.0, help="Offset to apply to x coordinates")
parser.add_argument("-y", type=float, default=0.0, help="Offset to apply to y coordinates")
args = parser.parse_args()

name = args.xml_file.split(".")[0]

tree = ET.parse(args.xml_file)
root = tree.getroot()

dict_element = root.find("dict")

for i in range(len(dict_element)):
	if dict_element[i].tag == "k" and dict_element[i].text == "k4":
		levelString = dict_element[i + 1].text
		break

def decode_level(level_data: str, is_official_level: bool) -> str:
	if is_official_level:
		level_data = "H4sIAAAAAAAAA" + level_data
	base64_decoded = base64.urlsafe_b64decode(level_data.encode())
	decompressed = zlib.decompress(base64_decoded, 15 | 32)
	return decompressed.decode()

def match_float(input_num):
	if input_num < 0.5 or input_num > 2:
		print("Major precision loss. Invalid scale value. You cannot use scalehack values.")
	
	mapping = {
		0.5: 244,
		0.53: 245,
		0.561: 246,
		0.595: 247,
		0.63: 248,
		0.667: 249,
		0.707: 250,
		0.749: 251,
		0.794: 252,
		0.841: 254,
		0.891: 254,
		0.944: 255,
		1.0: 0,
		1.059: 1,
		1.122: 2,
		1.189: 3,
		1.26: 4,
		1.335: 5,
		1.414: 6,
		1.498: 7,
		1.587: 8,
		1.682: 9,
		1.782: 10,
		1.888: 11,
		2.0: 12
	}
	
	closest_key = min(mapping.keys(), key=lambda x: abs(x - input_num))
	return mapping[closest_key]

def parse_angle(angle):
	while angle < 0:
		angle += 360
	while angle >= 360:
		angle -= 360

	return int(angle/5)

level_data = decode_level(levelString, False)
startString, objectString = level_data.split(";", 1)

IMPORTANT_IDS = [
	1, # id
	2, # x
	3, # y
	4, # flip horiz
	5, # flip vert
	6, # rotation
	32, # scale
	128, # scale x
	129, # scale Y
	131, # warp Y angle
	132, # warp X angle
	24, # z layer
	25, # z order
	21, # main colour
	22 # detail colour
]

Z_LAYER_MAPPING = {
	-5: 0,
	-3: 1,
	-1: 2,
	1: 3,
	3: 4,
	5: 5,
	7: 6,
	9: 7,
	11: 8
}

allColours = {
	0: { # default colour
		"r": 255,
		"g": 255,
		"b": 255,
		"opacity": 255,
		"blending": False
	}
}

start = startString.split(",")
startPairs = {start[i]: start[i+1] for i in range(0, len(start), 2)}

if "kS38" in startPairs:
	colours = startPairs["kS38"].split("|")
	for colour in colours:
		if not colour:
			continue
		colour = colour.split("_")
		colourPairs = {colour[i]: colour[i+1] for i in range(0, len(colour), 2)}

		colourObj = {
			"r": int(colourPairs["1"]),
			"g": int(colourPairs["2"]),
			"b": int(colourPairs["3"]),
			"opacity": 255,
			"blending": False
		}

		if "7" in colourPairs:
			colourObj["opacity"] = int(colourPairs["7"])

		if "5" in colourPairs and colourPairs["5"] == "1":
			colourObj["blending"] = True

		allColours[int(colourPairs["6"])] = colourObj

objects = []

for obj in objectString.split(";"):
	if not obj:
		continue
	obj = obj.split(",")
	objPairs = {int(obj[i]): obj[i+1] for i in range(0, len(obj), 2)}
	
	keys_to_remove = [key for key in objPairs if key not in IMPORTANT_IDS]

	returnObj = {
		"id": 1,
		"x": 0,
		"y": 0,
		"x_scale_exp": 0,
		"x_angle": 0,
		"y_scale_exp": 0,
		"y_angle": 0,
		"z_layer": 3,
		"z_order": 0,
		"main_color": allColours[0],
		"detail_color": allColours[0]
	}

	# id
	returnObj["id"] = int(objPairs[1])

 	# x and y
	# round x and y to nearest 0.5
	returnObj["x"] = round(float(objPairs[2]) * 2) / 2 + args.x
	returnObj["y"] = round(float(objPairs[3]) * 2) / 2 + args.y

	# scale
	if 32 in objPairs:
		if 128 in objPairs or 129 in objPairs:
			assert objPairs[32] == objPairs[128] == objPairs[129], "what"
		objPairs[128] = objPairs[129] = objPairs[32]

	if 128 not in objPairs:
		objPairs[128] = 1
	if 129 not in objPairs:
		objPairs[129] = 1
	
	returnObj["x_scale_exp"] = match_float(float(objPairs[128]))
	returnObj["y_scale_exp"] = match_float(float(objPairs[129]))

	# rotation
	if 131 not in objPairs:
		objPairs[131] = 0
	else:
		objPairs[131] = float(objPairs[131])
	
	if 132 not in objPairs:
		objPairs[132] = 0
	else:
		objPairs[132] = float(objPairs[132])

	if 4 in objPairs and objPairs[4] == "1":
		objPairs[132] += 180

	if 5 in objPairs and objPairs[5] == "1":
		objPairs[131] += 180

	if 6 in objPairs:
		rot = float(objPairs[6])
		objPairs[131] += rot
		objPairs[132] += rot

	returnObj["x_angle"] = parse_angle(objPairs[132])
	returnObj["y_angle"] = parse_angle(objPairs[131])


	# z layer/order
	if 24 in objPairs:
		returnObj["z_layer"] = Z_LAYER_MAPPING[int(objPairs[24])]

	if 25 in objPairs:
		returnObj["z_order"] = int(objPairs[25])

	# colours
	if 21 in objPairs:
		if int(objPairs[21]) in allColours:
			returnObj["main_color"] = allColours[int(objPairs[21])]

	if 22 in objPairs:
		if int(objPairs[22]) in allColours:
			returnObj["detail_color"] = allColours[int(objPairs[22])]

	objects.append(returnObj)

os.makedirs("output", exist_ok=True)

name = os.path.basename(name)

with open(f"output/{name}.json", "w") as f:
	json.dump(objects, f, indent=4)