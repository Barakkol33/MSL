import argparse
from selenium import webdriver
import os
import yaml
import traceback

USER_REPR_FORMAT = "{:8}{:8}{:20}{:6}{:6}"


def bool_repr(value):
    if value is None:
        return ""
    elif value is True:
        return "V"
    else:
        return "X"


class WebControl(object):
    def __init__(self):
        print("Opening driver...")
        self.driver = webdriver.Firefox()
        self.open_current("https://zoom.us/signin")

    def open_current(self, url):
        self.driver.get(url)

    def open_new(self, url):
        self.driver.execute_script('window.open("{}","_blank");'.format(url))

    def open_zoom(self, zoom_room_number):
        url = "https://zoom.us/wc/{}/start".format(zoom_room_number)
        self.open_new(url)

    def switch_tab(self, tab_index):
        self.driver.switch_to.window(self.driver.window_handles[tab_index])

    def reset_tab(self):
        self.switch_tab(0)

    def get_page_source(self):
        return self.driver.page_source


class WebControlStub(object):
    def open_current(self, url):
        pass

    def open_new(self, url):
        print("WebControlStub: Opening url {}.".format(url))

    def open_zoom(self, zoom_room_number):
        print("WebControlStub: Opening zoom room {}.".format(zoom_room_number))

    def switch_tab(self, tab_index):
        print("WebControlStub: Opening tab {}.".format(tab_index))

    def reset_tab(self):
        print("WebControlStub: resetting tab.")

    def get_page_source(self):
        return open(os.path.join("tests", "example.html")).read()


class Participant(object):
    """
    Participant in a Zoom meeting.
    """

    def __init__(self, text, is_video_on):
        self.text = text
        self.is_video_on = is_video_on

    @classmethod
    def from_text(cls, text):
        is_video_on = "video on " in text
        return cls(text, is_video_on)

    def compare_name(self, name):
        """
        Checking if the text starts with the words of name. (compare_name(text="hello world today ...", "hello world") == true)
        """
        words_in_name = name.count(" ") + 1
        name_from_text = " ".join(self.text.split(" ")[:words_in_name])
        return name == name_from_text

    def __repr__(self):
        return "Participant('{}')".format(self.text)


class ParticipantList(object):
    ARIA = "aria-label=\""
    START_MARK = "Participants ("

    def __init__(self, participants):
        self.items = participants

    @classmethod
    def from_page_source(cls, page_source):
        # TODO: What happens if the page is not a zoom meeting page, or the Participants tab is not shown?
        # Get relevant line.
        participants_line = [line for line in page_source.split("\n") if "participants-item__name" in line][0]

        # Remove unnecessary beginning
        text = participants_line[participants_line.index(cls.START_MARK):]

        # Get participants text from source
        all_raw = cls.get_all(text)

        # Create objects
        participants = [Participant.from_text(item) for item in all_raw]

        return cls(participants)

    @classmethod
    def get_all(cls, text):
        contents = []

        start_content_index, content = cls.get_next(text)

        while content:
            contents.append(content)
            text = text[start_content_index + len(content):]
            start_content_index, content = cls.get_next(text)

        # Ignore first one
        contents = contents[1:]

        return contents

    @classmethod
    def get_next(cls, text):
        if cls.ARIA in text:
            index = text.index(cls.ARIA)
            start_content_index = index + len(cls.ARIA)
            end_content_index = text[start_content_index:].index("\"")
            content = text[start_content_index:start_content_index + end_content_index]
            return start_content_index, content

        return None, None


class UsersData(object):
    def __init__(self, users_data):
        self.items = users_data

    def get_by_team(self, team):
        return [user_data for user_data in self.items if user_data.team == team]

    def get_by_group(self, group):
        return [user_data for user_data in self.items if user_data.group == group]

    def get_all(self):
        return list(self.items)

    @classmethod
    def from_file(cls, file_path):
        content = open(file_path).read()
        data = yaml.load(content, Loader=yaml.FullLoader)

        users_data = []
        for group, group_data in data.items():
            for team, team_data in group_data.items():
                for user_data in team_data:
                    users_data.append(UserData(name=user_data["name"],
                                               nicknames=user_data["nicknames"],
                                               team=team,
                                               group=group))

        return cls(users_data)


