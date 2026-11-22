# 🏫 SmartClass – Smart Classroom Management System

**A Web-Based Classroom Management and Scheduling Platform**

SmartClass is a web-based application designed to simplify classroom management, improve room utilization, and streamline academic scheduling in colleges and universities.

The platform connects students, teachers, and administrators through dedicated dashboards, providing an organized system for classroom availability, timetable management, rescheduling requests, and in-app notifications.

Developed as a collaborative team project, SmartClass represents our hands-on experience in building a full-stack web application using Python and Flask.

---

## 📌 Table of Contents

- [Project Overview](#-project-overview)
- [Key Features](#-key-features)
- [User Roles](#-user-roles)
- [Technology Stack](#-technology-stack)
- [Application Workflow](#-application-workflow)
- [Project Structure](#-project-structure)
- [Installation and Setup](#-installation-and-setup)
- [How to Run](#-how-to-run)
- [Future Enhancements](#-future-enhancements)
- [Learning Outcomes](#-learning-outcomes)
- [Contributors](#-contributors)

---

## 🚀 Project Overview

Managing classrooms, coordinating schedules, and communicating timetable changes can become challenging in educational institutions.

SmartClass addresses these challenges through a centralized platform where:

- Teachers can check classroom availability and manage their teaching schedules.
- Students can access their class timetables and receive schedule updates.
- Administrators can manage classroom operations and control timetable changes through an approval-based workflow.

The primary objective is to make classroom allocation more efficient, reduce scheduling conflicts, and improve communication across academic departments.

---

## ✨ Key Features

### 👨‍🎓 1. Student Dashboard

- Dedicated student interface and login.
- Access to class timetables.
- View updated classroom and scheduling information.
- Receive in-app notifications when classes are rescheduled.
- View-only access to academic scheduling information.

### 👩‍🏫 2. Teacher Dashboard

- Dedicated teacher interface.
- View personal teaching schedules.
- Search for available classrooms.
- Check classroom seating capacity.
- Filter classrooms based on projector availability.
- Submit class rescheduling requests.
- Track the status of submitted requests.

### 🛡️ 3. Admin Dashboard

- Dedicated administrative interface.
- Review classroom rescheduling requests.
- Approve or reject teacher requests.
- Manage timetable changes through an approval-based workflow.
- Maintain control over official scheduling updates.

### 🔔 4. In-App Notification System

- Notify administrators when teachers submit rescheduling requests.
- Inform teachers about request approval or rejection.
- Notify affected students after an approved timetable change.
- Keep users informed through application-based notifications.

### 📅 5. Classroom Availability Management

- Search for available classrooms based on timetable slots.
- View classroom capacity.
- Identify rooms equipped with projectors.
- Support more organized classroom allocation.

### 🔐 6. Role-Based Access Control

The application provides separate interfaces and permissions for:

- Students
- Teachers
- Administrators

Each role has access to features relevant to its responsibilities.

---

## 🧑‍💻 User Roles

| Role | Responsibilities |
|---|---|
| Student | View personal/section timetable and notifications |
| Teacher | View teaching schedule, search classrooms and request rescheduling |
| Admin | Review requests, approve or reject changes and manage scheduling |

---

## 🔄 Application Workflow

The rescheduling process follows an approval-based workflow to maintain scheduling control.

1. A teacher submits a request to reschedule a class.
2. The administrator receives an in-app notification.
3. The administrator reviews the requested changes.
4. The administrator can approve or reject the request.
5. If approved, the official timetable is updated.
6. The affected teacher and students receive in-app notifications.
7. If rejected, the existing timetable remains unchanged.

This workflow helps prevent unauthorized timetable changes and keeps students informed about approved schedule updates.

---

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| Flask | Web application framework |
| HTML5 | Frontend structure |
| CSS3 | Styling and responsive layouts |
| JavaScript | Frontend interactivity |
| SQLite | Database management |
| Flask-SQLAlchemy | Database integration and ORM |
| Visual Studio Code | Development environment |
| Git & GitHub | Version control and project collaboration |

---

## 📁 Project Structure

The following represents the intended organization of the application. Actual filenames may vary depending on the current implementation.

```text
SmartClass/
│
├── app.py
│
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── student_dashboard.html
│   ├── teacher_dashboard.html
│   └── admin_dashboard.html
│
├── static/
│   ├── style.css
│   ├── script.js
│   └── images/
│
├── instance/
│   └── smartclass.db
│
├── requirements.txt
│
├── .gitignore
│
└── README.md
```

---

## ⚙️ Installation and Setup

Follow these steps to run SmartClass locally.

### Prerequisites

Make sure you have installed:

- Python 3.x
- Visual Studio Code
- Git
- A web browser

### Step 1: Clone the Repository

```bash
git clone https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
```

### Step 2: Navigate to the Project Directory

```bash
cd SmartClass
```

### Step 3: Create a Virtual Environment

**Windows:**

```bash
python -m venv venv
```

### Step 4: Activate the Virtual Environment

```bash
venv\Scripts\activate
```

### Step 5: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 6: Run the Application

```bash
python app.py
```

### Step 7: Open in Browser

Visit:

```text
http://127.0.0.1:5000
```

The application will be accessible locally while the Flask development server is running.

---

## 🔮 Future Enhancements

Potential improvements for future versions include:

- Email notifications for timetable changes.
- Migration to PostgreSQL for larger deployments.
- Performance optimization and load testing.
- Advanced classroom occupancy detection.
- Equipment and maintenance reporting.
- Improved analytics for classroom utilization.
- Production deployment for institution-wide access.

---

## 📚 Learning Outcomes

Working on SmartClass has provided practical exposure to full-stack web development.

Key concepts explored during development include:

- Building web applications using the Flask framework.
- Understanding frontend and backend integration.
- Designing and integrating relational databases.
- Using Flask-SQLAlchemy for database operations.
- Implementing user authentication and role-based access.
- Developing dashboards for different user roles.
- Creating approval-based application workflows.
- Implementing in-app notifications.
- Debugging, testing, and integrating application components.
- Collaborating on a software development project.

This project helped us understand how individual technologies work together to solve a real-world problem.

---

## 👥 Contributors

**SmartClass was developed collaboratively as a team project.**

We worked together to plan, develop, integrate, and improve the application, combining our ideas and technical contributions to build a practical classroom management solution.

**Team Members:**

- [Contributor 1 – GitHub Profile](https://github.com/USERNAME)
- [Contributor 2 – GitHub Profile](https://github.com/USERNAME)
- [Contributor 3 – GitHub Profile](https://github.com/USERNAME)

*Replace the sample names and links with the actual team members.*

---

## 🌟 Project Vision

Our vision is to make academic classroom management more organized, accessible, and efficient through technology.

SmartClass is a step towards building smarter educational environments through practical software solutions.

---

**Built with 💙 by Team SmartClass**

