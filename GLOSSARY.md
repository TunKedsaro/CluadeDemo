# Event Registration

A website where Attendees register to join Events. Admins create Events and manage Registrations.

## Language

**Event**:
A single occurrence (event or course) that people can register to join, with a name, date and time, location and a fixed number of seats.
_Avoid_: Course, class, activity, session

**Attendee**:
A person who registers to join an Event, identified by email.
_Avoid_: User, participant, member, customer

**Registration**:
One Attendee's sign-up for one Event.
_Avoid_: Booking, enrollment, ticket, reservation

**Admin**:
A person who creates Events and views or cancels Registrations.
_Avoid_: Staff, organizer, operator

**Seat**:
One place in an Event; each `confirmed` Registration takes one Seat.
_Avoid_: Slot, spot, quota

**Capacity**:
The total number of Seats an Event offers.
_Avoid_: Limit, max

**Confirmed**:
The status of a Registration that holds a Seat.
_Avoid_: Active, approved

**Cancelled**:
The status of a Registration that has been cancelled by an Admin and no longer holds a Seat.
_Avoid_: Deleted, withdrawn

**Consent**:
An Attendee's agreement, given at registration, to the processing of their personal data.
_Avoid_: Agreement, opt-in
