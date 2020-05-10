from flask import Flask, request, Response, jsonify
from config import db,areas, ip_port
import requests
import re
from datetime import datetime



app = Flask(__name__)

@app.route('/api/v1/users', methods=["GET"])
def function_to_delete_user():
	if request.method == "GET":
		binded_data = {"many": 1, "table": "users", "columns": ["_id"], "where": {}}
		response = requests.post('http://' + ip_port + '/api/v1/db/read', json=binded_data)
		res = []
		for i in response.json():
			res.append(i['_id'])
		if not res:
			return Response(status=204)
		return jsonify(res)


@app.route('/api/v1/users/<u_name>', methods=["DELETE"])
def functio_to_remove_user(u_name):
	if check_rides_joined_or_created_by_user(u_name):
		return Response(status=400)
	binded_data = {'column': '_id', 'delete': u_name, 'table': 'users'}
	resp = requests.post('http://' + ip_port + '/api/v1/db/write', json=binded_data)
	if resp.status_code == 400:
		return Response(status=400)
	return jsonify({})

@app.route('/api/v1/users', methods=["PUT"])
def function_to_add_user():
	if request.method == "PUT":
		r_data = request.get_json(force=True)

		try:
			u_name = r_data["username"]
			pwd= r_data["password"]
		except KeyError:
			return Response(status=400)

		if re.match(re.compile(r'\b[0-9a-f]{40}\b'), pwd) is None:
			return Response(status=400)

		binded_data = {"insert": [u_name, pwd], "columns": ["_id", "password"], "table": "users"}
		resp = requests.post('http://' + ip_port + '/api/v1/db/write', json=binded_data)

		if resp.status_code == 400:
			return Response(status=400)

		return Response(status=201, response='{}', mimetype='application/json')

@app.route('/api/v1/rides', methods=["POST"])
def function_to_create_ride():
	r_data = request.get_json(force=True)
	try:
		created_by = r_data['created_by']
		time_stamp = r_data['timestamp']
		source = int(r_data['source'])
		destination = int(r_data['destination'])
	except KeyError:
		return Response(status=400)

	try:
		req_date = convert_timestamp_to_datetime(time_stamp)
	except:
		return Response(status=400)

	if (source > len(areas) or destination > len(areas)) and (source < 1 or destination < 1):
		return Response(status=400)

	if not check_user_exist(created_by):
		print("User not present")
		return Response(status=400)

	try:
		f = open('seq.txt', 'r')
		ride_count = int(f.read())
		f.close()

		binded_data = {
            "insert": [ride_count + 1, ride_count + 1, created_by, time_stamp, areas[source-1][1], areas[destination-1][1], []],
            "columns": ["_id", "rideId", "created_by", "timestamp", "source", "destination", "users"], "table": "rides"}
		resp = requests.post('http://' + ip_port + '/api/v1/db/write', json=binded_data)

		if resp.status_code == 400:
			return Response(status=400)
		else:
			filee = open('seq.txt', 'w')
			filee.write(str(ride_count + 1))
			filee.close()
			return Response(status=201, response='{}', mimetype='application/json')
	except:
		return Response(status=400)





@app.route('/api/v1/rides/<rideId>', methods=["GET"])
def get_details_of_ride_or_join_ride_or_delete_ride(rideId):
	try:
		a = int(rideId)
	except:
		return Response(status=400)

	if request.method == "GET":
		binded_data = {"table": "rides",
                     "columns": ["rideId", "created_by", "users", "timestamp", "source", "destination"],
                     "where": {"rideId": int(rideId)}}
		response = requests.post('http://' + ip_port + '/api/v1/db/read', json=binded_data)
		if response.text == "":
			return Response(status=204, response='{}', mimetype='application/json')
		res = response.json()
		del res["_id"]
		return jsonify(res)
@app.route('/api/v1/rides/<rideId>', methods=["POST"])
def join_ride(rideId):
	try:
		a = int(rideId)
	except:
		return Response(status=400)
	if request.method == "POST":
		username = request.get_json(force=True)["username"]
		if not check_user_exist(username):
			return Response(status=400)

		binded_data = {"table": "rides", "where": {"rideId": int(rideId)}, "update": "users", "data": username,
                     "operation": "addToSet"}
		response = requests.post('http://' + ip_port + '/api/v1/db/write', json=binded_data)
		if response.status_code == 400:
			return Response(status=400)
		return jsonify({})
@app.route('/api/v1/rides/<rideId>', methods=["DELETE"])
def function_to_delete_ride(rideId):
	try:
		a = int(rideId)
	except:
		return Response(status=400)
	if request.method == "DELETE":
		binded_data = {'column': 'rideId', 'delete': int(rideId), 'table': 'rides'}
		response = requests.post('http://' + ip_port + '/api/v1/db/write', json=binded_data)
		if response.status_code == 400:
			return Response(status=400)
		return jsonify({})

