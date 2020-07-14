import argparse
from selenium import webdriver
import os
import yaml
import traceback
import functools
import datetime
import sys
import io

USER_REPR_FORMAT = "{:8}{:8}{:25}{:6}{:6}"
ZOOM_LOGIN_PAGE_URL = "https://zoom.us/signin"
ZOOM_MEETING_URL_FORMAT = "https://zoom.us/wc/{}/start"
REMOVE_FROM_TEXT = ["(Host)", "(Me)", "(Guest)"]
VIDEO_ON_TEXT = "video on"

# TODO: Make get_status() receive either WebControl or static
# TODO: Improve code conventions (constants, nameing, docs, etc.).


def bool_repr(value):
    if value is None:
        return ""
    elif value is True:
        return "V"
    else:
        return "X"


def error_log(message):
    timestamp = datetime.datetime.now()
    io.open("errors.txt", "a", encoding="utf-8").write("{} {}".format(timestamp, message))


class IWebControl(object):
    def open_new(self, url):
        raise NotImplementedError()

    def open_zoom(self, zoom_room_number):
        raise NotImplementedError()

    def switch_tab(self, tab_index):
        raise NotImplementedError()

    def reset_tab(self):
        raise NotImplementedError()

    def get_page_source(self):
        raise NotImplementedError()


class WebControl(IWebControl):
    def __init__(self):
        print("Opening driver...")
        self.driver = webdriver.Firefox()

        # Open zoom login page.
        self.driver.get(ZOOM_LOGIN_PAGE_URL)

    def open_new(self, url):
        self.driver.execute_script('window.open("{}","_blank");'.format(url))

    def open_zoom(self, zoom_room_number):
        url = ZOOM_MEETING_URL_FORMAT.format(zoom_room_number)
        self.open_new(url)

    def switch_tab(self, tab_index):
        self.driver.switch_to.window(self.driver.window_handles[tab_index])

    def reset_tab(self):
        self.switch_tab(0)

    def get_page_source(self):
        return self.driver.page_source

    @classmethod
    def factory(cls):
        return cls()


class Participant(object):
    """
    Participant in a Zoom meeting.
    """

    def __init__(self, text, is_video_on):
        # Remove uninteresting tokens from text, that allow splitting by "  " and getting the name.
        for token in REMOVE_FROM_TEXT:
            text = text.replace(token, "")

        self.text = text
        self.name = self.text.split("  ")[0]
        self.is_video_on = is_video_on

    @classmethod
    def from_text(cls, text):
        is_video_on = VIDEO_ON_TEXT in text
        return cls(text, is_video_on)

    @staticmethod
    def _prepare_name(name):
        # Remove whitespace and make lowercase
        name = "".join(name.split())
        name = name.lower()

        return name

    @classmethod
    def s_compare_name(cls, name1, name2):
        return cls._prepare_name(name1) == cls._prepare_name(name2)

    def compare_name(self, name):
        return self.s_compare_name(self.name, name)

    def __repr__(self):
        return "Participant('{}')".format(self.text)


