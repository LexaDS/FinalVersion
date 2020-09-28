import json
import traceback
import deepdiff
from MyFinalProject.timeDeco import timeit
from MyFinalProject.logger import Logger,log_on_end,log_exception,log_on_start,log_on_error

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

        # version_r = requests.get(url+'version')
        # version = json.loads(version_r.text)
        j.writelines(' Database version is {}\n'.format(version['database']))
        dictmodel['Version']=version['database']

# creating the audits key in our dictionary

        dictmodel['Audits']={}

        audits=Databaseobj.getAudits()

        for audit in audits:
            dictmodel['Audits'][audit['audit_id']]={}
            dictmodel['Audits'][audit['audit_id']]['name']=audit['title']

# creating the assessment key of the dictmodel

        dictmodel['Assessments']={}

        assessments=Databaseobj.getAssessments()

        for assesment in assessments:
            assess=Databaseobj.getAssessments(assesment['uuid'])
            j.write(" Assessment: {}, UUID: {}, Test:{}".format(assesment['name'],assesment['uuid'],assess['test']))
            dictmodel['Assessments'][assesment['uuid']]={}
            dictmodel['Assessments'][assesment['uuid']]['auditlist']={}
            dictmodel['Assessments'][assesment['uuid']]['test']=assess['test']
            dictmodel['Assessments'][assesment['uuid']]['name']=assesment['name']
            dictmodel['Assessments'][assesment['uuid']]['category']= assesment['category']
            dictmodel['Assessments'][assesment['uuid']]['uuid']= assesment['uuid']
            for Assessment_stage in assess['assessment_stages']:
                for audit_list in Assessment_stage['audit_lists']:
                    for Audit_member in audit_list['audit_list_members']:

                        j.write(" ".format(Audit_member['member_id'],Databaseobj.getAudits(Audit_member['member_id'])['title']
                                               ,Databaseobj.getAudits(Audit_member['member_id'])['direction']))

                    dictmodel['Assessments'][assesment['uuid']]['auditlist'][Audit_member['member_id']]\
                        =Databaseobj.getAudits(Audit_member['member_id'])['title']

            j.write("Total number of audits {}\n\n".format(len(dictmodel['Assessments'][assesment['uuid']]['auditlist'])))

        for assesment in dictmodel['Assessments']:
            j.write('Assesment: {} id:{}, Total audits:{} \n'.format(dictmodel['Assessments'][assesment]['name'],assesment,len(dictmodel['Assessments'][assesment]['auditlist'])))


