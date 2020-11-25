import json
import traceback
import deepdiff
from FinalVersion.timeDeco import timeit
from FinalVersion.logger import Logger,log_on_end,log_exception,log_on_start,log_on_error

mainLogger = Logger('DEBUG', "master.log", '%(asctime)s | %(name)s | %(levelname)s | %(message)s', 'LoggerExample')

#creating a class to manipulate our docker container and extract information

@timeit
@log_on_end(Logger.levels["INFO"], "", logger=mainLogger)
@log_exception(Logger.levels["ERROR"], "", logger=mainLogger, on_exceptions=Exception)
@log_on_start(Logger.levels["INFO"], "", logger=mainLogger)
def DatabaseDictionary(Databaseobj=None):
    if Databaseobj is None:
        raise Exception ("The value must be an instance from the docker class")

# we are creating an empty dictionary instance which will populated as the flow of the class will run it's course

    dictmodel={}

    version =Databaseobj.getVersion()

# we are creating/opening a text file where the information regarding the Database will be stored

    with open("DatabaseInfo{}.txt".format(version['database']),'w') as j:

# determining and version of the Database and tracking it in a txt file
       
        j.writelines(' Database version is {}\n'.format(version['database']))
        dictmodel['Version']=version['database']        

# creating the child key in our dictionary

        dictmodel['Childs']={}

        audits=Databaseobj.getChilds()

        for audit in audits:
            dictmodel['Childs'][audit['child_id']]={}
            dictmodel['Childs'][audit['child_id']]['name']=audit['title']

# creating the parent key of the dictmodel

        dictmodel['Parent']={}

        parents=Databaseobj.getParents()

        for parent in parents:
            parent=Databaseobj.getParents(parent['uuid'])
            j.write(" Parent: {}, UUID: {}, Test:{}".format(parent['name'],parent['uuid'],parent['test']))
            dictmodel['Parents'][parent['uuid']]={}
            dictmodel['Parents'][parent['uuid']]['childlist']={}
            dictmodel['Parents'][parent['uuid']]['test']=parent['test']
            dictmodel['Parents'][parent['uuid']]['name']=parent['name']
            dictmodel['Parents'][parent['uuid']]['type']= parent['type']
            dictmodel['Parents'][parent['uuid']]['uuid']= parent['uuid']
            for Parent_sections in parent['parent_sections']:
                for child_list in parent_sections['child_lists']:
                    for child_member in child_list['child_list_members']:
                        j.write("{}{} ".format(Child_member['member_id'],Databaseobj.getChilds(Child_member['member_id'])['title'])
                               )
                    dictmodel['Parents'][parent['uuid']]['childlist'][Child_member['member_id']]
                        =Databaseobj.getChilds(Child_member['member_id'])['name']

            j.write("Total number of childs {}\n\n".format(len(dictmodel['Parents'][parent['uuid']]['childlist'])))

        for parent in dictmodel['Parents']:
            j.write('Parent: {} id:{}, Total childs:{} \n'.format(dictmodel['Parents'][parent]['name'],parent,len(dictmodel['Parents'][parent]['childlist'])))


            
# creating the Totals key and calculating the totals

        j.write("Totals:")
        dictmodel['Totals']={}

        TotalParents=len(dictmodel['Parents'])
        j.write('Total number of Parents : {} \n'.format(TotalParents))
        dictmodel['Totals']['TotalParents']=TotalParents

        TotalAudits=len(dictmodel['Childs'])
        j.write("Total number of Childs: {} \n".format(TotalAudits))
        dictmodel['Totals']['TotalChilds']=TotalAudits

        TotalFalseTests=len([parent for parent in dictmodel['Parents'] if not dictmodel['Parents'][parent]['test']])
        j.write("Total False Tests: {} \n".format(TotalFalseTests))
        dictmodel['Totals']['TotalFalseTests']=TotalFalseTests

        TotalTrueTests=len([parent for parent in dictmodel['Parents'] if dictmodel['Parents'][parent]['test']])
        j.write("Total True Tests:{} \n".format(TotalTrueTests))
        dictmodel['Totals']['TotalTrueTests']=TotalTrueTests

        TotalChildsinParents=sum([len(dictmodel['Parents'][parent]['childlist']) for parent in dictmodel['Parents']])
        j.write('Total childs in parents: {} \n'.format(TotalChildsinParents))
        dictmodel['Totals']['TotalChildsinParents']=TotalChildsinParents

    with open('dictmodel_json{}.json'.format(dictmodel['Version']),'w+') as d:
        json.dump(dictmodel,d,indent=2)

    with open('dictmodel_{}.txt'.format(dictmodel['Version']), "w+") as d1:
        print(dictmodel,file=d1)

    return dictmodel


