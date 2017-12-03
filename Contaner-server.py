# import part
from flask import Flask, Response, render_template, request
import json
from subprocess import Popen, PIPE
import os
from tempfile import mkdtemp
from werkzeug import secure_filename

app = Flask(__name__)

# ALL DIFFERENT API ENDPOINTS CAN BE USED
@app.route("/")
def index():
    return """
Available API endpoints:
GET /containers                     List all containers
GET /containers?state=running      List running containers (only)
GET /containers/<id>                Inspect a specific container
GET /containers/<id>/logs           Dump specific container logs
GET /images                         List all images
POST /images                        Create a new image
POST /containers                    Create a new container
PATCH /containers/<id>              Change a container's state
PATCH /images/<id>                  Change a specific image's attributes
DELETE /containers/<id>             Delete a specific container
DELETE /containers                  Delete all containers (including running)
DELETE /images/<id>                 Delete a specific image
DELETE /images                      Delete all images
"""


# UES GET METHOD TO ACEES CONTAINERS LIST
@app.route('/containers', methods=['GET'])
def containers_index():
    """
    List all containers

    curl -s -X GET -H 'Accept: application/json' http://localhost:8080/containers | python -mjson.tool
    curl -s -X GET -H 'Accept: application/json' http://localhost:8080/containers?state=running | python -mjson.tool
    """
    if request.args.get('state') == 'running':
        output = docker('ps')
        resp = json.dumps(docker_ps_to_array(output))

    else:
        output = docker('ps', '-a')
        resp = json.dumps(docker_ps_to_array(output))

    return Response(response=resp, mimetype="application/json")


# UES GET METHOD TO ACEES IMAGES LIST
@app.route('/images', methods=['GET'])
def images_index():
    """
    List all images
    Complete the code below generating a valid response.
    curl -s -X GET -H 'Accept' : application/json
    http://localhost:8080/images | python -mjson.tool

    """
    output = docker("images")
    resp = json.dumps(docker_images_to_array(output))
    return Response(response=resp, mimetype="application/json")


# UES GET METHOD TO INSPECT SPECIFIC CONTAINER
@app.route('/containers/<id>', methods=['GET'])
def containers_show(id):
    """
    Inspect specific container
    curl -s -X GET -H 'Accept: application/json'
    http://localhost:8080/container/<id> | python -mjson.tool
    """
    output = docker('inspect', id)
    resp = json.dumps(docker_logs_to_object(id,output))

    return Response(response=resp, mimetype="application/json")


# UES GET METHOD TO DUMP SPECIFIC CONTAINER LOGS
@app.route('/containers/<id>/logs', methods=['GET'])
def containers_log(id):
    """
    Dump specific container logs
    curl -s -X GET -H 'Accept: application/json'
    http://localhost:8080/container/<id>/logs | python -mjson.tool
    """
    output = docker('logs',id)
    resp = json.dumps(docker_logs_to_object(id,output))

    return Response(response=resp, mimetype="application/json")


# UES DELETE METHOD TO DELETE A SPECIFIC IMAGE
@app.route('/images/<id>', methods=['DELETE'])
def images_remove(id):
    """
    Delete a specific image
    curl -s -X DELETE -H 'Accept: application/json'
    http://localhost:8080/images/<id> | python -mjson.tool
    """

    docker ('rmi', id)
    resp = '{"id": "%s"}' % id

    return Response(response=resp, mimetype="application/json")

# USE DELETE METHOD TO DELETE A SPECIFIC CONTAINER
@app.route('/containers/<id>', methods=['DELETE'])
def containers_remove(id):
    """
    Delete a specific container - must be already stopped/killed
    curl -s -X DELETE -H 'Accept: application/json'
    http://localhost:8080/containers/<id> | python -mjson.tool
    """
    docker('stop',id)
    docker('rm',id)
    resp = '{"id": "%s"}' % id
    return Response(response=resp, mimetype="application/json")

# USE DELETE METHOD TO DELETE ALL CONTAINERS
@app.route('/containers', methods=['DELETE'])
def containers_remove_all():
    """
    Force remove all containers - dangrous
    curl -X DELETE -H 'Accept: application/json'
    http://localhost:8080/containers
    """
    output =docker('ps','-a')
    list = docker_ps_to_array(output)
    idS = []
    for c in list:
        id = c['id']
        docker('stop',id)
        docker('rm',id)
        idS.append(id)
    resp = json.dump(idS)
    return Response(response=resp, mimetype="application/json")

# USE DELETE METHOD TO REMOVE ALL IMAGES
@app.route('/images', methods=['DELETE'])
def images_remove_all():
    """
    Force remove all images - dangrous!
    curl -X DELETE -H 'Accept: application/json'
    http://localhost:8080/images
    """
    output = docker('images')
    list = docker_images_to_array(output)
    idS = []
    for c in list:
        id = c['id']
        docker('rmi', id)
        idS.append(id)
    resp = json.dumps(idS)
    return Response(response=resp, mimetype="application/json")

