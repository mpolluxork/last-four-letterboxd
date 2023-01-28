## https://devanshumehta.com/2020/01/04/building-a-movie-diary/ 

import feedparser
import ssl
from tmdbv3api import TMDb,Search,Movie
from datetime import datetime, timedelta
import urllib.request
from PIL import Image
import random
import string
import numpy as np
import tweepy 
import locale
import configparser as cf
import os

##variables de entorno 

_inifile = "config.ini"


#leer archivo ini para obtener credenciales
ini = cf.ConfigParser()
ini.sections()
ini.read(_inifile)

twitter_api_key = ini.get('credentials','tw_api_k')
twitter_api_key_secret = ini.get('credentials','tw_api_ks')
twitter_account_token = ini.get('credentials','tw_acc_tk')
twitter_account_token_secret = ini.get('credentials','tw_atk_sc')
tmdb_api_key = ini.get('credentials','tmdb_key')
tmdb_language = ini.get('credentials','tmdb_language')
letterboxd_username = ini.get('credentials','lettrbx_usr')


def is_within_last_week(date, days=7):
    now = datetime.now()
    diff = now - date
    if diff < timedelta(days=days):
        return True
    else:
        return False


def busca_TMDBID (title:str,year:int)->int:
    search = Search()
    results = search.movies({"query": title, "year": year})
    #print(results)
    tmdbid=-1
    for result in results:
        #print(result)
        if (int(year) == int(result.release_date[:4])) and (title == result.original_title or title == result.title):
            tmdbid = result.id
            break
    return tmdbid

def get_postertmdb(movieid:int)->list:
    ## https://bin.re/blog/tutorial-download-posters-with-the-movie-database-api-in-python/ 
    movie = Movie()
    imagenes = movie.images(movieid)
    url_base = 'http://image.tmdb.org/t/p/w500/'
    if len(imagenes['posters']) > 0 :
        poster =  imagenes['posters'][0]
        archivojpg = 'tmpost/' + generate_random_filename('jpg')
        image_url = url_base + poster['file_path'] 

        urllib.request.urlretrieve(image_url,archivojpg)
    else:
        archivojpg = 'tmpost/generic.jpg'
    
    img = Image.open(archivojpg)
    img = img.resize((600,900))
    #img.show()
    
    img.save(archivojpg)
    return [img,archivojpg]  


def generate_random_filename(extension):
    valid_chars = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(valid_chars) for i in range(8))
    return random_string + "." + extension    

def collage_maker(images:list, mode:str='h')->Image:

    # https://thecleverprogrammer.com/2021/07/31/collage-maker-using-python/

    # This Code was optimized by CHATGPT in  
    # https://chat.openai.com/chat/5395b648-6299-40a5-a52b-92e7e1262519 

    image_arrays = [np.asarray(Image.open(image)) for image in images]
    #image_arrays = [np.asarray(image) for image in images]
    
    if mode == 'h':
        collage = np.hstack(image_arrays)
    else:
        collage = np.vstack(image_arrays)
    return Image.fromarray(collage)    

def cacarea():
    #https://www.mattcrampton.com/blog/step_by_step_tutorial_to_post_to_twitter_using_python_part_two-posting_with_photos/

    auth = tweepy.OAuthHandler(twitter_api_key, twitter_api_key_secret)
    auth.set_access_token(twitter_account_token,twitter_account_token_secret)
    tuiter = tweepy.API(auth)
    media = tuiter.media_upload("collage.jpg")
    now = datetime.today()
    locale.setlocale(locale.LC_ALL,'')
    tweet = "Las últimas películas registradas en @letterboxd al día de hoy " + now.strftime('%d-%B-%Y') + ", #LastFourWatched #LetterboxdFriday" 
    print(tweet)
    tuiter.update_status(status=tweet,media_ids = [media.media_id])        

if __name__ == '__main__':

    ## inicializa datos api TMDB
    tmdb = TMDb()
    tmdb.api_key = tmdb_api_key
    tmdb.language = tmdb_language

    search = Search()

    ## inicia lectura feed rss
    print("Ejecutando lectura de RSS...")
    rss_url='https://letterboxd.com/'+letterboxd_username+'/rss'

    if hasattr(ssl, '_create_unverified_context'):
        ssl._create_default_https_context = ssl._create_unverified_context

    d = feedparser.parse(rss_url)

    entradas = []
    for entry in d.entries:
        if len(entradas) < 4:
            if 'letterboxd_watcheddate' in entry:
            
                my_date = datetime.strptime(entry['letterboxd_watcheddate'], "%Y-%m-%d")
                if is_within_last_week(my_date):
                    #print(my_date)
                    title = entry['letterboxd_filmtitle']
                    year = entry['letterboxd_filmyear']
                    entradas.append([title,year])

        else:
            break

    ### Inicia búsqueda en TMDB
    print("Ejecutando búsqueda en TMDB...")


    posters = []
    for peli in entradas:
        movtmdbid = busca_TMDBID(peli[0],peli[1])
        print("Creando poster...")
        posters.append(get_postertmdb(movtmdbid)[1])

    if len(posters) > 0:
        print("Ejecutando creación de collage...")
        collage = collage_maker(posters)
        #collage.show()
        collage.save('collage.jpg')
        cacarea()
        # rutina de limpieza para eliminar los archivos temporales
        for poster in posters:
            if poster != 'tmpost/generic.jpg':
                os.remove(poster)
        print("Archivos temporales eliminados.")