class UserData(object):
    def __init__(self, name, nicknames, team, group):
        self.name = name
        self.nicknames = nicknames
        self.team = team
        self.group = group


class User(object):
    def __init__(self, name, nicknames, team, group, participants):
        self.name = name
        self.nicknames = nicknames
        self.team = team
        self.group = group
        self.participants = participants

    @classmethod
    def from_data(cls, user_data, participants):
        return cls(name=user_data.name,
                   nicknames=user_data.nicknames,
                   team=user_data.team,
                   group=user_data.group,
                   participants=participants)

    @property
    def is_video_on(self):
        if not self.is_online:
            return None
        return any([participant.is_video_on for participant in self.participants])

    @property
    def is_online(self):
        return bool(self.participants)

    def __repr__(self):
        return USER_REPR_FORMAT.format(self.group, self.team, self.name, bool_repr(self.is_online),
                                       bool_repr(self.is_video_on))


class UserList(object):
    SORT_BY_NAME = "name"
    SORT_BY_GROUP = "group"
    SORT_BY_STATUS = "status"
    SORT_BY_DEFAULT = SORT_BY_STATUS

    def __init__(self, users):
        self.items = users
        self.sort()

    def sort(self):
        def sort_key_method(user):
            is_online_text = "1" if user.is_online else "2"
            return is_online_text + user.group + user.team + user.name

        self.items = sorted(self.items, key=sort_key_method)

    @classmethod
    def from_data(cls, expected_users_data, participant_list):
        users = []
        for user_data in expected_users_data:
            existing_participants = []

            # Get all existing participants of user
            for nickname in user_data.nicknames:
                for participant in participant_list.items:
                    if participant.compare_name(nickname):
                        existing_participants.append(participant)
                        break

            users.append(User.from_data(user_data, existing_participants))

        return cls(users)

    def __repr__(self):
        header = USER_REPR_FORMAT.format("Group", "Team", "Name", "Here?", "Vid?")
        return "Users:\n{}".format("\n".join([header] + [repr(user) for user in self.items]))


