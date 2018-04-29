from bs4 import BeautifulSoup
import requests
import os, sys

def clean_string(string):
    return string.replace("’", "'").replace("…", "...").replace("(", "").replace(")", "")

def get_chapters_from_toc(toc_data):
    '''
    Get chapters from toc
    '''
    chapters = []
    for chapter in toc_data.find_all('a'):
        print("CHAPTER ===> [%s]" % chapter)
        chapters.append({'title': clean_string(chapter.text), 'href': chapter.get('href')})
    return chapters

def get_table_of_content(url, author):
    '''
    Return Table of Content
    '''
    r = requests.get(url)
    if r.status_code != 200:
        return False
    soup = BeautifulSoup(r.text, 'html.parser')
    volumes = []
    index = 1
    for volume in soup.find_all('span', class_='collapseomatic'):
        chapters_data = volume.find_next('p')
        title = volume.text
        if title is not None:
            data = {'title': title, 'index': index, 'author': author}
            index += 1
            data['chapters'] = get_chapters_from_toc(chapters_data)
            volumes.append(data)
    print(index)
    return volumes

def display_chapter(chapter):
    print("* [%s](%s)" % (chapter['title'], chapter['href']))

def display_volume(light_novel, volume):
    '''
    '''
    print("%s - Volume [%02d] : %s" % (light_novel, volume['index'], volume['title']))
    for chapter in volume['chapters']:
        display_chapter(chapter)

def init_chapter(chapter, path):
    try:
        os.makedirs(path)
        with open(os.path.join(path, 'README.md'), 'w') as f:
            f.write("# %s\n\n" % chapter['title'])
    except FileExistsError as e:
        pass
    except Exception as e:
        print(e)
        return False
    return True

def write_chapters_in_summary(f, chapters, path):
    write_illustration(path)
    for chapter in chapters:
        write_chapter_in_summary(f, chapter)
    return True

def write_chapters(chapters, path):
    for chapter in chapters:
        print("Adding chapter [%s]..." % chapter['title'])
        write_chapter(chapter, path)
        print("Chapter done...")

def write_illustration(path):
    try:
        with open(os.path.join(path, 'README.md'), 'w') as f:
            f.write("# Illustrations\n")
    except Exception as e:
        print(e)
        return False
        
def write_chapter(chapter, path):
    r = requests.get(chapter['href'])
    path = os.path.join(path, chapter['title'])
    if r.status_code != 200:
        return False
    if not init_chapter(chapter, path):
        return False
    try:
        soup = BeautifulSoup(r.text, 'html.parser')
        with open(os.path.join(path, 'README.md'), 'a') as f:
            content = soup.find('div', class_='post-content')
            for line in content.find_all('p')[:-1]:
                text = line.text
                if text == b'\xc2\xa0':
                    f.write("\n\n")
                elif line.find('em'):
                    f.write("*%s*" % text)
                elif line.find('strong'):
                    pass
                else:
                    f.write("%s" % text)
                f.write("\n\n")
    except Exception as e:
        print(e)
        return False

def write_chapter_in_summary(f, chapter):
    f.write("* [%s](%s/README.md)\n" % (chapter['title'], chapter['title']))

def write_metadata(path, volume, light_novel):
    title = "%s - Volume [%s] : %s" % (light_novel, volume['index'], volume['title'])
    author = "%s" % volume['author']
    try:
        with open(os.path.join(path, 'book.json'), 'w') as f:
            f.write("{\n")
            f.write("\t\"title\": \"%s\",\n" % title)
            f.write("\t\"author\": \"%s\"\n" % author)
            f.write("}\n")
    except Exception as e:
        print(e)
        return False
    return True

def write_summary(path, volume):
   try:
       with open(os.path.join(path, 'SUMMARY.md'), 'w') as f:
           f.write("# Summary\n")
           f.write("\n")
           f.write("* [Illustrations](README.md)\n")
           write_chapters_in_summary(f, volume['chapters'], path)
   except Exception as e:
       print(e)
       return False
   return True

def create_ebook(volume, light_novel, path='./'):
    print("Creating volume [%s]" % volume['title'])
    path_volume = os.path.join(path, volume['title'])
    try:
        os.makedirs(path_volume)
    except FileExistsError as e:
        pass
    except Exception as e:
        print(e)
        return False
    write_metadata(path_volume, volume, light_novel)
    print("Writing summary...")
    write_summary(path_volume, volume)
    write_chapters(volume['chapters'], path_volume)

def print_help():
    print("Usage: python3 lncreator.py [volume]")
    
def main():
    volumes = get_table_of_content('http://tseirptranslations.com/growth-cheat-toc', 'Yousuke Tokino')
    [print(volume['title']) for volume in volumes]
    if volumes:
        if len(sys.argv) == 2:
            index = int(sys.argv[1])
            print(len(volumes))
            if index - 1 < len(volumes):
                create_ebook(volumes[index - 1], "I've become able to do anything with my Growth Cheat, but I can't seem to get out of being jobless")
            else:
                print_help()
                return 1
        else:
            for volume in volumes:
                create_ebook(volume, "I've become able to do anything with my Growth Cheat, but I can't seem to get out of being jobless")
if __name__ == "__main__":
    main()
