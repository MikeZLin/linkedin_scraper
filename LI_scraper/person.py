import requests
from lxml import html
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .functions import *
import time
from random import randint
from .objects import Experience, Education, Scraper
import os

class Person(Scraper):
    def __init__(self, linkedin_url = None, name = None, experiences = [], educations = [],also_viewed_urls = [],skills = [], driver = None, get = True, login=False , usrn='', pswd='', close_on_complete = True, scrape = True):
        self.linkedin_url = linkedin_url
        self.name = name
        self.experiences = experiences
        self.educations = educations
        self.also_viewed_urls = also_viewed_urls 
        self.skills = skills 
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

    def scrape_logged_in(self,max_try=10):
        driver = self.driver
        self.name = driver.find_element_by_class_name("pv-top-card-section__name").text.encode('utf-8').strip().decode('utf-8')

        driver.execute_script("window.scrollTo(0, Math.ceil(document.body.scrollHeight/2));")

        _ = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, "experience-section")))
        # get experience
        exp = driver.find_element_by_id("experience-section")
        
        #Removed Experience Expansion due to page not loading causing driver to detach
        
        #try:
        #    _ = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.pv-profile-section__see-more-inline")))
        #except: 
        #    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        #exp_buttons = exp.find_elements_by_css_selector('button.pv-profile-section__see-more-inline')
        #print('Sleeping')
        #time.sleep(randint(2000,5000)/1000.0)
        #while len(exp_buttons):
        #    print('Sleeping')
        #    time.sleep(randint(2000,5000)/1000.0)
        #    exp_buttons[0].click()
        #    try:
        #        _ = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.pv-profile-section__see-more-inline")))
        #    except: 
        #        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        #    exp_buttons = exp.find_elements_by_css_selector('button.pv-profile-section__see-more-inline')
        try:
            _ = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, "experience-section")))
        except: 
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        exp = driver.find_element_by_id("experience-section")
        for position in exp.find_elements_by_class_name("pv-position-entity"):
            position_title = position.find_element_by_tag_name("h3").text.encode('utf-8').strip().decode('utf-8')
            # Linked in uses hidden <span> text fields as labels, lets exploit this to get our data for us using key, data pairs.
            keywords = ['Company Name', 'Dates Employed',  'Employment Duration', 'Location' ]
            try:
                _ = WebDriverWait(position, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, "span")))
            except: 
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            span_texts = [get_pause(i.text) for i in position.find_elements_by_css_selector('span')]
            exp_data = {}
            for i in range(len(span_texts)):
                if span_texts[i] in keywords:
                    exp_data[span_texts[i]] = span_texts[i+1]
                    # increment i to skip next field
                    i += 1 

                    
            # Fallback to original method if failed:
            if 'Company Name' not in exp_data.keys():
                exp_data['Company Name'] =  position.find_element_by_class_name("pv-entity__secondary-title").text.encode('utf-8').strip().decode('utf-8')

            if 'Dates Employed' not in exp_data.keys():
                try:
                    exp_data['Dates Employed'] = position.find_element_by_class_name("pv-entity__date-range").text
                except Exception as e:
                    print(e)
                    exp_data['Dates Employed'] = ''

            if exp_data['Dates Employed'].count('–') == 1:
                from_date, to_date = exp_data['Dates Employed'].split('–')
            else:
                from_date, to_date = ('','')

            if 'Employment Duration' not in exp_data.keys():
                exp_data['Employment Duration'] = ''
            
            if 'Location' not in exp_data.keys():
                try:
                    exp_data['Location'] = position.find_element_by_class_name('pv-entity__location')
                    if '\n' in exp_data['Location']:
                        exp_data['Location'] = ' '.join(exp_data['Location'].split('\n')[1:])
                except Exception as e:
                    print(e)
                    exp_data['Location'] =''

            try:
                exp_data['desc'] = position.find_element_by_class_name("pv-entity__description").text
            except:
                exp_data['desc'] = ''

            exp_data['Title'] = position_title
            experience = Experience( position_title = position_title, description=exp_data['desc'] , from_date = from_date , to_date = to_date, raw_data = exp_data)
            experience.institution_name = exp_data['Company Name']

            for i in exp_data.keys():
                exp_data[i] = replace_symbols(exp_data[i])
                if exp_data[i].count('\n') != 0:
                    exp_data[i] = '<li>'.join(exp_data[i].split('\n')[1:])

            self.add_experience(experience)

        driver.execute_script("window.scrollTo(0, Math.ceil(document.body.scrollHeight/1.5));")

        _ = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, "education-section")))

        # get education
        edu = driver.find_element_by_id("education-section")
        for school in edu.find_elements_by_class_name("pv-profile-section__sortable-item"):
            edu_data = {}
            edu_data['university'] = school.find_element_by_class_name("pv-entity__school-name").text.encode('utf-8').strip().decode('utf-8')
            edu_data['degree'] = ''
            try:
                edu_data['degree'] = school.find_element_by_class_name("pv-entity__degree-name").text
                edu_data['times'] = school.find_element_by_class_name("pv-entity__dates").text
                if edu_data['times'].count('–') == 1:
                    edu_data['from_date'], edu_data['to_date'] = times.split('–')
                else:
                    raise Exception('Invalid Date')
            except:
                edu_data['from_date'], edu_data['to_date'] = ('', '')
            for i in edu_data.keys():
                edu_data[i] = replace_symbols(edu_data[i])
                if edu_data[i].count('\n') != 0:
                    edu_data[i] = ','.join(edu_data[i].split('\n')[1:])    
            education = Education(from_date =edu_data['from_date'], to_date = edu_data['to_date'], degree=edu_data['degree'],rawdata=edu_data)
            education.institution_name = edu_data['university']
            self.add_education(education)
        skill_list = ''
        tries = 0
        while skill_list == '' and tries < max_try:
            try:
                _ = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'section.pv-skill-categories-section')))
            except:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            skill_list = driver.find_element_by_css_selector('section.pv-skill-categories-section')
            tries += 1
        print('Sleeping')        
        time.sleep(randint(1000,3000)/1000.0)
        skill_list.find_element_by_css_selector('button[data-control-name="skill_details"]').click()
        for skill in skill_list.find_elements_by_css_selector('p.pv-skill-category-entity__name > a[data-control-name="skills_endorsement_full_list"]' ):
            self.add_skill(skill.text)
        if self.close_on_complete:
            driver.close()

    def get_dict_obj(self):
        dump = {}
        dump['name'] = self.name
        #dump['educations'] = [ {'degree': i.degree, 'institution':i.institution_name,'from_date':i.from_date,'to_date':i.to_date} for i in self.educations]
        dump['educations']  = [i.rawdata for i in self.educations]
        dump['experiences'] = [i.raw_data for i in self.experiences]
        dump['skills'] = self.skills
        return dump
        
    def scrape_not_logged_in(self, retry_limit = 10):
        driver = self.driver
        retry_times = 0
        while self.is_signed_in() and retry_times <= retry_limit:
            page = driver.get(self.linkedin_url)
            retry_times = retry_times + 1


        # get name
        self.name = driver.find_element_by_id("name").text.encode('utf-8').strip().decode('utf-8')

        # get experience
        exp = driver.find_element_by_id("experience")
        for position in exp.find_elements_by_class_name("position"):
            position_title = position.find_element_by_class_name("item-title").text.encode('utf-8').strip().decode('utf-8')
            company = position.find_element_by_class_name("item-subtitle").text.encode('utf-8').strip().decode('utf-8')

            try:
                times = position.find_element_by_class_name("date-range").text.encode('utf-8').strip().decode('utf-8')
                from_date, to_date, duration = time_divide(times)
            except:
                from_date, to_date = ('', '')
            experience = Experience( position_title = position_title , from_date = from_date , to_date = to_date)
            experience.institution_name = company
            self.add_experience(experience)

        # get education
        edu = driver.find_element_by_id("education")
        for school in edu.find_elements_by_class_name("school"):
            university = school.find_element_by_class_name("item-title").text.encode('utf-8').strip().decode('utf-8')
            degree = school.find_element_by_class_name("original").text.encode('utf-8').strip().decode('utf-8')
            try:
                times = school.find_element_by_class_name("date-range").text.encode('utf-8').strip().decode('utf-8')
                from_date, to_date, duration = time_divide(times)
            except:
                from_date, to_date = ('', '')
            education = Education(from_date = from_date, to_date = to_date, degree=degree)
            education.institution_name = university
            self.add_education(education)

        # get
        if self.close_on_complete:
            driver.close()

    def __repr__(self):
        return "{name}\n\nExperience\n{exp}\n\nEducation\n{edu}".format(name = self.name, exp = self.experiences, edu = self.educations)