# USE POST METHOD TO CREATE CONTAINERS
@app.route('/containers', methods=['POST'])
def containers_create():
    """
    Create container (from existing image using id or name)
    curl -X POST -H 'Content-Type: application/json' http://localhost:8080/containers -d '{"image": "my-app"}'
    curl -X POST -H 'Content-Type: application/json' http://localhost:8080/containers -d '{"image": "b14752a6590e"}'
    curl -X POST -H 'Content-Type: application/json' http://localhost:8080/containers -d '{"image": "b14752a6590e","publish":"8081:22"}'
    """
    body = request.get_json(force=True)
    image = body['image']
    args = ('run', '-d')
    id = docker(*(args + (image,)))[0:12]
    return Response(response='{"id": "%s"}' % id, mimetype="application/json")

# USE POST METHOD TO CREATE IMAGES
@app.route('/images', methods=['POST'])
def images_create():
    """
    Create image (from uploaded Dockerfile)
    curl -H 'Accept: application/json' -F file=@Dockerfile http://localhost:8080/images
    """
    dockerfile = request.files['file']
    m = md5.new()
    file_name = secure_filename(dockerfile.filename)
    number = random.randint(1, 1000)

    m.update (file_name)
    m.update(str(number))
    folder_name = m.hexdigest()
    os.makedirs(folder_name)
    dockerfile.save(os.path.join(folder_name, file_name))
    docker ('build', '-t', folder_name[0:12], os.path.join(os.getcwd(), folder_name))

    print 'docker build -t' + folder_name[0:12] + '' + os.path.join(os.getcwd(), folder_name)
    print os.path.join (os.getcwd(), folder_name, file_name)
    print os.getcwd()

    resp = 'File saved at: ' +  folder_name + ' and name:' + file_name
    return Response(response=resp, mimetype="application/json")



# USE PATCH METHOD TO UPDATE THE CONTAINERS
@app.route('/containers/<id>', methods=['PATCH'])
def containers_update(id):
    """
    Update container attributes (support: state=running|stopped)
    curl -X PATCH -H 'Content-Type: application/json' http://localhost:8080/containers/b6cd8ea512c8 -d '{"state": "running"}'
    curl -X PATCH -H 'Content-Type: application/json' http://localhost:8080/containers/b6cd8ea512c8 -d '{"state": "stopped"}'
    """
    body = request.get_json(force=True)
    try:
        state = body['state']
        if state == 'running':
            docker('restart', id)
        if state == 'stopped':
            docker('stop', id)
    except:
        pass

    resp = '{"id": "%s"}' % id
    return Response(response=resp, mimetype="application/json")

# USE PATCH METHOD TO UPDATE IMAGES
@app.route('/images/<id>', methods=['PATCH'])
def images_update(id):
    """
    Update image attributes (support: name[:tag])  tag name should be lowercase only
    curl -s -X PATCH -H 'Content-Type: application/json' http://localhost:8080/images/7f2619ed1768 -d '{"tag": "test:1.0"}'
    """
    body = request.get_json(force=True)
    try:
	newTag = body['tag']
    	docker ('tag', id, newTag)
    except:
	pass

    resp = '{"id": "%s"}' % id
    return Response(response=resp, mimetype="application/json")


def docker(*args):
    cmd = ['docker']
    for sub in args:
        cmd.append(sub)
    process = Popen(cmd, stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    if stderr.startswith('Error'):
        print 'Error: {0} -> {1}'.format(' '.join(cmd), stderr)
    return stderr + stdout

#
# Docker output parsing helpers
#

#
# Parses the output of a Docker PS command to a python List
#

def docker_ps_to_array(output):
    all = []
    for c in [line.split() for line in output.splitlines()[1:]]:
        each = {}
        each['id'] = c[0]
        each['image'] = c[1]
        each['name'] = c[-1]
        each['ports'] = c[-2]
        all.append(each)
    return all

#
# Parses the output of a Docker logs command to a python Dictionary
# (Key Value Pair object)
def docker_logs_to_object(id, output):
    logs = {}
    logs['id'] = id
    all = []
    for line in output.splitlines():
        all.append(line)
    logs['logs'] = all
    return logs

#
# Parses the output of a Docker image command to a python List
#
def docker_images_to_array(output):
    all = []
    for c in [line.split() for line in output.splitlines()[1:]]:
        each = {}
        each['id'] = c[2]
        each['tag'] = c[1]
        each['name'] = c[0]
        all.append(each)
    return all

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=8080, debug=True)
