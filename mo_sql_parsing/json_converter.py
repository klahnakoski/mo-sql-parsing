import numpy as np
import pandas as pd

def get_tables (req, alias) :
    
    liste_tables = []
    
    if 'from' in req :
        v = req['from']
        
        if isinstance(v,str) : # {'from' : 'str'}
            liste_tables.append(v)
        
        elif isinstance(v,dict) : # {'from' : {'value' : 'str' , 'name' : 'str'} }
            
            if '.' in v['value'] : 
                alia = v['value'].split('.',1)[0]
                if alia in alias :
                    table = v['value'].split('.', 1)[1]
                    table_mere = alias[alia]
                    nvl_table = table_mere + '.' + table
                    alias[v['name']] = nvl_table
                    liste_tables.append(nvl_table)
                
                else :
                    liste_tables.append(v['value'])
                    alias[v['name']] = v['value']
                    
            else :
                liste_tables.append(v['value'])
                alias[v['name']] = v['value']
             
            
        else : # if isinstance(v,list) {'from' : []}
            for elt in v : # dictionnary 
                if 'value' in elt : # {'value' : 'str' , 'name' : 'str'}           
                    if '.' in elt['value'] :
                        alia = elt['value'].split('.',1)[0]
                        if alia in alias :
                            table = elt['value'].split('.', 1)[1]
                            table_mere = alias[alia]
                            nvl_table = table_mere + '.' + table
                            alias[elt['name']] = nvl_table
                            liste_tables.append(nvl_table)
                        
                        else : 
                            liste_tables.append(elt['value'])
                            alias[elt['name']] = elt['value']
            
                    else :        
                        liste_tables.append(elt['value'])
                        alias[elt['name']] = elt['value']
                
                else : # {'* join' : }
                    join = list(elt.keys())[0]
                    if isinstance(elt[join],str): # {'* join' : 'str'}
                        
                        if '.' in elt[join] : # handling alias 
                            alia_table = elt[join]
                            alia = alia_table.split('.', 1)[0]                            
                            
                            if alia in alias : # ensure it is an alia not 'fr.inflogic*'
                                table = alia_table.split('.', 1)[1]
                                table_mere = alias[alia]
                                table_join = table_mere + '.' + table
                                liste_tables.append(table_join)
                                                                
                            else : 
                                liste_tables.append(elt[join])
                        
                        else :                  
                            liste_tables.append(elt[join])
                    
                    else : # {'* join' : {'value' : 'str' , 'name' : 'str'}}
                        alia_table = elt[join]['value']
                        alia = alia_table.split('.', 1)[0]
                        
                        if alia in alias :
                            table = alia_table.split('.', 1)[1]
                            table_mere = alias[alia]
                            table_join = table_mere + '.' + table
                            alias[elt[join]['name']] = table_join
                            liste_tables.append(table_join)
                        else :
                            alias[elt[join]['name']] = elt[join]['value']
                            liste_tables.append(elt[join]['value'])
    

    if 'where' in req :

        v = req['where']
        op = list(v.keys())[0]
        if op in ['and','or'] :
            liste_tables = liste_tables + get_op_tables(v[op],alias)[0]
            alias = {**alias, **get_op_tables(v[op], alias)[1]}

        else :
            if isinstance(v[op], dict) :
                liste_tables = liste_tables + get_tables(v[op],alias)[0]
                alias = {**alias, **get_tables(v[op], alias)[1]}

            else :
                for elt in v[op] :
                    if isinstance(elt,dict) :
                        liste_tables = liste_tables + get_tables(elt,alias)[0]
                        alias = {**alias, **get_tables(elt,alias)[1]}
                       
    
    return (liste_tables, alias)


def get_op_tables (req, alias) :
    
    list_op_tables = []
    alias_op = alias.copy()
    
    for elt in req : 
        sub_op = list(elt.keys())[0]
        if sub_op not in ['and','or'] : 
            if isinstance(elt[sub_op], list) :
                for sub_elt in elt[sub_op] :
                    if isinstance(sub_elt, dict) :                 
                        if list(sub_elt.keys())[0] == 'nvl' :
                            for sub_nvl_elt in sub_elt['nvl'] :
                                if isinstance(sub_nvl_elt, dict) :
                                    list_op_tables = list_op_tables + get_tables(sub_nvl_elt,alias_op)[0]
                                    alias_op = {**alias_op, **get_tables(sub_nvl_elt, alias_op)[1]}
                            
                        else :                  
                            list_op_tables = list_op_tables + get_tables(sub_elt,alias_op)[0]
                            alias_op = {**alias_op, **get_tables(sub_elt, alias_op)[1]}
            
            elif sub_op == 'not' :              
                elt_not = elt[sub_op]
                sub_sub_op = list(elt_not.keys())[0]
                list_op_tables = list_op_tables + get_tables(elt_not[sub_sub_op], alias_op)[0]
                alias_op = {**alias_op, **get_tables(elt_not[sub_sub_op], alias_op)[1]}
                                 
            else : 
                list_op_tables = list_op_tables + get_tables(elt[sub_op], alias_op)[0]
                alias_op = {**alias_op, **get_tables(elt[sub_op], alias_op)[1]}
                
        else :
            list_op_tables = list_op_tables + get_op_tables(elt[sub_op],alias_op)[0]
            alias_op = {**alias_op, **get_op_tables(elt[sub_op], alias_op)[1]}
                    
    return (list_op_tables, alias_op)