@app.route('/api/v1/rides', methods=["GET"])
def list_rides_between_src_and_dst():
	src = request.args.get("source")
	dst = request.args.get("destination")
	if src is None or dst is None:
		return Response(status=400)

	try:
		src = int(src)
		dst= int(dst)
	except:
		return Response(status=400)

	if (src > len(areas) or dst > len(areas)) and (src < 1 or dst < 1):
		return Response(status=400)

	binded_data = {"many": 1, "table": "rides", "columns": ["rideId", "created_by", "timestamp"],
                 "where": {"source": areas[src-1][1], "destination": areas[dst-1][1], "timestamp": {"$gt": convert_datetime_to_timestamp(datetime.now())}}}
	resp = requests.post('http://' + ip_port + '/api/v1/db/read', json=binded_data)

	if resp.status_code == 400:
		return Response(status=400)

	result = resp.json()
	for i in range(len(result)):
		if "_id" in result[i]:
			del result[i]["_id"]

	if not result:
		return Response(status=204)
	return jsonify(result)
@app.route('/api/v1/db/write', methods=["POST"])
def write_to_db():
	r_data = request.get_json(force=True)

	if 'delete' in r_data:
		try:
			delete = r_data['delete']
			column = r_data['column']
			collection = r_data['table']
		except KeyError:
			return Response(status=400)

		try:
			query = {column: delete}
			collection = db[collection]
			x = collection.delete_one(query)
			if x.raw_result['n'] == 1:
				return Response(status=200)
			return Response(status=400)
		except:
			return Response(status=400)

	if 'update' in r_data:
		try:
			collection = r_data['table']
			where = r_data['where']
			array = r_data['update']
			data = r_data['data']
			operation = r_data['operation']
		except KeyError:
			return Response(status=400)

		try:
			collection = db[collection]
			x = collection.update_one(where, {"$" + operation: {array: data}})
			if x.raw_result['n'] == 1:
				return Response(status=200)
			return Response(status=400)
		except:
			return Response(status=400)

		try:	
			insert = r_data['insert']
			columns = r_data['columns']
			collection = r_data['table']
		except KeyError:
			return Response(status=400)

		try:
			document = {}
			for i in range(len(columns)):
				if columns[i] == "timestamp":
					document[columns[i]] = convert_timestamp_to_datetime(insert[i])
				else:
					document[columns[i]] = insert[i]
	
			collection = db[collection]
			collection.insert_one(document)
			return Response(status=201)

		except:
			return Response(status=400)


@app.route('/api/v1/db/read', methods=["POST"])
def read_from_db():
	r_data = request.get_json(force=True)
	try:
		table = r_data['table']
		columns = r_data['columns']
		where = r_data['where']
	except KeyError:
		return Response(status=400)

	if "timestamp" in where:
		where["timestamp"]["$gt"] = convert_timestamp_to_datetime(where["timestamp"]["$gt"])

	filter = {}
	for i in columns:
		filter[i] = 1

	if 'many' in r_data:
		try:
			collection = db[table]
			res = []
			for i in collection.find(where, filter):
				if "timestamp" in i:
					i["timestamp"] = convert_datetime_to_timestamp(i["timestamp"])
				res.append(i)

			return jsonify(res)
		except:
			return Response(status=400)

	try:
		collection = db[table]
		result = collection.find_one(where, filter)
		if "timestamp" in result:
			result["timestamp"] = convert_datetime_to_timestamp(result["timestamp"])
		return jsonify(result)
	except:
		return Response(status=400)


@app.route('/api/v1/db/clear', methods=["POST"])
def clear_db():
	collection1 = db["users"]
	collection2 = db["rides"]
	try:
		collection1.delete_many({})
		collection2.delete_many({})
		f = open("seq.txt", "w")
		f.write("0")
		f.close()
		return Response(status=200)
	except:
		return Response(status=400)


def check_user_exist(username):
    binded_data = {'table': 'users', 'columns': ['_id'], 'where': {'_id': username}}
    response = requests.post('http://' + ip_port + '/api/v1/db/read', json=binded_data)
    return response.status_code != 400 and response.text != 'null\n'


def convert_datetime_to_timestamp(k):
	day = str(k.day) if len(str(k.day)) == 2 else "0" + str(k.day)
	month = str(k.month) if len(str(k.month)) == 2 else "0" + str(k.month)
	year = str(k.year)
	second = str(k.second) if len(str(k.second)) == 2 else "0" + str(k.second)
	minute = str(k.minute) if len(str(k.minute)) == 2 else "0" + str(k.minute)
	hour = str(k.hour) if len(str(k.hour)) == 2 else "0" + str(k.hour)
	return day + "-" + month + "-" + year + ":" + second + "-" + minute + "-" + hour


def convert_timestamp_to_datetime(time_stamp):
	day = int(time_stamp[0:2])
	month = int(time_stamp[3:5])
	year = int(time_stamp[6:10])
	seconds = int(time_stamp[11:13])
	minutes = int(time_stamp[14:16])
	hours = int(time_stamp[17:19])
	return datetime(year, month, day, hours, minutes, seconds)


def check_rides_joined_or_created_by_user(username):
	binded_data = {"table": "rides", "columns": [], "where": {"$or": [{"users": username}, {"created_by": username}]}}
	response = requests.post('http://' + ip_port + '/api/v1/db/read', json=binded_data)
	return response.status_code != 400 and response.text != 'null\n'


if __name__ == "__main__":
	app.run(debug=True)
