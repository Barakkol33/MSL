from selenium import webdriver
import os
import yaml

TEXT = """
dropdown-toggle btn btn-default"><div class="more-button__img-layer"><span class="more-button__more-icon"></span></div><div class="more-button__button-label">More</div></button><ul role="menu" class="more-button__pop-menu dropdown-menu" aria-labelledby="moreButton"><li role="presentation" class=""><a aria-label="Disable video receiving" role="menuitem" tabindex="-1" href="#">Disable video receiving</a></li></ul></div></div></div><div><button class="footer__leave-btn ax-outline" type="button">Leave Meeting</button></div></footer></div><div id="wc-container-right" style="width: 400px;"><div><div><div role="presentation" class="participants-header__header"><div class="dropdown btn-group"><button aria-label="Manage Chat Panel" id="participantSectionMenu" role="button" aria-haspopup="true" aria-expanded="false" type="button" class="participants-header__participants-pop-btn ax-outline-blue-important dropdown-toggle btn btn-default"></button><ul role="menu" class="participants-header__dropdown-menu dropdown-menu" aria-labelledby="participantSectionMenu"><li role="presentation" class="participants-header__menu"><a role="menuitem" tabindex="-1" href="#"><i class="participants-header__close-icon"></i>Close</a></li><li role="presentation" class="participants-header__menu"><a role="menuitem" tabindex="-1" href="#"><i class="participants-header__pop-out-icon"></i>Pop Out</a></li></ul></div><div class="participants-header__title"><span>Participants (3)</span></div></div><div><section data-scrollbar="true" tabindex="0" class="participant-scrollbar" style="height: 629px; overflow: hidden;" role="application" aria-label="participant list"><div class="scroll-content"><div><ul class="participants-ul"><li role="application" id="participants-list-0" class="item-pos participants-li " tabindex="-1" aria-label="User1 (Me) no audio connected video off     "><div class="participants-item__item-layout"><div class="participants-item__left-section"><img class="participants-item__avatar" src="https://us04images.zoom.us/p/t928RzpISLqY2rFK3tC2uA/cdf9754e-68a7-471c-9c91-3ca4fe1242b5-3233" alt="" aria-hidden="true"><span class="participants-item__name-section"><span class="participants-item__display-name" style="max-width: 283.333px;">User1</span><span class="participants-item__name-label">(Me)</span></span></div><span class="participants-item__right-section"><div class="participants-icon__icon-box"><i class="participants-icon__participant-video--stopped participants-icon__participant-video"></i></div></span></div></li><li role="application" id="participants-list-1" class="item-pos participants-li " tabindex="-1" aria-label="Barak Kolnik (Host) computer audio muted video off     "><div class="participants-item__item-layout"><div class="participants-item__left-section"><img class="participants-item__avatar" src="https://us04images.zoom.us/p/t928RzpISLqY2rFK3tC2uA/cdf9754e-68a7-471c-9c91-3ca4fe1242b5-3233?type=large" alt="" aria-hidden="true"><span class="participants-item__name-section"><span class="participants-item__display-name" style="max-width: 248.85px;">Barak Kolnik</span><span class="participants-item__name-label">(Host)</span></span></div><span class="participants-item__right-section"><div class="participants-icon__icon-box"><i class="participants-icon__participants-unmute"></i></div><div class="participants-icon__icon-box"><i class="participants-icon__participant-video--stopped participants-icon__participant-video"></i></div></span></div></li><li role="application" id="participants-list-2" class="item-pos participants-li " tabindex="-1" aria-label="Barak Kolnik  no audio connected video off     "><div class="participants-item__item-layout"><div class="participants-item__left-section"><img class="participants-item__avatar" src="https://us04images.zoom.us/p/t928RzpISLqY2rFK3tC2uA/cdf9754e-68a7-471c-9c91-3ca4fe1242b5-3233" alt="" aria-hidden="true"><span class="participants-item__name-section"><span class="participants-item__display-name" style="max-width: 308px;">Barak Kolnik</span><span class="participants-item__name-label"></span></span></div><span class="participants-item__right-section"><div class="participants-icon__icon-box"><i class="participants-icon__participant-video--stopped participants-icon__participant-video"></i></div></span></div></li></ul></div></div><div class="scrollbar-track scrollbar-track-x" style="display: none;"><div class="scrollbar-thumb scrollbar-thumb-x" style="width: 392px; transform: translate3d(0px, 0px, 0px);"></div></div><div class="scrollbar-track scrollbar-track-y" style="display: none;"><div class="scrollbar-thumb scrollbar-thumb-y" style="height: 629px; transform: translate3d(0px, 0px, 0px);"></div></div></section></div></div><div class="participants-section-container__participants-footer"><div class="participants-section-container__participants-footer-bottom"><button type="button" class="ax-outline-blue-important btn btn-sm btn-default">Invite</button><button type="button" class="btn btn-sm btn-default">Raise hand</button><button type="button" class="ax-outline-blue-important btn btn-sm btn-default">Reclaim Host</button></div></div></div></div></div></div></div></div></div>
"""

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
        pass

    def open_zoom(self, zoom_room_number):
        pass

    def switch_tab(self, tab_index):
        pass

    def reset_tab(self):
        pass

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
        self.users_data = UsersData.from_file(users_file_path)

    def check(self, team="", group=""):

        # Get participant list
        zoom_meeting_html = self.web.get_page_source()
        participant_list = ParticipantList.from_page_source(zoom_meeting_html)

        # Get expected users data.
        if team:
            expected_users_data = self.users_data.get_by_team(team)
        elif group:
            expected_users_data = self.users_data.get_by_group(group)
        else:
            expected_users_data = self.users_data.get_all()

        # Get user list
        user_list = UserList.from_data(expected_users_data, participant_list)

        return user_list

    def start(self):
        a = 3


def test():
    msl = MSL(WebControlStub())
    msl.load_users(os.path.join("tests", "users.yml"))
    user_list = msl.check()
    print(user_list)


def main():
    test()


if __name__ == "__main__":
    main()

"""
Start
open_current -u <url>
open_new -u <url>
open_existing -u <url> -i <index>
open_zoom -z zoom_room_number
switch_tab <index>
load_users <file_path>
get_status [-t <team>] [-g <group>] [-a] -s [{names,teams,group}]
save 


TODO: when loading - check that there are no 2 identical nicknames
TODO: Remove (Host) and (Me) 
"""
