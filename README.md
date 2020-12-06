# django_cinema
graduate work

## Cinema site.

login, logout, registration.
In all cases, a regular user, not an admin, should be automatically logged out 5 minutes after the last action of the person who got to the back!
For all actions of any of the options, you need to implement all actions or models to implement the full CRUD through the REST API too!


## Roles - user, admin


### Actions:


### Admin:


Can create a cinema hall in which he must indicate the name of the hall, the size of the hall


Can create sessions that specify the start time, end time, and show dates (February 5 to February 15, 2020, for example), the ticket price for the session.


Can change a room or session if no tickets have been purchased for this room or for this session.


Sessions in the same room cannot overlap.


### User:


He can view the list of sessions for today and in a separate tab for tomorrow, the number of free seats in the hall, buy a ticket / tickets for the session, if the hall has run out of seats, he should receive a corresponding notification.


Can view a list of purchases made by him, and the total amount spent for all time.


Sessions can be sorted by price or start time.


User not logged in, sees the list, can sort it, cannot


According to REST, add the ability to obtain information about all sessions for today, which begin at a certain period of time and / or go in a particular room.
