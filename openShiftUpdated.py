from subprocess import call
import subprocess
from pandas import DataFrame
import yaml
"""
To convert list value into a dictionary, extracting the first word from each iteration
"""
def listToDict(val):
    #Taking assumption that there are less than 20 environments
    if len(val)<20:
        names = []
        for v in val:
            if v is not '':
                names.append(v.split()[0])
        valDict = {}
        for i in range(len(names)):
            valDict[i] = names[i]
        #valDict[i+1] = "All"
    else:
        names = []
        for v in val:
            if v is not '':
                names.append(v.split()[0])
        valDict = {}
        for i in range(len(names)):
            valDict[i] = names[i]
        valDict[0] = "All"

    return valDict

"""
To convert the dictionary is a formatted output
"""
def printDictionary(dict):
    for i in dict:
        print(str(i) + ":" + dict[i])

"""
Function for restarting a Pod
"""
def podRestarterCmd(podName):
    #oc rollout latest dc/voice-utilities
    restartcmd = "oc rollout latest dc/"+podName
    call(restartcmd, shell=True)

"""
To Delete the containers
"""
def container_eliminator(podDelName, envName):
    # oc delete all - l app=www
    make_sure = input("Are you sure? [y/n] ")
    if make_sure == 'y':
        print("Deleting "+podDelName+" on "+envName)
        dc_svc_route_deleter = "oc delete all -l app="+podDelName
        call(dc_svc_route_deleter, shell=True)
        # oc delete configmap www
        configmap_deleter = "oc delete configmap "+podDelName
        call(configmap_deleter, shell=True)
    else:
        return

"""
To login to Openshift portals choose either of the options and provide the credentials
"""
def openShiftLogin():
    environ = input("Enter \n1 for Prod\n2 for Non-Prod : ")
    if int(environ) == 2:
        print("Login to Openshift Non-Prod Environment")
        call('oc login https://openshift_url/', shell=True)
    else:
        print("Login to Openshift Prod Environment")
        call('oc login https://openshift_url/', shell=True)

"""
To list the environments and change to a particular env.
"""
def openShiftEnvLister():
    allProjects = subprocess.Popen(["oc get project"], stdout=subprocess.PIPE, shell=True).communicate()[0]
    allProjects = allProjects.decode("utf-8")
    rawProjects = allProjects.split('\n')
    projectsDictionary = listToDict(rawProjects)
    #printDictionary(projectsDictionary)
    return projectsDictionary

"""
To change the env
"""
def openShiftEnvSelector(projectsDictionary):
    projectSelect = input("\nEnter the project key value : ")
    projectSelected = projectsDictionary[int(projectSelect)]
    projectSelectedCmd = "oc project " + projectSelected
    call(projectSelectedCmd, shell=True)

"""
List all the PODs in the project
"""
def openShiftPodLister():
    allPodNames = subprocess.Popen(["oc get svc"], stdout=subprocess.PIPE, shell=True).communicate()[0]
    allPodNames = allPodNames.decode("utf-8")
    rawPodNames = allPodNames.split('\n')
    podsDictionary = listToDict(rawPodNames)
    #printDictionary(podsDictionary)
    return podsDictionary

"""
To restart all PODs at once
"""
def openShiftAllPodsRestarter(podsDictionary):
    print("\n\t*Not Advisable to restart all PODs at once.*")
    restat = "yes"
    while restat == "yes":
        x, y = input("\nSelect a range of pods to restart [startPodKey, endPodKey] : ").split()
        for pid in range(int(x), int(y) + 1):
            podRestarterCmd(podsDictionary[pid])
        restat = input("Restart more? [yes/no] : ")

