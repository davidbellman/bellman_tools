from bellman_tools import sql_tools,scheduler_tools

def test_opening_one_command_window():
    """
    Test that opening one command window works without errors.
    """
    TSM = scheduler_tools.TaskSchedulerManager(sql_tools.Sql())
    TSM.run_scheduler_in_loop()



if __name__ == '__main__':
    test_opening_one_command_window()