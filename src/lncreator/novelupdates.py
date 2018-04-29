from bs4 import BeautifulSoup
import requests, sys, csv

def print_help():
    print("Usage: python3 novelupdates.py novelupdates_url")
    print("Example: python3 novelupdates.py https://www.novelupdates.com/series/ive-became-able-to-do-anything-with-my-growth-cheat-but-i-cant-seem-to-get-out-of-being-jobless")
    sys.exit(1)

def print_msg(message, msg_type="warning"):
    print(message)
    if msg_type == "warning":
        msg_type = "[!]"
    elif msg_type == "info":
        msg_type = "[+]"
    elif msg_type == "debug":
        msg_type = "[Debug]"
    print("%s %s" % (msg_type, message))

def search_chapters_range(releases, chapter_start, chapter_end):
    try:
        chapter_start = int(chapter_start)
    except ValueError:
        print_msg("chapter_start must be an integer greater or equal than 0")
        return False
    try:
        chapter_end = int(chapter_end)
    except ValueError:
        print_msg("chapter_end must be an integer greater or equal than 0")
        return False
    releases_range = []
    for release in releases:
        pass

def search_volume(releases, volume):
    pass

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
        print_msg("Unable to get your number of pages from novel updates, please verify")
        return False
    if pages[-1].get('rel') == ['next']:
        print(pages[-2].text)
        return int(pages[-2].text)
    else:
        print(pages[-1].text)
        return int(pages[-1].text)

def format_link(link):
    if link[:2] == "//":
        return "https:%s" % link
    else:
        return link
    
def get_releases_from_page(url):
    r = requests.get(url)
    if r.status_code != 200:
        print_msg("Error while processing your url [%s]" % url)
        return False
    releases = []
    soup = BeautifulSoup(r.text, 'lxml')
    tr = soup.find("table", id="myTable").find("tbody").find_all("tr")
    print_msg("Number of releases (normaly): [%d]" % len(tr), "debug")
    for release in tr:
        td = release.find_all("td")
        try:
            releases.insert(0, {"title": td[2].find("a").text, "href": format_link(td[2].find("a").get("href")), "date": td[0].text, "group": td[1].find("a").text, "group_href": format_link(td[1].find("a").get("href"))})
        except IndexError as e:
            print_msg("Unable to get release, novelupdates may have been updated...", "warning")
            print("Unable to get release, novelupdates may have been updated...", file=sys.stderr)
            print(e, file=sys.stderr)
            return False
        except Exception as e:
            print_msg("Unable to get release, novelupdates may have been updated...", "warning")
            print("Unable to get release, novelupdates may have been updated...", file=sys.stderr)
            print(e, file=sys.stderr)
            return False
    return releases
    
def get_releases_from_ln(url):
    '''
    '''
    print_msg("Processing [%s]..." % url, "info")
    r = requests.get(url)
    if r.status_code != 200:
        print_msg("Error while processing your url [%s]" % url)
        print("Error while processing your url [%s]" % url, file=sys.stderr)
        print(r.status_code, file=sys.stderr)
        print(r.text, file=sys.stderr)
        return False
    soup = BeautifulSoup(r.text, 'lxml')
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

def get_data_from_chapter(soup):
    '''
    Try to guess where the chapter may be (with <p>)
    '''
    p = soup.find_all("p")
    potential_content = {"index": -1, "size": 0, "parent_classes": "", "parent_id": ""}
    i = 0
    while i < len(p):
        tmp_len = len([x for x in p[i].next_siblings if x.name == 'p'])
        if tmp_len > potential_content['size']:
            tmp_parent = p[i].parent
            print("parent data (p index [%d])" % i)
            print("name: [%s]" % tmp_parent.name)
            print("===================")
            potential_content["index"] = i
            potential_content["size"] = tmp_len
            potential_content["parent_classes"] = "" if not tmp_parent else tmp_parent["class"] if "class" in tmp_parent else ""
            potential_content["parent_id"] = "" if not tmp_parent else tmp_parent["id"] if "id" in tmp_parent else ""
        i += tmp_len + 1
    return potential_content

