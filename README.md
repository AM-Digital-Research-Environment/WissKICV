# WissKICV

On terminal
>> git checkout 
>> git submodule update
or
>> git submodule update --init --recursive
   #if this does not work, remove wisski_py directory, and clone wisski_py.
>> git clone wisski_py

>> pip install wisski_py  
>> pip install SPARQLWrapper  
>> pip install pandas  

>> python  
- from projects.project_data_management import Core, ProjectManage  
- data = Core.mongo_data("UBT_DigiRet2021")  
	-> list of proj. ids or one proj. id  
	-> gets a list of one project metadata in dict.  
		contains all the project properties.  
	-> gets a list of dictionaries (all proj IDs should exist in the db)
- manager = ProjectManage()  
- manager.set_mode(1)
	-> 0 for insert; 1 for update
	#the difference between mongoDB and wisski will be detected and wisski will be updated from MongoDB data.
- manager.set_document(data[i]) 
	-> data[0] is a dictionary of the first data in the data list.

- manager.run(dry_run=True)  
	-> dry_run == True: It returns the wisski uri for all the field values of drop-down menus (controlled vocabulary). such as associated persons, research section, type of resources, etc.
