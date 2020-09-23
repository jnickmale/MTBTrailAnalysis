# -*- coding: utf-8 -*-
"""
Created on Fri Sep  4 15:19:13 2020

@author: nmale
"""
from pymongo import MongoClient

import area_hierarchy_building as ahb

from bs4 import BeautifulSoup
from requests import get

import re

#scrape all "leaf" (bottom level) areas and their trails while adding them to the database
def scrape_trails():
    client = MongoClient()
    db = client.mountain_bike_trails
    
    area_trees = ahb.import_trees("area_trees.txt")

    for tree in area_trees:
        state_area = {}
        us_state = tree.data[1]
        areas_in_state = []
        
        num_trails_state = 0
        specific_areas = ahb.get_leaves(tree)
        for area in specific_areas:
            leaf_area = {}
            leaf_area_url = area.data[0]
            leaf_area_id = us_state + "/" + area.data[1]
            
            trails_in_area = []
            areas_in_state.append(leaf_area_id)
            
            #make an http request and open the response with beautiful soup
            area_page = get(leaf_area_url)
            area_html = area_page.text
            area_soup = BeautifulSoup(area_html)
            
            table = area_soup.find("table", class_="trail-table")
            print(table)
            
            #there is a different html format when an area has "only_one" trail
            only_one = False
            try:
                trail_info = table.find_all("tr")
            except:
                print(leaf_area_id)
                only_one = True
                trail_info = []
                try:
                    trail_info.append(area_soup.find("div", class_="col-lg-3 col-md-4 col-sm-6 card-container").a["href"])
                except:
                    print(leaf_area_id)
                    #trail_info.append(area_soup.find("div", class_="col-lg-3 col-md-4 col-sm-6 card-container").a["href"])

                
            leaf_area_num_trails = len(trail_info)
            num_trails_state += leaf_area_num_trails
            
            #scrape each individual trail
            if not only_one:
                for trail_meta in trail_info:
                    scrape_trail(trail_meta["data-href"], leaf_area_id, trails_in_area, db)
            elif len(trail_info) > 0:
                scrape_trail(trail_info[0], leaf_area_id, trails_in_area, db)
            
                
            leaf_area["url"] = leaf_area_url
            leaf_area["id"] = leaf_area_id
            leaf_area["num_trails"] = leaf_area_num_trails
            leaf_area["trails"] = trails_in_area
            db.leaf_areas.insert_one(leaf_area)
            
            print(leaf_area_id + " completed")
            
            
        
        state_area["id"] = us_state
        state_area["number_leaf_areas"] = len(specific_areas)
        state_area["areas"] = areas_in_state
        
        db.states.insert_one(state_area)
        
        print("\n" + tree.data[1] + " completed" + "\n")

def scrape_trail(trail_url, area_id, trails_in_area, db):
    trail = {}
    
    trail_soup = BeautifulSoup(get(trail_url).text)
    
    trail_name = trail_soup.find("h1", id="trail-title").text.strip()
    trail_id = area_id + "/" + trail_name
    
    trails_in_area.append(trail_id)
    
    #extract the "shorter" trail description
    trail_meta_description = trail_soup.find("meta", attrs={"name":"description"})['content']
    
    #extract the trail feature types and trail description from the html
    trail_text = trail_soup.find(id="trail-text")
    trail_text_span = trail_text.span
    trail_text_span_sections = trail_text_span.find_all("div", class_="mb-1")
    try:
        trail_features = trail_text_span_sections[1].find_all("h3")[2].find("span").text
    except:
        trail_features = "unlisted"
    
    try:
        trail_description = trail_text_span_sections[2].text.strip()
    except:
        trail_description = "unlisted"
    try:
        trail_voted_difficulty = trail_soup.find("span", class_="difficulty-text").text.strip()
    except:
        trail_voted_difficulty = "unlisted"
    try:
        stars_pictures_el = trail_soup.find("span", class_="scoreStars")
        trail_star_score = stars_pictures_el.find_next_sibling("span").text.strip().split()[0]
    except:
        trail_star_score = "unlisted"
    
    print(trail_text_span_sections)
    
    #scrape the altitude data and other features here
    scraped_javascript = trail_soup.find_all(string=re.compile("rawProfileData = \[(\[.*\],?)*\]"))[0]
    scraped_altitude_data_javascript = re.search(re.compile("rawProfileData = \[(\[.*\],?)*\]"), scraped_javascript)[0]
    scraped_altitude_data_python = scraped_altitude_data_javascript.replace("rawProfileData", "globals()[\"raw_profile_data\"]", 1)
    
    #take advantage of the fact that javascript arrays follow the same format as python lists. Run the code extracted from the javascript
    #the code executed will have the following form: raw_profile_data = [[],[],...]
    #thus we will now have a list of nested lists containing altitude data called raw_profile_data
    exec(scraped_altitude_data_python)
    trail_altitude_feet = []
    trail_incline_grade = []
    trail_mile_mark = []
    #keep the two unknown feature values in case we later discover that they are useful
    trail_unk1 = []
    trail_unk2 = []
    
    #break list of data points into lists of individual features
    #raw_profile_data comes from the executed code from exec above
    for tup in globals()["raw_profile_data"]:
        trail_altitude_feet.append(tup[0])
        trail_incline_grade.append(tup[1])
        trail_mile_mark.append(tup[2])
        trail_unk1.append(tup[3])
        trail_unk2.append(tup[4])
    
    
    trail["area"] = area_id
    trail["name"] = trail_name
    trail["id"] = trail_id
    trail["url"] = trail_url
    trail["meta-description"] = trail_meta_description
    trail["features"] = trail_features
    trail["description"] = trail_description
    trail["voted_difficulty"] = trail_voted_difficulty
    trail["star_score"] = trail_star_score
    
    trail["altitude_feet"] = trail_altitude_feet
    trail["incline_grade"] = trail_incline_grade
    trail["mile_mark"] = trail_mile_mark
    trail["unk1"] = trail_unk1
    trail["unk2"] = trail_unk2
    
    db.trails.insert_one(trail)

scrape_trails()