@timeit
@log_on_end(Logger.levels["INFO"], "", logger=mainLogger)
@log_exception(Logger.levels["ERROR"], "", logger=mainLogger, on_exceptions=Exception)
@log_on_start(Logger.levels["INFO"], "", logger=mainLogger)
def getDifferences(d1,d2,filename=None):

    try:
        d1Version=d1.pop('Version')
        d2Version=d2.pop('Version')

    except:
        print("The dictionaries do not contain the 'version' key")

    if filename is None:
        filename="DatabaseDifferencesBetween{}and{}.txt".format(d1Version,d2Version)

    with open(filename,"w") as f:
        if type(d1) != type(d2):
            raise Exception("The two dictionaries are not of the same type --- d1 type:{} , d2 type:{}".format(type(d1), type(d2)))
        if len(d1['Parents']) == len(d2['Parents']):
            f.write("\n" + "Version {} Parents d1:{} == Version {} Parents of d2:{}".format(d1Version,len(d1['Parents']),d2Version,len(d2['Parents'])))
        else:
            f.write("\nWARN: Version {} Parents d1:{} != Version {} Parents of d2:{}".format(d1Version, len(d1['Parents']), d2Version,len(d2[ 'Parents'])))

        differences_summary={}
        childsinParents_differences={}

    #checking the content of specific keys from the dictionaries and creating a report based on the information found which will be stored in the argument filename

        @log_on_end(Logger.levels["INFO"], "", logger=mainLogger)
        @log_exception(Logger.levels["ERROR"], "", logger=mainLogger, on_exceptions=Exception)
        @log_on_start(Logger.levels["INFO"], "", logger=mainLogger)
        def Assessments(d1, d2, path=""):

            for k in d1.keys():
                if isinstance(d2, dict) and k not in d2:
                    if all([_ in d1[k] for _ in ['name', 'uid', 'category', 'childlist', 'test']]):
                        f.write("\n {}\n{}:{}\nUUID:{}\nTEST:{}\n\n".format(
                            "=" * len("{}:{}".format('Parent', d1[k]['name'])), 'Parent', d1[k]['name'],
                            d1[k]['uid'], d1[k]['test']))
                        f.write("\n Expected Parent(d1:{}) {} was not found in (d2:{})".format(d1Version,
                                                                                                   d1[k]['name'],
                                                                                                   d2Version))
                        f.write(
                            "\n" + "Expected Childs for {} : \nnumber:{} \nlist:\n".format(d1[k]['name'],
                                                                                                      len(d1[k][
                                                                                                              'childlist'])))
                        for child in d1[k]['childlist']:
                              f.write("\n" + child + " - " + d1[k]['childlist'][child])

                else:
                    if isinstance(d1[k], dict):

                        if all([_ in d1[k] for _ in ['name', 'uid', 'childlist', 'test']]):
                            f.write("\n" + "{}\n{}:{}\nUUID:{}\nTEST:{}\n\n".format(
                                "*" * len("{}:{}".format('Parent', d1[k]['name'])), 'Parent', d1[k]['name'],
                                d1[k]['uid'], d1[k]['test']))

                            if len(d1[k]['childlist']) != len(d2[k]['childlist']):
                                f.write(
                                    "\n" + "Expected d1-{} childs :{} \nFound d2-{} childs : {}".format(d1Version, len(
                                        d1[k]['childlist']), d2Version, len(d2[k]['childlist'])))

                                NotFoundElementsList = [notFoundelem + " - " + d1[k]['childlist'][notFoundelem] for notFoundelem in
                                                      d1[k]['childlist'] if notFoundelem not in d2[k]['childlist']]

                                if NotFoundElementsList:
                                    f.write(
                                        "\n" + "Expected d1-{} childs not found({} childlist) in d2-{} Childs\nNotFoundElementsList:\n".format(
                                            d1Version, len(NotFoundElementsList), d2Version))
                                    for child in NotFoundElementsList:
                                        f.write("\n" + child)

                                # track all parents with modified child lists for summary report
                                childsinParents_differences[k] = d1[k]

                        if path == "":
                            path = str(k)
                        else:
                            path = path + "->" + str(k)
                        Parents(d1[k], d2[k])

                    else:

                        if d1[k] != d2[k]:

                            f.write('\n\Value does not match')
                            f.write(
                                '\n"Check: {} Key: {}\":\nEXPECTED d1-{} : \"{}\";\nFOUND d2-{}  :    \"{}\"!!!'.format(
                                    path, k, d1Version, d1[k], d2Version, d2[k]))



        def Childs(d1, d2, path=""):

            for k in d1.keys():
                if isinstance(d2, dict) and k not in d2:
                    f.write('Key {} is missing'.format(k))

                else:
                    if isinstance(d1[k], dict):

                        if path == "":
                            path = str(k)
                        else:
                            path = path + "->" + str(k)
                        Childs(d1[k], d2[k], path)

                    else:

                        if d1[k] != d2[k]:

                            f.write('\n\nValues do not match')
                            f.write('\n"Check : {} Key: {}\":\nEXPECTED d1-{} : \"{}\";\nFOUND d2-{} :   \"{}\"!!!'.format(
                                    path, k, d1Version, d1[k], d2Version, d2[k]))




        def Totals(d1, d2, path=""):
            for k in d1.keys():
                if isinstance(d2, dict) and k not in d2:
                    f.write(' {} is missing'.format(k))

                else:
                    if isinstance(d1[k], dict):

                        if path == "":
                            path = str(k)
                        else:
                            path = path + "->" + str(k)
                        Totals(d1[k], d2[k], path)

                    else:

                        if d1[k] != d2[k]:

                            f.write('\n\nValues do not match')
                            f.write(
                                '\n"Check : {} Key: {}\":\nEXPECTED d1-: \"{}\";\nFOUND d2- :\"{}\"'.format(
                                    path, k, d1[k], d2[k]))


        def checkMissingElements(d1,d2):

            if len(d1) != len(d2):
                f.write("\n" + "EXPECTED d1-{}  :{} \nFOUND d2-{}  : {}".format(d1Version, len(d1),d2Version,len(d2)))

            MissingElem = {MissingElement:d1[MissingElement] for MissingElement in d1 if MissingElement not in d2}

            if MissingElem:
                f.write(
                    "\n" + "EXPECTED d1-{} items not FOUND({}) in d2-{} \n MissingElem:".format(
                        d1Version, len(MissingElem), d2Version))
            for missingChild in MissingElem:
                f.write("\n" + missingChild + " - " + MissingElem[missingChild]['name'])
            return MissingElem

        # check for missing elements and will create a summary dictionary
        # wil help to check the keys of the dictionary and if there are any existing functions with the same name they will be called

        for checkType in sorted(d1.keys()):
            if checkType == "Totals":
                f.write("\n" + "*" * 10 + "{}".format(checkType) + "*" * 10 + "\n")
                locals()[checkType](d1[checkType], d2[checkType])
            else:
                f.write("\n" + "*" * 10 + "{}".format(checkType) + "*" * 10 + "\n")
                differences_summary[checkType] = checkMissingElements(d1[checkType], d2[checkType])
                try:
                    if callable(locals()[checkType]):
                        locals()[checkType](d1[checkType], d2[checkType])
                except KeyError as e:
                    print ('WARNING: No callable function for {}, encountered error {}'.format(checkType,e))
                 

    return d1Version, d1, d2Version, d2, differences_summary, childsinParents_differences

