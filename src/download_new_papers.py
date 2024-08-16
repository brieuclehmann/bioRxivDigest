# encoding: utf-8
import os
import tqdm
import json
import datetime
import pytz
import requests


def _download_new_papers(server="biorxiv"):
    base_url = "https://api.biorxiv.org/details/" + server + "/1d"  # https://arxiv.org/list/cs/new
    response = requests.get(base_url)
    data = response.json()
    dt_list = data['collection']
    # iterate through articles in collection
    
    doi_base = "https://doi.org/"
    new_paper_list = []
    for i in tqdm.tqdm(range(len(dt_list))):
        paper = {}
        paper_number = dt_list[i]['doi']
        paper['main_page'] = doi_base + paper_number

        paper['title'] = dt_list[i]['title']
        paper['authors'] = dt_list[i]['authors']
        paper['subjects'] = dt_list[i]['category']
        paper['abstract'] = dt_list[i]['abstract']
        new_paper_list.append(paper)

    #  check if ./data exist, if not, create it
    if not os.path.exists("./data"):
        os.makedirs("./data")

    # save new_paper_list to a jsonl file, with each line as the element of a dictionary
    date = datetime.date.fromtimestamp(datetime.datetime.now(tz=pytz.timezone("America/New_York")).timestamp())
    date = date.strftime("%a, %d %b %y")
    with open(f"./data/{server}_{date}.jsonl", "w") as f:
        for paper in new_paper_list:
            f.write(json.dumps(paper) + "\n")


def get_papers(server, limit=None):
    date = datetime.date.fromtimestamp(datetime.datetime.now(tz=pytz.timezone("America/New_York")).timestamp())
    date = date.strftime("%a, %d %b %y")
    if not os.path.exists(f"./data/{server}_{date}.jsonl"):
        _download_new_papers(server)
    results = []
    with open(f"./data/{server}_{date}.jsonl", "r") as f:
        for i, line in enumerate(f.readlines()):
            if limit and i == limit:
                return results
            results.append(json.loads(line))
    return results