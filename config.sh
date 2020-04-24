#TODO: Ansible script to setup master and replica nodes

#<from master node, in project directory>
# add proxies in /etc/environment(internal)
sudo mv environment /etc/environment

# <for all nodes, including master>
# get packages (use ansible package module)
sudo apt-get update
sudo apt --assume-yes install git
sudo apt-get --assume-yes install python3-pip
sudo apt-get --assume-yes install python3-venv


# <for nodes excluding master (need to clone repo, master has it already)>
git clone https://s-karki:freefall1378@github.com/Reyham4/CloudComputingAssignment2.git
cd CloudComputingAssignment2/

# <for all nodes, including master>
python3 -m venv .
source bin/activate

pip install --upgrade pip
pip install -r requirements.txt


# enable the Apache CouchDB package repository
sudo apt-get install -y apt-transport-https gnupg ca-certificates
echo "deb https://apache.bintray.com/couchdb-deb bionic main"  | sudo tee -a /etc/apt/sources.list.d/couchdb.list
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 8756C4F765C9AC3CB6B85D62379CE192D401AB61
sudo apt update

#install couched
sudo apt install -y couchdb


# add couchdb admin (user: admin, password: secret)
# HOST="http://127.0.0.1:5984"
# curl -X PUT $HOST/_config/admins/admin -d  '"secret"'