"""
To list out the POD names inside the environment selected and perform operation on the same
"""
def openShiftPodListener():
    projDictionary = openShiftEnvLister()
    printDictionary(projDictionary)
    openShiftEnvSelector(projDictionary)
    podsDictionary = openShiftPodLister()
    printDictionary(podsDictionary)
    podSelect = list(input("\nEnter the pod key values seperated with spaces : ").split())

    print("\nEnter the operations to be done")
    podVariableName = input("\nEnter the POD variable to be updated : ")
    podVariableValue = input("\nEnter the POD variable's value : ")

    for i in podSelect:
        podSelected = podsDictionary[int(i)]

        if podSelected == 'All':
            while True:
                print("Performing the value update on all the PODs")
                # oc set env dc/account CSDB_DBLINK=JANUS_DB_LINK_Q3.WORLD -n cbma-qa3
                for podNames in podsDictionary.values():
                    if podNames == 'All':
                        continue
                    podVariableUpdateCmd = "oc set env dc/" + podNames + " " + podVariableName + "=" + podVariableValue
                    #print(podVariableUpdateCmd)
                    call(podVariableUpdateCmd, shell=True)
                break
        else:
            podVariableUpdateCmd = "oc set env dc/" + podSelected + " " + podVariableName + "=" + podVariableValue
            call(podVariableUpdateCmd, shell=True)
            #print(podVariableUpdateCmd)

    restarter = input("Re-Deploy the Pod to pick the env variables update [y/n] : ")
    if restarter == "y":
        for i in podSelect:
            podSelected = podsDictionary[int(i)]
            if podSelected == "All":
                openShiftAllPodsRestarter(podsDictionary)
            else:
                podRestarterCmd(podsDictionary[int(i)])
    else:
        pass


"""
To create containers in particular/all environments
"""
def container_creator(newPodName, projNames):
    config_names = ["dc", "svc", "route"]
    srcPodName = input("\nEnter the source POD name from which config has to be extracted : ")

    for cn in config_names:
        # oc export dc/ticket > dc_{{ vars.pod_name }}.yml
        export_cmd = "oc export " + cn + "/"+ srcPodName +" > " + cn + "_" + newPodName + ".yml"
        #print(export_cmd)
        call(export_cmd, shell=True)
        # sed -i 's/ticket/{{ vars.pod_name }}/g' dc_{{ vars.pod_name }}.yml
        replace_cmd = "sed -i 's/"+srcPodName+"/" + newPodName + "/g' " + cn + "_" + newPodName + ".yml"
        #print(replace_cmd)
        call(replace_cmd, shell=True)
        # oc create -f dc_{{ vars.pod_name }}.yml
        config_file_create_cmd = "oc create -f " + cn + "_" + newPodName + ".yml"
        #print(config_file_create_cmd)
        call(config_file_create_cmd, shell=True)
        moveCreatedYml(cn, newPodName, projNames)
    # "oc create configmap {{ vars.pod_name }} --from-literal=application.properties=''"
    config_map_cmd = "oc create configmap " + newPodName + " --from-literal=application.properties=''"
    #print(config_map_cmd)
    call(config_map_cmd, shell=True)

"""
To move the files to respective env created folders
"""
def moveCreatedYml(file_type, newPodName, projNames):
    # Create the folder
    create_dir_cmd = "mkdir -p " + projNames
    call(create_dir_cmd, shell=True)
    # mv dc_$podName.yml $i/dc_$podName.yml_$i
    file_name = file_type + "_" + newPodName + ".yml"
    move_cmd = "mv " + file_name + " " + projNames + "/" + file_name + "_" + projNames
    call(move_cmd, shell=True)

"""
Container create helper and caller
"""
def openShiftContainerCreator():
    projectsDictionary = openShiftEnvLister()
    proj_dict_length = len(projectsDictionary)
    projectsDictionary[proj_dict_length] = 'All'

    newPodName = input("Enter the POD name to be created : ")

    printDictionary(projectsDictionary)

    projectSelect = list(input("\nEnter the project-env key value seperated with spaces : ").split())

    for i in projectSelect:
        projectSelected = projectsDictionary[int(i)]

        if projectSelected == 'All':
            while True:
                print("Performing the container creation on all envs")
                for projNames in projectsDictionary.values():
                    if projNames == 'All':
                        continue
                    oc_project_cmd = "oc project "+ projNames
                    call(oc_project_cmd, shell=True)
                    container_creator(newPodName, projNames)
                break
        else:
            proj_chg_cmd = "oc project "+projectSelected
            call(proj_chg_cmd, shell=True)
            container_creator(newPodName, projectSelected)

