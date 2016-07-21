from flask import Flask, render_template, request, redirect, url_for,flash, jsonify
app = Flask(__name__)
from flask import session as login_session
import random,string
from sqlalchemy import create_engine,desc,func
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Poll, User, Option, Votes

import httplib2,urllib
import json
from flask import make_response
import requests

##CLIENT_ID = json.loads(open('client_secrets.json','r').read())['web']['client_id']

engine = create_engine('postgres://mjugseuryqvrac:XUnNTExgmDoIYV3Ef1wBnvaPtM@ec2-54-243-201-58.compute-1.amazonaws.com:5432/dc033pbqf9kspd')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route('/')
def main():
    	if 'username' not in login_session:
         	user = None
        else:
            user = session.query(User).filter_by(name = login_session['username']).one()
        poll = session.query(Poll).all()
	return render_template('main.html',USER=user,POLL=poll)


@app.route('/<int:poll_id>/', methods=['GET','POST'])
def option(poll_id):
    	vot = session.query(Votes).filter_by(poll_id = poll_id)
	if request.method == 'GET':
        	if 'username' not in login_session:
        		user = None
	        else:
       			user = session.query(User).filter_by(name = login_session['username']).one()
    		poll = session.query(Poll).filter_by(id = poll_id).one()
		op = session.query(Option).filter_by(poll_id = poll_id)
		return render_template('poll.html', POLL=poll, OP=op, USER=user)
	else:
     		result = json.loads(request.data)
       		op = session.query(Option).filter_by(name = result['Vote'])
		if op.count()==0: ##Meaning custom vote
    			poll = session.query(Poll).filter_by(id = poll_id).one()
               		op = Option(name = result["Vote"],poll_id = poll_id,poll=poll)
                 	session.add(op)
                op = session.query(Option).filter_by(name = result['Vote']).one()
                print(op.name)
                if 'username' not in login_session:
           		newVote = Votes(option_id= op.id, poll_id= poll_id, ip = request.remote_addr)
             		for i in vot:
              			if i.ip == request.remote_addr:
                    			return "You have Already voted"

        	else:
             		user = session.query(User).filter_by(name = login_session['username']).one()
               		for i in vot:
              			if i.user_id == user.id:
                    			return "You have Already voted"
                    	newVote = Votes(user_id= user.id, option_id= op.id, poll_id= poll_id,user=user)
         	session.add(newVote)
         	session.commit()
		return ("you voted for "+ op.name)

@app.route('/<int:poll_id>/data', methods=['POST'])
def optionJSON(poll_id):
    vot = session.query(Votes).filter_by(poll_id = poll_id)
    poll = session.query(Poll).filter_by(id = poll_id).one()
    op = session.query(Option).filter_by(poll_id = poll_id)
    arr = []
    name=[]
    for i in op:
	arr.append(vot.filter_by(option_id = i.id).count())
 	name.append(i.name.encode('ascii','ignore'))
    result = {"value":name, "data":arr}
    return jsonify(result)


@app.route('/myPoll/',methods=['GET','POST'])
def myPoll():
    	if request.method == 'GET':
    		if 'username' not in login_session:
        		return "<html><center><h4>You nedd to login to view yor polls.<br><a href='"+url_for('login')+"'>Login</a></h4></center></html>"
		else:
       			user = session.query(User).filter_by(name = login_session['username']).one()
		poll = session.query(Poll).filter_by(user_id = user.id)
		return render_template('myPoll.html',USER=user,POLL=poll)
 	else:
      		user = session.query(User).filter_by(name = login_session['username']).one()
      		result = json.loads(request.data)
		poll = session.query(Poll).filter_by(id = result["delete"]).one()
  		if poll.user_id != user.id:
        		return ("You don't have acess to delete it")
          	session.delete(poll)
           	session.commit()
            	return ("Deleted")


@app.route('/createPoll/',methods=['GET','POST'])
def create():
    if request.method =='GET':
    	if 'username' not in login_session:
         	user = None
        else:
            user = session.query(User).filter_by(name = login_session['username']).one()

	return render_template('create.html',USER=user)
    else:
        if 'username' not in login_session:
         	flash('Cannot create without login');
         	return 'Login to create'
        else:
		result = json.loads(request.data)
  		user = session.query(User).filter_by(name = login_session['username']).one()
    		print user.name
    		new_poll = Poll(name=result['pollName'],user_id=user.id, user = user)
      		session.add(new_poll)
      		for i in result['option']:
            		new_option = Option(name = i,poll_id = new_poll.id,poll=new_poll)
              		session.add(new_option)
                session.commit()
  		return 'Sucessfully Created the Poll <br> share it via URL'


@app.route('/login/')
def login():
	state = ''.join(random.choice(string.ascii_uppercase+string.digits) for x in xrange(32))
	login_session['state'] = state
	parm = {'client_id':'4fb92ff9a3afec9417a0','redirect_uri':'https://pollit-app.herokuapp.com/gitLogin','scope':'user','state':state}
	url = 'https://github.com/login/oauth/authorize?'
	return redirect(url+urllib.urlencode(parm))

@app.route('/disconnect/')
def disconnect():
	del login_session['access_token']
  	del login_session['provider']
  	del login_session['username']
  	del login_session['picture']
	del login_session['email']
	return redirect(url_for('main'))

@app.route('/gitLogin/')
def gitLogin():
	if request.args['state'] != login_session['state']:
     		return "<html><title>Error</title><h1>Error State does not match</h1>.</html>"
    	print request.args['code']
    	parm = {'client_id':'4fb92ff9a3afec9417a0','client_secret':'Your secret key here','code':request.args['code'],'state':login_session['state']}
	url = 'https://github.com/login/oauth/access_token?'+ urllib.urlencode(parm)
 	h = httplib2.Http()
  	result = h.request(url,'POST')[1]
  	print (result)
  	url = 'https://api.github.com/user?'+result
  	data = h.request(url,'GET')[1]
  	data = json.loads(data)
  	login_session['access_token'] = result
  	login_session['provider'] = 'github'
  	login_session['username'] = data["login"]
  	login_session['picture'] = data['avatar_url']
	login_session['email'] = data['url']
	if (getUserId(login_session['email']) != None):
    		print("Oho")
    		login_session['user_id'] = getUserId(login_session['email'])
    	else:
    		login_session['user_id'] = createUser(login_session)
    	return redirect(url_for('main'))

def createUser(login_session):
	newUser = User(name = login_session['username'], email = login_session['email'], picture = login_session['picture'])
	session.add(newUser)
	session.commit()
	user = session.query(User).filter_by(email = login_session['email']).one()
	return user.id

def getUserInfo(user_id):
	user = session.query(User).filter_by(id = user_id).one()
	return user

def getUserId(user_email):
	try:
		user =  session.query(User).filter_by(email=user_email).one()
		return user.id
	except:
		return None

##if __name__ == '__main__':
app.secret_key = 'super_secret_key'
app.debug = True
##app.run(host = '0.0.0.0', port = 5000)