################################################################################################################################

def get_tables_fj (req, alias) :
    
    liste_tables_from = []
    liste_tables_join = []
    
    if 'from' in req :
        v = req['from']
        
        if isinstance(v,str) : # {'from' : 'str'}
            liste_tables_from.append(v)
        
        elif isinstance(v,dict) : # {'from' : {'value' : 'str' , 'name' : 'str'} }
            
            if '.' in v['value'] : 
                alia = v['value'].split('.',1)[0]
                if alia in alias :
                    table = v['value'].split('.', 1)[1]
                    table_mere = alias[alia]
                    nvl_table = table_mere + '.' + table
                    alias[v['name']] = nvl_table
                    liste_tables_from.append(nvl_table)
                
                else :
                    liste_tables_from.append(v['value'])
                    alias[v['name']] = v['value']
                    
            else :
                liste_tables_from.append(v['value'])
                alias[v['name']] = v['value']
             
            
        else : # if isinstance(v,list) {'from' : []}
            for elt in v : # dictionnary 
                if 'value' in elt : # {'value' : 'str' , 'name' : 'str'}           
                    if '.' in elt['value'] :
                        alia = elt['value'].split('.',1)[0]
                        if alia in alias :
                            table = elt['value'].split('.', 1)[1]
                            table_mere = alias[alia]
                            nvl_table = table_mere + '.' + table
                            alias[elt['name']] = nvl_table
                            liste_tables_from.append(nvl_table)
                        
                        else : 
                            liste_tables_from.append(elt['value'])
                            alias[elt['name']] = elt['value']
            
                    else :        
                        liste_tables_from.append(elt['value'])
                        alias[elt['name']] = elt['value']
                
                else : # {'* join' : }
                    join = list(elt.keys())[0]
                    if isinstance(elt[join],str): # {'* join' : 'str'}
                        
                        if '.' in elt[join] : # handling alias 
                            alia_table = elt[join]
                            alia = alia_table.split('.', 1)[0]                            
                            
                            if alia in alias : # ensure it is an alia not 'fr.inflogic*'
                                table = alia_table.split('.', 1)[1]
                                table_mere = alias[alia]
                                table_join = table_mere + '.' + table
                                liste_tables_join.append(table_join)
                                                                
                            else : 
                                liste_tables_join.append(elt[join])
                        
                        else :                  
                            liste_tables_join.append(elt[join])
                    
                    else : # {'* join' : {'value' : 'str' , 'name' : 'str'}}
                        alia_table = elt[join]['value']
                        alia = alia_table.split('.', 1)[0]
                        
                        if alia in alias :
                            table = alia_table.split('.', 1)[1]
                            table_mere = alias[alia]
                            table_join = table_mere + '.' + table
                            alias[elt[join]['name']] = table_join
                            liste_tables_join.append(table_join)
                        else :
                            alias[elt[join]['name']] = elt[join]['value']
                            liste_tables_join.append(elt[join]['value'])
    

    if 'where' in req :

        v = req['where']
        op = list(v.keys())[0]
        if op in ['and','or'] :
            liste_tables_from = liste_tables_from + get_op_tables_fj(v[op],alias)[0]
            liste_tables_join = liste_tables_join + get_op_tables_fj(v[op],alias)[1]
            alias = {**alias, **get_op_tables_fj(v[op], alias)[2]}

        else :
            if isinstance(v[op], dict) :
                liste_tables_from = liste_tables_from + get_tables_fj(v[op],alias)[0]
                liste_tables_join = liste_tables_join + get_tables_fj(v[op],alias)[1]
                alias = {**alias, **get_tables_fj(v[op], alias)[2]}

            else :
                for elt in v[op] :
                    if isinstance(elt,dict) :
                        liste_tables_from = liste_tables_from + get_tables_fj(elt,alias)[0]
                        liste_tables_join = liste_tables_join + get_tables_fj(elt,alias)[1]
                        alias = {**alias, **get_tables_fj(elt,alias)[2]}
    
    return (liste_tables_from, liste_tables_join, alias)


