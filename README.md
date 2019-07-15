# OpenShiftAutomator
OpenShift Operations automated using Python

Functionalities included :
- Update Environment variables of a project and restart the same to pick the changes
- Create containers depending on the existing containers configurations (Deployment-Config,Routes,Service and config maps for application.properties) 
Note : Requires a containers configuration
- Restart specific or all pod instances
- Display health of the pod instances across projects having status other than "Running"
- Scale number of pod instances to be running inside a container
- Creation of secrets with encrpyted base64 encoder
- Delete the created containers across projects

# Usage Steps :
1. Update the openshift entry URL's in the login function
2. Install the required libraries in the requirements file
3. Run the program on a linux shell[with oc installted]

Note : Min Python version required on the linux shell : Python 3.6+
