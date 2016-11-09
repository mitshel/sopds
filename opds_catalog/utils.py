#######################################################################
#
# Вспомогательные функции
#
def translit(s):
   """Russian translit: converts 'привет'->'privet'"""
   assert s is not str, "Error: argument MUST be string"

   table1 = str.maketrans("абвгдеёзийклмнопрстуфхъыьэАБВГДЕЁЗИЙКЛМНОПРСТУФХЪЫЬЭ",  "abvgdeezijklmnoprstufh'y'eABVGDEEZIJKLMNOPRSTUFH'Y'E")
   table2 = {'ж':'zh','ц':'ts','ч':'ch','ш':'sh','щ':'sch','ю':'ju','я':'ja',  'Ж':'Zh','Ц':'Ts','Ч':'Ch','Ш':'Sh','Щ':'Sch','Ю':'Ju','Я':'Ja', 
             '«':'', '»':'','"':'','\n':'_',' ':'_',"'":"",':':'_','№':'N'}
   for k in table2.keys():
       s = s.replace(k,table2[k])
   return s.translate(table1)
def badsym(s):
    """Replace special web-symbols"""
    result = s
    table = {' ':'_', "'":"", '"':'', '№':'N'}
    for k in table.keys():
        result = result.replace(k,table[k])
    return result;