class ParticipantList(object):
    ARIA = "aria-label=\""
    START_MARK = "participant list"
    USERS_LINE_IDENTIFIER = "participants-item__name"
    SKIP_CONTENTS = ["Input search keyword Find a participant", "participant list"]

    def __init__(self, participants):
        self.items = participants

    @classmethod
    def from_page_source(cls, page_source):
        # TODO: What happens if the page is not a zoom meeting page, or the Participants tab is not shown?
        # Get relevant line.
        participants_line_filter = [line for line in page_source.split("\n") if cls.USERS_LINE_IDENTIFIER in line]
        if not participants_line_filter:
            raise RuntimeError("Participants not found in page!\nCheck that the focus is on correct tab and the "
                               "you can see all the participants in the page")
        participants_line = participants_line_filter[0]

        # Remove unnecessary beginning
        text = participants_line[participants_line.index(cls.START_MARK):]

        # Get participants text from source
        all_raw = cls.get_all(text)

        # Create objects
        participants = [Participant.from_text(item) for item in all_raw]

        return cls(participants)

    @classmethod
    def get_all(cls, text):
        """
        Get all text representations of users from part of page source.
        The text representations are in the following format: 'aria-label="<User Text>"'.
        """
        contents = []

        start_content_index, content = cls.get_next(text)

        while content:
            contents.append(content)
            text = text[start_content_index + len(content):]
            start_content_index, content = cls.get_next(text)

        # Ignore irrelevant contents
        relevant_contents = []
        for content in contents:
            for token in cls.SKIP_CONTENTS:
                if token in content:
                    continue
            relevant_contents.append(content)

        return relevant_contents

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
    def __init__(self, users_data, teams, groups):
        self.items = users_data
        self.teams = teams
        self.groups = groups
        self._validate_users_data(self.items)

    def get_by_team(self, team):
        return [user_data for user_data in self.items if user_data.team == team]

    def get_by_group(self, group):
        return [user_data for user_data in self.items if user_data.group == group]

    def get_all(self):
        return list(self.items)

    @staticmethod
    def _validate_users_data(users_data):
        """
        Check that there are no two nicknames that might clash in the users data.
        For example, "Itay" and "Itay Levi" Clash - If there is one participant with the name of "Itay Levi" then
        both will think it matches them
        """
        nicknames = [user_data.nicknames for user_data in users_data]
        nicknames = functools.reduce(lambda x, y: x + y, nicknames)

        for i in range(len(nicknames)):
            for j in range(i + 1, len(nicknames)):
                if Participant.s_compare_name(nicknames[i], nicknames[j]):
                    raise ValueError("Found two clashing nicknames: {}".format(nicknames[i]))

    @classmethod
    def from_file(cls, file_path):
        content = io.open(file_path, encoding="utf-8").read()
        data = yaml.load(content, Loader=yaml.FullLoader)

        users_data = []
        teams = []
        groups = []
        for group, group_data in data.items():
            groups.append(group)
            for team, team_data in group_data.items():
                teams.append(team)
                for user_data in team_data:
                    # Filter users with no names
                    if not user_data["name"]:
                        continue
                    users_data.append(UserData(name=user_data["name"],
                                               nicknames=user_data["nicknames"],
                                               team=team,
                                               group=group))

        return cls(users_data, teams, groups)


class UserData(object):
    def __init__(self, name, nicknames, team, group):
        # Remove redundant whitespace
        self.name = name.strip()

        # Filter empty nicknames and strip nicknames
        self.nicknames = [nickname.strip() for nickname in nicknames if nickname]
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
        if not self.nicknames:
            return None
        return bool(self.participants)

    def __repr__(self):
        return USER_REPR_FORMAT.format(self.group, self.team, self.name, bool_repr(self.is_online),
                                       bool_repr(self.is_video_on))


class UserList(object):
    SORT_BY_NAME = "name"
    SORT_BY_GROUP = "group"
    SORT_BY_STATUS = "status"
    SORT_BY_DEFAULT = SORT_BY_STATUS

    def __init__(self, users, teams):
        self.items = users
        self.teams = teams
        self.sort()

    def sort(self):
        def sort_key_method(user):
            is_online_text = "1" if user.is_online else "2"
            return is_online_text + user.group + user.team + user.name

        self.items = sorted(self.items, key=sort_key_method)

    @classmethod
    def from_data(cls, expected_users_data, participant_list, teams):
        users = []

        for user_data in expected_users_data:
            existing_participants = []

            # Get all existing participants of user
            for nickname in user_data.nicknames:
                for participant in participant_list.items:
                    if participant.compare_name(nickname):
                        existing_participants.append(participant)
                        # Don't break here - someone might have a few profiles with the same names.

            users.append(User.from_data(user_data, existing_participants))

        return cls(users, teams)

    def get_msls(self):
        msls = []
        for team in self.teams:
            team_users = [user for user in self.items if user.team == team]
            msl = TeamMSL(team, team_users)
            msls.append(msl)

        return msls

    def __repr__(self):
        header = USER_REPR_FORMAT.format("Group", "Team", "Name", "Here?", "Vid?")
        return "Users:\n{}".format("\n".join([header] + [repr(user) for user in self.items]))


class TeamMSL(object):
    def __init__(self, team, users):
        self.team = team
        self.users = users

    def __repr__(self):
        total_amount = len(self.users)
        team_missing = [user for user in self.users if not user.is_online]
        repr_format = "*Team {}*\nNormal: {}\nCurrent: {}\nDescription:\n{}\n\n"
        output = repr_format.format(self.team,
                                    len(self.users),
                                    total_amount - len(team_missing),
                                    "\n".join(["- " + user.name for user in team_missing]))
        return output