def get_data_from_release(url):
    r = requests.get(url)
    if r.status_code != 200:
        print_msg("Unable to get data from [%s]..." % url, "warning")
        print("Unable to get data from [%s]..." % url, file=sys.stderr)
        print(r.status_code, file=sys.stderr)
        print(r.text, file=sys.stderr)
        return False
    soup = BeautifulSoup(r.text, "lxml")
    data = {"href": r.url, "title": soup.title.string}
    content = get_data_from_chapter(soup)
    return [data, content]

def get_ln_from_list(spamwriter, data):
    '''
    '''
    print_msg("Processing title [%s]" % data.text, "info")
    lightnovel_title = [data.text, data.get('href')]
    releases = get_releases_from_ln(data.get('href'))
    if not releases:
        return False
    releases_length = len(releases)
    for release in releases:
        lightnovel = lightnovel_title + [release['group'], release['group_href'], release['title'], releases_length]
        data = get_data_from_release(release['href'])
        if data:
            lightnovel += [data[0]['title'], data[0]['href'], data[1]['size'], data[1]['parent_classes'], data[1]['parent_id']]
            spamwriter.writerow(lightnovel)
    return True

def get_list_from_range_ranking(url_ranking, page_start, page_end, csvname="ranking.csv"):
    try:        
        page_start = int(page_start)
        if page_start < 1:
            raise ValueError()
    except ValueError:
        print_msg("page_start must be an integer greater or equal than 1")
        return False
    try:
        page_end = int(page_end) + 1
        if page_end < 1:
            raise ValueError()
    except ValueError:
        print_msg("page_end must be an integer greater or equal than 1")
        return False
    if page_start > page_end:
        print_msg("page_end (%d) must be greater (or equal) than page_start (%d)" % (page_end, page_start))
        return False
    try:
        print_msg("Processing ranking list...", "info")
        with open(csvname, "w") as f:
            spamwriter = csv.writer(f, delimiter=";")
            spamwriter.writerow(["Name", "Light Novel URL", "Group trad", "Group trad url", "Release name Novelupdates", "Number releases", "Release name fansub", "link", "p_size", "parent_classes", "parent_id"])
            for page in range(page_start, page_end):
                page_url = "%s&pg=%d" % (url_ranking, page)
                print_msg("Processing ranking page [%s] (page=[%d])" % (page_url, page), "info")
                r = requests.get(page_url)
                if r.status_code != 200:
                    print_msg("Unable to get page rank [%s]" % page_url, "warning")
                    print("Unable to get page rank [%s]" % page_url, file=sys.stderr)
                    print(r.status_code, file=sys.stderr)
                    print(r.text, file=sys.stderr)
                    return False
                soup = BeautifulSoup(r.text, "lxml")
                tr = soup.find_all("tr", class_="bdrank")
                if not tr:
                    print_msg("Unable to find [<tr>] with class [bdrank]", "warning")
                    continue
                lightnovels = []
                for element in tr:
                    lightnovel = []
                    tmp = element.find_all("td")
                    if not tmp:
                        print_msg("Unable to find [<td>]", "warning")
                        continue
                    tmp = tmp[-1].find("a")
                    if not tmp:
                        print_msg("Unable to find [<a>]", "warning")
                        continue
                    get_ln_from_list(spamwriter, tmp)
        return True
    except Exception as e:
        print(e)
        return False

def display_releases(releases):
    for release in releases:
        print("[%s](%s)" % (release['title'], release['href']))

def main():
    if len(sys.argv) != 3:
        print_msg("Usage: %s start_page end_page" % sys.argv[0], "warning")
        return 1
    url = "https://www.novelupdates.com/series-ranking/?rank=popular"
    if not get_list_from_range_ranking(url, int(sys.argv[1]), int(sys.argv[2])):
        print_msg("An error occured...", "warning")
            
if __name__ == "__main__":
    main()
