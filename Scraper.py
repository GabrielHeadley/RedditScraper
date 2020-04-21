from os.path import isfile
import os
import praw
import prawcore
import pandas as pd
from time import sleep
import datetime as dt
import urllib.request
from tkinter import *

reddit = praw.Reddit("credentials")

class SubredditScraper:
    
    def __init__(self, sub, sort, lim, mode):
        self.sub = sub
        self.sort = sort
        self.lim = lim
        self.mode = mode

        print(f'SubredditScraper instance created with values sub = {sub}, sort = {sort}, lim = {lim}, mode= {mode}')
    
    def set_sort(self):
        if self.sort == 'new':
            return self.sort, reddit.subreddit(self.sub).new(limit=self.lim)
        elif self.sort == 'top':
            return self.sort, reddit.subreddit(self.sub).top(limit=self.lim)
        elif self.sort == 'hot':
            return self.sort, reddit.subreddit(self.sub).hot(limit=self.lim)
        else:
            self.sort = 'hot'
            ui.updates('Sort method was not recognized, defaulting to hot.')
            return self.sort, reddit.subreddit(self.sub).hot(limit=self.lim)
    
    def get_image(self,link):
        image_dir = 'reddit_images/'
        cwd = os.getcwd()
        directory = cwd + "/" + image_dir
        if os.path.isdir(directory):
            pass
        else:
            try:
                os.makedirs(directory,exist_ok=True)
                print("Directory '%s' created successfully" % directory)
            except OSError as error:
                print("Directory '%s' can not be created")
        name = os.path.basename(link)
        if name == "":
            pass
        elif name.isalnum() == False:
            pass
        else:
            print('Name is ',name)
            filename = os.path.join(image_dir, name)
            print('Filename is ',filename)
            if not os.path.isfile(filename):
                urllib.request.urlretrieve(link, filename)

        
    def get_posts(self):

        sub_dict = {'selftext': [], 'title': [], 'id': [], 'sorted_by': [], 'num_comments': [], 'score': [], 'created':[], 'url':[]}
        csv = f'{self.sub}_posts.csv'
        sort, subreddit = self.set_sort()
        df, csv_loaded = (pd.read_csv(csv), 1) if isfile(csv) else ('',0)

        print(f'csv = {csv}')
        print(f'After set_sort(), sort = {sort} and sub = {self.sub}')
        print(f'csv_loaded = {csv_loaded}')

        ui.updates(f'Collecting information from r/{self.sub}.')

        for post in subreddit:
            unique_id = post.id not in tuple(df.id) if csv_loaded else True

            if unique_id:
                sub_dict['selftext'].append(post.selftext)
                sub_dict['title'].append(post.title)
                sub_dict['id'].append(post.id)
                sub_dict['sorted_by'].append(sort)
                sub_dict['num_comments'].append(post.num_comments)
                sub_dict['score'].append(post.score)
                sub_dict['created'].append(dt.datetime.fromtimestamp(post.created))
                sub_dict['url'].append(post.url)
                self.get_image(post.url)
            sleep(0.1)
        
        new_df = pd.DataFrame(sub_dict)

        if 'Dataframe' in str(type(df)) and self.mode == 'w+':
            pd.concat([df, new_df], axis=0, sort=0).tto_csv(csv, index=False)
            ui.updates(f'{len(new_df)} new posts were collected and saved to {csv}')
        elif self.mode == 'w+':
            new_df.to_csv(csv, index=False)
            ui.updates(f'{len(new_df)} posts collected and saved to {csv}')
        else:
            print(f'{len(new_df)} posts were collected but they were not added to {csv} because mode was set to "{self.mode}')

class UserInterface(Frame):

    def __init__(self, master):
        Frame.__init__(self,master)
        self.master = master
        master.title('Reddit Scraper')
        self.inputs()

        self.scrape_button = Button(self, text='Initiate Scrape', command=self.scrape)
        self.scrape_button.grid(row=3, column=1, sticky='S')

        self.grid()
        col_count, row_count = self.grid_size()
        for col in range(col_count):
            self.grid_columnconfigure(col, minsize=0)
        for row in range(row_count):
            self.grid_rowconfigure(row, minsize=30)

    def inputs(self):
        self.sub_entry = Entry(self, width=12, font=('Arial',10))
        self.sub_entry.grid(row=0, column=1)
        self.sub_lbl = Label(self, text='Enter the desired Subreddit:')
        self.sub_lbl.grid(row=0)

        sort_dict = {'top', 'new', 'hot'}
        self.tkvar = StringVar(root)
        self.tkvar.set('top')
        self.sort_menu = OptionMenu(self, self.tkvar, *sort_dict)
        self.sort_menu.grid(row=1, column=1)
        self.sort_lbl = Label(self, text='Select the sorting method: ')
        self.sort_lbl.grid(row=1)

        self.lim_entry = Entry(self, width=8, font=('Arial',10))
        self.lim_entry.grid(row=2, column=1)
        self.lim_lbl = Label(self, text='Enter the amount of posts to download (Max 1000): ')
        self.lim_lbl.grid(row=2)

    def scrape(self):
        sub_in = self.sub_entry.get()
        sort_in = self.tkvar.get()
        try:
            limit_in = int(self.lim_entry.get())
        except ValueError:
            self.updates('Please enter a limit.')
        if sub_in == '':
            self.updates('Please enter a subreddit.')
        elif limit_in == 0:
            self.updates('Please enter a limit.')
        else:
            if limit_in <= 1000:
                try:
                    SubredditScraper(sub=sub_in,lim=limit_in,mode='w+',sort=sort_in).get_posts()
                except prawcore.exceptions.Redirect:
                    self.updates(f'Please check that {sub_in} is an existing subreddit.')
            else:
                self.updates('Error post download limit is 1000')

    def updates(self,message):
        self.update_lbl = Label(self, text=message, foreground='red')
        self.update_lbl.grid(row=3, column=0, sticky='S')
        self.update()
        
if __name__ == '__main__':
    root = Tk()
    root.geometry()
    ui = UserInterface(root)
    root.mainloop()