import os
import subprocess
import time
from config import cfg
# from src.log import logger
from threading import Thread
import queue
from src.base import EdgiseBase
from multiprocessing import Queue, Event


class UpdateWatcher(Thread, EdgiseBase):
    def __init__(self, stop_event: Event, cmd_q: Queue, logging_q: Queue):
        self._stop_event = stop_event
        self._cmd_q = cmd_q
        Thread.__init__(self)
        EdgiseBase.__init__(self, name="UPDATE", logging_q=logging_q)

    def check_update(self):
        # Initialization
        branch = cfg.updateBranch
        cmd_git_diff = ['/usr/bin/git', 'diff', '--name-only', f'{branch}', f'origin/{branch}']
        cmd_git_pull = ['/usr/bin/git', 'pull']
        cmd_git_fetch = ['/usr/bin/git', 'fetch', '--all']
        cmd_git_branch = ['/usr/bin/git', 'branch']
        cmd_git_deploy = ['/usr/bin/git', 'checkout', branch]
        cmd_git_reset = ['/usr/bin/git', 'reset', '--hard']
        output_git_diff = 0

        # make sure we are on branch deploy
        try:
            os.chdir(cfg.root_dir)
            subprocess.Popen(cmd_git_reset)
            subprocess.Popen(cmd_git_fetch)
            subprocess.Popen(cmd_git_deploy)
        except Exception as e:
            self.error(f'GIT reset/fetch/deploy error : {e}')

        time.sleep(5)

        # Check if update is necessary
        try:
            output_git_diff = subprocess.check_output(cmd_git_diff)
        except Exception as e:
            self.error(f'GIT diff error : {e}')

        if len(output_git_diff) == 0:
            self.info('Branch is up to date')
        else:
            self.info('Branch needs pull')

            try:
                output_git_pull = subprocess.check_output(cmd_git_pull)
                self.info(output_git_pull)
                self.error("Device updated, can be restarted")
            except Exception as e:
                self.error(f'GIT pull error : {e}')

    def run(self) -> None:
        while not self._stop_event.is_set():

            time.sleep(0.1)
            cmd = ""
            try:
                cmd = self._cmd_q.get_nowait()
            except queue.Empty:
                pass

            if cmd == "UPDATE":
                if cfg.updateBranch:
                    self.info("Update command received")
                    self.check_update()
                
                else:
                    self.info(f"No update branch set, not updating")

        self.info(f"Quitting.")