class MSLManager(object):
    def __init__(self):
        self.users_data = None

    def load_users(self, users_file_path):
        print("Loading users file {}...".format(users_file_path))
        self.users_data = UsersData.from_file(users_file_path)

    def get_status(self, team="", group="", html_source=None, users_file_path=""):
        # Get zoom meeting html.
        # If html source is a string - it is an html file name.
        if isinstance(html_source, str):
            zoom_meeting_html = io.open(html_source, encoding="utf-8").read()
        # Otherwise - source is a IWebControl. 
        else:
            zoom_meeting_html = html_source.get_page_source()

        # Get participant list by parsing html.
        participant_list = ParticipantList.from_page_source(zoom_meeting_html)

        # Get expected users data (Who are we focusing on now?).
        # If users file was given - load it.
        if users_file_path:
            self.load_users(users_file_path)

        if not self.users_data:
            raise RuntimeError("Users not set!")

        if team:
            expected_users_data = self.users_data.get_by_team(team)
            expected_teams = [team]
        elif group:
            expected_users_data = self.users_data.get_by_group(group)

            # group == {'A', 'B', 'C'}, team = {'A1', 'A2', 'B1', 'B2'...}
            expected_teams = [team for team in self.users_data.teams if group == team[0]]
        else:
            expected_users_data = self.users_data.get_all()
            expected_teams = self.users_data.teams

        # Get user list
        user_list = UserList.from_data(expected_users_data=expected_users_data,
                                       participant_list=participant_list,
                                       teams=expected_teams)

        # Get msls from user list.
        msls = user_list.get_msls()

        return msls


class WebMSLManager(object):
    def __init__(self):
        self.web = WebControl()
        self.msl_manager = MSLManager()


class MSLParser(object):
    def __init__(self, web_control_factory,):
        self.msl_manager = MSLManager()
        self.web_control = None
        self.web_control_factory = web_control_factory

    def get_web_control(self):
        if not self.web_control:
            self.web_control = self.web_control_factory()

        return self.web_control

    def open_new(self, args):
        self.get_web_control().open_new(args.url)
        print("Opening url {}...".format(args.url))

    def open_zoom(self, args):
        self.get_web_control().open_zoom(args.room)

    def switch_tab(self, args):
        self.get_web_control().switch_tab(args.tab_index)

    def load_users(self, args):
        self.msl_manager.load_users(args.file_path)

    def reset_tab(self, _):
        self.get_web_control().reset_tab()

    def get_status(self, args):
        # If file given use it, otherwise use web.
        if args.html_file_path:
            html_source = args.html_file_path
        else:
            html_source = self.get_web_control()

        msls = self.msl_manager.get_status(team=args.team,
                                           group=args.group,
                                           html_source=html_source,
                                           users_file_path=args.users_file_path)

        output = "\n".join([repr(msl) for msl in msls])

        if output:
            print(output)
            # If output file path was given - save output to it.
            if args.output_file_path:
                io.open(args.output_file_path, "w", encoding="utf-8").write(output)

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
        get_status_parent_parser.add_argument("-m", "--html-file-path")
        get_status_parent_parser.add_argument("-u", "--users-file-path")
        get_status_parent_parser.add_argument("-o", "--output-file-path")

        parser = subparsers.add_parser("get_status", parents=[get_status_parent_parser])
        parser.set_defaults(func=self.get_status)

        args = main_parser.parse_args(raw_args)

        return args

    def execute(self, raw_args):
        args = self.parse_args(raw_args)
        args.func(args)
        print("Done!")

    def safe_execute(self, raw_args):
        try:
            self.execute(raw_args)
        except (Exception, SystemExit) as e:
            if isinstance(e, KeyboardInterrupt):
                print("Keyboard interrupt!")
                raise KeyboardInterrupt()
            else:
                traceback.print_exc()

    def start(self):
        user_input = ""
        while user_input != "exit":
            if user_input:
                self.safe_execute(user_input.split())
            user_input = input("==> ")


def main():
    program_args = sys.argv[1:]

    # If arguments were given - execute command. Otherwise - enter interactive mode.
    if program_args:
        MSLParser(WebControl.factory).execute(program_args)
    else:
        MSLParser(WebControl.factory).start()


if __name__ == "__main__":
    main()
