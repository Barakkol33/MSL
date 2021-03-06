# Testing
import os

import msl


class WebControlStub(object):
    def __init__(self, source_html_file):
        self.source_html_file = source_html_file

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
        return open(self.source_html_file).read()


class Tests(object):
    @staticmethod
    def check_throws(exception, func, *args, **kwargs):
        try:
            func(*args, **kwargs)
            return False
        except exception:
            return True

    @classmethod
    def commands_tests(cls):
        def stub_web_control_factory():
            return WebControlStub("tests/avengers.html")

        msl_parser = msl.MSLParser(stub_web_control_factory)
        msl_parser.execute("open_new -u https://google.com".split())

        msl_parser.execute("open_zoom -r 12345".split())

        msl_parser.execute("load_users -f tests/avengers.yml".split())
        cls.check_throws(ValueError, msl_parser.execute, "load_users -f tests/users_invalid_file.yml".split())
        msl_parser.execute("load_users -f users.yml".split())

        msl_parser.execute("switch_tab -i 12345".split())

        msl_parser.execute("reset_tab".split())

        msl_parser.execute("get_status -u tests/avengers.yml -m tests/avengers.html".split())
        msl_parser.execute("get_status -u tests/avengers.yml -t A2".split())
        msl_parser.execute("get_status -u tests/avengers.yml -g B".split())
        msl_parser.execute("get_status -u tests/avengers.yml -o tests/avengers_test_output.txt".split())

        # Checking error - Getting status before settings users
        cls.check_throws(RuntimeError, msl.MSLParser(stub_web_control_factory).execute, "get_status -m tests/avengers.html".split())

    @staticmethod
    def try1():
        msl_parser = msl.MSLParser(msl.WebControl.factory)
        msl_parser.execute("get_status -g B -u users.yml -m samples/course2.html".split())

    @staticmethod
    def logic_test():
        m = msl.MSLManager(WebControlStub())
        m.load_users(os.path.join("tests", "users.yml"))
        user_list = m.get_status()
        print(user_list)


def main():
    #Tests.commands_tests()
    Tests.try1()


if __name__ == "__main__":
    main()
