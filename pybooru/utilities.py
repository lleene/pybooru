#!/usr/bin/env python3
from __future__ import unicode_literals
from pybooru import Danbooru
from pybooru import Gelbooru
from pybooru import E621
import urllib.request
import logging
import sys
import os
import time


def progressHandle(item_str, index_int, set_size_int):
  logging.info('Starting:' + item_str + ' ' + str(index_int) + '/' + str(set_size_int))
  while os.path.exists('./pause'):
    time.sleep(2)


def mapResponse(items, map_type):
  # Define mappings,
  map_keys = { 'gelbooru_posts':{'hash':'md5', 'tags':'tag_string'},
    'gelbooru_tags':{'count':'post_count'},
    'rule34_posts':{'tags':'tag_string'},
    'rule34_tags':{'count':'post_count'},
    'e621_posts':{},
    'e621_tags':{}}
  map_urls = { 'gelbooru_posts':'https://img2.gelbooru.com/images',
    'rule34_posts':'https://img.rule34.xxx/images',
    'danbooru_posts':'https://danbooru.donmai.us/data',
    'e621_posts':'https://static1.e621.net/data'}
  if map_type == 'e621_tags' and 'tags' in items: # E621 returns nested data structure also
    temp = items['tags']
    items = temp
  if map_type == 'e621_posts' and 'posts' in items: # E621 returns nested data structure also
    temp = items['posts']
    items = temp
    for item in items:
      item['tag_string'] = ' '.join(item['tags']['general'] + item['tags']['artist'] + item['tags']['character'] + item['tags']['meta'] + item['tags']['species'] + item['tags']['copyright'])
      item['file_ext'] = item['file']['ext']
      item['file_url'] = item['file']['url']
      item['md5'] = item['file']['md5']
  map_category = {'tag':0,'artist':1,'copyright':3,'character':4,'meta':5}
  # iterate trough items
  for item in items:
    for key,value in map_keys[map_type].items():
      item[value] = item.pop(key)
    if 'directory' in item and 'image' in item:
      item['file_url'] = '{0}/{1}/{2}'.format(map_urls[map_type], item['directory'], item['image'])
    if 'type' in item and item['type'] in map_category:
      item['category'] = map_category[item['type']]
    if 'file_ext' not in item and 'image' in item:
      item['file_ext'] = os.path.splitext(item['image'])[-1]
    if 'file_ext' not in item and 'file_url' in item:
      item['file_ext'] = os.path.splitext(item['file_url'])[-1]
    if 'tag_string' in item:
      item['tag_string'] = ' '.join(item['tag_string'].split(','))
  return items


def get_tag_list(target_client, target_tag):
  try:
    tag_query = target_client.tag_list(name=target_tag)
    if target_client.site_name != 'danbooru' and len(tag_query) > 0:
      tag_query = mapResponse(tag_query, target_client.site_name + '_tags')
  except Exception as Message:
    logging.warning('ETag:' + target_tag)
    logging.warning(Message)
    return []
  return tag_query


def get_post_list(target_client, target_tag, page_index):
  try:
    post_query = target_client.post_list(tags=target_tag, page=page_index)
    if target_client.site_name != 'danbooru' and len(post_query) > 0:
      post_query = mapResponse(post_query, target_client.site_name + '_posts')
  except Exception as Message:
    logging.warning('ETag:' + target_tag)
    logging.warning(Message)
    return []
  return post_query


def retrieveMD5Set(target_client, artist_tag):
  # We are just asking for one set of results
  artist_query = get_tag_list(target_client, artist_tag)
  if len(artist_query) <= 0:
    return set()
  md5_list = []
  tag_count = int(artist_query[0]['post_count'])
  if tag_count <= 0:  # Handle exception properly
    return set()
  page_index = 1
  while tag_count > 0:
    posts = get_post_list(target_client, artist_tag, page_index)
    if len(posts) <= 0:
        break
    md5_list += [sub['md5'] for sub in posts]
    tag_count -= len(posts)
    page_index += 1
  return(set(md5_list))