@timeit
@log_on_end(Logger.levels["INFO"], "", logger=mainLogger)
@log_exception(Logger.levels["ERROR"], "", logger=mainLogger, on_exceptions=Exception)
@log_on_start(Logger.levels["INFO"], "", logger=mainLogger)
def Summary(d1,d2,file=None):


    try:
        d1Version=d1.pop('Version')
        d2Version=d2.pop('Version')

    except:
        print("The dictionaries do not contain the 'version' key")

    print("Creating the summary report for the differences between {} and {}".format(d1Version, d2Version))

    if file is None:
        file="DatabaseDifferencesBetween{}and{}Summary.txt".format(d1Version,d2Version)
    diff_parents = deepdiff.DeepDiff(d1['Parents'],d2['Parents'])
    diff_childs=deepdiff.DeepDiff(d1['Childs'],d2['Childs'])
    diff_totals=deepdiff.DeepDiff(d1['Totals'],d2['Totals'])
    summary_parents=json.dumps(json.loads(diff_parents.to_json()),indent=2)
    summary_childs=json.dumps(json.loads(diff_childs.to_json()),indent=2)
    summary_totals=json.dumps(json.loads(diff_totals.to_json()),indent=2)

    with open(file, "w+") as f:
        f.write("The differences between version {} and version {} are: \n Summary Parents:{}\n Summary Childs: {}\n Summary Totals: {} \n".format(d1Version,
                                                                                                                                                       d2Version,summary_parents,summary_childs, summary_totals))

