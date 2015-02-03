Spearmint is a self-hosted webapp for tracking your personal finances.

## Deployment instructions
```
scp ~/.ssh/config ~/.ssh/id_rsa_github* aws:/home/ubuntu/.ssh
ssh aws
sudo apt-get update
sudo apt-get install -y git python-virtualenv
git clone git@github.com:theandrewdavis/spearmint.git
cd spearmint
virtualenv .
source bin/activate
pip install -r requirements.txt
cp config.yaml.example config.yaml
vi config.yaml
shovel empty
shovel load_config
shovel server
```