def uploadFile(target_client, post, file_path):
  try:
    target_client.upload_create(tags=post['tag_string'], rating=post['rating'], file_=file_path)
  except Exception as Message:
    logging.warning('ETag:' + str(post['id']))
    logging.warning(Message)


def downloadFile(post):
  file_path = '/tmp/' + 'tmp_data.' + str(os.getpid())
  if 'file_url' not in post:
    return ''
  file_link = post['file_url']
  if post['file_ext'] in [ 'zip', 'rar', 'tar', 'tar.gz' ] and 'large_file_url' in post:
    file_link = post['large_file_url']
  try:
    logging.debug('Downloading:' + post['file_url'] + ':' + file_path)
    urllib.request.urlretrieve(file_link, file_path)
  except Exception as Message:
    logging.warning('ETag:' + str(post['id']))
    logging.warning(Message)
    return ''
  return file_path


def resolveNewTags(target_client, tag_string_list):
  tag_set = set()
  for tag_string in tag_string_list:
    tags = set(tag_string.split(','))
    tag_set.update(tags)
  # Check which tags are new
  new_tags = set()
  for tag in tag_set:
    if len(get_tag_list(target_client, tag)) <= 0:
      new_tags.update(tag)


def updateNewTags(source_client, local_client, post_list):
  tag_string_list = [sub['tag_string'] for sub in post_list]
  resolveNewTags(target_client, tag_string_list)


def commitPostList(target_client, post_list, md5_set, artist_tag):
  for post in post_list:
    # Skip any exising post
    if 'md5' in post and (post['md5'] in md5_set or target_client.post_exists(post['md5'])):
        continue
    # Prepare to download source
    file_path = downloadFile(post)
    if file_path != '':
      uploadFile(target_client, post, file_path)


def fetchArtistPosts(target_client, artist_tag):
  artist_query = get_tag_list(target_client, artist_tag)
  if len(artist_query) <= 0 or int(artist_query[0]['post_count']) <= 0:
    return []
  tag_count = int(artist_query[0]['post_count'])
  post_list = []
  page_index = 1
  while tag_count > 0:
    posts = get_post_list(target_client, artist_tag, page_index)
    if len(posts) <= 0:
      break
    post_list += posts
    tag_count -= len(posts)
    page_index += 1
  return post_list


def shallowFetchPosts(target_client, md5_set, artist_tag):
  artist_query = get_tag_list(target_client, artist_tag)
  if len(artist_query) <= 0 or int(artist_query[0]['post_count'] <= 0):
    return []
  tag_count = int(artist_query[0]['post_count'])
  post_list = []
  page_index = 1
  md5_new = set(0)  # Always Pull once
  while not md5_new.issubset(md5_set) and tag_count > 0:
    posts = get_post_list(target_client, artist_tag, page_index)
    if len(posts) <= 0:
      break
    md5_new = [sub['md5'] for sub in posts]
    post_list += posts
    tag_count -= len(posts)
    page_index += 1
  return post_list


def getSourceCatagory(target_client, category, threshold=0):
  tag_name_list = []
  request_size = 100
  map_category = {'general':'0', 'artist':'1', 'copyright':'3', 'character':'4', 'meta':'5'}
  category_str = map_category[category]
  # Fetch close to all artists on Source Booru
  for page_id in range(999):
    logging.info('Completed: ' + str(page_id) + '/999')
    try:
      tag_list = target_client.tag_list(hide_empty='yes', order='count', category=category_str, extra_params={'limit':request_size, 'page':page_id})
    except Exception as Message:
      logging.warning(Message)
      break
    tag_name_list += [sub['name'] for sub in tag_list if sub['post_count'] > threshold]
    if( len(tag_list) < request_size ):
      break
  return set(tag_name_list)


def saveSourceCatagory(target_client, category, file_name):
  source_set = getSourceCatagory(target_client, category)
  logging.info('Writing to file:' + file_name)
  with open(file_name, 'w') as output_file:
    for item in source_set:
      output_file.write("%s\n" % item)


