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
(Releases - https://github.com/mozilla/geckodriver/releases
    Specific release -  https://github.com/mozilla/geckodriver/releases/download/v0.26.0/geckodriver-v0.26.0-win64.zip)

### 1.Configure Users Data
Create users.yml file, containing your users data.\
An example can be found in tests/users.yml.\
- name - The user's name
- nicknames - Display names in Zoom meetings.
  The nicknames must be unique

### 2.Run
```
python ./msl.py
```
The program will enter interactive mode.

### 3. Load users file
- Default - If there is a users.yml file in the current working directory, it will be loaded.
- Dynamically - load_users (command) - load users file.

### 5. Login to zoom
Login to zoom using the opened browser.

### 4. Enter zoom room
Enter a zoom room using browser.\
Can be done manually or using the open_zoom command

### 5. Switch tab
The program needs to be focused on the Zoom tab.\
If the only thing you did was open it then it is probably focused on it.\
\
Each tab has an index (0-based), according to the current order of tabs in browser.\
Commands that allow switching focus on tabs:
- reset_tab (command) -  Changes to tab 0.
- switch_tab (command) - Changes to the given tab index.

### 6. Get status
- get_status (command) - prints status to screen.
- save_status (command) - saves status to a file.


### 7. Exit
Exit program by terminating it or using the exit command.