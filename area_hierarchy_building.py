# -*- coding: utf-8 -*-
"""
Created on Mon Sep  7 19:46:59 2020

@author: nmale
"""

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.common.by import By

#a node in a tree
class TreeNode:
    def __init__(self, parent, data):
        self.parent = parent
        self.children = []
        self.data = data
        if parent is not None:
            self.depth = parent.depth + 1
        else:
            self.depth = 0
         
    def __str__(self):
        return str(self.data)
    
    def __repr__(self):
        return str(self.data)
    
    #add a child node to this node
    def add_child(self, child):
        self.children.append(child)
        
    #get the list of all child nodes for this node
    def get_children(self):
        return self.children
    
    #get a child at a specific index in the list
    def get_child(self, child_index):
        try:
            child = self.children[child_index]
        except:
            child = None
        return child

#scrape the MTBProject website to create the tree-like structure of all US areas and subareas
def build_structure(chrome_path):
    root_nodes = []
    #code to create trees here
    
    
    
    options = webdriver.ChromeOptions()
    
    driver = webdriver.Chrome(executable_path = chrome_path, options=options)
    driver.set_window_size(800, 1000)
    url = "https://www.mtbproject.com/directory/areas"
    
    driver.get(url)
    
    card_els = []
    try:
        card_els = driver.find_elements_by_class_name("area-card")
    except:
        pass
    
    #extract the area url and the area name
    for el in card_els:
        data_point = [el.find_element(By.TAG_NAME, 'a').get_attribute('href'), el.find_element(By.TAG_NAME, 'h3').text]
        root_nodes.append(TreeNode(None, data_point))
    
    for root in root_nodes:
        #open the web page for the "root" region. Ex: Pennsylvania
        driver.get(root.data[0])
        
        #create a stack and append all areas right below the root
        node_stack = []
        subareas = driver.find_elements_by_class_name("area")
        for area in subareas:
            data = [area.find_element(By.TAG_NAME, 'a').get_attribute('href'), area.find_element_by_class_name("link").text]
            area_node = TreeNode(root, data)
            root.add_child(area_node)
            node_stack.append(area_node)
        
        #perform a depth first search to create the area/subarea tree
        while node_stack:
            current_node = node_stack.pop()
            
            url = current_node.data[0]
            driver.get(url)
            
            subareas = driver.find_elements_by_class_name("area")
            for area in subareas:
                data = [area.find_element(By.TAG_NAME, 'a').get_attribute('href'), area.find_element_by_class_name("link").text]
                area_node = TreeNode(root, data)
                current_node.add_child(area_node)
                node_stack.append(area_node)
    return root_nodes

#convert our list of trees into a list of canonical strings which we save in a file
def export_trees(trees, export_path):
    tree_strings = []
    for tree in trees:
        build_string = stringify_node_and_children(tree)
        tree_strings.append(build_string)
    
    with open(export_path, 'w', encoding="utf-8") as filehandle:
        for tree_string in tree_strings:
            filehandle.write(tree_string + "\n")

#open a file containing canonical strings of trees and convert them to a list of trees
def import_trees(file_path):
    tree_strings = []
    
    with open (file_path, 'r', encoding="utf-8") as filehandle:
        filecontents = filehandle.readlines()

        for line in filecontents:
            # remove linebreak which is the last character of the string
            current_string = line[:-1]
    
            # add item to the list
            tree_strings.append(current_string)
        
    trees = []
    for tree_string in tree_strings:
        trees.append(objectify_tree_string(tree_string))
        
    return trees

#recursively convert given node and descendant nodes into strings
def stringify_node_and_children(node):
    stringified = ""
    
    stringified += ("<" + node.data[0] + ";" + node.data[1] + ">")
    for child in node.get_children():
        stringified += stringify_node_and_children(child)
    
    stringified += "^"
    
    return stringified

#turn the tree string into a tree of treenode objects
def objectify_tree_string(tree_string):
    temp = ""
    previously_finished_parent = None
    current_parent = None
    for c in tree_string:
        if c == "<":
            temp = ""
        elif c == ">":
            data = temp.split(";")
            new_node = TreeNode(current_parent, data)
            if current_parent is not None:
                current_parent.add_child(new_node)
            current_parent = new_node
        elif c == "^":
            previously_finished_parent = current_parent
            current_parent = current_parent.parent
        else:
            temp += c
    return previously_finished_parent

def get_leaves(root):
    leaf_nodes = []
    
    remaining_nodes = []
    remaining_nodes.append(root)
    
    while remaining_nodes:
        current_node = remaining_nodes.pop()
        
        if not current_node.get_children():
            leaf_nodes.append(current_node)
        else:
            children = current_node.get_children()
            for child in children:
                remaining_nodes.append(child)
    
    return leaf_nodes
    
#trees = build_structure("C:\\Users\\nmale\\chromedriver_win32\\chromedriver.exe")
#export_trees(trees, "area_trees.txt")
#read_trees = import_trees("area_trees.txt")


                
    