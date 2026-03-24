# Standard Library Imports
import subprocess
import importlib.util
import sys
import threading

# Third-party imports
import tkinter as tk
from tkinter import messagebox

# Local application imports
from utils.app_logging import LogLevel


class DependencyManager:
    def __init__(self, parent, controller, required_modules):
        self.parent = parent
        self.controller = controller
        self.required_modules = required_modules
        self._cancel_install = False

    def handle_missing_dependencies(self):
        # Separate the dependencies that aren't installed
        missing_modules = [mod for mod in self.required_modules if importlib.util.find_spec(mod) is None]

        # There might be no missing dependencies, if so return success
        if not missing_modules:
            return True

        if messagebox.askyesno(
                "Missing Dependencies",
                f"The following dependencies are missing:\n\n"
                f"{', '.join(missing_modules)}\n\n"
                "Would you like to install them now?"
        ):
            # Try to install each dependency with the user's permission.
            installed_modules = []

            # Show progress window.
            self._show_progress_popup(len(missing_modules))

            # Define the thread.
            def do_installs():
                try:
                    for idx, mod in enumerate(missing_modules, start=1):
                        # Check if a cancel has happened before downloading next module.
                        if self._cancel_install:
                            raise RuntimeError("Installation cancelled by user.")

                        # Install the module
                        subprocess.check_call(
                            [sys.executable, "-m", "pip", "install", mod],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL  # Suppress pip updates
                        )

                        self.controller.log(LogLevel.INFO, f"Installed missing module: {mod}")
                        installed_modules.append(mod)

                        # Ensure UI update happens in main thread
                        # Schedule progress indicator update
                        self.controller.after(0, self._update_progress_label, idx, len(missing_modules))

                    # Check if a cancel has happened after downloading everything.
                    if self._cancel_install:
                        raise RuntimeError("Installation cancelled by user.")

                # In the event of ANY error, we must roll back previous installs
                except Exception as e:
                    # Use an if statement instead of declaring mod before try
                    # because we want to add or remove a space at the end.
                    self.controller.log(
                        LogLevel.ERROR,
                        f"Failed to install{f' {mod}' if 'mod' in locals() else ''}: {e}"
                    )

                    # Iterate through each module already installed and uninstall them.
                    for installed in installed_modules[::-1]:
                        try:
                            # Attempt to uninstall module
                            subprocess.check_call(
                                [sys.executable, "-m", "pip", "uninstall", "-y", installed],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL
                            )
                            self.controller.log(LogLevel.WARN, f"Rolled back module: {installed}")

                        # Notify the user if we fail to uninstall a module then carry on.
                        except Exception as uninstall_error:
                            self.controller.log(LogLevel.ERROR, f"Failed to roll back {installed}: {uninstall_error}")

                # Schedule to close progress window.
                finally:
                    self.controller.after(0, self._progress_popup.destroy)

            # Create and start installer daemon.
            install_thread = threading.Thread(target=do_installs, daemon=True)
            install_thread.start()

            # Pause main thread until progress window closes.
            self.controller.wait_window(self._progress_popup)

            # Tell the handler the download was cancelled if it was.
            if self._cancel_install:
                return False

        # If the user declined the download
        else:
            self.controller.log(LogLevel.WARN, "User declined to install missing dependencies.")
            return False  # Tell the handler the download was cancelled.

        # Successful download
        return True

    def _show_progress_popup(self, total_modules):
        # Reset cancelled flag
        self._cancel_install = False

        # Create window.
        self._progress_popup = tk.Toplevel(self.parent)

        # Configure window
        self._progress_popup.title("Installing Dependencies")
        self._progress_popup.grab_set()  # User can't interact with main window until the window closes.

        # Labels and progress bar
        tk.Label(self._progress_popup, text="Installing missing dependencies...").pack(pady=(10, 5))
        self._progress_label = tk.Label(self._progress_popup, text=f"0 / {total_modules}")
        self._progress_label.pack(pady=(0, 10))

        # Cancel button
        cancel_btn = tk.Button(self._progress_popup, text="Cancel", command=self._cancel_dependency_install)
        cancel_btn.pack(pady=(0, 10))

        # X button cancels the download too.
        self._progress_popup.protocol("WM_DELETE_WINDOW", self._cancel_dependency_install)

    def _update_progress_label(self, current, total):
        self._progress_label.config(text=f"{current} / {total}")

        # Move the UI update to the front of the event queue
        self._progress_label.update_idletasks()

    def _cancel_dependency_install(self):
        self._cancel_install = True
