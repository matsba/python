from bs4 import BeautifulSoup
import urllib.request
import requests
import json
from pymongo import MongoClient
import pprint

#artist to search lyrics for
artist = "Black Sabbath"
print("Artist: " + artist)

parameters = {"q": artist}
a = {"Authorization":"Bearer 1wOgNe8BRUUV0nFi6duRJk2UPS2eb26pfIkPAYWJOj6X02zHhTn8jPEPnSUgabO3"}

response = requests.get("https://api.genius.com/search", params=parameters, headers=a)

searchData = response.json()

#finding the correct artist from search result
for item in searchData["response"]["hits"]:
      if item["result"]["primary_artist"]["name"] == artist:
            apiPath = item["result"]["primary_artist"]["api_path"]
            break
      else:
            print("No artist found!")
            exit()      
#this is needed for urllib 403 error: non-browser user agents are blocked by some sites
h = {"User-Agent": "Mozilla/5.0"}

#opening database connection
client = MongoClient()
db = client.doomDB
#"table" lyrics
dbLyrics = db.lyrics

addedCount = 0
pageNumber = 1

#getting artist's songs
while True:
      response = requests.get("https://api.genius.com" + apiPath +"/songs?page=" +str(pageNumber), headers=a)
      artistSongData = response.json()             

      #going through each song for the artist
      for item in artistSongData["response"]["songs"]:
            id = str(item["id"])
            r = requests.get("https://api.genius.com/songs/" + id, headers=a).json()
            url = r["response"]["song"]["url"]      
            
            urlWithHeaders = urllib.request.Request(url,None,h)
            with urllib.request.urlopen(urlWithHeaders) as u:
                  page = u.read()
            soup = BeautifulSoup(page, "lxml")

            print("On page: " + str(pageNumber) + ". Scrapping url for lyrics: " + url)
            l = soup.select(".lyrics > p")
            for i in l:
                  lyrics = i.get_text()

            #info for database
            title = r["response"]["song"]["title"]
            try:
                  artworkUrl = r["response"]["song"]["song_art_image_url"]
            except:
                  artworkUrl = "null"
            try:
                  fromAlbum = r["response"]["song"]["album"]["name"]
            except:
                  fromAlbum = "null"

            #inserting data
            dbLyrics.insert_one({"id" : id, "songTitle": title, "artist": artist, "fromAlbum": fromAlbum, "artworkUrl" : artworkUrl, "lyrics": lyrics})
            print("Song added: " + dbLyrics.find_one({"id" : id})["songTitle"])
            addedCount += 1

      try:
            pageNumber = artistSongData["response"]["next_page"]
      except:
            print("No more pages. Stopped at page " + str(pageNumber))
            break      

print("Added " + str(addedCount) + " songs to database. Total of " + str(dbLyrics.count()) +" rows in the database")