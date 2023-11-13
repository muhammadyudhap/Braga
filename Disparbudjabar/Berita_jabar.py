import requests
from bs4 import BeautifulSoup
from time import sleep
from datetime import datetime
import psycopg2 as pg2
import re

def lambda_handler(event, context):
    # Connecting to the database
    conn = pg2.connect(
        host="tcc.jabarprov.go.id",
        database="disparbud_mkk",
        user="disparbud_mkk_admin",
        password="yW8bQ2VgFFa15dEJ")
    

    cur = conn.cursor()
    
    ## First, the jabarprov
    header = {
        'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
        'referer':'https://jabarprov.go.id/'
    }

    home_url = 'https://jabarprov.go.id/berita?kategori='
    topic = ['ekonomi','kesehatan','pendidikan','pemerintahan','infrastruktur','sosial','teknologi']
    
    def date_indo_world(tanggal_indo=None):
        new_date = tanggal_indo.lower()
        world_date = new_date.replace(' wib','').replace('jan', 'Jan').replace('feb', 'Feb').replace('mar', 'Mar').replace('apr', 'Apr').replace('mei', 'May').replace('jun', 'Jun').replace('jul', 'Jul').replace('agu', 'Aug').replace('sep', 'Sep').replace('okt', 'Oct').replace('nov', 'Nov').replace('des', 'Dec')
        return datetime.strptime(world_date, "%d %b %Y %H:%M")
    
    def date_indo_world_jabarprov(tanggal_indo=None):
        new_date = tanggal_indo.lower()
        world_date = new_date.replace('januari', 'Jan').replace('februari', 'Feb').replace('maret', 'Mar').replace('april', 'Apr').replace('mei', 'May').replace('juni', 'Jun').replace('juli', 'Jul').replace('agustus', 'Aug').replace('september', 'Sep').replace('oktober', 'Oct').replace('november', 'Nov').replace('desember', 'Dec')
        return datetime.strptime(world_date, "%d %b %Y")
    
    def get_url_jabarprov(homepage):
        test = requests.get(url = homepage, headers = header)
        bsobj = BeautifulSoup(test.content,'html.parser')
        Link = []
        five_berita = bsobj.find('div', {'class':'flex-auto w-full flex flex-col gap-5 md:gap-6 gap-6'})
        for uri in five_berita.find_all('a')[1::2]:
            Link.append('https://jabarprov.go.id' + uri['href']) 

        return Link
    
    def get_detail_jabarprov(url):
        test_detail = requests.get(url = url, headers = header)
        bsobj_detail = BeautifulSoup(test_detail.content,'html.parser')

        Judul = bsobj_detail.find('h1', {'class':'font-lora font-bold text-2xl leading-9 md:text-[32px] md:leading-[48px] text-white max-w-3xl'}).text.strip()
        time = bsobj_detail.find('p', {'class':'text-sm'}).text.strip().split(',')[1].strip()
        Tanggal = date_indo_world_jabarprov(time)

        Gambar = bsobj_detail.find('div', {'class':'article__body w-full min-h-screen'}).img['src']
        Konten = bsobj_detail.find('div', {'class':'article__body w-full min-h-screen'}).text.strip().replace('\n',' ').replace('\xa0','')
        Sumber = url
        Admin = bsobj_detail.find('p', {'class':'flex line-clamp-1 md:line-clamp-none items-center'}).text.replace('\n',' ').replace('Penulis:','').strip()

        data_list = [Judul, Tanggal, Konten, Sumber, Gambar, Admin]
        return data_list
    
    
    def into_db(list):
        Judul = list[0]
        Tanggal = list[1]
        Konten = list[2]
        Sumber = list[3]
        Gambar = list[4]
        Admin = list[5]
        Status = False
        # connecting to DB
        cur = conn.cursor()
        cur.execute("INSERT INTO scrape_berita (judul, date_created, isi_berita, sumber_data, foto, status, nama_admin) VALUES (%s, %s, %s, %s, %s, %s, %s)", (Judul, Tanggal, Konten, Sumber, Gambar, Status, Admin))
        conn.commit()
    
    ## Execute
    for item in topic:
        five_url = get_url_jabarprov(home_url+item)
        for uri in five_url:
            data_list = get_detail_jabarprov(uri)
            into_db(data_list)
            
    ## Now, DetikJabar
    header = {
        'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
        'referer':'https://www.detik.com/tag/jawa-barat/'
    }
    
    url_detikjabar = 'https://www.detik.com/tag/jawa-barat/?sortby=time&page='
    
    def get_url_detikjabar(homepage):
        test = requests.get(url = homepage, headers = header)
        bsobj = BeautifulSoup(test.content,'html.parser')
        Link = []
        for item in bsobj.findAll('a', onclick=lambda onclick: onclick and "newsfeed" in onclick):
            Link.append(item["href"])

        return Link

    def get_detail_detikjabar(url):
        test_detail = requests.get(url = url, headers = header)
        bsobj_detail = BeautifulSoup(test_detail.content,'html.parser')

        Judul = bsobj_detail.find('h1', {'class':'detail__title'}).text.strip()

        time = bsobj_detail.find('div', {'class':'detail__date'}).text.split(',')[1].strip()
        Tanggal = date_indo_world(time)

        try:
            Gambar = bsobj_detail.find('div', {'class':'detail__media'}).img['src']
        except:
            Gambar = bsobj_detail.find('div', {'class':'detail__media'}).iframe['src']

        Konten = bsobj_detail.find('div', {'class':'detail__body-text itp_bodycontent'}).text.replace('\n','').replace('\r','').replace('ADVERTISEMENT','').replace('SCROLL TO RESUME CONTENT','')
        Sumber = url

        Admin = bsobj_detail.find('div', {'class':'detail__author'}).text.replace('- detikJabar','').strip()

        data_list = [Judul, Tanggal, Konten, Sumber, Gambar, Admin]
        return data_list
    
    
    # Execute the detikjabar

    for i in range(1,5):
        urls = url_detikjabar + str(i)
        link_one_page = get_url_detikjabar(urls)

        for uri in link_one_page:
            try:
                data_list = get_detail_detikjabar(uri)
            except:
                continue
            into_db(data_list)
            sleep(0.5)
            print(uri)
            
    ## Delete Duplicate
    delete_duplicate = '''
        DELETE FROM
            scrape_berita a
                USING scrape_berita b
        WHERE
            a.id < b.id
            AND a.sumber_data = b.sumber_data;
        '''
    cur.execute(delete_duplicate)
    conn.commit()
        
       
    conn.close()
    print("done")