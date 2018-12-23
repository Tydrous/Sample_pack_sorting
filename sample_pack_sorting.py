#! python3

r'''
Verison .01
Written by Nick Bordo
Limitations
 - 

#Create lists of names to search for and what category they go in.
#Get the source folder location														- DONE
#Get the destination folder location												- DONE		
#Read in all of the files and folders in the source folder 							- DONE
#Save off the original file name 													- DONE
#Prompt from a list of sample companies 											- DONE
#	Read in a list of companies from the destination folder. 						- DONE
#		If one doesn't exists prompt the user to find the file. 					- DONE
#	Allow for the addition of a new company 										- DONE
#	Save off the list to the destination folder 									- DONE
#Determine if the current folder structure is acceptable.							- DONE						
#	If files are broken up into folders and sub folders with the samples broken out just move the entire folder
#	If not then search through the files in all of the folders and move them into the new folder structure
	If there are duplicates for any reason while moving rename the file with a - 01 or next available number.



Notes of things to try and optimize
- Sorting
	- right now the sorting is rather inificient. Need to find some way of reducing the number of loop iterations. 
		- Try to figure out gow to remove all files form file list that are within a folder that has already been marked for movement. 

- On roll back remove folders created in the destination folder. 
\




What i'm currently working on
- printing paer of the file path from the source folder rather than printing the entire new path when summarizing
					>>> import os
					>>> full_path = '/book/html/wa/foo/bar/'
					>>> print os.path.relpath(full_path, '/book/html')
					'wa/foo/bar'
- Finding a way to sort the catagories list into a longest prefix match type search so that most specific path matches first when searching through the files and folders. 
	- Create a list rather than a dict so it is done in order. 
	- List
		tag 		category
		0 			1
- Figure out why the file open dialog doesn't quit on cancel

'''
import os, re, tkinter, logging, traceback, shutil, distutils
from tkinter import filedialog
from tkinter import simpledialog
from tkinter import messagebox
import logging
from distutils import dir_util
from distutils import file_util
from tqdm import tqdm

