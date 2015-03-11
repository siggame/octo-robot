import requests  # Obtains a url page's source code
from arena.settings.secret_settings import GITHUB_API_TOKEN

def main():
    #  User's input
    language = raw_input('Please enter the keyword (python, java, csharp, cpp) '
                         'for the language you would like the usernames for. ')

    #  Loop that makes sure the user input is acceptable
    while valid_input(language) == 0:
        # User input assuming first attempt was a failure
        language = raw_input('Please enter the keyword (python, java, csharp, cpp) '
                             'for the language you would like the usernames for. ')

    #  Obtains the usernames from the specifid language and places them into a text file
    if valid_input(language) == 1:  # PYTHON
        r = requests.get('https://github.com/siggame/plants-python/network/members')
        print r.text
        soup = BeautifulSoup(r.text)

        #Finds specific tags within source code
        soup = soup.find_all('a', tabindex=False, data=False, href=True)

        print(soup)  # Prints found tags within source code, only used till program runs correctly

        f = open('python_usernames.txt', 'w')
        f.write('hi\n')  # Was just testing file i/o
        f.close()
    elif valid_input(language) == 2:  # JAVA
        r = requests.get('https://github.com/siggame/plants-java/network/members')
        soup = BeautifulSoup(r.text)
        soup = soup.find_all('a', href=True)  #Finds specific tags within source code

        print(soup)  # Prints found tags within source code, only used till program runs correctly

        f = open('java_usernames.txt', 'w')
        f.write('hi\n')  # Was just testing file i/o
        f.close()
    elif valid_input(language) == 3:  # CSHARP 
        r = requests.get('https://github.com/siggame/plants-csharp/network/members')
        soup = BeautifulSoup(r.text)
        soup = soup.find_all('a', href=True)  #Finds specific tags within source code
        
        print(soup)  # Prints found tags within source code, only used till program runs correctly  

        f = open('csharp_usernames.txt', 'w')
        f.write('hi\n')  # Was just testing file i/o
        f.close()
    else:  # C++
        r = requests.get('https://github.com/siggame/plants-cpp/network/members')
        soup = BeautifulSoup(r.text)
        soup = soup.find_all('a', href=True)  #Finds specific tags within source code

        print(soup)  # Prints found tags within source code, only used till program runs correctly

        f = open('cpp_usernames.txt', 'w')
        f.write('hi\n')  # Was just testing file i/o
        f.close()

# Determines whether user input is acceptable
def valid_input(string):
    if string == "python":
        return 1
    elif string == "java":
        return 2
    elif string == "csharp":
        return 3
    elif string == "cpp":
        return 4
    else:
        return 0


def get_all_forks(game_name, languages=['cpp', 'python', 'csharp', 'java']):
    return [j for i in languages for j in get_forks("%s-%s" % (game_name, i))]
    # t = []
    # for i in languages:
    #    t.append(get_forks("%s-%s" % (game_name, i)))
    # return t

def get_forks(repo_name):
    uri = 'https://api.github.com/repos/siggame/%s/forks' % repo_name
    headers = {'Authorization': "token {}".format(GITHUB_API_TOKEN)}
    r = requests.get(uri, headers=headers)
    if r.status_code != 200:
        return 
    json = r.json()
    for i in json:
        yield 'https://github.com/' + i['full_name']

if __name__ == "__main__":
    get_all_forks('pharaoh')
