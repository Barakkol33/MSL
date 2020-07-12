# MSL
## What does it do?
Automated attendance checking.

## How does it work?
Python script that parses HTML.


## How to use?
### 0. Prerequisites
python
selenium
pyyaml

geckodriver.exe
(Releases - https://github.com/mozilla/geckodriver/releases \
Specific release -  https://github.com/mozilla/geckodriver/releases/download/v0.26.0/geckodriver-v0.26.0-win64.zip)

## Setup - Configure Users Data
Create users.yml file, containing your users data.\
An example can be found in tests/users.yml.\
- name - The user's name
- nicknames - Display names in Zoom meetings.
  The nicknames must be unique.
  Nicknames are not case sensitive, and when compared all whitespace is removed.

## Running - General Idea
The program needs a users file (who should be in the meeting?) and current html data (Who is actually in the meeting?).

## Running - Static Run
Run this commandline:
```
python msl.py get_status -m copy_from_browser.html -u users.yml [-g group] [-t team] [-o output_file]

```
- Using the -g (group filtering) or -t (team filtering) you can choose which teams and groups should be in the meeting.\
For example, if the meeting is of group B, then use "-g B".
- Using the -o flag you can save the MSL to a file.

## Running - Dynamic run

### 1. Start program
```
python msl.py
```
The program will enter interactive mode.

### 2. Login to zoom
Run a web command to create browser:
```
reset_tab
```
Login to zoom using the opened browser.

### 3. Enter zoom room
Enter a zoom room using the browser.\

### 4. Switch tab
The program needs to be focused on the Zoom tab.\
If the only thing you did was open it then it is probably focused on it.\
\
Each tab has an index (0-based), according to the current order of tabs in browser.\
Commands that allow switching focus on tabs:
- reset_tab (command) -  Changes to tab 0.
- switch_tab (command) - Changes to the given tab index.

### 5. Get status
- get_status (command) - prints status to screen. (You can use the -g and -t flag for filtering and -o flag for output.)

### 6. Exit
Exit program by terminating it or using the exit command.

## TODO: Add to doc
- Some room numbers will not work with open_zoom, you can just open the tab in the browser - press link, press "open app"
  or something like that once and cancel, and then open in browser.
- You can also run msl.py with a command and then it will be executed 
Useful 
- You can load users file using the load_users command and then skip the -u flag of get_status.
- You can open a zoom room url using the open_zoom command