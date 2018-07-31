import requests
from lxml import html
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from functions import time_divide
import time
from objects import Experience, Education, Scraper
import os

class Person(Scraper):
    name = None
    experiences = []
    skills = []
    educations = []
    also_viewed_urls = []
    linkedin_url = None
    def __init__(self, linkedin_url = None, name = None, experiences = [], educations = [], driver = None, get = True, login=False , usrn='', pswd='', close_on_complete = True, scrape = True):
        self.linkedin_url = linkedin_url
        self.name = name
        self.experiences = experiences
        self.educations = educations
        self.usrn = usrn
        self.pswd = pswd
        self.login = login
        self.close_on_complete = close_on_complete
        if driver is None:
            try:
                if os.getenv("CHROMEDRIVER") == None:
                    driver_path = os.path.join(os.path.dirname(__file__), 'drivers/chromedriver')
                else:
                    driver_path = os.getenv("CHROMEDRIVER")

                driver = webdriver.Chrome(driver_path)
            except:
                driver = webdriver.Chrome()
        
        if get:
            driver.get(linkedin_url)
            self.driver = driver
            if self.login and not self.is_signed_in():
                self.do_login()
                driver.get(linkedin_url)
        self.driver = driver
        

        if scrape:
            self.scrape()


    def add_experience(self, experience):
        self.experiences.append(experience)

    def add_skill(self,skill):
        self.skills.append(skill)

    def add_skills (self,skills:list):
        self.skills += skills

    def add_education(self, education):
        self.educations.append(education)

    def do_close_on_complete(self, ifclose=True):
        '''Method to change if to close on complete, setting as opposed to parameter'''
        self.close_on_complete = ifclose

    def scrape(self):
        if self.is_signed_in():
            self.scrape_logged_in()
        else:
            self.scrape_not_logged_in()

    def do_login(self):
        driver = self.driver        
        driver.get("https://www.linkedin.com/uas/login?")
        driver.find_element_by_name('session_key').send_keys(self.usrn)
        driver.find_element_by_class_name('password').send_keys(self.pswd)
        driver.find_element_by_name('signin').click()

    def scrape_logged_in(self,attempts=10):
        driver = self.driver
        self.name = driver.find_element_by_class_name("pv-top-card-section__name").text.encode('utf-8').strip()

        driver.execute_script("window.scrollTo(0, Math.ceil(document.body.scrollHeight/2));")

        _ = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, "experience-section")))

        # get experience
        exp = driver.find_element_by_id("experience-section")
        for position in exp.find_elements_by_class_name("pv-position-entity"):
            position_title = position.find_element_by_tag_name("h3").text.encode('utf-8').strip()
            # Linked in uses hidden <span> text fields as labels, lets exploit this to get our data for us using key, data pairs.
            keywords = ['Company Name', 'Dates Employed',  'Employment Duration', 'Location' ]
            span_texts = [i.text for i in position.find_elements_by_css_selector('span')]
            exp_data = {}
            for i in range(len(span_texts)):
                if span_texts[i] in keywords:
                    exp_data[span_texts[i]] = span_texts[i+1]
                    # increment i to skip next field
                    i += 1 

                    
            # Fallback to original method if failed:
            if 'Company Name' not in exp_data.keys():
                exp_data['Company Name'] =  position.find_element_by_class_name("pv-entity__secondary-title").text.encode('utf-8').strip()

            if 'Dates Employed' not in exp_data.keys():
                try:
                    exp_data['Dates Employed'] = position.find_element_by_class_name("pv-entity__date-range").text
                except Exception as e:
                    print(e)
                    exp_data['Dates Employed'] = None

            if exp_data['Dates Employed'].count('–') == 1:
                from_date, to_date = exp_data['Dates Employed'].split('–')
            else:
                from_date, to_date = (None,None)

            if 'Employment Duration' not in exp_data.keys():
                exp_data['Employment Duration'] = None
            
            if 'Location' not in exp_data.keys():
                try:
                    exp_data['Location'] = position.find_element_by_class_name('pv-entity__location')
                    if '\n' in exp_data['Location']:
                        exp_data['Location'] = ' '.join(exp_data['Location'].split('\n')[1:])
                except Exception as e:
                    print(e)
                    exp_data['Location'] = None

            try:
                exp_data['desc'] = position.find_element_by_class_name("pv-entity__description").text
            except:
                exp_data['desc'] = None


            experience = Experience( position_title = position_title, description=exp_data['desc'] , from_date = from_date , to_date = to_date, raw_data = exp_data)
            experience.institution_name = exp_data['Company Name']
            self.add_experience(experience)

        driver.execute_script("window.scrollTo(0, Math.ceil(document.body.scrollHeight/1.5));")

        _ = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, "education-section")))

        # get education
        edu = driver.find_element_by_id("education-section")
        for school in edu.find_elements_by_class_name("pv-profile-section__sortable-item"):
            university = school.find_element_by_class_name("pv-entity__school-name").text.encode('utf-8').strip()
            degree = None
            try:
                degree = school.find_element_by_class_name("pv-entity__degree-name").text
                times = school.find_element_by_class_name("pv-entity__dates").text
                if times.count('–') == 1:
                    from_date, to_date = times.split('–')
                else:
                    raise Exception('Invalid Date')
            except:
                from_date, to_date = (None, None)
            education = Education(from_date = from_date, to_date = to_date, degree=degree)
            education.institution_name = university
            self.add_education(education)
        skill_list = ''
        tries = 0
        # Skills section not always found in time, thus, have ability to research
        while skill_list == '' and tries < attempts: 
            try:
                skill_list = driver.find_element_by_css_selector('section.pv-skill-categories-section')
            except:
                time.sleep(0.5)
            tries += 1


        skill_list.find_element_by_css_selector('button[data-control-name="skill_details"]').click()
        for skill in skill_list.find_elements_by_css_selector('p.pv-skill-category-entity__name > a[data-control-name="skills_endorsement_full_list"]' ):
            self.add_skill(skill.text)
        if self.close_on_complete:
            driver.close()


    def scrape_not_logged_in(self, retry_limit = 10):
        driver = self.driver
        retry_times = 0
        while self.is_signed_in() and retry_times <= retry_limit:
            page = driver.get(self.linkedin_url)
            retry_times = retry_times + 1


        # get name
        self.name = driver.find_element_by_id("name").text.encode('utf-8').strip()

        # get experience
        exp = driver.find_element_by_id("experience")
        for position in exp.find_elements_by_class_name("position"):
            position_title = position.find_element_by_class_name("item-title").text.encode('utf-8').strip()
            company = position.find_element_by_class_name("item-subtitle").text.encode('utf-8').strip()

            try:
                times = position.find_element_by_class_name("date-range").text.encode('utf-8').strip()
                from_date, to_date, duration = time_divide(times)
            except:
                from_date, to_date = (None, None)
            experience = Experience( position_title = position_title , from_date = from_date , to_date = to_date)
            experience.institution_name = company
            self.add_experience(experience)

        # get education
        edu = driver.find_element_by_id("education")
        for school in edu.find_elements_by_class_name("school"):
            university = school.find_element_by_class_name("item-title").text.encode('utf-8').strip()
            degree = school.find_element_by_class_name("original").text.encode('utf-8').strip()
            try:
                times = school.find_element_by_class_name("date-range").text.encode('utf-8').strip()
                from_date, to_date, duration = time_divide(times)
            except:
                from_date, to_date = (None, None)
            education = Education(from_date = from_date, to_date = to_date, degree=degree)
            education.institution_name = university
            self.add_education(education)

        # get
        if self.close_on_complete:
            driver.close()

    def __repr__(self):
        return "{name}\n\nExperience\n{exp}\n\nEducation\n{edu}".format(name = self.name, exp = self.experiences, edu = self.educations)
