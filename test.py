# Testing
import os

import msl


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


class Tests(object):
    @staticmethod
    def commands_tests():
        msl_parser = msl.MSLParser(WebControlStub())
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
        msl.MSLParser(WebControlStub()).execute("get_status".split())

        msl_parser.execute("load_users -f tests/users_invalid_file.yml".split())

        msl_parser.execute("load_users -f users2.yml".split())

    @staticmethod
    def logic_test():
        m = msl.MSL(WebControlStub())
        m.load_users(os.path.join("tests", "users.yml"))
        user_list = m.get_status()
        print(user_list)


def main():
    Tests.commands_tests()


if __name__ == "__main__":
    main()
