# Cinemetrics - Movie Chain Database Management System

## 📌 Project Description
Cinemetrics is a comprehensive database management system designed for a movie theater chain. It centralizes core operational data including movies, theaters, screening schedules, staff assignments, customer transactions, and concession sales.

The project features an **interactive Streamlit dashboard** that connects to a live PostgreSQL database. This interface allows administrators to execute custom SQL queries, analyze theater performance, and visualize trends (such as ticket sales or revenue) through dynamic charts.

## 🚀 Features
* **Interactive Web Dashboard:** A user-friendly interface built with Streamlit for easy database interaction.
* **Custom SQL Query Runner:** Dedicated input section to write and execute raw SQL queries directly against the database.
* **Dynamic Data Visualization:** Instantly generate Bar and Line charts from query results using Plotly to identify trends.
* **Real-time Database Connection:** Connects securely to a cloud-hosted PostgreSQL instance to fetch live data.
* **Comprehensive Schema:** Manages complex relationships between theaters, movies, staff, shifts, and customer transactions.

## 🛠️ Tech Stack
* **Language:** Python 3.x
* **Web Framework:** Streamlit
* **Database:** PostgreSQL
* **Data Analysis:** Pandas
* **Visualization:** Plotly Express
* **Database Adapter:** Psycopg2

## 💾 Database Schema
The system runs on the `cinimetrics` database, containing the following core tables:

### **Movies & Screenings**
* `movies`: Stores movie details (Name, Rating, Production House, Runtime, Release Date).
* `screening_schedule`: Manages showtimes, linking movies to specific screens and times.
* `screen_details` & `screen_registry`: Tracks screen types (e.g., IMAX, Standard), capacities, and their assignments to theaters.

### **Operations & Staff**
* `theatres`: Locations and details of all theaters in the chain.
* `staff_contacts`: Contact information for employees.
* `theatre_staff_id_map`: Maps staff to specific theaters, roles, and salaries.
* `daily_shifts`: Tracks daily work schedules for staff members.

### **Sales & Customers**
* `transactions`: Central table for booking data, including ticket prices, food amounts, and total revenue.
* `customer_contacts` & `customer_id_map`: Stores customer profiles and contact details.
* `food_details`: Records concession items sold per transaction.
* `promotions`: Tracks discount codes applied to transactions.

