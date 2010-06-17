
import gevent
import ldrfullfeed
import ad_filter
import urllib2
import types
from lxml import etree, html

FETCH_TYPES = ["text/plain", "text/html"]

def fetch_full(url, encoding, xpath, default_value):
    if not encoding:
        encoding = "utf-8"
    try:
        data = urllib2.urlopen(url).read().decode(encoding)
        root = html.fromstring(data)
        elems = root.xpath(xpath)
    except:
        elems = None
    
    if not elems:
        return {"value": default_value,
                "type": "text/plain"}
    else:
        return {"value": etree.tounicode(elems[0]),
                "type": "text/html"}

def merge(entry, url, xitem, default_value):
    entry["full_content"] = fetch_full(url, xitem.get("enc"), xitem["xpath"], default_value)

def get_content(entry):
    content = entry.get("content")
    if not content:
        content = {"type": "text/text",
                   "value": entry.get("summary", "")}
        entry["content"] = [content]
        return content
    
    return content[0]

def regist_filter(global_config, options):
    data = ldrfullfeed.load(global_config["filter.ldrfullfeed.path"])
    def fetch(context):
        index, feed = context
        if global_config.get("verbose"):
            print "fetching content for %d" % index
        jobs = []
        for entry in feed["entries"]:
            content = get_content(entry)
            if entry.get("full_content"):
                pass
            elif entry.get(ad_filter.AD_FILTER_KEY) or content["type"] not in FETCH_TYPES:
                entry["full_content"] =  {"type": content["type"],
                                         "value": content["value"]}
            else:
                url = entry["link"]
                xitem = ldrfullfeed.match(data, url)
                if xitem.get("default", False):
                    entry["default_feed"] = "original"
                else:
                    entry["default_feed"] = "full_content"
                jobs.append(gevent.spawn(merge, entry, url, xitem, content["value"]))
        gevent.joinall(jobs)
        
        if global_config.get("verbose"):
            print "fetched content for %d" % index
            
        return context

    return fetch