"""
Function for restarting PODs.
"""
def openShiftPodRestarter():
    envDict = openShiftEnvLister()
    printDictionary(envDict)
    openShiftEnvSelector(envDict)

    podsDictionary = openShiftPodLister()
    printDictionary(podsDictionary)
    podSelect = list(input("\nEnter the pod key values seperated with spaces to be restarted : ").split())
    for i in podSelect:
        podSelected = podsDictionary[int(i)]
        if podSelected == "All":
            openShiftAllPodsRestarter(podsDictionary)
        else:
            podRestarterCmd(podsDictionary[int(i)])
        #podRestarterCmd(podSelected)


def getPodHealthState(envName):
    allPods = subprocess.Popen(["oc get pods"], stdout=subprocess.PIPE, shell=True).communicate()[0]
    allPods = allPods.decode("utf-8")
    rawPods = allPods.split('\n')
    consoled = []
    for i in rawPods:
        consoled.append(i.split())
    consoled.remove([])

    conso = DataFrame(consoled)
    header_value = conso.iloc[0]
    conso = conso[1:]
    conso.columns = header_value
    #print(conso)

    complete_list = conso[~conso.NAME.str.contains("deploy", na=False)]

    #errorCount = len(complete_list[complete_list['STATUS'].str.contains("Error")])
    errorCount = len(complete_list[complete_list['STATUS'] != "Running"])
    #print(errorCount)
    if errorCount > 0:
        #print environment name and pods erroring out
        print(envName)
        #print(complete_list[complete_list['STATUS'].str.contains("Error")])
        print(complete_list[complete_list['STATUS'] != "Running"])
    #return errorCount
    else:
        print("No Erroring PODs")

"""
Function for performing health check of the PODs across environments
"""
def healthChecker():
    projectsDictionary = openShiftEnvLister()
    proj_dict_length = len(projectsDictionary)
    projectsDictionary[proj_dict_length] = 'All'
    printDictionary(projectsDictionary)

    projectSelect = list(input("\nEnter the project key values seperated with spaces : ").split())
    for projSelt in projectSelect:
        projectSelected = projectsDictionary[int(projSelt)]
        if projectSelected == "All":
            while True:
                for projNames in projectsDictionary.values():
                    if projNames == 'All':
                        continue
                    oc_project_cmd = "oc project " + projNames
                    call(oc_project_cmd, shell=True)
                    getPodHealthState(projNames)
                break
        else:
            projectSelectedCmd = "oc project " + projectSelected
            call(projectSelectedCmd, shell=True)
            getPodHealthState(projectSelected)

"""
Create secrets across environments
"""
def openShiftSecretsCreator():
    passwordKeyValue = input("Secret Key Name : ")
    passwordKeyCode = input("Secret Key Value (encryted) : ")
    secretYmlTemplate = {'apiVersion': 'v1', 'data':{passwordKeyValue: passwordKeyCode}, 'kind': 'Secret', 'metadata': {'creationTimestamp': None, 'name': passwordKeyValue}, 'type': 'Opaque'}
    #Writing the contents of the secret into a file.
    with open('secretFile.yml', 'w') as outfile:
        yaml.dump(secretYmlTemplate, outfile, default_flow_style=False)

    secretCreateCmd = "oc create -f secretFile.yml"

    projectsDictionary = openShiftEnvLister()
    proj_dict_length = len(projectsDictionary)
    projectsDictionary[proj_dict_length] = 'All'

    printDictionary(projectsDictionary)

    projectSelect = list(input("\nEnter the project-env key value seperated with spaces : ").split())

    for i in projectSelect:
        projectSelected = projectsDictionary[int(i)]

        if projectSelected == 'All':
            while True:
                print("Performing the secret key creation on all envs")
                for projNames in projectsDictionary.values():
                    if projNames == 'All':
                        continue
                    oc_project_cmd = "oc project " + projNames
                    call(oc_project_cmd, shell=True)
                    call(secretCreateCmd, shell=True)
                break
        else:
            proj_chg_cmd = "oc project " + projectSelected
            call(proj_chg_cmd, shell=True)
            call(secretCreateCmd, shell=True)