# creating the Totals key and calculating the totals

        j.write("Totals:")
        dictmodel['Totals']={}

        TotalAssess=len(dictmodel['Assessments'])
        j.write('Total number of Assessments : {} \n'.format(TotalAssess))
        dictmodel['Totals']['TotalAssessments']=TotalAssess

        TotalAudits=len(dictmodel['Audits'])
        j.write("Total number of Audits: {} \n".format(TotalAudits))
        dictmodel['Totals']['TotalAudits']=TotalAudits

        TotalFalseTests=len([assesment for assesment in dictmodel['Assessments'] if not dictmodel['Assessments'][assesment]['test']])
        j.write("Total False Tests: {} \n".format(TotalFalseTests))
        dictmodel['Totals']['TotalFalseTests']=TotalFalseTests

        TotalTrueTests=len([assesment for assesment in dictmodel['Assessments'] if dictmodel['Assessments'][assesment]['test']])
        j.write("Total True Tests:{} \n".format(TotalTrueTests))
        dictmodel['Totals']['TotalTrueTests']=TotalTrueTests

        TotalAuditsinAssesments=sum([len(dictmodel['Assessments'][assesment]['auditlist']) for assesment in dictmodel['Assessments']])
        j.write('Total audits in assesssments: {} \n'.format(TotalAuditsinAssesments))
        dictmodel['Totals']['TotalAuditsinAssesments']=TotalAuditsinAssesments

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
        if len(d1['Assessments']) == len(d2['Assessments']):
            f.write("\n" + "Version {} Assessments d1:{} == Version {} Assessments of d2:{}".format(d1Version,len(d1['Assessments']),d2Version,len(d2['Assessments'])))
        else:
            f.write("\nWARN: Version {} Assessments d1:{} != Version {} Assessments of d2:{}".format(d1Version, len(d1['Assessments']), d2Version,len(d2[ 'Assessments'])))

        differences_summary={}
        auditsinAssessment_differences={}

    #checking the content of specific keys from the dictionaries and creating a report based on the information found which will be stored in the argument filename

        @log_on_end(Logger.levels["INFO"], "", logger=mainLogger)
        @log_exception(Logger.levels["ERROR"], "", logger=mainLogger, on_exceptions=Exception)
        @log_on_start(Logger.levels["INFO"], "", logger=mainLogger)
        def Assessments(d1, d2, path=""):

            for k in d1.keys():
                if isinstance(d2, dict) and k not in d2:
                    if all([_ in d1[k] for _ in ['name', 'uuid', 'category', 'auditlist', 'test']]):
                        f.write("\n {}\n{}:{}\nUUID:{}\nTEST:{}\n\n".format(
                            "=" * len("{}:{}".format('Assessment', d1[k]['name'])), 'Assessment', d1[k]['name'],
                            d1[k]['uuid'], d1[k]['test']))
                        f.write("\n Expected Assessment(d1:{}) {} was not found in (d2:{})".format(d1Version,
                                                                                                   d1[k]['name'],
                                                                                                   d2Version))
                        f.write(
                            "\n" + "Expected Audits for {} : \nnumber:{} \nlist:\n".format(d1[k]['name'],
                                                                                                      len(d1[k][
                                                                                                              'auditslist'])))
                        for audit in d1[k]['auditlist']:
                              f.write("\n" + audit + " - " + d1[k]['auditlist'][audit])

                else:
                    if isinstance(d1[k], dict):

                        if all([_ in d1[k] for _ in ['name', 'uuid', 'category', 'auditlist', 'test']]):
                            f.write("\n" + "{}\n{}:{}\nUUID:{}\nTEST:{}\n\n".format(
                                "*" * len("{}:{}".format('Assessment', d1[k]['name'])), 'Assessment', d1[k]['name'],
                                d1[k]['uuid'], d1[k]['test']))

                            if len(d1[k]['auditlist']) != len(d2[k]['auditlist']):
                                f.write(
                                    "\n" + "Expected d1-{} audits :{} \nFound d2-{} audits : {}".format(d1Version, len(
                                        d1[k]['auditlist']), d2Version, len(d2[k]['auditlist'])))

                                NotFoundElementsList = [notFoundelem + " - " + d1[k]['auditlist'][notFoundelem] for notFoundelem in
                                                      d1[k]['auditlist'] if notFoundelem not in d2[k]['auditlist']]

                                if NotFoundElementsList:
                                    f.write(
                                        "\n" + "Expected d1-{} audits not found({} auditslist) in d2-{} Audits\nNotFoundElementsList:\n".format(
                                            d1Version, len(NotFoundElementsList), d2Version))
                                    for audit in NotFoundElementsList:
                                        f.write("\n" + audit)

                                # track all assessments with modified audit lists for summary report
                                auditsinAssessment_differences[k] = d1[k]

                        if path == "":
                            path = str(k)
                        else:
                            path = path + "->" + str(k)
                        Assessments(d1[k], d2[k])

                    else:

                        if d1[k] != d2[k]:

                            f.write('\n\Value does not match')
                            f.write(
                                '\n"Check: {} Key: {}\":\nEXPECTED d1-{} : \"{}\";\nFOUND d2-{}  :    \"{}\"!!!'.format(
                                    path, k, d1Version, d1[k], d2Version, d2[k]))




        def Audits(d1, d2, path=""):

            for k in d1.keys():
                if isinstance(d2, dict) and k not in d2:
                    f.write('Key {} is missing'.format(k))

                else:
                    if isinstance(d1[k], dict):

                        if path == "":
                            path = str(k)
                        else:
                            path = path + "->" + str(k)
                        Audits(d1[k], d2[k], path)

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
            for missingAudit in MissingElem:
                f.write("\n" + missingAudit + " - " + MissingElem[missingAudit]['name'])
            return MissingElem

        # check for missing elements and will create a summary dictionary
        # wil help to check the keys of the dictionary and if there are any existing functions with the same name they will be called

        for checkType in sorted(d1.keys()):
            if checkType == "Totals":
                f.write("\n" + "*" * 50 + "{}".format(checkType) + "*" * 50 + "\n")
                locals()[checkType](d1[checkType], d2[checkType])
            else:
                f.write("\n" + "*" * 50 + "{}".format(checkType) + "*" * 50 + "\n")
                differences_summary[checkType] = checkMissingElements(d1[checkType], d2[checkType])
                try:
                    if callable(locals()[checkType]):
                        locals()[checkType](d1[checkType], d2[checkType])
                except KeyError as e:
                    print ('WARNING: No callable function for {}'.format(checkType))
                    print (e)
                    print (traceback.format_exc())

    return d1Version, d1, d2Version, d2, differences_summary, auditsinAssessment_differences

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
    diff_assessments = deepdiff.DeepDiff(d1['Assessments'],d2['Assessments'])
    diff_audits=deepdiff.DeepDiff(d1['Audits'],d2['Audits'])
    diff_totals=deepdiff.DeepDiff(d1['Totals'],d2['Totals'])
    summary_assesments=json.dumps(json.loads(diff_assessments.to_json()),indent=2)
    summary_audits=json.dumps(json.loads(diff_audits.to_json()),indent=2)
    summary_totals=json.dumps(json.loads(diff_totals.to_json()),indent=2)

    with open(file, "w+") as f:
        f.write("The differences between version {} and version {} are: \n Summary Assessments:{}\n Summary Audits: {}\n Summary Totals: {} \n".format(d1Version,
                                                                                                                                                       d2Version,summary_assesments,summary_audits, summary_totals))