def pullCategorySet(source_client):
  logging.basicConfig(filename=('output'+str(os.getpid())), level=logging.INFO, format='')
  for category in ['general', 'artist', 'copyright', 'character', 'meta']:
    file_name = 'Lists/source_'+category+'_list.'+target_client.site_name
    saveSourceCatagory(source_client, category, file_name)


def pullTagAliases(source_client, local_client):
  logging.basicConfig(filename=('output'+str(os.getpid())), level=logging.INFO, format='')
  alias_list = []
  for page_id in range(999):
    logging.info('Completed: ' + str(page_id) + '/999')
    alias_list = source_client.tag_list(hide_empty='yes', order='count',category='0',
      extra_params={'limit':100,'page':page_id})


def syncLocalCategory(local_client, category_file, category):
  map_category = {'general':'0', 'artist':'1', 'copyright':'3', 'character':'4', 'meta':'5'}
  category_str = map_category[category]
  item_list = []
  with open(category_file, 'r') as input_file:
    item_list = input_file.read().splitlines()
  source_set = set(item_list)
  # Start checking for tag discreptancies
  for page_id in range(999):
    tag_list = local_client.tag_list(hide_empty='yes', order='count', category='0',
      extra_params={'limit':100, 'page':page_id})
    local_name_list = [sub['name'] for sub in tag_list]
    local_id_list = [sub['id'] for sub in tag_list]
    local_cat_list = [sub['category'] for sub in tag_list]
    local_count_list = [sub['post_count'] for sub in tag_list]
    for index,name in enumerate(local_name_list):
      if name in source_set and local_cat_list[index] == 0:
        try:
          local_client.tag_update(local_id_list[index], category=category_str)
        except Exception as Message:
          logging.warning('ETag:' + local_name_list[index])
          logging.warning(Message)
        finally:
          time.sleep(local_count_list[index]/10+0.2)
    progressHandle(category, page_id, 999)


def deepArtistRefresh(source_client, local_client, progress_file):
  with open(progress_file, 'r') as file:
    completed = set(file.read().splitlines())
    artist_tags = getSourceCatagory(local_client, 'artist', threshold=10) ^ completed
    set_size = len(artist_tags)
    for index, artist_tag in enumerate(artist_tags):
      if len(artist_tag) < 3:  # 2 character names at not valid
        continue
      post_list = fetchArtistPosts(source_client, artist_tag)
      if len(post_list) > 0:
        md5_set = retrieveMD5Set(local_client, artist_tag)
        commitPostList(local_client, post_list, md5_set, artist_tag)
      progressHandle(artist_tag, index, set_size)


def pullNewArtist(source_client, local_client, input_file, progress_file = None, force = False):
  with open(input_file, 'r') as file:
    artist_tags = set(file.read().splitlines())
    with open(progress_file, 'r') as progress:
      completed = set(progress.read().splitlines())
      artist_tags = artist_tags ^ completed
    if force == False:
      artist_tags = new - getSourceCatagory(local_client, 'artist', threshold=10)
    set_size = len(artist_tags)
    for index, artist_tag in enumerate(artist_tags):
      if len(artist_tag) < 3:
        continue
      post_list = fetchArtistPosts(source_client, artist_tag)
      if len(post_list) > 0:
        md5_set = retrieveMD5Set(local_client, artist_tag)
        commitPostList(local_client, post_list, md5_set, artist_tag)
      progressHandle(artist_tag, index, set_size)


def syncAllCategories(local_client):
  syncLocalCategory(local_client, 'Lists/source_1_list.danbooru', 'artist')
  syncLocalCategory(local_client, 'Lists/source_3_list.danbooru', 'copyright')
  syncLocalCategory(local_client, 'Lists/source_4_list.danbooru', 'character')
  syncLocalCategory(local_client, 'Lists/source_5_list.danbooru', 'meta')