def get_op_tables_fj (req, alias) :
    
    list_op_tables_from = []
    list_op_tables_join = []
    alias_op = alias.copy()
    
    for elt in req : 
        sub_op = list(elt.keys())[0]
        if sub_op not in ['and','or'] : 
            if isinstance(elt[sub_op], list) :
                for sub_elt in elt[sub_op] :
                    if isinstance(sub_elt, dict) :                 
                        if list(sub_elt.keys())[0] == 'nvl' :
                            for sub_nvl_elt in sub_elt['nvl'] :
                                if isinstance(sub_nvl_elt, dict) :
                                    list_op_tables_from = list_op_tables_from + get_tables_fj(sub_nvl_elt,alias_op)[0]
                                    list_op_tables_join = list_op_tables_join + get_tables_fj(sub_nvl_elt,alias_op)[1]
                                    alias_op = {**alias_op, **get_tables_fj(sub_nvl_elt, alias_op)[2]}
                            
                        else :                  
                            list_op_tables_from = list_op_tables_from + get_tables_fj(sub_elt,alias_op)[0]
                            list_op_tables_join = list_op_tables_join + get_tables_fj(sub_elt,alias_op)[1]
                            alias_op = {**alias_op, **get_tables_fj(sub_elt, alias_op)[2]}
            
            elif sub_op == 'not' :              
                elt_not = elt[sub_op]
                sub_sub_op = list(elt_not.keys())[0]
                list_op_tables_from = list_op_tables_from + get_tables_fj(elt_not[sub_sub_op], alias_op)[0]
                list_op_tables_join = list_op_tables_join + get_tables_fj(elt_not[sub_sub_op], alias_op)[1]
                alias_op = {**alias_op, **get_tables_fj(elt_not[sub_sub_op], alias_op)[2]}
                                 
            else : 
                list_op_tables_from = list_op_tables_from + get_tables_fj(elt[sub_op], alias_op)[0]
                list_op_tables_join = list_op_tables_join + get_tables_fj(elt[sub_op], alias_op)[1]
                alias_op = {**alias_op, **get_tables_fj(elt[sub_op], alias_op)[2]}
                
        else :
            list_op_tables_from = list_op_tables_from + get_op_tables_fj(elt[sub_op],alias_op)[0]
            list_op_tables_join = list_op_tables_join + get_op_tables_fj(elt[sub_op],alias_op)[1]
            alias_op = {**alias_op, **get_op_tables_fj(elt[sub_op], alias_op)[2]}
                    
    return (list_op_tables_from, list_op_tables_join, alias_op)


################################################################################################################################


def get_projections (req, alias) :
    
    liste_projections = []
    
    if 'select' in req :
        liste_projections = get_projections_int(req['select'], alias)
    
    
    if 'where' in req :
        v = req['where']
        op = list(v.keys())[0]
        if op in ['and', 'or'] :
            liste_projections = liste_projections + get_op_projections (v[op], alias)
        
        else : 
            if isinstance(v[op], dict) : 
                liste_projections = liste_projections + get_projections(v[op], alias)
            
            else :
                for elt in v[op] :
                    if isinstance(elt, dict) :
                        liste_projections = liste_projections + get_projections(elt, alias)
            
    return liste_projections

def get_projections_int (v, alias) :
    
    liste_projections = []
        
    if isinstance(v,str) :
        
        if '.' in v :
            alia = v.split('.', 1)[0]
            if alia in alias :
                projection = v.split('.', 1)[1]
                table = alias[alia]
                full_projection = table + '.' + projection
                liste_projections = liste_projections + [full_projection]
        
        else :
            if v == '*' :
                liste_projections = liste_projections + ['*']
                
            elif not (v == 'dd/mm/yyyy' or is_date(v)):

                if v in alias : 
            
                    liste_projections = liste_projections + [alias[v]]

                else :
                    liste_projections = liste_projections + [v] 
                
    elif isinstance(v,dict) : 
        liste_projections = liste_projections + get_projections_int((list(v.values())[0]), alias)
                  
    elif isinstance(v,list) :
        for elt in v :
            liste_projections = liste_projections + get_projections_int(elt, alias)
    
    return liste_projections


