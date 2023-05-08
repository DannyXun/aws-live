from flask import Flask, render_template, request
from decimal import Decimal
from pymysql import connections
import os
import boto3
from config import *

app = Flask(__name__)

bucket = custombucket
region = customregion

db_conn = connections.Connection(
    host=customhost,
    port=3306,
    user=customuser,
    password=custompass,
    db=customdb

)
output = {}
table = 'employee'


@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('index.html')

@app.route("/add", methods=['GET', 'POST'])
def add():
    select_sql = "Select emp_id from employee ORDER BY emp_id DESC LIMIT 1"
    cursor = db_conn.cursor()
    try:
        cursor.execute(select_sql)
        last_id = cursor.fetchone()
        last_id = last_id[0] + 1
    except Exception as e:
        last_id = 1
    finally:
        cursor.close()  
    return render_template('addemp.html', last_id = last_id)

@app.route("/search", methods=['GET', 'POST'])
def search():
    select_sql = "Select emp_id from employee"
    cursor = db_conn.cursor()
    cursor.execute(select_sql)
    employees = cursor.fetchall()
    cursor.close()  
    return render_template('searchemp.html', employees = employees)

@app.route("/attendance", methods=['GET', 'POST'])
def attendance():
    select_sql = "Select emp_id from employee"
    cursor = db_conn.cursor()
    cursor.execute(select_sql)
    employees = cursor.fetchall()
    cursor.close()  
    return render_template('attendance.html', employees = employees)

@app.route("/payroll", methods=['GET', 'POST'])
def payroll():
    select_sql = "Select emp_id from employee"
    cursor = db_conn.cursor()
    cursor.execute(select_sql)
    employees = cursor.fetchall()
    cursor.close()  
    return render_template('payroll.html', employees = employees)
    
@app.route("/sales", methods=['GET', 'POST'])
def sales():
    select_sql = "Select emp_id from employee"
    cursor = db_conn.cursor()
    cursor.execute(select_sql)
    employees = cursor.fetchall()
    cursor.close()  
    return render_template('sales.html', employees = employees)

@app.route("/portfolio", methods=['GET', 'POST'])
def portfolio(): 
    return render_template('portfolio_cx.html')
    
@app.route("/addemp", methods=['POST'])
def AddEmp():
    emp_id = request.form['emp_id_ref']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    pri_skill = request.form['pri_skill']
    emp_gender = request.form['gender']
    emp_birthdate = request.form['birthdate']
    location = request.form['location']
    hire_date = request.form['hire_date']
    job_role = request.form['emp_job']
    emp_dep = request.form['emp_dep']
    emp_office = request.form['emp_office']
    emp_pay = request.form['emp_pay']
    emp_image_file = request.files['emp_image_file']

    insert_sql = "INSERT INTO employee (first_name, last_name, pri_skill, emp_gender, emp_birthdate, location, hire_date, job_role, emp_dep, emp_office, emp_pay, img_src) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()

    if emp_image_file.filename == "":
        return "Please select a file"

    try:
        emp_name = "" + first_name + " " + last_name
        # Uplaod image file in S3 #
        file_extension = os.path.splitext(emp_image_file.filename)[1]
        emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file" + file_extension
        s3 = boto3.resource('s3')

        try:
            print("Data inserted in MySQL RDS... uploading image to S3...")
            s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3, Body=emp_image_file)
            bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
            s3_location = (bucket_location['LocationConstraint'])

            if s3_location is None:
                s3_location = ''
            else:
                s3_location = '-' + s3_location

            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                custombucket,
                emp_image_file_name_in_s3)

        except Exception as e:
            return str(e)

        cursor.execute(insert_sql, (first_name, last_name, pri_skill, emp_gender, emp_birthdate, location, hire_date, job_role, emp_dep, emp_office, emp_pay, object_url))
        db_conn.commit()
    finally:
        cursor.close()

    print("all modification done...")
    return render_template('addemp_output.html', emp_id = emp_id)

@app.route("/addattendance", methods=['POST'])
def AddAttendance():
    emp_id = request.form['emp_id']
    attendance_date = request.form['attendance_date']
    in_time = request.form['in_time']
    out_time = request.form['out_time']

    insert_sql = "INSERT INTO employee_attendance VALUES (%s, %s, %s, %s)"
    cursor = db_conn.cursor()


    try:
        cursor.execute(insert_sql, (emp_id, attendance_date, in_time, out_time))
        db_conn.commit()

    except Exception as e:
        return str(e)

    finally:
        cursor.close()

    return render_template('attendance_output.html', emp_id=emp_id, date = attendance_date)

