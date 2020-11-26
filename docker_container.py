import time
import docker
import argparse
from FinalVersion.database import *
import datetime
import requests
from FinalVersion import custom_logger as cl
import logging


class Docker(object):

    log = cl.customLogger(logging.DEBUG)

    def __init__(self, dockerRepo=None, dockerPort=None):
        self.dockerRepo = dockerRepo
        self.dockerPort = dockerPort
        self.client = docker.from_env()
        self.images = None
        self.container = None


    def createContainerInstance(self, dockerImage, containerName, ports):
        log.info("\n\nCreating Container instance name {} from image {}".format(containerName, dockerImage))
        try:
            self.container = self.client.containers.run(image=dockerImage, name=containerName, auto_remove=True,
                                                        tty=True, detach=True, ports=ports)
        except Exception as e:
            log.error("Container {} could not be instantiated\nException:".format(containerName, e))
            return

        time.sleep(5)
        log.info("Finished Container instance name {} from image {}".format(containerName, dockerImage))
        return self.container


    def stopContainer(self, containerName):
        self.log.info("\n\nStopping container {}".format(containerName))
        try:
            self.container.stop()
        except Exception as e:
            log.error("Container {} could not be stopped\nException encountered:{}".format(containerName, e))
            return
        log.info("Container stopped {}\n".format(containerName))

class DatabaseTemplate(object):

    def __init__(self, dockerImageName=None, containerName=None, ports=None, branch=None , version=None):
        # x is meant to replace the docker repository domain name or ip
        self.docker = Docker(dockerRepo="x", dockerPort=5000)
        self.sess = requests
        self.branch = branch
        self.version = version
        self.externalIP = "127.0.0.1"
        self.dockerImageName = dockerImageName
        self.dockerImage = "{}:{}/{}-{}:{}".format(self.docker.dockerRepo, self.docker.dockerPort, self.dockerImageName,
                                                   self.branch, self.version)
        timeVariable = str(datetime.datetime.now().time())
        self.containerName = containerName + '_' + timeVariable if containerName else self.dockerImageName + '_' + timeVariable
        self.ports = ports
        self.urls = {'api/v1/parents': 'api/v1/parents',
                     'api/v1/childs': 'api/v1/childs',                     
                     'api/v1/version': 'api/v1/version'}


    def createDockerContainer(self):
        self.docker.createContainerInstance(self.dockerImage, self.containerName, self.ports)


    def stopDockerContainer(self):
        self.docker.stopContainer(self.containerName)

# we will use the request module to get the version of the Database which will be returned in the form of a dictionary


    def getVersion(self):
        log.info("*****************************")
        r=self.sess.get("http://{}:{}/{}".format(self.externalIP,self.ports['3000'],self.urls['api/v1/version']))
        if r.status_code!=200:
            raise Exception ("Status code {}.".format(r.status_code))
        return json.loads(r.text)

# we will use the request module to get the parents of the Database which will be returned in the form of a dictionary


    def getParents(self,uid=None):
        if uid:
            r=self.sess.get("http://{}:{}/{}/{}".format(self.externalIP,self.ports['3000'],self.urls['api/v1/parents'],uid))
        else:
            r = self.sess.get("http://{}:{}/{}".format(self.externalIP,self.ports['3000'], self.urls['api/v1/parents']))
            if r.status_code!=200:
                raise Exception ("Status code {}.".format(r.status_code))
        return json.loads(r.text)

# we will use the request module to get the childs of the Database which will be returned in the form of a dictionary


    def getChilds(self,memberid=None):
        if memberid:
            r = self.sess.get("http://{}:{}/{}/{}".format(self.externalIP,self.ports['3000'],
                                                   self.urls['api/v1/childs'],memberid))
        else:
            r = self.sess.get("http://{}:{}/{}".format(self.externalIP,self.ports['3000'],
                                            self.urls['api/v1/childs']))
            if r.status_code != 200:
                raise Exception("Status code {}.".format(r.status_code))
        return json.loads(r.text)


class Database(DatabaseTemplate):

# class scope is to manipulate docker container and RestSession and to keep track of its properties

    def __init__(self,dockerImageName="Imagename", containerName=None, ports=None, branch=None , version=None):
        super(Database, self).__init__(dockerImageName=dockerImageName, containerName=containerName, ports=ports, branch=branch , version=version)


def initVariables(Branch1=None, Version1=None, Branch2=None, Version2=None):
    argsDictionary = {}
    parser = argparse.ArgumentParser()
    parser.add_argument('--Branch1', action='store', dest='Branch1',
                        help='Branch ')
    parser.add_argument('--Version1', action='store', dest='Version1',
                        help='Version')
    parser.add_argument('--Branch2', action='store', dest='Branch2',
                        help='Branch')
    parser.add_argument('--Version2', action='store', dest='Version2',
                        help='Version')


    args = parser.parse_args()

    argsDictionary['Branch1'] = Branch1 if Branch1 else args.Branch1
    argsDictionary['Version1'] = Version1 if Version1 else args.Version1
    argsDictionary['Branch2'] = Branch2 if Branch2 else args.Branch2
    argsDictionary['Version2'] = Version2 if Version2 else args.Version2

    return argsDictionary


def init(*args):

    # docker code
    Database1 = DatabaseTemplate(ports={"3000": 3001, "3001":49514}, branch=args['Branch1'], version=args['Version1'])
    Database2 = DatabaseTemplate(ports={"3000": 3001, "3001":49514}, branch=args['Branch2'], version=args['Version2'])



    log.info( "\nRunning Datebase deltas script for :\n{}:{} \nand \n{}:{}\n".format(Database1.containerName,
                                                                            Database1.dockerImage,
                                                                            Database2.containerName,
                                                                            Database2.dockerImage))

    #creating containers
    Database1.createDockerContainer()
    Database2.createDockerContainer()


    try:
        getDifferences(DatabaseDictionary(Databaseobj=Database1), DatabaseDictionary(Databaseobj=Database2), False)
        Summary(DatabaseDictionary(Databaseobj=Database1),DatabaseDictionary(Databaseobj=Database2),file=None)

    except Exception as e:
        log.error( "Exception encountered {}\n".format(e))



    log.info("Stopping containers.")
    Database1.stopDockerContainer()
    Database1.stopDockerContainer()

