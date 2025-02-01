from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mail import Mail, Message
import pickle
import pathlib

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'

# ------------------------------------------------------------------------------------- #

app.config['MAIL_SERVER'] = 'smtp.gmail.com'          # SMTP server for Gmail
app.config['MAIL_PORT'] = 587                        # Port for TLS
app.config['MAIL_USE_TLS'] = True                    # Enable TLS encryption
app.config['MAIL_USE_SSL'] = False                   # Do not use SSL
app.config['MAIL_USERNAME'] = 'vaibhavgupta5262@gmail.com' # Your email address
app.config['MAIL_PASSWORD'] = 'vaibhav@8851112737'        # Your email password
app.config['MAIL_DEFAULT_SENDER'] = 'vaibhavgupta5262@gmail.com' # Default sender address

mail = Mail(app)

# ------------------------------------------------------------------------------------- #

# Define the email notification function
def send_confirmation_email(user_email, event_name, ticket_reference):
    msg = Message(
        'Ticket Booking Confirmation',
        recipients=[user_email]
    )
    msg.body = f'You have successfully booked a ticket for {event_name}! Your ticket reference number is {ticket_reference}.'
    try:
        mail.send(msg)
        print(f"Email sent to {user_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")


# ------------------------------------------------------------------------------------- #

# Ticket Class
class Ticket:
    reference = 200000

    @classmethod
    def get_next_reference(cls):
        cls.reference += 1
        return cls.reference

    def __init__(self):
        self.name = ''
        self.email = ''
        self.event = ''
        self.reference = Ticket.get_next_reference()

    def check(self):
        """Check if the customer has already booked a ticket for the same event."""
        file = pathlib.Path("tickets.data")
        if file.exists():
            with open('tickets.data', 'rb') as infile:
                ticketdetails = pickle.load(infile)
            for ticket in ticketdetails:
                if ticket.email == self.email and ticket.event == self.event:
                    return True
        return False

    def gettotalticketcount(self):
        """Get the total number of seats available for the selected event."""
        file = pathlib.Path("events.data")
        if file.exists():
            with open('events.data', 'rb') as infile:
                eventdetails = pickle.load(infile)
            for event in eventdetails:
                if event.eventcode == self.event:
                    return int(event.eventTotalAvaibleSeat)
        return 0

    def getBookedSeatCount(self):
        """Get the number of booked seats for the selected event."""
        file = pathlib.Path("tickets.data")
        counter = 0
        if file.exists():
            with open('tickets.data', 'rb') as infile:
                ticketdetails = pickle.load(infile)
            for ticket in ticketdetails:
                if ticket.event == self.event:
                    counter += 1
        return counter

# Event Class
class Event:
    def __init__(self):
        self.eventname = ''
        self.eventcode = ''
        self.eventTotalAvaibleSeat = 10

# ------------------------------------------------------------------------------------- #

# Save Ticket Details to File
def saveTicketDetiails(ticket):
    file = pathlib.Path("tickets.data")
    oldlist = []
    if file.exists():
        with open('tickets.data', 'rb') as infile:
            oldlist = pickle.load(infile)
    oldlist.append(ticket)
    with open('tickets.data', 'wb') as outfile:
        pickle.dump(oldlist, outfile)

# Save Event Details to File
def saveEventDetails(event):
    file = pathlib.Path("events.data")
    oldlist = []
    if file.exists():
        with open('events.data', 'rb') as infile:
            oldlist = pickle.load(infile)
    oldlist.append(event)
    with open('events.data', 'wb') as outfile:
        pickle.dump(oldlist, outfile)

# ------------------------------------------------------------------------------------- #

# Flask Routes

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/view_events')
def view_events():
    file = pathlib.Path("events.data")
    events = []
    if file.exists():
        with open('events.data', 'rb') as infile:
            events = pickle.load(infile)
    return render_template('view_events.html', events=events)

@app.route('/create_event', methods=['GET', 'POST'])
def create_event():
    if request.method == 'POST':
        eventname = request.form['eventname']
        eventcode = request.form['eventcode']
        eventseats = request.form['eventseats']

        event = Event()
        event.eventname = eventname
        event.eventcode = eventcode
        event.eventTotalAvaibleSeat = eventseats
        saveEventDetails(event)
        return redirect(url_for('view_events'))
    return render_template('create_event.html')

@app.route('/book_ticket', methods=['GET', 'POST'])
def book_ticket():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        event_code = request.form['event_code']

        ticket = Ticket()
        ticket.name = name
        ticket.email = email
        ticket.event = event_code

        if ticket.check():
            return "Warning: You Already Booked a Seat!"
        elif ticket.getBookedSeatCount() >= ticket.gettotalticketcount():
            return "Warning: All Tickets are Sold Out!"
        else:
            saveTicketDetiails(ticket)
             # Send confirmation email
            send_confirmation_email(email, ticket.event, ticket.reference)
            flash("Ticket booked successfully! A confirmation email has been sent to your email address.", "success")
            return redirect(url_for('book_ticket'))
    file = pathlib.Path("events.data")
    events = []
    if file.exists():
        with open('events.data', 'rb') as infile:
            events = pickle.load(infile)
    return render_template('book_ticket.html', events=events)


@app.route('/view_tickets')
def view_tickets():
    file = pathlib.Path("tickets.data")
    tickets = []
    events = []
    
    # Load events to check for existing events
    if pathlib.Path("events.data").exists():
        with open('events.data', 'rb') as infile:
            events = pickle.load(infile)
    
    # Load tickets and filter them based on valid events
    if file.exists():
        with open('tickets.data', 'rb') as infile:
            tickets = pickle.load(infile)
    
    # Remove tickets that belong to deleted events
    valid_event_codes = {event.eventcode for event in events}
    tickets = [ticket for ticket in tickets if ticket.event in valid_event_codes]
    
    return render_template('view_tickets.html', tickets=tickets)


# ------------------------------------------------------------------------------------- #

@app.route('/delete_event/<event_code>', methods=['GET'])
def delete_event(event_code):
    file = pathlib.Path("events.data")
    events = []
    if file.exists():
        with open('events.data', 'rb') as infile:
            events = pickle.load(infile)

    # Find event by event_code and remove it
    event_to_delete = None
    for event in events:
        if event.eventcode == event_code:
            event_to_delete = event
            break

    if event_to_delete:
        events.remove(event_to_delete)  # Remove the event

        # Now, remove tickets for this event
        file = pathlib.Path("tickets.data")
        tickets = []
        if file.exists():
            with open('tickets.data', 'rb') as infile:
                tickets = pickle.load(infile)

        # Remove tickets related to the deleted event
        tickets = [ticket for ticket in tickets if ticket.event != event_code]

        # Save updated event and ticket data
        with open('events.data', 'wb') as outfile:
            pickle.dump(events, outfile)
        with open('tickets.data', 'wb') as outfile:
            pickle.dump(tickets, outfile)

        flash('Event and related tickets deleted successfully!', 'success')
    else:
        flash('Event not found!', 'danger')

    return redirect('/view_events')


# ------------------------------------------------------------------------------------- #

@app.route('/about')
def about():
    return render_template('about.html')
 
# ------------------------------------------------------------------------------------- #

@app.route('/help')
def help():
    return render_template('help.html')

# ------------------------------------------------------------------------------------- #

if __name__ == '__main__':
    app.run(debug=True)

# ------------------------------------------------------------------------------------- #