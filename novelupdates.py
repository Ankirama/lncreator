from bs4 import BeautifulSoup
import requests, sys

def print_help():
    print("Usage: python3 novelupdates.py novelupdates_url")
    print("Example: python3 novelupdates.py https://www.novelupdates.com/series/ive-became-able-to-do-anything-with-my-growth-cheat-but-i-cant-seem-to-get-out-of-being-jobless")
    sys.exit(1)

def print_msg(message, msg_type="warning"):
    if msg_type == "warning":
        msg_type = "[!]"
    elif msg_type == "info":
        msg_type = "[+]"
    elif msg_type == "debug":
        msg_type = "[Debug]"
    print("%s %s" % (msg_type, message))
        
        
def get_number_pagination(soup):
    '''
    Return number of pages for a specific LN
    If there is a 'next' button then the number of page is just before
    Else this is the last element

    The class used to find it in novelupdates is `digg_pagination`
    '''
    div = soup.find('div', class_='digg_pagination')
    pages = div.find_all('a')
    if not pages:
        print_message("Unable to get your number of pages from novel updates, please verify")
        return False
    if pages[-1].get('rel') == ['next']:
        print(pages[-2].text)
        return int(pages[-2].text)
    else:
        print(pages[-1].text)
        return int(pages[-1].text)

def get_releases_from_page(url):
    r = requests.get(url)
    if r.status_code != 200:
        print_message("Error while processing your url [%s]" % url)
        return False
    releases = []
    soup = BeautifulSoup(r.text, 'html.parser')
    tr = soup.find("table", id="myTable").find("tbody").find_all("tr")
    print_msg("Number of releases (normaly): [%d]" % len(tr), "debug")
    for release in tr:
        links = release.find_all("a")
        if len(links) >= 2:
            href = links[1].get('href')
            if href[:2] == "//":
                href = "https:%s" % href
            releases.insert(0, {"title": links[1].text, "href": href})
            print_msg("Release [%s] added" % links[1].text, "info")
        else:
            print_msg("Unable to find your release [%s]" % "\n".join(links), "debug")
    return releases
    
    
def get_releases_from_ln(url):
    '''
    '''
    print_msg("Processing [%s]..." % url, "info")
    r = requests.get(url)
    if r.status_code != 200:
        print_message("Error while processing your url [%s]" % url)
        return False
    soup = BeautifulSoup(r.text, 'html.parser')
    number_pages = get_number_pagination(soup)
    if not number_pages:
        return False
    releases = []
    print_msg("Number of pages: [%d]" % number_pages, "debug")
    for page_id in range(1, number_pages):
        page_url = "%s?pg=%d" % (url, page_id)
        print_msg("Processing url [%s]" % page_url, "info")
        tmp = get_releases_from_page(page_url)
        if tmp:
            releases = tmp + releases
        else:
            print_msg("Unable to get releases from page [%d]" % page_id, "warning")
    return releases

def display_releases(releases):
    for release in releases:
        print("[%s](%s)" % (release['title'], release['href']))

def main():
    if len(sys.argv) != 2:
        print_help()
    else:
        releases = get_releases_from_ln(sys.argv[1])
        if releases:
            display_releases(releases)

if __name__ == "__main__":
    main()