# converting the jsons into dict

        Parents_summary=json.loads(summary_parents)
        Childs_summary=json.loads(summary_childs)
        Totals_summary=json.loads(summary_totals)

# calculating the exact diff between the added, removed and changed keys from the Parent summary

        count_added_parents = 0
        count_removed_parents = 0
        count_changed_parents = 0

        for k in Parents_summary:
            for k1 in Parents_summary[k]:
                if k == 'dictionary_item_added':
                    count_added_parents += 1
                elif k == 'dictionary_item_removed':
                    count_removed_parents += 1
                elif k == 'values_changed':
                    count_changed_parents += 1
        f.write("\n\n *********************************************** \n\n)")
        f.write("\n\nShort overview of the differences found between {}  and {}: \n\n".format(d1Version,d2Version))
        f.write("The total number of added assessments: {}, changed: {}, removed: {} \n\n.".format(count_added_parents,count_changed_parents,count_removed_parents))

# calculating the exact diff between the added, removed and changed keys from the Child summary

        count_added_childs = 0
        count_removed_childs = 0
        count_changed_childs = 0

        for k in Childs_summary:
            for k1 in Childs_summary[k]:
                if k == 'dictionary_item_added':
                    count_added_childs += 1
                elif k == 'dictionary_item_removed':
                    count_removed_childs += 1
                elif k == 'values_changed':
                    count_changed_childs += 1
        f.write(
            "\nThe total number of added audits: {}, changed: {}, removed: {}.\n\n".format(
                count_added_childs, count_changed_childs, count_removed_childs))

# calculating the exact diff between the totals registered in each version

        for k in Totals_summary:
            f.write("\nTotal parents difference: {} \n\n".format(
                Totals_summary[k]["root['TotalParents']"]['new_value'] - Totals_summary[k]["root['TotalParents']"][
                    'old_value']))
            f.write("\nTotal Childs difference: {}\n\n".format(Totals_summary[k]["root['TotalChilds']"]['new_value'] - Totals_summary[k]["root['TotalChilds']"][
                'old_value']))
            f.write("\nTotal True tests differences: {}\n\n".format(Totals_summary[k]["root['TotalTrueTests']"]['new_value'] - Totals_summary[k]["root['TotalTrueTests']"][
                'old_value']))
            f.write("\nTotal false tests differences: {}\n\n".format(Totals_summary[k]["root['TotalFalseTests']"]['new_value'] - Totals_summary[k]["root['TotalFalseTests']"][
                'old_value']))
            f.write("\nTotal childs differences: {}".format(Totals_summary[k]["root['TotalChildsinParents']"]['new_value'] -
                Totals_summary[k]["root['TotalChildsinParents']"]['old_value']))

        f.write("\n\n***************************************************************************")

    print("Summary compiled")