@app.route("/search_emp", methods=['GET', 'POST'])
def Search_Emp():
    emp_id = request.form['emp_id2']
    select_sql = "SELECT * FROM employee WHERE emp_id = %s"
    cursor = db_conn.cursor()
    cursor.execute(select_sql, emp_id)
    employee = cursor.fetchone()
    if employee:
        emp_id, first_name, last_name, pri_skill, emp_gender, emp_birthdate, location, hire_date, job_role, emp_dep, emp_office, emp_pay, img_src = employee
        emp_name = "" + first_name + " " + last_name
        emp_pay = round(emp_pay, 2)
        return render_template('searchemp_output.html',img_src = img_src, emp_id = emp_id, emp_name = emp_name, pri_skill = pri_skill, gender = emp_gender, birth_date = emp_birthdate, loc = location, hire_date = hire_date, job = job_role, dep = emp_dep, office = emp_office, pay = emp_pay)
    else:
        return "No employee found with ID {}".format(emp_id)

@app.route('/manageemp', methods=['GET', 'POST'])
def manage_employee():
        emp_id = request.form['emp_id']
        action = request.form['action']
        if action == 'Update':
            return render_template('updateemp.html', emp_id = emp_id)
        elif action == 'Delete':
            delete_sql = "Delete FROM employee WHERE emp_id = %s"
            cursor = db_conn.cursor()
            try: 
                cursor.execute(delete_sql, emp_id)
                db_conn.commit()
            except Exception as e:
                return str(e)

            finally:
                cursor.close()
            return render_template('delemp_output.html', emp_id = emp_id)

@app.route('/updemp', methods=['GET', 'POST'])
def updemp():
    emp_id = request.form['emp_id']
    info = request.form['choose_info']
    new_val = request.form['new_val']
    update_sql = "UPDATE employee SET " + info + " = %s WHERE emp_id = %s"
    cursor = db_conn.cursor()
    try: 
        cursor.execute(update_sql, (new_val, emp_id))
        db_conn.commit()
    except Exception as e:
        return str(e)

    finally:
        cursor.close()
    return render_template('updateemp_output.html', info = info, value = new_val, emp_id = emp_id)

@app.route('/comp_payroll', methods=['GET', 'POST'])
def comp_payroll():
    emp_id = request.form['emp_id']
    cal_month = request.form['cal_month']
    year, month = cal_month.split('-')
    select_pay_sql = "SELECT emp_pay FROM employee WHERE emp_id = %s"
    salary = 0
    working_hr = 0
    cursor = db_conn.cursor()
    try:
        cursor.execute(select_pay_sql, emp_id)
        employee_pay = cursor.fetchone()
        select_attend_sql = "SELECT ROUND(TIME_TO_SEC(TIMEDIFF(clock_out_time, clock_in_time)) / 3600) AS working_hr FROM employee_attendance WHERE emp_id = %s AND EXTRACT(YEAR FROM attendance_date) = %s AND EXTRACT(MONTH FROM attendance_date) = %s"
        select_sales_sql = "SELECT sum(amount) AS sales FROM employee_sales WHERE emp_id = %s AND EXTRACT(YEAR FROM sales_date) = %s AND EXTRACT(MONTH FROM sales_date) = %s"
        cursor.execute(select_attend_sql, (emp_id, year, month))
        days = cursor.fetchall()
        cursor.execute(select_sales_sql, (emp_id, year, month))
        sales = cursor.fetchone()
        for day in days:
            salary += day[0] * employee_pay[0]
            working_hr += day[0]
        salary = round(salary, 2)
        commission = round(sales[0] * Decimal(0.005),2)
        total_salary = round(salary + commission,2)
    except Exception as e:
        return str(e)

    finally:
        cursor.close()
    
    return render_template('payroll_output.html', emp_id = emp_id, cal_month = cal_month, hours = working_hr, salary = salary, sales = sales[0], commission =commission, total_salary = total_salary)

@app.route('/add_sales', methods=['GET', 'POST'])
def add_sales():
    emp_id = request.form['emp_id']
    date = request.form['sales_date']
    amount = request.form['amount']
    insert_sql = "INSERT INTO employee_sales VALUES (%s, %s, %s)"
    cursor = db_conn.cursor()
    try:
        cursor.execute(insert_sql, (emp_id, date, amount))
        db_conn.commit()
    except Exception as e:
        return str(e)
    finally:
        cursor.close()   
    select_sql = "SELECT job_role FROM employee WHERE emp_id = %s"
    select_sql2 = "SELECT sales_date, amount FROM employee_sales WHERE emp_id = %s"
    total_sales = 0
    try:
        cursor = db_conn.cursor()
        cursor.execute(select_sql, emp_id)
        emp_job = cursor.fetchone()
        emp_job = emp_job[0]
        cursor.execute(select_sql2, emp_id)
        sales_rows = cursor.fetchall()
        for sales_row in sales_rows:
            total_sales += sales_row[1]
    except Exception as e:
        return str(e)
    finally:
        cursor.close()
    return render_template('sales_output.html', emp_id = emp_id, job = emp_job, sales_rows = sales_rows, total_sales = total_sales)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)