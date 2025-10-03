import datetime
from idlelib.configdialog import ConfigDialog

from schedule import Scheduler
import subprocess
import threading
import os, sys
import getpass, socket
import pandas as pd
import uuid
import time
import random
from dotenv import load_dotenv

# Load .env only from the current working directory (user's working dir).
# Best practice is to let the application load env vars; this is a convenience fallback.
_cwd_env = os.path.join(os.getcwd(), ".env")
if os.path.isfile(_cwd_env):
    load_dotenv(_cwd_env, override=False)
else:
    print(f"No .env file found in current directory: {os.getcwd()}")

from bellman_tools import sql_tools,upload_tools
from bellman_tools.database import (
    Task_Scheduled,
    Log_Task_Scheduler,
    Task_Scheduler_Heartbeat,
)


class TaskSchedulerHeartBeat:

    def __init__(self, sql: sql_tools.Sql):
        self.session_id = str(int(datetime.datetime.now().timestamp() * 1000000))
        self.user = getpass.getuser()
        self.host = socket.gethostname()
        self.is_prod = not (bool(getattr(sys, "gettrace", None)()))
        self.sql = sql

    def save_heartbeat(self):

        new_entry = Task_Scheduler_Heartbeat.Task_Scheduler_Heartbeat(
            SessionID=self.session_id,
            IsProd=self.is_prod,
            InsertedAt=datetime.datetime.now(),
            InsertedBy=self.user,
            InsertedHost=self.host,
        )

        self.sql.add_to_session_and_commit(new_entry)

    def is_another_previous_heartbeat_session_running(self, last_x_minutes=3):
        list_session = self.get_other_heartbeat_running_list(
            last_x_minutes=last_x_minutes
        )
        if len(list_session) > 0:
            # see comment on the next function next_heartbeat_session
            return any([each < self.session_id for each in list_session])
        else:
            return False

    def is_another_next_heartbeat_session_running(
        self,
        heartbeat_table_in_last_x_minutes: int = 3,
        heartbeat_in_log_task_scheduler_in_last_x_minutes: int = 60 * 24,
    ):
        list_session = self.get_other_heartbeat_running_list(
            last_x_minutes=heartbeat_table_in_last_x_minutes
        )
        if len(list_session) > 0:
            # If none of the other session ID that run has a higher number
            # I want to keep the new python scheduler and stop the old one (because for Wanjun case the code may have been updated)
            another_heartbeat_more_recent_is_running = any(
                [each > self.session_id for each in list_session]
            )
        else:
            another_heartbeat_more_recent_is_running = False

        # Todo : refactor to make it clearer in 2 different methods and group those 2 at the end
        list_session_task_scheduler = (
            self.get_other_heartbeat_running_list_from_task_scheduler(
                last_x_minutes=heartbeat_in_log_task_scheduler_in_last_x_minutes
            )
        )
        if len(list_session_task_scheduler) > 0:
            another_heartbeat_task_scheduler_more_recent_is_running = any(
                [each > self.session_id for each in list_session_task_scheduler]
            )
        else:
            another_heartbeat_task_scheduler_more_recent_is_running = False

        return (
            another_heartbeat_more_recent_is_running
            or another_heartbeat_task_scheduler_more_recent_is_running
        )

    def get_other_heartbeat_running_list(self, last_x_minutes: int):
        start_datetime = datetime.datetime.now() - datetime.timedelta(
            minutes=last_x_minutes
        )
        sql_query = f"""
			SELECT * FROM Task_Scheduler_Heartbeat 
			WHERE InsertedBy = '{self.user}' 
				AND InsertedHost = '{self.host}' 
				AND SessionID != '{self.session_id}' 
				AND InsertedAt >= '{start_datetime.strftime('%Y-%m-%d %H:%M:%S')}'
		"""
        df = self.sql.load_dataframe_from_query(sql_query)
        if df is None or len(df) == 0:
            return []
        else:
            return list(set(df["SessionID"].tolist()))

    def get_other_heartbeat_running_list_from_task_scheduler(self, last_x_minutes: int):
        start_datetime = datetime.datetime.now() - datetime.timedelta(
            minutes=last_x_minutes
        )
        sql_query = f"""
			SELECT * FROM Log_Task_Scheduler 
			WHERE InsertedBy = '{self.user}' 
				AND InsertedHost = '{self.host}' 
				AND HeartbeatID != '{self.session_id}' 
				AND InsertedAt >= '{start_datetime.strftime('%Y-%m-%d %H:%M:%S')}'
		"""
        df = self.sql.load_dataframe_from_query(sql_query)
        if df is None or len(df) == 0:
            return []
        else:
            return list(set(df["HeartbeatID"].tolist()))