class MSL(object):
    DEFAULT_USERS_FILE_PATH = "users.yml"

    def __init__(self, web):
        self.web = web

        self.users_data = None

        # If default configuration exists - use it.
        if os.path.exists(self.DEFAULT_USERS_FILE_PATH):
            self.load_users(self.DEFAULT_USERS_FILE_PATH)

    def load_users(self, users_file_path):
        print("Loading users file {}...".format(users_file_path))
        self.users_data = UsersData.from_file(users_file_path)

    def get_status(self, team="", group=""):

        # Get participant list
        zoom_meeting_html = self.web.get_page_source()
        participant_list = ParticipantList.from_page_source(zoom_meeting_html)

        # Get expected users data.
        if not self.users_data:
            raise RuntimeError("Users not set!")

        if team:
            expected_users_data = self.users_data.get_by_team(team)
        elif group:
            expected_users_data = self.users_data.get_by_group(group)
        else:
            expected_users_data = self.users_data.get_all()

        # Get user list
        user_list = UserList.from_data(expected_users_data, participant_list)

        return user_list

    def save_status(self, output_file_path, team="", group=""):
        user_list = self.get_status(team=team, group=group)
        open(output_file_path, "w").write(repr(user_list))

    @staticmethod
    def safe_invoke(func, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if isinstance(e, KeyboardInterrupt):
                return
            else:
                traceback.print_exc()

        return None


class MSLParser(object):
    def __init__(self, web):
        self.msl = MSL(web)

    def open_new(self, args):
        print("Opening url {}...".format(args.url))
        self.msl.safe_invoke(self.msl.web.open_new, args.url)

    def open_zoom(self, args):
        self.msl.safe_invoke(self.msl.web.open_zoom, args.room)

    def switch_tab(self, args):
        self.msl.safe_invoke(self.msl.web.switch_tab, args.tab_index)

    def load_users(self, args):
        self.msl.safe_invoke(self.msl.load_users, args.file_path)

    def get_status(self, args):
        user_list = self.msl.safe_invoke(self.msl.get_status, team=args.team, group=args.group)
        if user_list:
            print(user_list)

    def save_status(self, args):
        self.msl.safe_invoke(self.msl.save_status, output_file_path=args.file_path, team=args.team, group=args.group)

    def reset_tab(self, _):
        self.msl.safe_invoke(self.msl.web.reset_tab)

    def parse_args(self, raw_args):
        main_parser = argparse.ArgumentParser()
        subparsers = main_parser.add_subparsers()

        url_parser = argparse.ArgumentParser(add_help=False)
        url_parser.add_argument("-u", "--url", required=True)

        index_parser = argparse.ArgumentParser(add_help=False)
        index_parser.add_argument("-i", "--tab-index", type=int, required=True)

        parser = subparsers.add_parser("open_new", parents=[url_parser])
        parser.set_defaults(func=self.open_new)

        parser = subparsers.add_parser("open_zoom")
        parser.add_argument("-r", "--room", type=int, required=True)
        parser.set_defaults(func=self.open_zoom)

        parser = subparsers.add_parser("switch_tab", parents=[index_parser])
        parser.set_defaults(func=self.switch_tab)

        parser = subparsers.add_parser("reset_tab")
        parser.set_defaults(func=self.reset_tab)

        parser = subparsers.add_parser("load_users")
        parser.add_argument("-f", "--file-path", required=True)
        parser.set_defaults(func=self.load_users)

        get_status_parent_parser = argparse.ArgumentParser(add_help=False)
        get_status_parent_parser.add_argument("-t", "--team")
        get_status_parent_parser.add_argument("-g", "--group")

        parser = subparsers.add_parser("get_status", parents=[get_status_parent_parser])
        parser.set_defaults(func=self.get_status)

        parser = subparsers.add_parser("save_status", parents=[get_status_parent_parser])
        parser.add_argument("-f", "--file-path", required=True)
        parser.set_defaults(func=self.save_status)

        args = main_parser.parse_args(args=raw_args)

        return args

    def execute(self, raw_args):
        args = self.parse_args(raw_args)
        args.func(args)
        print("Done!")

    def start(self):
        user_input = ""
        while user_input != "exit":
            if user_input:
                try:
                    self.execute(user_input.split())
                except:
                    pass
            user_input = input("==> ")


class Tests(object):
    @staticmethod
    def commands_tests():
        msl_parser = MSLParser(WebControlStub())
        msl_parser.execute("open_new -u https://google.com".split())

        msl_parser.execute("open_zoom -r 12345".split())

        msl_parser.execute("load_users -f tests/users.yml".split())

        msl_parser.execute("switch_tab -i 12345".split())

        msl_parser.execute("reset_tab".split())

        msl_parser.execute("get_status".split())
        msl_parser.execute("get_status -t k2-t2".split())
        msl_parser.execute("get_status -g kapa1".split())

        msl_parser.execute("save_status -f tests/save_status_test.txt".split())

        # Checking error - Getting status before settings users
        MSLParser(WebControlStub()).execute("get_status".split())

    @staticmethod
    def logic_test():
        msl = MSL(WebControlStub())
        msl.load_users(os.path.join("tests", "users.yml"))
        user_list = msl.get_status()
        print(user_list)


def main():
    MSLParser(WebControl()).start()


if __name__ == "__main__":
    main()

"""
TODO: when loading - check that there are no 2 identical nicknames
TODO: Remove (Host) and (Me) 
"""
