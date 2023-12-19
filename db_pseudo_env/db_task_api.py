import requests
import time
import uuid

server_url = "http://127.0.0.1:5000"

def send_task(task_content):
    task_id = str(uuid.uuid4())
    response = requests.post(f"{server_url}/task", json={"task_id": task_id, "task_content": task_content})
    if response.status_code == 200:
        print(f"Text sent successfully, check the {server_url}/task.")
        return task_id
    else:
        print(f"Failed to send text:{response.status_code}")
        return None

def get_reply(task_id):
    while True:
        response = requests.get(f"{server_url}/result", params={"task_id": task_id})
        if response.status_code == 200:
            reply = response.json()['response']
            if reply != 'No reply yet':
                print(f"Reply: {reply}")
                break
        time.sleep(5)
    return response


def Assign_DB_Task(task_content):
    task_id = send_task(task_content)
    if task_id:
        response = get_reply(task_id)
        print(response.json())
    else:
        return "Failed to assign task"
    return response.json()
    
    

# Example usage
Example = """
I have a specific task interacting with a database environment that involves executing a SELECT query within a relational database. 
The database consists of two tables: Employees, which includes columns for EmployeeID (integer), Name (varchar), and DepartmentID (integer); 
and Departments, containing DepartmentID (integer) and DepartmentName (varchar). 
The task is to retrieve the names of employees who work in the 'IT' department. 
This requires a JOIN operation between the Employees and Departments tables on the DepartmentID column, along with a WHERE clause to filter for 'IT' in the DepartmentName column. 
The expected outcome is a list of names of employees in the IT department. 
A key aspect of this task is optimizing the query for performance due to the large number of rows in both tables.
"""

Assign_DB_Task(Example) 
