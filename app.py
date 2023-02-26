from flask import Flask, render_template, request
from bs4 import BeautifulSoup as bs
import logging
import undetected_chromedriver as uc
import pymongo
import time
import threading
import csv

logging.basicConfig(filename = "scrapping.log", level = logging.INFO)

username = "ntuan0910"
password = "031009"
client = pymongo.MongoClient("mongodb+srv://{username}:{password}@coursereviewswebscrappi.giv3sed.mongodb.net/?retryWrites=true&w=majority".format(username = username, password = password))

app = Flask(__name__)

def CourseAccess(course_boxes, i, platform, reviews):
    try:
        course_product_link = "https://www.udemy.com" + course_boxes[i].div.find_all("div", {"class": "course-card--main-content--2XqiY course-card--has-price-text--1c0ze"})[0].h3.a["href"]
        new_options = uc.ChromeOptions() 
        new_options.add_argument('--headless')
        new_driver =  uc.Chrome(use_subprocess=True, options=new_options)
        new_driver.get(course_product_link)
        new_driver.maximize_window()
        time.sleep(5)
        productPage = new_driver.page_source
        product_html = bs(productPage, "html.parser")
        comment_boxes = product_html.find_all("div", {"class": "review--review-container--snUvY reviews--review--2X8Ge review--review-desktop-container--r0Nor"})
        product_comment_list = []
        for comment in comment_boxes:
            try:
                name = comment.div.div.div.p.text
            except:
                name = "Not Found"
                logging.info(name) 
                
            try:
                rating = comment.div.div.div.div.span.span.text
            except:
                rating = "None"
                logging.info(rating)
            
            try:
                text = comment.find_all("div", {"class": "ud-text-md review--review-content-with-modal-trigger--2_j-P"})[0].span.text
            except Exception as e:
                text = "Not Found"
                logging.info(text)
            
            product_comment = {"name": name, "rating": rating, "text": text}
            product_comment_list.append(product_comment)
        my_dict = {"platform": platform, "course": new_driver.title,"comment": product_comment_list}
        reviews.append(my_dict)
    except Exception as e:
        logging.info(e)
        return "Something has went wrong"
    finally:
        new_driver.quit()

@app.route("/", methods = ["GET"])
def home_page():
    return render_template("index.html")

@app.route("/search", methods = ["GET", "POST"])
def course_search():
    if request.method == "POST":
        logging.info("BEGIN SEARCH")
        platform = request.form["platform"]
        searchString = "https://www.udemy.com/courses/search/?src=ukw&q=" + request.form["content"].replace(" ", "+")
        if platform == "Udemy":
            logging.info("UDEMY PLATFORM")
            try:
                options = uc.ChromeOptions()
                options.add_argument('--headless')
                driver = uc.Chrome(use_subprocess=True, options=options)
                driver.get(searchString)
                driver.maximize_window()
                time.sleep(5)
                course_find_page = driver.page_source
                course_find_html = bs(course_find_page, "html.parser")
                course_boxes = course_find_html.find_all('div', {'class':"popper-module--popper--2BpLn"})
                del course_boxes[0:3]
                reviews = []
                thread = [threading.Thread(target = CourseAccess, args = (course_boxes, i, platform, reviews)) for i in range(3)]
                for t in thread:
                    t.start()
                for t in thread:
                    t.join()
                
                try:
                    with open("data.csv", mode = "w") as f:
                        writer = csv.writer(f)
                        writer.writerow(["Platform", "Course", "Name", "Rating", "Comment"])
                        for review in reviews:
                            course = review.get("course")
                            for detail in review.get("comment"):
                                writer.writerow([platform, course] + list(detail.values()))
                        f.close()
                except Exception as e:
                    logging.info(e)
                    
                try:
                    db = client["Course_Reviews"]
                    coll_create = db["Udemy"]
                    coll_create.insert_many(reviews)
                except Exception as e:
                    logging.info(e)

                logging.info("Final Result: {}".format(reviews))
                return render_template("result.html", reviews = reviews[0: (len(reviews))])
            except Exception as e:
                logging.info(e)
                return "Something has went wrong"
            finally:
                driver.close()
    else:
        return render_template("index.html")

if __name__ == "__main__":
    app.run(host='127.0.0.1', port = 8000, debug = True)