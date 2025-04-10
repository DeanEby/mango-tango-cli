import sys
from multiprocessing import freeze_support

from analyzers import suite
from app import App, AppContext
from components import ViewContext, main_menu, splash
from storage import Storage
from terminal_tools import enable_windows_ansi_support
from terminal_tools.inception import TerminalContext

if __name__ == "__main__":
    freeze_support()
    enable_windows_ansi_support()
    storage = Storage(app_name="MangoTango", app_author="Civic Tech DC")
    if "--noop" in sys.argv or "/noop" in sys.argv:
        print("No-op flag detected. Exiting successfully.")
        sys.exit(0)

    splash()
    main_menu(
        ViewContext(
            terminal=TerminalContext(),
            app=App(context=AppContext(storage=storage, suite=suite)),
        )
    )
