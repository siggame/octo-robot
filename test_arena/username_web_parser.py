import requests  # Obtains a url page's source code
from arena.settings.secret_settings import GITHUB_API_TOKEN

# returns a list of all the github url locations of possible forks
def get_all_forks(game_name, languages=['cpp', 'python', 'csharp', 'java']):
    return [j for i in languages for j in get_forks("%s-%s" % (game_name, i))]
    # t = []
    # for i in languages:
    #    t.append(get_forks("%s-%s" % (game_name, i)))
    # return t

# returns all the forks for a specific repo name
def get_forks(repo_name):
    uri = 'https://api.github.com/repos/siggame/%s/forks' % repo_name
    headers = {'Authorization': "token {}".format(GITHUB_API_TOKEN)}
    r = requests.get(uri, headers=headers)
    if r.status_code != 200:
        return 
    json = r.json()
    for i in json:
        yield 'https://github.com/' + i['full_name']

def repo_username(repo_url):
    return repo_url.strip("https://github.com/").split("/")[0]

if __name__ == "__main__":
    get_all_forks('pharaoh')