#Setup logging
logging.basicConfig(filename='log_file.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
#logging.basicConfig( level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
root = tkinter.Tk()
root.withdraw()#hides the initial dialog window

#folder_categories_file = 'categories.txt'
folder_categories_file = ''

file_moves = []#Will hold all of the sources and destination paths of files to be moved. 
folder_moves = []#Will hold all of the sources and destination paths of folders to be moved. 
unmatched_files = []#will holld all the files that did not match anything
unmatched_folders = []#Will hold all the folders that did not match anything
skipped_files = []#Tracks the files that were skipped because they already existsed
skipped_folders = []#Tracks the files that were skipped because they already existsed

class Error(Exception):
   """Base class for other exceptions"""
   pass#Define Python user-defined exceptions. Required for custom exceptions

def txt_to_dict(filepath):#Reads in all of the items from a text file into a list.
	file = open(filepath)
	file_dict = {}
	keys_list = []
	tags_list = []
	for line in file:
		colon_seperated = line.split(':')
		key = colon_seperated[0].strip()
		file_dict[key] = []
		if key != "":
			file_dict[key].append([x.strip() for x in colon_seperated[1].split(',')])
	return file_dict

def insert_key_folder_location(dest_dict, dest_path, company):
	for key in dest_dict:
		path = os.path.abspath(os.path.join(dest_path, key))#Save off the path
		dest_dict[key].insert(0, path)#insert the location of the folder to place things that match 
		logging.debug('Adding path %s to dictionary' % path)

	return dest_dict

def dest_folder_setup(dest_path, dest_dict,company):#Appends the full file path to the list attached to each key. Checks if the folder exists if not the folder gets created.  
	for key in dest_dict.keys():
		dest_dict[key].append(os.path.abspath(os.path.join(dest_path, key, company)))#Creates the file path to the possible destination folder. 
		if dest_path == None:
			logging.debug('User did not enter a destination folder')
			if os.path.isdir(dest_dict[key][0]) == False:#Checks if the folder in the list already exists. If so nothing happens. If not the folder is created. 
				logging.debug('Creating Folder at %s' % dest_dict[key][0])
				#os.makedirs(dest_dict[key][0])#no longer needed since the move and copy functions I am using create the necessary folders. This just creates clutter.
			else:
				logging.debug('Destination Folder for %s already exists.' % dest_dict[key][0])
	return dest_dict

def get_folder_name(message="Please select a folder: "):#Prompts the user to select a folder 
	class NoInput(Error):
		#Raised if the user did not select a file when prompted.
		pass

	class Cancel(Error):
		#Raised if the user did not select a file when prompted.
		pass
	
	prompt_output = message
	tries = 3
	tries = range(1,(tries + 1))
	for i in tries:
		try:
			user_input = filedialog.askdirectory(title=prompt_output)
			prompt_output = message#resets the prompt back to the original message so that the retries can be added on
			if user_input != None:#checks if what was returned was the None Value 
				user_input = user_input.strip()#Removes any white spaces that might be input before checking for valid input

			if user_input == None or user_input =='':
				raise Cancel

			elif user_input == '':
				raise NoInput

			else:
				logging.debug('User selected Folder %s' % user_input)
				break

		except NoInput:
			logging.debug('User did not input a response for prompt \"%s\" ' % message)
			attempt = len(tries) - i
			if attempt == 1:#Changes the retry prompt to last prompt
				prompt_output = "%s\nLast Attempt" % (prompt_output)

			elif attempt == 0:#Exits the program if the user does not enter a valid input after the max number of retries.
				logging.debug('User ran out of tries on prompt \"%s\" Exiting...' % message)
				exit()
			else:
				prompt_output = "%s\n%d attempts remaining " % (prompt_output, attempt)

		except Cancel:
			logging.debug('User canceled program on prompt \"%s\" Exiting...' % message)
			exit()

		except:
			logging.debug('Unable to get input from user for \"%s\"" .'% message)
			logging.debug(traceback.format_exc())

	return user_input#Gets a string input from user

def get_file_name(message="Please select a file: "):#Prompts the user to select a file 
	class NoInput(Error):
		#Raised if the user did not select a file when prompted.
		pass

	class Cancel(Error):
		#Raised if the user did not select a file when prompted.
		pass
	
	prompt_output = message
	tries = 3
	tries = range(1,(tries + 1))
	for i in tries:
		try:
			user_input = filedialog.askopenfilename(title=prompt_output)
			prompt_output = message#resets the prompt back to the original message so that the retries can be added on

			if user_input != None:#checks if what was returned was the None Value 
				user_input = user_input.strip()#Removes any white spaces that might be input before checking for valid input

			if user_input == '':
				raise NoInput

			elif user_input == None:
				raise Cancel

			else:
				logging.debug('User selected File %s' % user_input)
				break

		except NoInput:
			logging.debug('User did not input a response for prompt \"%s\" ' % message)
			attempt = len(tries) - i
			if attempt == 1:#Changes the retry prompt to last prompt
				prompt_output = "%s\nLast Attempt" % (prompt_output)

			elif attempt == 0:#Exits the program if the user does not enter a valid input after the max number of retries.
				logging.debug('User ran out of tries on prompt \"%s\" Exiting...' % message)
				exit()
			else:
				prompt_output = "%s\n%d attempts remaining " % (prompt_output, attempt)

		except Cancel:
			logging.debug('User canceled program on prompt \"%s\" Exiting...' % message)
			exit()

		except:
			logging.debug('Unable to get input from user for \"%s\"" .'% message)
			logging.debug(traceback.format_exc())

	return user_input#Gets a string input from user

def get_yes_no_cancel(message="Yes, No, or Cancel? "):#Prompts the user for an answer to a yes, no, or cancel question. 
	class Cancel(Error):
		#Raised if the user did not select a file when prompted.
		pass

	try:
		user_input = messagebox.askyesnocancel('', message)

		if user_input == True:
			logging.debug('Answered %s to %s' % (str(user_input), message))
			return True
		elif user_input == False:
			logging.debug('Answered %s to %s' % (str(user_input), message))
			return False
		else:
			logging.debug('Answered %s to %s' % (str(user_input), message))
			raise Cancel

	except Cancel:
		logging.debug('User canceled program on prompt \"%s\" Exiting...' % message)
		exit()

def get_user_string_input(message="Input: ", custom_condition_list=[]):
	class NoInput(Error):
		#Raised if the user did not select a file when prompted.
		pass
	class InvalidInput(Error):
		#Raised if the user did not select a file when prompted.
		pass
	class Cancel(Error):
		#Raised if the user hit cancel.
		pass
	
	prompt_output = message
	tries = 3
	tries = range(1,(tries + 1))
	for i in tries:
		try:
			user_input = simpledialog.askstring('Input', prompt_output)
			prompt_output = message#resets the prompt back to the original message so that the retries can be added on

			if user_input != None:#checks if what was returned was the None Value 
				user_input = user_input.strip()#Removes any white spaces that might be input before checking for valid input

			if user_input == '':
				logging.debug('User input: %s' % user_input)
				raise NoInput

			elif user_input == None:
				logging.debug('User input: %s' % user_input)
				raise Cancel
			elif custom_condition_list != []:
				for item in custom_condition_list:
					if user_input.lower() == item.lower():#check to see if any of the items in the custom condition list match the input and does that by ignoreing case. 
						logging.debug('User input: %s' % user_input)
						return user_input
						break
					else:
						raise InvalidInput
			else:
				logging.debug('User input: %s' % user_input)
				return user_input
				break

		except NoInput:
			logging.debug('User did not input a response for prompt \"%s\" input was: "%s" ' % (message, user_input))
			attempt = len(tries) - i
			if attempt == 1:#Changes the retry prompt to last prompt
				prompt_output = "%s\nLast Attempt" % (prompt_output)

			elif attempt == 0:#Exits the program if the user does not enter a valid input after the max number of retries.
				logging.debug('User ran out of tries on prompt \"%s\" Exiting...' % message)
				exit()
			else:
				prompt_output = "%s\n%d attempts remaining " % (prompt_output, attempt)

		except InvalidInput:
			logging.debug('User did not enter valid input for prompt \"%s\" input was: "%s" ' % (message, user_input))
			attempt = len(tries) - i
			if attempt == 1:#Changes the retry prompt to last prompt
				prompt_output = "%s\nLast Attempt" % (prompt_output)

			elif attempt == 0:#Exits the program if the user does not enter a valid input after the max number of retries.
				logging.debug('User ran out of tries on prompt \"%s\" Exiting...' % message)
				exit()
			else:
				prompt_output = "%s\n%d attempts remaining " % (prompt_output, attempt)

		except Cancel:
			logging.debug('User canceled program on prompt \"%s\" Exiting...' % message)
			exit()

		except:
			logging.debug('Unable to get input from user for \"%s\"" .'% message)
			logging.debug(traceback.format_exc())

def company_folder_setup(company, dest_dict):#Takes the company passed in and addes it to all the folders that are listed in dest_dict
	if company == 'None':
		logging.debug('No company folders were created because the user did NOT input a company')
	else:
		for key in dest_dict.keys():
			company_path = os.path.abspath(os.path.join(dest_dict[key][0], company))#Creates the file path to the possible destination folder. Makes all the words in the destination company folder name capital. 
			if os.path.isdir(company_path) == False:#Checks if the folder in the list already exists. If so nothing happens. If not the folder is created. 
				logging.debug('Creating Folder at %s' % company_path)
				#os.makedirs(company_path)#no longer needed since the move and copy functions I am using create the necessary folders. This just creates clutter.
		logging.debug("All required Company Folders exist")

def get_dest_folder_file():#Checks if the file needed to build the the destination folders. If not it prompts the user to locate the file. 
	file = folder_categories_file
	print(file)
	print(os.getcwd())
	if os.path.exists(file):
		return file
	else:
		file = get_file_name('Please select the "%s" file: '% (folder_categories_file))
		return file

def summarize_folder_moves(list_of_moves):#Will take in a list of the source and destination of folders and print them to the screen for review before moving them.
	max_length = 150
	for item in list_of_moves:
		if len(item) * 2 > max_length:
			max_length = ( len(item) * 2) + 5

	print('FOLDERS TO BE MOVED'.center(max_length, '='))
	print('%-80s  |  %-80s ' %('Source Folders', 'Destination'))
	for move in list_of_moves:
		source = '"' + get_rel_path([move[0],move[2]]) + '"'
		destination = '"' + get_rel_path([move[1],move[3]])  + '"'
		print('%-80s  >  %-80s ' %(source, destination))
	print('END'.center(max_length, '='))

def summarize_files_moves(list_of_moves):#Will take in a list of the source and destination of folders and print them to the screen for review before moving them.
	max_length = 150
	for item in list_of_moves:
		if len(item) * 2 > max_length:
			max_length = ( len(item) * 2) + 5
	print('FILES TO BE MOVED'.center(max_length, '='))
	print('%-80s  |  %-80s ' %('Source Files', 'Destination'))
	for move in file_moves:
		source = '"' + get_rel_path([move[0],move[2]]) + '"'
		destination = '"' + get_rel_path([move[1],move[3]])  + '"'
		print('%-80s  >  %-80s ' %(source, destination))
	print('END'.center(max_length, '='))

def summarize_unmoved_folders(list_of_umoved_items):#This will take a list of folders that did not match on anything and output them for review
	max_length = 150
	for item in list_of_umoved_items:
		if len(item) * 2 > max_length:
			max_length = ( len(item) * 2) + 5
	print('ALL OF THE UNMATCHED FOLDERS'.center(max_length, '='))
	print('%s' %('Folders'))
	for move in list_of_umoved_items:
		source = get_rel_path([move[0],move[2]])
		destination = get_rel_path([move[1],move[3]])
		print('"%s" will NOT be moved ' %(move))
	print('END'.center(max_length, '='))

def summarize_unmoved_files(list_of_umoved_items):##This will take a list of files that did not match on anything and output them for review
	max_length = 150
	for item in list_of_umoved_items:
		if len(item) * 2 > max_length:
			max_length = ( len(item) * 2) + 5
	print('ALL OF THE UNMATCHED FILES'.center(max_length, '='))
	print('%s' %('Files'))
	for item in list_of_umoved_items:
		print('File "%s" will NOT be moved ' %(item))
	print('END'.center(max_length, '='))

def execute_folder_moves(list_of_folder_moves):#Actually performs the moves passed into the function
	total_files_counter, total_folders_counter = count_files_and_folders(list_of_folder_moves[0][2])
	files_bar = tqdm(total=total_files_counter, desc="Files")
	folders_bar = tqdm(total=total_folders_counter, desc="Folders")
	for move in list_of_folder_moves:
		folders_bar.set_description('Folder name %-35s ' % os.path.basename(move[0]))
		try:
			#local_folder = os.path.basename(move[0])#not sure i need this
			for folderName, subfolders, filenames in os.walk(move[0]):
				moving_to_folder = os.path.join(move[1], os.path.relpath(folderName, move[0]))
				if os.path.exists(moving_to_folder) == False:
					os.makedirs(moving_to_folder)
				for filename in filenames:
					shutil.copy(os.path.join(folderName,filename), moving_to_folder)
					files_bar.set_description('File name %-37s ' % os.path.basename(filename))
					files_bar.update(1)
			folders_bar.update(1)
			print()
			'''
			this part does in fact actually work
			distutils.dir_util.copy_tree(move[0],move[1])
			logging.debug('Folder "%s" has been moved.'%(move[0]))
			'''
			#bypassing delete
			#distutils.dir_util.remove_tree(move[0])
			#logging.debug('Folder "%s" has been deleted.'%(move[0]))
		except distutils.errors.DistutilsFileError:
			logging.debug('Folder already exists: "%s" TO %s SKIPPED.'%(move[0], move[1]))
			print('Folder already exists: "%s" TO %s SKIPPED.'%(move[0], move[1]))
			skipped_folders.append([move[0],move[1]])
			continue
		'''
		except:
			logging.debug('Error while trying to move Folder "%s" to %s SKIPPED.'%(move[0], move[1]))
			print('Error while trying to move Folder "%s" to %s SKIPPED.'%(move[0], move[1]))
			skipped_folders.append([move[0],move[1]])
			continue
		'''

def execute_file_moves(list_of_file_moves):#Actually performs the moves passed into the function
	with tqdm(total = len(list_of_file_moves)) as pbar:
		for move in list_of_file_moves:
			try:
				path = os.path.dirname(move[1])
				if os.path.exists(os.path.abspath(os.path.dirname(move[1]))) == False:
					os.makedirs(move[1])

				if os.path.exists(move[0]) :
					logging.debug('Trying to move File "%s" to Folder: %s '%(move[0], move[1]))
					#bypassing move
					#distutils.file_util.move_file(move[0],os.path.abspath(os.path.join(move[1], os.path.basename(move[0]))))
					distutils.file_util.copy_file(move[0],os.path.abspath(os.path.join(move[1], os.path.basename(move[0]))))
					logging.debug('File "%s" has been moved.'%(move[0]))
				else:
					logging.debug('File "%s" has already been moved.'%(move[0]))
				pbar.update(1)
			except distutils.errors.DistutilsFileError:
				logging.debug('File already exists: "%s" TO %s SKIPPED.'%(move[0], move[1]))
				#print('File already exists: "%s" TO %s SKIPPED.'%(move[0], move[1]))
				pbar.update(1)
				continue
			except:
				logging.debug('Error while trying to move File "%s" to %s SKIPPED.'% (str(move[0]), str(move[1])))
				#print('Error while trying to move File "%s" to %s SKIPPED.'%(str(move[0]), str(move[1])))
				pbar.update(1)
				continue

def count_files_and_folders(folder_path):#Takes in a folder path then counts all the files and folders inside that directory. Then returns a list of intergers. Index 0 is the total of files and Index 1 is the total of folders.
	total_files_counter = 0
	total_folders_counter = 0 
	file_count_bar = tqdm(desc="Files Counted ")
	folder_count_bar = tqdm(desc="Folders Counted ")
	for folderName, subfolders, filenames in os.walk(folder_path):
		for filename in sorted(filenames):
			total_files_counter += 1
			file_count_bar.update(1)
		folder_count_bar.update(1)
		total_folders_counter += 1
	return [total_files_counter,total_folders_counter]
	r'''
	Description		Total Files		Total Folders 	
	Index			0				1	
	'''
			
def roll_back_moves(list_of_folder_moves, list_of_file_moves):#Takes in 2 lists of all the moves performed and reverses them. 
	r'''
	Before:
		Description		Source 			Destination 	Source Folder 			Destination Folder
		Index			0				1				2						3
	After:
		Description		Destination 	Source 	 		Destination Folder		Source Folder
		Index			0				1				2						3
	'''
	roll_back_folder_moves = []
	roll_back_file_moves = []
	for move in list_of_folder_moves:
		roll_back_folder_moves.append([move[1],move[0],move[3],move[2]])
		logging.debug('Folder move %s has been reversed: %s'%(move[1], move[0]))
	for move in list_of_file_moves:
		filename = os.path.basename(move[0])
		file_path = os.path.join(move[1], filename)
		dest_folder_name = os.path.dirname(move[0])
		
		logging.debug('File Move %s has been reversed: %s'%(file_path, dest_folder_name))

		roll_back_file_moves.append([file_path,dest_folder_name,move[3],move[2]])

	execute_folder_moves(roll_back_folder_moves)#Moves the folders back to their original location and deletes the folder in the new destination.
	execute_file_moves(roll_back_file_moves)#Moves the files back to their original location.

def get_rel_path(move=[]):
	r'''
	move list
	Description		Full path					Folder path to be removed.
	Index			0							1				
	'''
	rel_path = ''
	rel_path = os.path.relpath(move[0], move[1])
	return rel_path

source_folder = get_folder_name("Please select the source folder: ")
destination_folder = get_folder_name("Please select the destination folder: ")

#For when I am feeling lazy
#source_folder = r'''C:\Users\s294422\Desktop\Test Folder\Source Folder'''
#destination_folder = r'''C:\Users\s294422\Desktop\Test Folder\Destination Folder'''

#source_folder = r'''C:\Users\Bordo\Desktop\Test Folder\Source Folder'''
#destination_folder = r'''C:\Users\Bordo\Desktop\Test Folder\Destination Folder'''

print("Source Folder: " + str(source_folder))
print("Destination Folder: " + str(destination_folder))

dest_dict = txt_to_dict(get_dest_folder_file())#Creates the dictionary that will be used to setup the sub folders within the defined destination folder

current_company = str(get_user_string_input("What company is this for?"))#Queries the user to determine what the company being sorted is 
device_family = str(get_user_string_input("What device family is this for?"))#Queries the user to determine what the device family being sorted is 

#For when I am feeling lazy
#current_company = 'Cisco'
#device_family = 'ASR'


current_company = os.path.join(current_company, device_family)#joines together the device family and the company name.
dest_dict = insert_key_folder_location(dest_dict, destination_folder, current_company)#insert all of the file paths for the destination folders into the destination dictionary. 

dest_folder_setup(destination_folder, dest_dict,current_company)#Creates the sub folders within the defined destination folder
company_folder_setup(current_company, dest_dict)#Creates the company folder. 

'''
Moves consists of a list of lists. Each list will have 2 items in it. 1 will be the source folder and 1 will be the destination folder. Source Folder and Destination Folder are the original folders sorting through. 
Description		Source 		destination 	Source Folder 	Destination Folder
Index			0			1				2				3
'''

for root, folders, files in os.walk(source_folder):
	#Searches through all of the folders 

	for key in dest_dict:
		with tqdm(total = len(dest_dict[key][1]), desc=key) as pbar1:
			for tag in dest_dict[key][1]:#iterates through all of the possible tags in the dest_dict
				tag_regex = re.compile('.*(' + tag + ').*', re.IGNORECASE)#builds a regex string to match on any string that contains one of the tag strings. Ignores case
				local_matches = list(filter(tag_regex.match, folders))#This is where the actual matching takes place. the filter method is called and the tag_regex..match is passed in to determine the match criteria. The files list is passed in which is a list of all file names in the directory currently being iterated through.
				for match in local_matches:#Iterates through the filter object which contains all matches from the filter
					match_path = os.path.abspath(os.path.join(root, match))#Creates the full path of the matched file
					dest_path =  os.path.abspath(os.path.join(dest_dict[key][0],current_company, match))#Creates the full path of the matched file
					logging.debug('A match was made on %s' % (match_path))
					folder_moves.append([match_path, dest_path,source_folder,destination_folder])#appends the matched file path and the location it came from to the moves list which tracks all of the items to be moved.
					folders.remove(match)#removes the match from the files list so that it isn't matched more than once.
				pbar1.update(1)
	for folder in folders:#this will search through any file left in the files list and add it as a unmatched file. 
		logging.debug('NO MATCH WAS MADE ON %s' % (folder))
		unmatched_folders.append(folder)

	#Searches through all of the files 
	for key in dest_dict:
		for tag in dest_dict[key][1]:#iterates through all of the possible tags in the dest_dict
			tag_regex = re.compile('.*(' + tag + ').*', re.IGNORECASE)#builds a regex string to match on any string that contains one of the tag strings. Ignores case
			local_matches = list(filter(tag_regex.match, files))#This is where the actual matching takes place. the filter method is called and the tag_regex..match is passed in to determine the match criteria. The files list is passed in which is a list of all file names in the directory currently being iterated through.
			for match in local_matches:#Iterates through the filter object which contains all matches from the filter
				match_path = os.path.abspath(os.path.join(root, match))#Creates the full path of the matched file
				dest_path =  os.path.abspath(os.path.join(dest_dict[key][0],current_company))#Creates the full path of the matched file
				logging.debug('A match was made on %s' % (match_path))
				file_moves.append([match_path, dest_path,source_folder,destination_folder])#appends the matched file path and the location it came from to the moves list which tracks all of the items to be moved.
				files.remove(match)#removes the match from the files list so that it isn't matched more than once.
	for file in files:#this will search through any file left in the files list and add it as a unmatched file. 
		logging.debug('NO MATCH WAS MADE ON %s' % (file))
		unmatched_files.append(file)

'''
Moves consists of a list of lists. Each list will have 2 items in it. 1 will be the source folder and 1 will be the destination folder. Source Folder and Destination Folder are the original folders sorting through.
Description		Source 		destination 	Source Folder 	Destination Folder
Index			0			1				2				3
'''
#prints file moves

summarize_folder_moves(folder_moves)
summarize_files_moves(file_moves)
summarize_unmoved_folders(unmatched_folders)
summarize_unmoved_files(unmatched_files)

prompt_user = True# While this value is true the program will continue to prompt the user for input.
#Execute moves

while prompt_user:

	if get_yes_no_cancel('Would you like to proceed with the moves?'):
		logging.debug('Executing moves!')
		execute_folder_moves(folder_moves)
		execute_file_moves(file_moves)
		prompt_user = False

	else:
		logging.debug('User chose not to execute the moves. Exiting...')
		prompt_user = False
		exit()

print('File moves have completed.\n\n\n')

summarize_unmoved_folders(unmatched_folders)
summarize_unmoved_files(unmatched_files)

'''
prompt_user = True# While this value is true the program will continue to prompt the user for input.
#Execute moves
while prompt_user:

	if get_yes_no_cancel('Would you like to roll back?'):
		logging.debug('ROLLING BACK!')
		roll_back_moves(folder_moves, file_moves)
		prompt_user = False

	else:
		logging.debug('User chose NOT to roll back moves. Exiting...')
		prompt_user = False
		exit()

summarize_folder_moves(folder_moves)
summarize_files_moves(file_moves)
print('File have been moved back to their original location.')
'''
print('Exiting...')