# converting the jsons into dict

        Assessments_summary=json.loads(summary_assesments)
        Audits_summary=json.loads(summary_audits)
        Totals_summary=json.loads(summary_totals)

# calculating the exact diff between the added, removed and changed keys from the Assessment summary

        count_added_assesments = 0
        count_removed_assesments = 0
        count_changed_assessments = 0

        for k in Assessments_summary:
            for k1 in Assessments_summary[k]:
                if k == 'dictionary_item_added':
                    count_added_assesments += 1
                elif k == 'dictionary_item_removed':
                    count_removed_assesments += 1
                elif k == 'values_changed':
                    count_changed_assessments += 1
        f.write("\n\n *********************************************** \n\n)")
        f.write("\n\nShort overview of the differences found between {}  and {}: \n\n".format(d1Version,d2Version))
        f.write("The total number of added assessments: {}, changed: {}, removed: {} \n\n.".format(count_added_assesments,count_changed_assessments,count_removed_assesments))

# calculating the exact diff between the added, removed and changed keys from the Audit summary

        count_added_audits = 0
        count_removed_audits = 0
        count_changed_audits = 0

        for k in Audits_summary:
            for k1 in Audits_summary[k]:
                if k == 'dictionary_item_added':
                    count_added_audits += 1
                elif k == 'dictionary_item_removed':
                    count_removed_audits += 1
                elif k == 'values_changed':
                    count_changed_audits += 1
        f.write(
            "\nThe total number of added audits: {}, changed: {}, removed: {}.\n\n".format(
                count_added_audits, count_changed_audits, count_removed_audits))

# calculating the exact diff between the totals registered in each version

        for k in Totals_summary:
            f.write("\nTotal assessments difference: {} \n\n".format(
                Totals_summary[k]["root['TotalAssessments']"]['new_value'] - Totals_summary[k]["root['TotalAssessments']"][
                    'old_value']))
            f.write("\nTotal Audits difference: {}\n\n".format(Totals_summary[k]["root['TotalAudits']"]['new_value'] - Totals_summary[k]["root['TotalAudits']"][
                'old_value']))
            f.write("\nTotal True tests differences: {}\n\n".format(Totals_summary[k]["root['TotalTrueTests']"]['new_value'] - Totals_summary[k]["root['TotalTrueTests']"][
                'old_value']))
            f.write("\nTotal false tests differences: {}\n\n".format(Totals_summary[k]["root['TotalFalseTests']"]['new_value'] - Totals_summary[k]["root['TotalFalseTests']"][
                'old_value']))
            f.write("\nTotal audits differences: {}".format(Totals_summary[k]["root['TotalAuditsinAssesments']"]['new_value'] -
                Totals_summary[k]["root['TotalAuditsinAssesments']"]['old_value']))

        f.write("\n\n***************************************************************************")

    print("Summary compiled")