"""
Container Deletion
"""
def openShiftContainerEliminate():

    containerName = input("Enter the container to be deleted : ")
    envList = openShiftEnvLister()
    proj_dict_length = len(envList)
    envList[proj_dict_length] = 'All'
    printDictionary(envList)

    projectSelect = list(input("\nEnter the project-env key value seperated with spaces : ").split())

    for i in projectSelect:
        projectSelected = envList[int(i)]

        if projectSelected == 'All':
            while True:
                print("Performing the container deletion on all envs")
                for projNames in envList.values():
                    if projNames == 'All':
                        continue
                    oc_project_cmd = "oc project " + projNames
                    call(oc_project_cmd, shell=True)
                    container_eliminator(containerName, projNames)
                break
        else:
            proj_chg_cmd = "oc project " + projectSelected
            call(proj_chg_cmd, shell=True)
            container_eliminator(containerName, projectSelected)

"""
To change to a particular project
"""
def openShiftProjectChanger():
    projDict = openShiftEnvLister()
    printDictionary(projDict)
    openShiftEnvSelector(projDict)

#oc scale dc frontend --replicas=3
"""
To Scale the pods up and down
"""
def openShiftPodsScaler():
    openShiftProjectChanger()
    podsDict = openShiftPodLister()
    printDictionary(podsDict)
    podSelect = list(input("\nEnter the pod key values seperated with spaces to be scaled : ").split())
    scaleCount = input("\nEnter the scale count : ")
    for i in podSelect:
        scalecmd = "oc scale dc "+ podsDict[int(i)] + " --replicas="+scaleCount
        call(scalecmd, shell=True)

"""
Show logs of the pod selected
"""
#oc logs -f --follow=false dc/voice-utilities | grep ERROR
def openShiftLogsDisplayer():
    openShiftProjectChanger()
    podsDict = openShiftPodLister()
    printDictionary(podsDict)
    podSelect = input("\nEnter the pod key value to check logs : ")
    logsDisplayType = input("\n1. Search a pattern in the logs\n2.Display pod logs\nInput:")
    if int(logsDisplayType) == 1:
        patternValue = input("\nEnter the pattern to be searched for [Case-Sensitive]: ")
        logscmd = "oc logs -f --follow=false dc/"+podsDict[int(podSelect)]+" | grep "+patternValue
        call(logscmd,shell=True)
    else:
        logscmd = "oc logs -f --follow=false dc/"+podsDict[int(podSelect)]
        call(logscmd, shell=True)


"""
Main entry point
"""
def main_switcher(args):
    switcher = {
        1: openShiftPodListener,
        2: openShiftContainerCreator,
        3: openShiftPodRestarter,
        4: healthChecker,
        5: openShiftPodsScaler,
        6: openShiftSecretsCreator,
        7: openShiftContainerEliminate,
        8: openShiftLogin,
        9: openShiftProjectChanger,
        10: openShiftLogsDisplayer,
        11: exit
    }
    func = switcher.get(args, lambda: 'Invalid Input')
    return func()

if __name__ == "__main__" :
    openShiftLogin()
    while True:
        operation_choice = input("\nEnter the operation value :\n1 : Env Varaibles\n2 : Create Container\n3 : Restart POD"
                                 "\n4 : HealthCheck\n5 : Pods Scaler\n6 : Secrets\n7 : Delete Container\n8 : Login"
                                 "\n9 : Change environment\n10 : Display Logs\n11 : Exit\nInput : ")
        main_switcher(int(operation_choice))