def get_op_projections (req, alias) : 
    
    listes_op_projections = []
    
    for elt in req : 
        sub_op = list(elt.keys())[0]
        if sub_op not in ['and','or'] : 
            if isinstance(elt[sub_op], list) :
                for sub_elt in elt[sub_op] :
                    if isinstance(sub_elt, dict) :                 
                        if list(sub_elt.keys())[0] == 'nvl' :
                            for sub_nvl_elt in sub_elt['nvl'] :
                                if isinstance(sub_nvl_elt, dict) :
                                    listes_op_projections = listes_op_projections + get_projections(sub_nvl_elt,alias)
                            
                        else :                  
                            listes_op_projections = listes_op_projections + get_projections(sub_elt, alias)
            
            elif sub_op == 'not' :              
                elt_not = elt[sub_op]
                sub_sub_op = list(elt_not.keys())[0]
                listes_op_projections = listes_op_projections + get_projections(elt_not[sub_sub_op], alias)
                                 
            else : 
                listes_op_projections = listes_op_projections + get_projections(elt[sub_op], alias)
                
        else :
            listes_op_projections = listes_op_projections + get_op_projections(elt[sub_op], alias)
                    
    return listes_op_projections

################################################################################################################################


def get_atts_where (req, alias) :
    
    liste_atts_where = []
    
    if 'where' in req :
        liste_atts_where = get_atts_where_int(req['where'], alias)
    
    return liste_atts_where
        

def get_atts_where_int(v, alias) :
    
    liste_atts_where = []
    
    if isinstance(v,str) :
            
            if '.' in v :
                alia = v.split('.', 1)[0]
                if alia in alias :
                    att = v.split('.', 1)[1]
                    table = alias[alia]
                    full_att = table + '.' + att
                    liste_atts_where = liste_atts_where + [full_att]
            
            #else : 
                #liste_atts_where = liste_atts_where + [v]
    
    elif isinstance(v,dict) :
        
        if v : 
            if 'where' in v :    
                liste_atts_where = liste_atts_where + get_atts_where_int(v['where'], alias)
            else :
                liste_atts_where = liste_atts_where + get_atts_where_int((list(v.values())[0]), alias)
        
    elif isinstance(v,list) :
        for elt in v :
            liste_atts_where = liste_atts_where + get_atts_where_int(elt, alias)
    
    return liste_atts_where 

################################################################################################################################


def get_op_atts_order_by(v, alias) :
    
    liste_atts_orderby = []
    
    if isinstance(v, dict):
        
        if v :
            if 'orderby' in v :
                liste_atts_orderby = liste_atts_orderby + get_atts_order_by(v, alias)

            else :
                liste_atts_orderby = liste_atts_orderby + get_op_atts_order_by((list(v.values())[0]), alias)
    
    elif isinstance(v,list) :
        for elt in v :
            liste_atts_orderby = liste_atts_orderby + get_op_atts_order_by(elt, alias)
    
    return liste_atts_orderby
            
    
def get_atts_order_by(req, alias) :
    
    liste_atts_orderby = []
    
    if 'orderby' in req :
        liste_atts_orderby = get_atts_orderby_int(req['orderby'], alias)
    
    if 'where' in req :
        liste_atts_orderby = liste_atts_orderby + get_op_atts_order_by(req['where'], alias)
    
    return liste_atts_orderby


def get_atts_orderby_int(v, alias) :
    
    liste_atts_orderby = []
    
    if isinstance(v,str) :
            
            if '.' in v :
                alia = v.split('.', 1)[0]
                if alia in alias :
                    att = v.split('.', 1)[1]
                    table = alias[alia]
                    full_att = table + '.' + att
                    liste_atts_orderby = liste_atts_orderby + [full_att]
            
            else :
                liste_atts_orderby = liste_atts_orderby + [v]
    elif isinstance(v,dict) :
            liste_atts_orderby = liste_atts_orderby + get_atts_orderby_int((list(v.values())[0]), alias)
        
    elif isinstance(v,list) :
        for elt in v :
            liste_atts_orderby = liste_atts_orderby + get_atts_orderby_int(elt, alias)
    
    return liste_atts_orderby 


################################################################################################################################

def get_op_atts_group_by(v, alias) :
    
    liste_atts_groupby = []
    
    if isinstance(v,dict) :
        if v :
            if 'groupby' in v :
                liste_atts_groupby = liste_atts_groupby + get_atts_group_by(v, alias)

            else :
                liste_atts_groupby = liste_atts_groupby + get_op_atts_group_by((list(v.values())[0]), alias)
    
    elif isinstance(v,list) :
        for elt in v :
            liste_atts_groupby = liste_atts_groupby + get_op_atts_group_by(elt, alias)
    
    return liste_atts_groupby
            

