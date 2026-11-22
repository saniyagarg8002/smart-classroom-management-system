from datetime import datetime, date, time, timedelta
from functools import wraps
import os
import sqlite3

from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "smartclass.db")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SMARTCLASS_SECRET_KEY", "change-this-dev-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + DATABASE_PATH
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ---------------------------------------------------------------------------
# DATABASE MODELS
# ---------------------------------------------------------------------------

class Batch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True, nullable=False)
    course_name = db.Column(db.String(100), nullable=False, default="B.Tech CSE")

    def __repr__(self):
        return self.name


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(160), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="teacher")

    # Used only for the demo student account. In the real system, this value
    # will come from the university's student information system/email identity.
    batch_id = db.Column(db.Integer, db.ForeignKey("batch.id"), nullable=True)
    batch = db.relationship("Batch", backref="students")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_code = db.Column(db.String(30), unique=True, nullable=False)
    building = db.Column(db.String(80), nullable=False)
    floor = db.Column(db.Integer, nullable=False, default=1)
    capacity = db.Column(db.Integer, nullable=False)
    has_projector = db.Column(db.Boolean, nullable=False, default=False)
    active = db.Column(db.Boolean, nullable=False, default=True)


class ClassSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(120), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey("room.id"), nullable=False)
    batch_id = db.Column(db.Integer, db.ForeignKey("batch.id"), nullable=True)
    start_at = db.Column(db.DateTime, nullable=False, index=True)
    end_at = db.Column(db.DateTime, nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default="scheduled")

    teacher = db.relationship("User", backref="classes")
    room = db.relationship("Room", backref="classes")
    batch = db.relationship("Batch", backref="class_sessions")


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    message = db.Column(db.String(300), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    user = db.relationship("User", backref="notifications")


class RescheduleRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    class_session_id = db.Column(
        db.Integer, db.ForeignKey("class_session.id"), nullable=False
    )
    teacher_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    new_room_id = db.Column(db.Integer, db.ForeignKey("room.id"), nullable=False)
    new_start_at = db.Column(db.DateTime, nullable=False)
    new_end_at = db.Column(db.DateTime, nullable=False)
    reason = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pending")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime, nullable=True)

    class_session = db.relationship("ClassSession")
    teacher = db.relationship("User")
    new_room = db.relationship("Room")


# ---------------------------------------------------------------------------
# SAFE SQLITE MIGRATION
# create_all() creates missing tables, but it does not add columns to old
# tables. This migration adds only the two new nullable columns and preserves
# all existing rows and passwords. It never drops or recreates smartclass.db.
# ---------------------------------------------------------------------------

def migrate_existing_database():
    if not os.path.exists(DATABASE_PATH):
        return

    connection = sqlite3.connect(DATABASE_PATH)
    try:
        cursor = connection.cursor()
        table_names = {
            row[0] for row in cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }

        if "user" in table_names:
            user_columns = {
                row[1] for row in cursor.execute("PRAGMA table_info(user)").fetchall()
            }
            if "batch_id" not in user_columns:
                cursor.execute("ALTER TABLE user ADD COLUMN batch_id INTEGER")

        if "class_session" in table_names:
            class_columns = {
                row[1] for row in cursor.execute(
                    "PRAGMA table_info(class_session)"
                ).fetchall()
            }
            if "batch_id" not in class_columns:
                cursor.execute(
                    "ALTER TABLE class_session ADD COLUMN batch_id INTEGER"
                )

        connection.commit()
    finally:
        connection.close()


with app.app_context():
    db.create_all()
    migrate_existing_database()


# ---------------------------------------------------------------------------
# LOGIN, ROLES AND COMMON HELPERS
# ---------------------------------------------------------------------------

def current_user():
    user_id = session.get("user_id")
    return db.session.get(User, user_id) if user_id else None


@app.context_processor
def inject_user():
    user = current_user()
    unread_count = (
        Notification.query.filter_by(user_id=user.id, is_read=False).count()
        if user else 0
    )
    return {"logged_in_user": user, "unread_count": unread_count}


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user():
            flash("Please sign in to continue.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def role_required(*allowed_roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            user = current_user()
            if not user:
                flash("Please sign in to continue.", "warning")
                return redirect(url_for("login"))
            if user.role not in allowed_roles:
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator


def overlaps(start_at, end_at, query):
    # A class ending at 11:00 does not block another starting at 11:00.
    return query.filter(
        ClassSession.start_at < end_at,
        ClassSession.end_at > start_at,
        ClassSession.status == "scheduled"
    )


def room_is_free(room_id, start_at, end_at, exclude_session_id=None):
    query = overlaps(
        start_at, end_at, ClassSession.query.filter_by(room_id=room_id)
    )
    if exclude_session_id:
        query = query.filter(ClassSession.id != exclude_session_id)
    return query.first() is None


def teacher_is_free(teacher_id, start_at, end_at, exclude_session_id=None):
    query = overlaps(
        start_at, end_at, ClassSession.query.filter_by(teacher_id=teacher_id)
    )
    if exclude_session_id:
        query = query.filter(ClassSession.id != exclude_session_id)
    return query.first() is None


def parse_datetime(value):
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M")
    except (TypeError, ValueError):
        return None


def notify(user_id, message):
    db.session.add(Notification(user_id=user_id, message=message))


def get_or_create_batches():
    batches = []
    for letter in "ABCDE":
        name = f"Batch {letter}"
        batch = Batch.query.filter_by(name=name).first()
        if not batch:
            batch = Batch(name=name, course_name="B.Tech CSE")
            db.session.add(batch)
        batches.append(batch)
    db.session.flush()
    return batches


def home_for_user(user):
    if user.role == "student":
        return url_for("student_dashboard")
    if user.role == "admin":
        return url_for("admin_dashboard")
    return url_for("dashboard")


# ---------------------------------------------------------------------------
# MAIN ROUTES
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    user = current_user()
    return redirect(home_for_user(user)) if user else redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user():
        return redirect(home_for_user(current_user()))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            session.clear()
            session["user_id"] = user.id
            flash(f"Welcome, {user.name}.", "success")
            return redirect(home_for_user(user))

        flash("Email or password is incorrect.", "danger")

    return render_template("login.html")


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
@role_required("teacher")
def dashboard():
    user = current_user()
    today = date.today()
    day_start = datetime.combine(today, time.min)
    day_end = datetime.combine(today, time.max)

    todays_classes = ClassSession.query.filter(
        ClassSession.teacher_id == user.id,
        ClassSession.start_at >= day_start,
        ClassSession.start_at <= day_end,
        ClassSession.status == "scheduled"
    ).order_by(ClassSession.start_at).all()

    rooms = Room.query.filter_by(active=True).all()
    now = datetime.now()
    free_now = sum(
        1 for room in rooms
        if room_is_free(room.id, now, now + timedelta(minutes=1))
    )

    recent_notifications = Notification.query.filter_by(
        user_id=user.id
    ).order_by(Notification.created_at.desc()).limit(5).all()

    return render_template(
        "dashboard.html",
        todays_classes=todays_classes,
        rooms_count=len(rooms),
        free_now=free_now,
        recent_notifications=recent_notifications
    )


@app.route("/student-dashboard")
@login_required
@role_required("student")
def student_dashboard():
    user = current_user()
    today = date.today()
    start_at = datetime.combine(today, time.min)
    end_at = datetime.combine(today, time.max)

    # Demo account has a sample batch linked to it. Students do not select
    # or edit their batch from the interface.
    if not user.batch_id:
        classes = []
        batch_name = "Batch not linked"
    else:
        classes = ClassSession.query.filter(
            ClassSession.batch_id == user.batch_id,
            ClassSession.start_at >= start_at,
            ClassSession.start_at <= end_at,
            ClassSession.status == "scheduled"
        ).order_by(ClassSession.start_at).all()
        batch_name = user.batch.name if user.batch else "Assigned batch"

    notifications = Notification.query.filter_by(
        user_id=user.id
    ).order_by(Notification.created_at.desc()).limit(5).all()

    return render_template(
        "student_dashboard.html",
        classes=classes,
        batch_name=batch_name,
        selected_date=today.isoformat(),
        notifications=notifications
    )


@app.route("/admin")
@login_required
@role_required("admin")
def admin_dashboard():
    pending_requests = RescheduleRequest.query.filter_by(
        status="pending"
    ).order_by(RescheduleRequest.created_at.asc()).all()
    batches = Batch.query.order_by(Batch.name).all()
    return render_template(
        "admin_dashboard.html",
        pending_requests=pending_requests,
        batches=batches
    )


@app.route("/rooms")
@login_required
def rooms():
    day_value = request.args.get("date", date.today().isoformat())
    start_value = request.args.get("start", "10:00")
    end_value = request.args.get("end", "11:00")
    seats_value = request.args.get("seats", "1")
    projector_value = request.args.get("projector", "any")
    building_value = request.args.get("building", "any")

    start_at = parse_datetime(f"{day_value}T{start_value}")
    end_at = parse_datetime(f"{day_value}T{end_value}")
    errors = []
    matches = []

    if not start_at or not end_at or end_at <= start_at:
        errors.append("Choose a valid date and an end time later than the start time.")

    try:
        seats = max(1, int(seats_value))
    except (TypeError, ValueError):
        seats = 1
        errors.append("Seat count must be a number.")

    if not errors:
        query = Room.query.filter_by(active=True).filter(Room.capacity >= seats)
        if projector_value == "yes":
            query = query.filter_by(has_projector=True)
        elif projector_value == "no":
            query = query.filter_by(has_projector=False)
        if building_value != "any":
            query = query.filter_by(building=building_value)

        for room in query.order_by(Room.building, Room.room_code).all():
            if room_is_free(room.id, start_at, end_at):
                matches.append(room)

    buildings = [
        row[0] for row in db.session.query(Room.building).distinct()
        .order_by(Room.building).all()
    ]

    return render_template(
        "rooms.html",
        matches=matches,
        errors=errors,
        buildings=buildings,
        selected_date=day_value,
        selected_start=start_value,
        selected_end=end_value,
        selected_seats=seats_value,
        selected_projector=projector_value,
        selected_building=building_value
    )


@app.route("/timetable")
@login_required
def timetable():
    user = current_user()
    date_value = request.args.get("date", date.today().isoformat())

    try:
        chosen_date = date.fromisoformat(date_value)
    except ValueError:
        chosen_date = date.today()
        date_value = chosen_date.isoformat()

    start_at = datetime.combine(chosen_date, time.min)
    end_at = datetime.combine(chosen_date, time.max)

    query = ClassSession.query.filter(
        ClassSession.start_at >= start_at,
        ClassSession.start_at <= end_at,
        ClassSession.status == "scheduled"
    )

    if user.role == "student":
        if not user.batch_id:
            classes = []
        else:
            classes = query.filter(
                ClassSession.batch_id == user.batch_id
            ).order_by(ClassSession.start_at).all()
    elif user.role == "teacher":
        classes = query.filter(
            ClassSession.teacher_id == user.id
        ).order_by(ClassSession.start_at).all()
    elif user.role == "admin":
        classes = query.order_by(ClassSession.start_at).all()
    else:
        abort(403)

    return render_template(
        "timetable.html",
        classes=classes,
        selected_date=date_value
    )


# ---------------------------------------------------------------------------
# TEACHER RESCHEDULE REQUESTS
# ---------------------------------------------------------------------------

@app.route("/reschedule/<int:session_id>", methods=["GET", "POST"])
@login_required
@role_required("teacher")
def reschedule(session_id):
    class_session = db.get_or_404(ClassSession, session_id)
    user = current_user()

    if class_session.teacher_id != user.id:
        abort(403)

    if request.method == "POST":
        new_start = parse_datetime(request.form.get("start_at"))
        new_end = parse_datetime(request.form.get("end_at"))
        reason = request.form.get("reason", "").strip()

        try:
            new_room_id = int(request.form.get("room_id", ""))
        except (TypeError, ValueError):
            new_room_id = 0

        new_room = db.session.get(Room, new_room_id)

        if not new_start or not new_end or new_end <= new_start:
            flash("Choose a valid start and end time.", "danger")
        elif not reason:
            flash("Please provide a reason for the reschedule request.", "danger")
        elif not new_room or not new_room.active:
            flash("Select a valid active classroom.", "danger")
        elif not room_is_free(new_room.id, new_start, new_end, class_session.id):
            flash("That classroom is already booked for the selected time.", "danger")
        elif not teacher_is_free(user.id, new_start, new_end, class_session.id):
            flash("You already have another class during that time.", "danger")
        else:
            existing_pending = RescheduleRequest.query.filter_by(
                class_session_id=class_session.id,
                status="pending"
            ).first()

            if existing_pending:
                flash("A reschedule request for this class is already pending.", "warning")
            else:
                new_request = RescheduleRequest(
                    class_session_id=class_session.id,
                    teacher_id=user.id,
                    new_room_id=new_room.id,
                    new_start_at=new_start,
                    new_end_at=new_end,
                    reason=reason
                )
                db.session.add(new_request)
                notify(
                    user.id,
                    f"Your reschedule request for '{class_session.subject}' has been sent to the administrator."
                )
                db.session.commit()
                flash("Reschedule request submitted. The timetable will change only after admin approval.", "success")
                return redirect(url_for("timetable"))

    rooms_list = Room.query.filter_by(active=True).order_by(Room.room_code).all()
    return render_template(
        "reschedule.html",
        class_session=class_session,
        rooms=rooms_list
    )


@app.route("/admin/reschedule/<int:request_id>/<decision>", methods=["POST"])
@login_required
@role_required("admin")
def review_reschedule(request_id, decision):
    if decision not in ("approve", "reject"):
        abort(404)

    reschedule_request = db.get_or_404(RescheduleRequest, request_id)

    if reschedule_request.status != "pending":
        flash("This request has already been reviewed.", "warning")
        return redirect(url_for("admin_dashboard"))

    class_session = reschedule_request.class_session
    teacher = reschedule_request.teacher
    new_room = reschedule_request.new_room

    if decision == "reject":
        reschedule_request.status = "rejected"
        reschedule_request.reviewed_at = datetime.utcnow()
        notify(
            teacher.id,
            f"Your reschedule request for '{class_session.subject}' was rejected. The original timetable remains unchanged."
        )
        db.session.commit()
        flash("Reschedule request rejected.", "info")
        return redirect(url_for("admin_dashboard"))

    # Re-check conflicts at approval time because the room/teacher schedule
    # may have changed after the teacher submitted the request.
    if not new_room or not new_room.active:
        conflict_message = "The requested classroom is no longer available."
    elif not room_is_free(
        new_room.id,
        reschedule_request.new_start_at,
        reschedule_request.new_end_at,
        class_session.id
    ):
        conflict_message = "The requested classroom now has a scheduling conflict."
    elif not teacher_is_free(
        teacher.id,
        reschedule_request.new_start_at,
        reschedule_request.new_end_at,
        class_session.id
    ):
        conflict_message = "The teacher now has another class during the requested time."
    else:
        conflict_message = None

    reschedule_request.reviewed_at = datetime.utcnow()

    if conflict_message:
        reschedule_request.status = "rejected"
        notify(
            teacher.id,
            f"Your reschedule request for '{class_session.subject}' could not be approved: {conflict_message} The original timetable remains unchanged."
        )
        db.session.commit()
        flash(conflict_message + " The request was rejected; the original timetable is unchanged.", "danger")
        return redirect(url_for("admin_dashboard"))

    class_session.room_id = new_room.id
    class_session.start_at = reschedule_request.new_start_at
    class_session.end_at = reschedule_request.new_end_at
    reschedule_request.status = "approved"

    notify(
        teacher.id,
        f"Your reschedule request for '{class_session.subject}' was approved. New time: {class_session.start_at:%d %b, %H:%M}; room: {new_room.room_code}."
    )
    db.session.commit()
    flash("Request approved and timetable updated.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/notifications")
@login_required
def notifications():
    user = current_user()
    items = Notification.query.filter_by(
        user_id=user.id
    ).order_by(Notification.created_at.desc()).all()

    for item in items:
        item.is_read = True
    db.session.commit()

    return render_template("notifications.html", items=items)


# ---------------------------------------------------------------------------
# DEMO DATA
# ---------------------------------------------------------------------------

@app.route("/seed-demo")
def seed_demo():
    # Development/demo helper only. Do not expose publicly in production.
    batches = get_or_create_batches()

    teacher1 = User.query.filter_by(email="teacher@smartclass.local").first()
    if not teacher1:
        teacher1 = User(
            name="Saniya Garg",
            email="teacher@smartclass.local",
            role="teacher"
        )
        teacher1.set_password("Teacher123!")
        db.session.add(teacher1)

    teacher2 = User.query.filter_by(email="teacher2@smartclass.local").first()
    if not teacher2:
        teacher2 = User(
            name="Demo Teacher",
            email="teacher2@smartclass.local",
            role="teacher"
        )
        teacher2.set_password("Teacher123!")
        db.session.add(teacher2)

    admin = User.query.filter_by(email="admin@smartclass.local").first()
    if not admin:
        admin = User(
            name="Demo Administrator",
            email="admin@smartclass.local",
            role="admin"
        )
        admin.set_password("Admin123!")
        db.session.add(admin)

    student = User.query.filter_by(email="student@smartclass.local").first()
    if not student:
        student = User(
            name="Demo Student",
            email="student@smartclass.local",
            role="student",
            batch=batches[2]  # Sample demo student: Batch C.
        )
        student.set_password("Student123!")
        db.session.add(student)
    elif student.role == "student" and not student.batch_id:
        # Only provide a sample batch if this demo account has no batch yet.
        # Never overwrite an existing assigned batch.
        student.batch = batches[2]

    db.session.flush()

    room_data = [
        ("C-201", "Block C", 2, 60, True),
        ("C-204", "Block C", 2, 40, False),
        ("B-105", "Block B", 1, 80, True),
        ("A-302", "Block A", 3, 35, True),
        ("B-210", "Block B", 2, 55, True),
        ("A-101", "Block A", 1, 30, False),
    ]

    room_objects = []
    for code, building, floor, capacity, projector in room_data:
        room = Room.query.filter_by(room_code=code).first()
        if not room:
            room = Room(
                room_code=code,
                building=building,
                floor=floor,
                capacity=capacity,
                has_projector=projector
            )
            db.session.add(room)
        room_objects.append(room)

    db.session.flush()

    # Preserve existing classes. Legacy classes without a batch are linked
    # to Batch A as sample data; no existing class is deleted or rescheduled.
    for old_class in ClassSession.query.filter_by(batch_id=None).all():
        old_class.batch_id = batches[0].id

    # Add sample classes only for batches that do not already have a timetable.
    # Each batch gets its own sample day, preventing clashes with existing demo
    # classes while still allowing the user to inspect all five batch schedules.
    today = date.today()
    subjects = [
        "Data Structures",
        "Database Systems",
        "Web Development",
        "Computer Networks"
    ]
    for index, batch in enumerate(batches):
        if ClassSession.query.filter_by(batch_id=batch.id).count() > 0:
            continue

        sample_day = today + timedelta(days=index)
        teachers = [teacher1, teacher2, teacher1, teacher2]
        for lesson_index, subject in enumerate(subjects):
            start_hour = 9 + lesson_index * 2
            room = room_objects[(index + lesson_index) % len(room_objects)]
            class_item = ClassSession(
                subject=subject,
                teacher=teachers[lesson_index],
                room=room,
                batch=batch,
                start_at=datetime.combine(sample_day, time(start_hour, 0)),
                end_at=datetime.combine(sample_day, time(start_hour + 1, 0))
            )
            db.session.add(class_item)

    if not Notification.query.filter_by(
        user_id=teacher1.id,
        message="Welcome to SmartClass. This is a demo notification."
    ).first():
        db.session.add(Notification(
            user_id=teacher1.id,
            message="Welcome to SmartClass. This is a demo notification."
        ))

    db.session.commit()

    return """
    <h2>SmartClass demo data is ready.</h2>
    <p>Teacher: teacher@smartclass.local / Teacher123!</p>
    <p>Second teacher: teacher2@smartclass.local / Teacher123!</p>
    <p>Admin: admin@smartclass.local / Admin123!</p>
    <p>Student: student@smartclass.local / Student123! (sample Batch C)</p>
    <p>Five B.Tech CSE batches have been prepared. Sample timetables use different dates.</p>
    <p><strong>Existing users and existing class records are preserved.</strong></p>
    <p><a href="/login">Go to Login</a></p>
    """


@app.errorhandler(403)
def forbidden(_error):
    return render_template(
        "error.html",
        code=403,
        message="You do not have permission to access this page."
    ), 403


@app.errorhandler(404)
def not_found(_error):
    return render_template(
        "error.html",
        code=404,
        message="The page or class was not found."
    ), 404


if __name__ == "__main__":
    app.run(debug=True)
