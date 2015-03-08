import requests
import json

from thunderdome.config import api_url_template
from thunderdome.models import Client
from masterblaster.utilities.webinteraction import update_clients

import sys

def main():
    api_url = sys.argv[1]
    update_client(api_url)

if __name__ == "__main__":
    main()