class SafeScheduler(Scheduler):
    """
    An implementation of Scheduler that catches jobs that fail, logs their
    exception tracebacks as errors, optionally reschedules the jobs for their
    next run time, and keeps going.
    Use this to run jobs that may or may not crash without worrying about
    whether other jobs will run or if they'll crash the entire script.
    """

    def __init__(self, reschedule_on_failure=False, heartbeat_id=None):
        """
        If reschedule_on_failure is True, jobs will be rescheduled for their
        next run as if they had completed successfully. If False, they'll run
        on the next run_pending() tick.
        """
        self.heartbeat_id = heartbeat_id
        self.reschedule_on_failure = reschedule_on_failure
        super().__init__()

    def _run_job(self, job):
        try:
            super()._run_job(job)
        except Exception as e:
            print("ERROR1456: ", e)

            job.last_run = datetime.datetime.now()
            job._schedule_next_run()


def new_console_conda(
    func_file_name: str,
    script_folder: str,
    lib_path: str,
    conda_activate_path: str,
    conda_env_name: str,
):
    return subprocess.call(
        [
            "Task_Scheduler_Launcher.bat",
            func_file_name,
            f"{lib_path}\\{script_folder}\\",
            conda_activate_path,
            conda_env_name
        ],
        creationflags=subprocess.CREATE_NEW_CONSOLE,
        cwd=lib_path,  # config_path.LIB_PATH_TASK_SCHEDULER,
    )

