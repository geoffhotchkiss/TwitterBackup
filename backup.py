import twython
import MySQLdb
import getpass
import sys


if len(sys.argv) != 5:
	print 'You entered the wrong number of arguements... everything is
	going to break!'

"""Do a whole bunch of database connection stuff"""
db = MySQLdb.connect(host=sys.argv[1], 
					user=sys.argv[2], 
					passwd=sys.argv[3],		
					db=sys.argv[4])
c = db.cursor()

twitter_user = raw_input("Enter your twitter username: ")
twitter_user_password = getpass.getpass("Enter your twitter password: ")

who_to_get = raw_input("Whose tweets do you want: ")

twython_api = twython.core.setup(twitter_user, twitter_user_password)

user = twython_api.showUser(who_to_get)
who_to_get_count = user["statuses_count"]/200
if user["statuses_count"] % 200 != 0:
	who_to_get_count += 1

"""Checks to see if the user already exists in the database by querying for 
   the largest tweet_id."""

c.execute("""SELECT MAX(tweet_id) FROM Tweets WHERE user_id=%s""", 
			(user["id"]))
result = c.fetchone()[0]

c.execute("""SELECT * FROM Users WHERE user_id=%s""", (user["id"]))
other_result = c.fetchone()
max = who_to_get_count
exists = False;
if other_result != None:
	max = 1 # fuck whoever posts > 200 tweets a day
	exists = True;
	print "User already exists"
else:
	c.execute("""INSERT INTO Users (user_id, name, user_name) VALUES 
				 (%s, %s, %s)""", 
				(user["id"],
				user["name"].encode('utf_8'),
				user["screen_name"].encode('utf_8')))

"""Does the adding of everything into the database... whoo!"""
for curr in range(1, max + 1):
	print 'Working on page', curr
	timeline = None
	if exists:
		timeline = twython_api.getUserTimeline(screen_name=who_to_get, 
			count = 200, since_id=result, page=curr)
	else:
		timeline = twython_api.getUserTimeline(screen_name=who_to_get, 
			count = 200, page=curr)
	for status in timeline:
		c.execute("""INSERT INTO Tweets (tweet_id, user_id, text, replyto, 
					date) VALUES (%s, %s, %s, %s, %s)""",
					(status["id"],
					status["user"]["id"],
					status["text"].encode('utf_8'),
					status["in_reply_to_status_id"],
					status["created_at"].encode('utf_8')))

print 'Updating current people'
c.execute("""SELECT user_id FROM Users""")
list_of_ids = c.fetchall()
for id in list_of_ids:
	print twython_api.getRateLimitStatus()
	c.execute("""SELECT MAX(tweet_id) FROM Tweets WHERE user_id=%s""", (id))
	max_tweet_id = c.fetchone()[0]
	c.execute("""SELECT user_name FROM Users WHERE user_id=%s""", (id))
	username = c.fetchone()[0]
	print id, max_tweet_id
	timeline = twython_api.getUserTimeline(screen_name = username, count = 
		200, since_id = max_tweet_id)
	for status in timeline:
		c.execute("""INSERT INTO Tweets (tweet_id, user_id, text, replyto, 
					date) VALUES (%s, %s, %s, %s, %s)""",
					(status["id"],
					status["user"]["id"],
					status["text"].encode('utf_8'),
					status["in_reply_to_status_id"],
					status["created_at"].encode('utf_8')))

print 'All done!'
