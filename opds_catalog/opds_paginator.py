'''
Created on 21 нояб. 2016 г.

@author: mitsh
'''

class Paginator:
    def __init__(self, d1_count, d2_count, page_num=1, maxitems=60, half_pages_link = 3):
        self.d1_count = d1_count
        self.d2_count = d2_count
        self.count = self.d1_count + self.d2_count
        self.MAXITEMS = maxitems
        self.HALF_PAGES_LINK = half_pages_link
        self.page_num = page_num      
        self.calc_data()                   
    
    def calc_data(self):
        d1_MAXITEMS = self.MAXITEMS
        self.d1_first_pos = d1_MAXITEMS*(self.page_num-1);
        self.d1_first_pos = self.d1_first_pos if self.d1_first_pos<self.d1_count else (self.d1_count-1 if self.d1_count else 0)
        self.d1_last_pos =  d1_MAXITEMS*self.page_num - 1;
        self.d1_last_pos = self.d1_last_pos if self.d1_last_pos<self.d1_count else (self.d1_count-1 if self.d1_count else 0) 
        
        d2_MAXITEMS = self.MAXITEMS - self.d1_last_pos + self.d1_first_pos
        self.d2_first_pos = d2_MAXITEMS*(self.page_num-1);
        self.d2_first_pos = self.d2_first_pos if self.d2_first_pos<self.d2_count else (self.d2_count-1 if self.d2_count else 0)
        self.d2_last_pos =  d2_MAXITEMS*self.page_num - 1;
        self.d2_last_pos = self.d2_last_pos if self.d2_last_pos<self.d2_count else (self.d2_count-1 if self.d2_count else 0)
        
        self.num_pages = self.count//self.MAXITEMS + 1
        self.firstpage = self.page_num - self.HALF_PAGES_LINK
        self.lastpage = self.page_num + self.HALF_PAGES_LINK
        if self.firstpage<1:
            self.lastpage = self.lastpage - self.firstpage + 1
            self.firstpage = 1
            
        if self.lastpage>self.num_pages:
            self.firstpage = self.firstpage - (self.lastpage-self.num_pages)
            self.lastpage = self.num_pages
            if self.firstpage<1:
                self.firstpage = 1
        
        self.has_previous = (self.page_num > 1)
        self.has_next = (self.page_num < self.num_pages)
        self.previous_page_number = (self.page_num-1) if self.page_num>1 else 1
        self.next_page_number = (self.page_num+1) if self.page_num<self.num_pages else self.num_pages
        self.number = self.page_num
        self.page_range = [ i for i in range(self.firstpage,self.lastpage+1) ]
                   
    
    def get_data_dict(self):
        p = {}
        p['num_pages'] = self.num_pages
        p['has_previous'] = self.has_previous
        p['has_next'] = self.has_next
        p['previous_page_number'] = self.previous_page_number
        p['next_page_number'] = self.next_page_number
        p['number'] = self.number    
        p['page_range'] = self.page_range      
        return p