def get_atts_group_by(req, alias) :
    
    liste_atts_groupby = []
    
    if 'groupby' in req :
        liste_atts_groupby = get_atts_groupby_int(req['groupby'], alias)
    
    if 'where' in req :
        liste_atts_groupby = liste_atts_groupby + get_op_atts_group_by(req['where'], alias)
    
    return liste_atts_groupby


def get_atts_groupby_int(v, alias) :
    
    liste_atts_groupby = []
    
    if isinstance(v,str) :
        if '.' in v :
            alia = v.split('.', 1)[0]
            if alia in alias :
                att = v.split('.', 1)[1]
                table = alias[alia]
                full_att = table + '.' + att
                liste_atts_groupby = liste_atts_groupby + [full_att]
        
        else :
            liste_atts_groupby = liste_atts_groupby + [v] 


    elif isinstance(v,dict) :
            liste_atts_groupby = liste_atts_groupby + get_atts_groupby_int((list(v.values())[0]), alias)
        
    elif isinstance(v,list) :
        for elt in v :
            liste_atts_groupby = liste_atts_groupby + get_atts_groupby_int(elt, alias)
    
    return liste_atts_groupby 


################################################################################################################################

def get_op_atts_having(v, alias) :
    
    liste_atts_having = []
    
    if isinstance(v,dict) :
        
        if v :
            if 'having' in v :
                liste_atts_having = liste_atts_having + get_atts_having(v, alias)

            else :
                liste_atts_having = liste_atts_having + get_op_atts_having((list(v.values())[0]), alias)
    
    elif isinstance(v,list) :
        for elt in v :
            liste_atts_having = liste_atts_having + get_op_atts_having(elt, alias)
    
    return liste_atts_having




def get_atts_having(req, alias) :
    
    liste_atts_having = []
    
    if 'having' in req :
        liste_atts_having = get_atts_having_int(req['having'], alias)
    
    if 'where' in req :
        liste_atts_having = liste_atts_having + get_op_atts_having(req['where'], alias)
    
    return liste_atts_having


def get_atts_having_int(v, alias) :
    
    liste_atts_having = []
    
    if isinstance(v,str) :
            
            if '.' in v :
                alia = v.split('.', 1)[0]
                if alia in alias :
                    att = v.split('.', 1)[1]
                    table = alias[alia]
                    full_att = table + '.' + att
                    liste_atts_having = liste_atts_having + [full_att]
            else : 
                liste_atts_having = liste_atts_having + [v]
    
    elif isinstance(v,dict) :
            liste_atts_having = liste_atts_having + get_atts_having_int((list(v.values())[0]), alias)
        
    elif isinstance(v,list) :
        for elt in v :
            liste_atts_having = liste_atts_having + get_atts_having_int(elt, alias)
    
    return liste_atts_having 

################################################################################################################################


def get_op_functions (v) :
    
    liste_functions = []
    
    if isinstance(v,dict) :
        if v :
            if 'select' in v :
                liste_functions = liste_functions + get_functions(v)

            else :
                liste_functions = liste_functions + get_op_functions(list(v.values())[0])
    
    elif isinstance(v,list) :
        for elt in v :
            liste_functions = liste_functions + get_op_functions(elt)
    
    return liste_functions
        

def get_functions (req) :
    
    liste_functions = [] 
    
    if 'select' in req :
        liste_functions = get_functions_int(req['select'])
        
    if 'where' in req : 
        liste_functions = liste_functions + get_op_functions(req['where'])
    
    if 'groupby' in req : 
        liste_functions = liste_functions + get_functions_int(req['groupby'])
        
    if 'orderby' in req : 
        liste_functions = liste_functions + get_functions_int(req['orderby'])
        
    if 'having' in req : 
        liste_functions = liste_functions + get_functions_int(req['having'])
            
        
    return liste_functions


def get_functions_int(v) :
    
    liste_functions = []
    functions = ['sum', 'avg', 'count', 'max', 'min']
    
    if isinstance(v,dict) :
        if (list(v.keys())[0]) in functions :
            liste_functions = liste_functions + [list(v.keys())[0]]

        liste_functions = liste_functions + get_functions_int(list(v.values())[0])
    
    
    elif isinstance(v,list) :
        for elt in v :
            liste_functions = liste_functions + get_functions_int(elt)
    
    return liste_functions

################################################################################################################################

from dateutil.parser import parse as par

def is_date(string, fuzzy=False):

    try: 
        par(string, fuzzy=fuzzy)
        return True

    except ValueError:
        return False

################################################################################################################################
