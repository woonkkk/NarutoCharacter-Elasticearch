from flask import Flask, request
from markupsafe import escape
from flask import render_template
from elasticsearch import Elasticsearch
import math

ELASTIC_PASSWORD = "u6488045"

es = Elasticsearch("https://localhost:9200", http_auth=("elastic", ELASTIC_PASSWORD), verify_certs=False)
app = Flask(__name__, static_url_path="/static")

app.config['STATIC_FOLDER'] = 'static'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search')
def search():
    page_size = 10
    keyword = request.args.get('keyword')
    if request.args.get('page'):
        page_no = int(request.args.get('page'))
    else:
        page_no = 1

    body = {
        "size": page_size,
        "from": page_size * (page_no - 1),
        "query": {
        "function_score": {
            "query": {
                "bool": {
                    "should": [
                        {
                            "match_phrase_prefix": {
                                "character_name": keyword
                            }
                        },
                        {
                            "multi_match": {
                                "query": keyword,
                                "fields": ["character_name", "description", "affiliation", "background", "ability", "appearance"],
                                "fuzziness": "AUTO"
                            }
                        },
                        {
                            "match": {
                            "affiliation": {
                                "query": keyword,
                                "boost": 1
                            }
                            }
                        }
                    ],
                    "minimum_should_match" : 1,
                    "boost" : 2.0
                }
            },
            "functions": [
                {
                    "filter": { "exists": { "field": "character_name" } },
                    "weight": 3
                }
            ],
            "score_mode": "sum"
            }
        }
    }
    res = es.search(index='t0', body=body)
    hits = [{'character_name': doc['_source']['character_name'], 'character_pic': doc['_source']['character_pic'], 'description': doc['_source']['description']
             , 'affiliation': doc['_source']['affiliation'], 'background': doc['_source']['background'], 'ability': doc['_source']['ability']
             , 'appearance': doc['_source']['appearance'] } for doc in res['hits']['hits']]
    page_total = math.ceil(res['hits']['total']['value']/page_size)
    return render_template('index.html',keyword=keyword, hits=hits, page_no=page_no, page_total=page_total)