class TaskSchedulerManager:

    def __init__(self, sql: sql_tools.Sql):
        self.sql = sql
        self.upload = upload_tools.Upload(sql=sql)

        self.CONDA_ACTIVATE_BIN_PATH = os.getenv("CONDA_ACTIVATE_BIN_PATH")
        if not self.CONDA_ACTIVATE_BIN_PATH:
            raise RuntimeError(
                "Missing env var CONDA_ACTIVATE_BIN_PATH. Define it in your environment or .env"
            )

        self.CONDA_ENV_NAME = os.getenv("CONDA_ENV_NAME")
        if not self.CONDA_ENV_NAME:
            raise RuntimeError(
                "Missing env var CONDA_ENV_NAME. Define it in your environment or .env"
            )

        self.heartbeat = TaskSchedulerHeartBeat(sql=self.sql)
        self.schedule = SafeScheduler(heartbeat_id=self.heartbeat.session_id)


    def get_task_asap(self):
        df_asap = self.sql.load_dataframe_from_query(
            f"""
                SELECT * FROM Task_Scheduler
                WHERE RunBy = '{getpass.getuser().lower()}'
                AND RunHost = '{socket.gethostname()}'
                AND ToRunAsap = 1
            """
        )
        df_asap_enabled = df_asap[df_asap.Enable.eq(True)]

        # Check if any disabled scripts are set to ASAP and warn if so
        df_conflicting = df_asap[df_asap.Enable.eq(False)]

        if not df_conflicting.empty:
            print(
                f"WARN: Disabled script set as ASAP {df_conflicting.ScriptName.to_list()}"
            )

        return df_asap_enabled


    def get_tasks_from_db(self):
        try:
            df_asap = self.get_task_asap()
            if len(df_asap) == 0:
                sql_query = f"""
                        SELECT * FROM Task_Scheduler
                        WHERE RunBy = '{getpass.getuser().lower()}'
                        AND RunHost = '{socket.gethostname()}'
                        AND Enable = 1
                    """
                df = self.sql.load_dataframe_from_query(sql_query)
                return df.to_dict("records")
            else:
                return df_asap.to_dict("records")

        except Exception as e:
            print(e)
            return {}


    def log_task_scheduler_window(self, file_name, is_prod=None, heartbeat_id=None):

        try:
            new_entry = Log_Task_Scheduler.Log_Task_Scheduler(
                ScriptFile=file_name,
                InsertedAt=datetime.datetime.now(),
                Status="Run",
                SessionID="From_Python_Scheduler",
                IsProd=is_prod,
                InsertedBy=getpass.getuser(),
                InsertedHost=socket.gethostname(),
                HeartbeatID=heartbeat_id,
            )
            # print(new_entry)
            self.sql.add_to_session_and_commit(new_entry)

        except Exception as e:
            try:
                print("There was an exception in the Insert Log_Task_Scheduler")
            except Exception as e:
                print("Nothing else to do here mate")


    def run_threaded_file_name(
        self, func_file_name, script_folder, remove_asap=False, **args
    ):

        print("Running file : ", func_file_name)
        # Todo : pass the heartbeat here and then to the task_scheduler
        heartbeat_id = args.get("heartbeat_id")
        self.log_task_scheduler_window(
            file_name=func_file_name,
            is_prod=not (bool(getattr(sys, "gettrace", None)())),
            heartbeat_id=heartbeat_id,
        )
        job_thread = threading.Thread(
            target=new_console_conda,
            args=(
                func_file_name,
                script_folder,
                "",
                self.CONDA_ACTIVATE_BIN_PATH,
                self.CONDA_ENV_NAME,
            ),
        )
        job_thread.start()

        if remove_asap:
            sql_query = f"""
                    SELECT * FROM Task_Scheduler 
                    WHERE RunBy = '{getpass.getuser().lower()}' 
                        AND ToRunAsap = 1 
                        AND ScriptName = '{func_file_name}' 
                        AND ScriptFolder = '{script_folder}'
                """
            df_task_to_cancel = self.sql.load_dataframe_from_query(
                sql_query=sql_query
            )
            for index, row in df_task_to_cancel.iterrows():
                sql_update = sql_tools.update_sql_query_for_id(
                    table_name="Task_Scheduler",
                    dico_name_value=dict(ToRunAsap=0),
                    id=row["ID"],
                )
                print(sql_update)
                self.sql.execute_sql(sql_update)

    def weekday_job(self,schedule, job, script_folder, at=None, heartbeat_id=None):
        schedule.every().monday.at(at).do(self.run_threaded_file_name, job, script_folder, heartbeat_id=heartbeat_id).tag(schedule.heartbeat_id)
        schedule.every().tuesday.at(at).do(self.run_threaded_file_name, job, script_folder, heartbeat_id=heartbeat_id).tag(schedule.heartbeat_id)
        schedule.every().wednesday.at(at).do(self.run_threaded_file_name, job, script_folder, heartbeat_id=heartbeat_id).tag(schedule.heartbeat_id)
        schedule.every().thursday.at(at).do(self.run_threaded_file_name, job, script_folder, heartbeat_id=heartbeat_id).tag(schedule.heartbeat_id)
        schedule.every().friday.at(at).do(self.run_threaded_file_name, job, script_folder, heartbeat_id=heartbeat_id).tag(schedule.heartbeat_id)


    def dico_tasks_to_scheduler_task(self, dico_tasks, heartbeat_id: str = None):

        # Todo : all that bellow need to be redone in an Object, so it can easily associate tags and heartbeat_id - we had a nice run tho

        for task in dico_tasks:

            # if True:
            try:
                script_name = task.get("ScriptName", None)
                script_folder = task.get("ScriptFolder", None)
                every = task.get("Every", None)
                at = task.get("AtTime", None)
                is_enable = task.get("Enable", False)
                to_run_asap = task.get("ToRunAsap", False)

                schedule = self.schedule

                if is_enable is False:
                    continue

                if to_run_asap:
                    # in_a_minute = (datetime.datetime.now()+datetime.timedelta(minutes=1)).strftime('%H:%M')
                    # schedule.every.day.at(in_a_minute).do(scheduler_tools.run_threaded_file_name, script_name, script_folder, True, engine=engine, heartbeat_id=heartbeat_id).tag(schedule.heartbeat_id)
                    self.run_threaded_file_name(
                        func_file_name=script_name,
                        script_folder=script_folder,
                        remove_asap=True,
                        heartbeat_id=heartbeat_id,
                    )
                elif every == "weekday":
                    self.weekday_job(schedule=schedule,job=script_name,script_folder=script_folder,at=at,heartbeat_id=heartbeat_id)
                elif every == "day":
                    schedule.every().day.at(at).do(self.run_threaded_file_name, script_name, script_folder, heartbeat_id=heartbeat_id).tag(schedule.heartbeat_id)
                elif every == "monday":
                    schedule.every().monday.at(at).do(self.run_threaded_file_name, script_name, script_folder, heartbeat_id=heartbeat_id).tag(schedule.heartbeat_id)
                elif every == "tuesday":
                    schedule.every().tuesday.at(at).do(self.run_threaded_file_name, script_name, script_folder, heartbeat_id=heartbeat_id).tag(schedule.heartbeat_id)
                elif every == "wednesday":
                    schedule.every().wednesday.at(at).do(self.run_threaded_file_name, script_name, script_folder, heartbeat_id=heartbeat_id).tag(schedule.heartbeat_id)
                elif every == "thursday":
                    schedule.every().thursday.at(at).do(self.run_threaded_file_name, script_name, script_folder, heartbeat_id=heartbeat_id).tag(schedule.heartbeat_id)
                elif every == "friday":
                    schedule.every().friday.at(at).do(self.run_threaded_file_name, script_name, script_folder, heartbeat_id=heartbeat_id).tag(schedule.heartbeat_id)
                elif every == "saturday":
                    schedule.every().saturday.at(at).do(self.run_threaded_file_name, script_name, script_folder, heartbeat_id=heartbeat_id).tag(schedule.heartbeat_id)
                elif every == "sunday":
                    schedule.every().sunday.at(at).do(self.run_threaded_file_name, script_name, script_folder, heartbeat_id=heartbeat_id).tag(schedule.heartbeat_id)
                elif every == "day":
                    schedule.every().day.at(at).do(self.run_threaded_file_name, script_name, script_folder, heartbeat_id=heartbeat_id).tag(schedule.heartbeat_id)
                elif every == "minutes":
                    schedule.every(int(at)).minutes.do(self.run_threaded_file_name, script_name, script_folder, heartbeat_id=heartbeat_id).tag(schedule.heartbeat_id)
                elif every == "hours":
                    schedule.every(int(at)).hours.do(self.run_threaded_file_name, script_name, script_folder, heartbeat_id=heartbeat_id).tag(schedule.heartbeat_id)
                elif every == "seconds":
                    schedule.every(int(at)).seconds.do(self.run_threaded_file_name, script_name, script_folder, heartbeat_id=heartbeat_id).tag(schedule.heartbeat_id)
                elif every == "every_day_hour":
                    for i in [f"0{i}:00" if i < 10 else f"{i}:50" for i in range(0, 24, 1)]:
                        schedule.every().day.at(i).do(self.run_threaded_file_name, script_name, script_folder, heartbeat_id=heartbeat_id).tag(schedule.heartbeat_id)
                elif every == "every_4_hour":
                    for i in [f"0{i}:00" if i < 10 else f"{i}:00" for i in range(0, 24, 4)]:
                        schedule.every().day.at(i).do(self.run_threaded_file_name, script_name, script_folder, heartbeat_id=heartbeat_id).tag(schedule.heartbeat_id)

            except Exception as e:
                print("ERROR1454: ", e)


    def print_jobs_in_schedule(
        self,
        only_next_task=None
    ):
        list_jobs = self.schedule.get_jobs()
        list_tuple_jobs = [(job.next_run, job) for job in list_jobs]
        list_tuple_jobs.sort()

        print(
            f"Displaying {'all' if only_next_task is None else only_next_task} next jobs : "
        )

        if only_next_task is None:
            for next_run, job in list_tuple_jobs:
                print(
                    f"Job : {job} At time : {job.at_time} Last Run : {job.last_run} Next Run {job.next_run}"
                )
        else:
            for i in range(min(len(list_tuple_jobs), only_next_task)):
                next_run, job = list_tuple_jobs[i]
                print(
                    f"Job : {job} At time : {job.at_time} Last Run : {job.last_run} Next Run {job.next_run}"
                )


    def get_df_scheduled_jobs(
        self,
        run_by=getpass.getuser().lower(),
        run_host=socket.gethostname()
    ):
        list_jobs = self.schedule.get_jobs()
        list_tuple_jobs = [(job.next_run, job) for job in list_jobs]
        list_tuple_jobs.sort()

        list_all_jobs = []
        for next_run, job in list_tuple_jobs:
            res = dict(
                RunBy=run_by,
                RunHost=run_host,
                NextRun=job.next_run,
                ScriptName=job.job_func.args[0],
                ScriptFolder=job.job_func.args[1],
                HeartbeatID=None if len(job.tags) == 0 else str(next(iter(job.tags))),
            )
            list_all_jobs.append(res)

        df = pd.DataFrame(list_all_jobs)

        return df



    def save_scheduled_job_to_db(self):

        # Only issue with this approch, is that if someone scheduler is not running, we won't saved either the scheduled job.
        df  = self.get_df_scheduled_jobs()
        # Controversial : ignoring HeartbeatID, but will assume, the scheduler at not getting re-run every day
        self.upload.load_basic_df_to_db(
            df_incoming=df,
            SQL_Alchemy_Table=Task_Scheduled.Task_Scheduled,
            check_with_existing=True,
            extra_col_to_ignore=['HeartbeatID'],
            str_existing_query="SELECT * FROM Task_Scheduled WHERE InsertedAt >= GETDATE()-5"
        )


    def run_scheduler_in_loop(self):

        # Adding a little bit of randomness at the begining, to be sure,
        # in case 2 script run at the same second,
        # the sessionID is going to be different

        time.sleep(random.randint(0, 1000000) / 1000000)

        heartbeat = self.heartbeat
        schedule = self.schedule

        running = True
        another_instance_is_running = 0
        while running:

            print("\nRun time : ", datetime.datetime.now())

            heartbeat.save_heartbeat()

            if not heartbeat.is_another_next_heartbeat_session_running(
                heartbeat_table_in_last_x_minutes=3,
                heartbeat_in_log_task_scheduler_in_last_x_minutes=60 * 24,
            ):

                print("Load all the Task Scheduler")
                print("SessionID : ", heartbeat.session_id)

                # Get Tasks from DB
                dico_tasks = self.get_tasks_from_db()

                self.dico_tasks_to_scheduler_task(
                    dico_tasks, heartbeat_id=heartbeat.session_id
                )
                self.print_jobs_in_schedule(only_next_task=4)
                self.save_scheduled_job_to_db()

                for i in range(60):
                    try:
                        schedule.run_pending()
                    except Exception as e:
                        print("ERROR1455 : ", e)
                    time.sleep(1)

                time.sleep(1)
                # print('Cancelling temporarily all jobs...')
                schedule.clear()

                another_instance_is_running = 0

            else:
                print("BE AWARE (and report to quant) : Another scheduler is running")
                print("SessionID : ", heartbeat.session_id)
                time.sleep(60)
                another_instance_is_running += 1
                print("# Try another session running ", another_instance_is_running)
                if another_instance_is_running >= 5:
                    return


def RunDashboard(port=5000, debug=False, sql=None):
    """
    Launch the Task Scheduler Dashboard
    
    This function creates and launches a web-based dashboard for monitoring
    and managing scheduled tasks.
    
    Args:
        port (int): Port to run the dashboard on (default: 5000)
        debug (bool): Run Flask in debug mode (default: False)
        sql (Sql): SQL connection object (optional, will create one if not provided)
    
    Example:
        >>> from bellman_tools import scheduler_tools
        >>> scheduler_tools.RunDashboard(port=5000)
        
        # Or with custom SQL connection
        >>> from bellman_tools import sql_tools, scheduler_tools
        >>> sql = sql_tools.Sql(db='YourDatabase')
        >>> scheduler_tools.RunDashboard(port=5000, sql=sql)
    """
    from bellman_tools.dashboard import RunDashboard as _RunDashboard
    _RunDashboard(port=port, debug=debug, sql=sql)


if __name__ == "__main__":
    pass
